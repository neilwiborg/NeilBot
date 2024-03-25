import asyncio
import logging
import threading
from collections import defaultdict, deque
from typing import cast

import discord
from discord import FFmpegPCMAudio
from discord.ext import commands

from neilbot.cogs._downloader import Downloader
from neilbot.cogs._playerButtons import PlayerButtons
from neilbot.cogs._youtubeDownloader import YouTubeDownloader
from neilbot.neilbot import NeilBot


class Player(commands.Cog):
    """Discord Bot cog that includes slash commands for playing audio.

    Attributes:
        bot (NeilBot): the instance of the Discord bot this cog is added to
    """

    def __init__(self, bot: NeilBot):
        """Inits the Player cog.

        Args:
            bot (NeilBot): the Discord bot this cog is being added to
        """
        self.bot = bot

        # configure logging for warnings and errors
        logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.WARN)

        # maps a server id to a queue containing song downloaders
        self._songQueue: defaultdict[int, deque[Downloader]] = defaultdict(deque)
        # store the current song downloader for each server, or None if no song is
        # playing
        self._currentSongs: defaultdict[int, Downloader | None] = defaultdict(None)
        # mutex lock for modifying the queue and currentSongs
        self._queueLock = threading.Lock()

    async def _getVoiceChannel(
        self, voice_channels: list[discord.VoiceChannel]
    ) -> discord.VoiceChannel | None:
        """Gets the voice channel that the bot is currently in.

        Args:
            voice_channels (list[discord.VoiceChannel]): all voice channels on a server

        Returns:
            discord.VoiceChannel | None: the voice channel the bot is in, or None
            if the bot is not found in a voice channel.
        """
        # iterate through every voice channel on the server
        for vc in voice_channels:
            # iterate through every member currently connected to the voice channel
            for m in vc.members:
                # check if the member is the bot
                if m == self.bot.user:
                    # set the status so we know the bot was found and stop looking
                    return vc
        return None

    def _getVoiceClient(self, server: discord.Guild) -> discord.VoiceClient | None:
        """Gets the voice client for the server.

        Searches the list of voice clients that the bot is connected to,
        and finds the one for the given server.

        Args:
            server (discord.guild): the Discord server the bot is in

        Returns:
            discord.VoiceClient | None: The voice client for the server, or None if
            the bot is not currently connected to a voice client in the server
        """
        # need to cast because the voice_client list uses VoiceProtocol,
        # the super class
        return cast(
            discord.VoiceClient | None,
            discord.utils.get(self.bot.voice_clients, guild=server),
        )

    async def _playSongQueue(
        self,
        ctx: discord.ApplicationContext,
        serverID: int,
        voice_client: discord.VoiceClient,
    ) -> None:
        """Play the songs in the queue.

        Args:
            ctx (discord.ApplicationContext): the Discord application context
            serverID (int): the ID for the server to play audio in
            voice_client (discord.VoiceClient): the voice client for the server to play
            audio in
        """
        song = None
        # obtain a mutex lock because we need to modify the queue and currentSong
        with self._queueLock:
            # reset the currentSong before we start playing a new song
            self._currentSongs[serverID] = None
            # check if there are still songs in the queue
            if self._songQueue[serverID]:
                # set the currently playing song to the next song in the queue,
                # and pop it from the queue
                song = self._songQueue[serverID].popleft()
                # add the song to the dictionary for later use
                self._currentSongs[serverID] = song
        # check if song is still None
        if song:
            # download the song from YouTube to play it
            file = await song.downloadSong()

            with self._queueLock:
                # if the current song has not been skipped while downloading
                if self._currentSongs[serverID] == song:
                    # get the async event loop so we can use this method as a callback
                    # to continue playing from the queue after the currentSong ends
                    event_loop = asyncio.get_event_loop()

                    try:
                        # play the downloaded song
                        voice_client.play(
                            FFmpegPCMAudio(file),
                            after=lambda e: (
                                logging.error(e)
                                if e
                                else event_loop.create_task(
                                    self._playSongQueue(ctx, serverID, voice_client)
                                )
                            ),
                        )
                        await ctx.channel.send(
                            content=f"Now playing **{song.getSongName()}**"
                        )
                    except discord.ClientException:
                        # if bot is no longer connected to voice, then don't do anything
                        pass

    @discord.slash_command(name="controls", description="Show music player controls")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def show_controls(self, ctx: discord.ApplicationContext) -> None:
        """Show controls for the music player.

        Args:
            ctx (discord.ApplicationContext): the Discord application context
        """
        # get the server
        server = ctx.guild

        # store the current song for this server
        song = self._currentSongs[server.id]

        songDescription = (
            f"Currently playing **{song.getSongName()}**"
            if song
            else "No song currently playing"
        )
        controlsEmbed = discord.Embed(
            title="Music Player Controls",
            description=songDescription,
        )
        await ctx.respond("Controls:")
        await ctx.channel.send(embed=controlsEmbed, view=self._buttons)

    async def _show_queue_helper(
        self, ctx: discord.ApplicationContext | discord.Interaction
    ) -> str:
        """Helper method for showing the queue contents.

        Args:
            ctx (discord.ApplicationContext | discord.Interaction): the Discord
            application context or interaction

        Returns:
            str: the queue in string form or an error message
        """
        # get the server
        server = ctx.guild

        # obtain a mutex lock so that the queue doesn't change while we are listing
        # the songs
        with self._queueLock:
            # store the songs queued up
            songList = ""
            # store the current song for this server
            song = self._currentSongs[server.id]
            # if a song is currently playing, then display it first
            if song:
                songList += "Currently playing " f"**{song.getSongName()}**\n\n"

            # check if the queue contains songs or is empty
            if self._songQueue[server.id]:
                songList += "Song queue:\n"
                # print each song, using a 1-indexed list
                for i, song in enumerate(self._songQueue[server.id]):
                    # if the song is stored in the list then it will always return the
                    # song name
                    songName = cast(str, song.getSongName())
                    songList += (
                        str(i + 1) + ". " + songName + " [" + song.getSource() + "]"
                        "\n"
                    )
                return songList
            else:
                return "No songs currently in the queue"

    @discord.slash_command(name="queue", description="Show the music queue")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def show_queue(self, ctx: discord.ApplicationContext) -> None:
        """Show all songs currently in the music queue.

        Args:
            ctx (discord.ApplicationContext): the Discord application context
        """
        # give us 15 minutes instead of 3 seconds to respond
        await ctx.defer(ephemeral=False)
        message = await self._show_queue_helper(ctx)
        await ctx.respond(message)

    async def _connect_to_voice(
        self, ctx: discord.ApplicationContext
    ) -> discord.VoiceChannel | None:
        """Connects the bot to the voice channel the user is in.

        If the bot successfully joins a voice channel, a reference to the joined
        channel is returned.

        If the bot is not able to join a voice channel, an error message is sent
        using the application context and None is returned.

        Args:
            ctx (discord.ApplicationContext): the Discord application context

        Returns:
            discord.VoiceChannel | None: The joined channel, or None if the bot was
            unable to connect.
        """
        # check if the member is connected to a voice channel
        if ctx.author.voice and ctx.author.voice.channel:
            # get the voice channel the member is connected to
            channel = ctx.author.voice.channel
            try:
                # attempt to connect to the same voice channel as the member
                await channel.connect()
                return channel

            except discord.ClientException:
                await ctx.respond(f"Already connected to {channel.name}!")
            except (asyncio.TimeoutError, discord.opus.OpusNotLoaded):
                await ctx.respond(
                    f"Unable to connect to {channel.name}, please try again later"
                )
        else:
            await ctx.respond("Please join a voice channel first!")

        return None

    @discord.slash_command(
        name="join", description="Have NeilBot join your voice channel"
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def join_voice(self, ctx: discord.ApplicationContext) -> None:
        """Have the bot join a voice channel.

        Args:
            ctx (discord.ApplicationContext): the Discord application context
        """
        # give us 15 minutes instead of 3 seconds to respond
        await ctx.defer(ephemeral=False)

        channel = await self._connect_to_voice(ctx)
        if channel:
            await ctx.respond(f"Connected to {channel.name}")

    async def _disconnect_from_voice(
        self, ctx: discord.ApplicationContext
    ) -> discord.VoiceChannel | None:
        """Clear the music queue and disconnect the bot from a voice channel.

        Args:
            ctx (discord.ApplicationContext): the Discord application context

        Returns:
            discord.VoiceChannel | None: the channel the bot was disconnected from,
            or None if the bot was not in a voice channel
        """
        # get the server
        server = ctx.guild
        # get all voice channels on the server
        voice_channels = server.voice_channels

        # remove all songs from the queue
        with self._queueLock:
            self._songQueue[server.id].clear()

        # the voice channel we found the bot in
        botVoiceChannel = await self._getVoiceChannel(voice_channels)

        # if we found the bot in a voice channel
        if botVoiceChannel:
            # get the server voice client
            voice_client = self._getVoiceClient(server)
            # check if a song is playing
            if voice_client and voice_client.is_playing():
                # stop the audio
                voice_client.stop()
                # discord won't recognize the audio has stopped unless we wait
                # before disconnecting
                await asyncio.sleep(1)
            # disconnect the bot in this server
            await server.voice_client.disconnect()
            return botVoiceChannel
        else:
            await ctx.respond("Error: not connected to voice channel")
        return None

    @discord.slash_command(
        name="leave", description="Have NeilBot leave your voice channel"
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def leave_voice(self, ctx: discord.ApplicationContext) -> None:
        """Have the bot leave a voice channel.

        Args:
            ctx (discord.ApplicationContext): the Discord application context
        """
        # give us 15 minutes instead of 3 seconds to respond
        await ctx.defer(ephemeral=False)

        channel = await self._disconnect_from_voice(ctx)
        if channel:
            await ctx.respond(f"Disconnected from {channel.name}")

    @discord.slash_command(
        name="play_youtube",
        description="Add the YouTube video url or first search result to the queue",
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def play_youtube_audio(
        self, ctx: discord.ApplicationContext, url_or_search: str
    ) -> None:
        """Add the music from YouTube from either a URL or a search query to the queue.

        If no audio is currently playing, then the song queue starts playing.

        Args:
            ctx (discord.ApplicationContext): the Discord application context
            url_or_search (str): either a YouTube url or a search query
        """
        # give us 15 minutes instead of 3 seconds to respond
        await ctx.defer(ephemeral=False)

        # get the server
        server = ctx.guild
        # get all voice channels on the server
        voice_channels = server.voice_channels

        # the voice channel we found the bot in
        botVoiceChannel = await self._getVoiceChannel(voice_channels)
        # if the bot is not already connected, try to join the voice channel
        if not botVoiceChannel:
            await self._connect_to_voice(ctx)
            botVoiceChannel = await self._getVoiceChannel(voice_channels)

        video: Downloader = YouTubeDownloader()
        await video.validateAndStoreURLOrSearch(url_or_search)
        if video:
            with self._queueLock:
                self._songQueue[server.id].append(video)

            # only play music if the bot is in or was able to join a voice channel
            if botVoiceChannel:
                # get the server voice client
                voice_client = self._getVoiceClient(server)
                # check if a song is already playing
                if voice_client and not voice_client.is_playing():
                    await ctx.respond("Starting to play queue...")
                    await self._playSongQueue(ctx, server.id, voice_client)
                else:
                    await ctx.respond("Song added to queue!")
        else:
            await ctx.respond("Error: unable to find any matching videos")

    async def _skip_audio_helper(
        self, ctx: discord.ApplicationContext | discord.Interaction
    ) -> str:
        """Helper method for skipping audio.

        Args:
            ctx (discord.ApplicationContext | discord.Interaction): the Discord
            application context or interaction

        Returns:
            str: a message describing if the operation was successful or an error
            message
        """
        # get the server
        server = ctx.guild
        # get all voice channels on the server
        voice_channels = server.voice_channels

        # the voice channel we found the bot in
        botVoiceChannel = await self._getVoiceChannel(voice_channels)

        # only play music if the bot is in a voice channel
        if botVoiceChannel:
            message = ""
            # get the server voice client
            voice_client = self._getVoiceClient(server)

            if voice_client:
                # obtain a mutex lock so that the queue doesn't change while we are
                # skipping to the next song
                with self._queueLock:
                    # check to see if the queue contains more songs
                    if self._songQueue[server.id]:
                        message = "Skipping to next song..."
                    else:
                        message = "No songs remaining in queue"
                # stopping the currently playing song will trigger the callback and
                # start the next song in the queue
                voice_client.stop()
            return message

        else:
            return "Bot not in a voice channel!"

    @discord.slash_command(
        name="skip", description="Skip to the next song in the queue"
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def skip_audio(self, ctx: discord.ApplicationContext) -> None:
        """Skip to the next song in the music queue.

        Args:
            ctx (discord.ApplicationContext): the Discord application context
        """
        # give us 15 minutes instead of 3 seconds to respond
        await ctx.defer(ephemeral=False)
        message = await self._skip_audio_helper(ctx)
        await ctx.respond(message)

    async def _stop_audio_helper(
        self, ctx: discord.ApplicationContext | discord.Interaction
    ) -> str:
        """Helper method for stopping audio.

        Args:
            ctx (discord.ApplicationContext | discord.Interaction): the Discord
            application context or interaction

        Returns:
            str: a message describing if the operation was successful or an error
            message
        """
        # get the server
        server = ctx.guild
        # get all voice channels on the server
        voice_channels = server.voice_channels

        # obtain a mutex lock so the queue is not changed elsewhere while it is being
        # cleared
        with self._queueLock:
            # remove all songs from the queue
            self._songQueue[server.id].clear()

        # the voice channel we found the bot in
        botVoiceChannel = await self._getVoiceChannel(voice_channels)

        # only stop the music if the bot is in a voice channel
        if botVoiceChannel:
            # get the server voice client
            voice_client = self._getVoiceClient(server)
            # check if a song is playing
            if voice_client and voice_client.is_playing():
                # stop the audio
                voice_client.stop()
                return "Stopped playing audio"
            else:
                return "Error: no audio is playing"
        else:
            return "Bot not in a voice channel!"

    @discord.slash_command(
        name="stop",
        description="Stop the currently playing audio and clear the music queue",
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def stop_audio(self, ctx: discord.ApplicationContext) -> None:
        """Stop any audio currently playing from the bot and clear the music queue.

        Args:
            ctx (discord.ApplicationContext): the Discord application context
        """
        # give us 15 minutes instead of 3 seconds to respond
        await ctx.defer(ephemeral=False)
        message = await self._stop_audio_helper(ctx)
        await ctx.respond(message)

    async def _toggle_play_pause_audio(
        self, ctx: discord.ApplicationContext | discord.Interaction
    ) -> str:
        """Toggles the audio between paused and resumed.

        Args:
            ctx (discord.ApplicationContext | discord.Interaction): the Discord
            application context or interaction

        Returns:
            str: a message describing if the operation was successful or an error
            message
        """
        # get the server
        server = ctx.guild
        # get all voice channels on the server
        voice_channels = server.voice_channels

        # the voice channel we found the bot in
        botVoiceChannel = await self._getVoiceChannel(voice_channels)

        # only pause the music if the bot is in a voice channel
        if botVoiceChannel:
            # get the server voice client
            voice_client = self._getVoiceClient(server)
            # check if a song is playing
            if voice_client and voice_client.is_playing():
                # pause the audio
                voice_client.pause()
                return "Paused audio. Use /resume to continue playing"
            elif voice_client and voice_client.is_paused():
                voice_client.resume()
                return "Resumed playing audio"
            else:
                return "Error: no audio is playing"
        else:
            return "Bot not in a voice channel!"

    @discord.slash_command(
        name="pause", description="Pause the currently playing audio"
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def pause_audio(self, ctx: discord.ApplicationContext) -> None:
        """Pause any audio currently playing from the bot.

        Args:
            ctx (discord.ApplicationContext): the Discord application context
        """
        # give us 15 minutes instead of 3 seconds to respond
        await ctx.defer(ephemeral=False)

        # get the server
        server = ctx.guild
        # get all voice channels on the server
        voice_channels = server.voice_channels

        # the voice channel we found the bot in
        botVoiceChannel = await self._getVoiceChannel(voice_channels)

        # only pause the music if the bot is in a voice channel
        if botVoiceChannel:
            # get the server voice client
            voice_client = self._getVoiceClient(server)
            # check if a song is playing
            if voice_client and voice_client.is_playing():
                # pause the audio
                voice_client.pause()
                await ctx.respond("Paused audio. Use /resume to continue playing")
            else:
                await ctx.respond("Error: no audio is playing")
        else:
            await ctx.respond("Bot not in a voice channel!")

    @discord.slash_command(name="resume", description="Resume the paused audio")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def resume_audio(self, ctx: discord.ApplicationContext) -> None:
        """Resume playing any audio that has been paused.

        Args:
            ctx (discord.ApplicationContext): the Discord application context
        """
        # give us 15 minutes instead of 3 seconds to respond
        await ctx.defer(ephemeral=False)

        # get the server
        server = ctx.guild
        # get all voice channels on the server
        voice_channels = server.voice_channels

        # the voice channel we found the bot in
        botVoiceChannel = await self._getVoiceChannel(voice_channels)

        # only resume the music if the bot is in a voice channel
        if botVoiceChannel:
            # get the server voice client
            voice_client = self._getVoiceClient(server)
            # check if a song is playing
            if voice_client and not voice_client.is_playing():
                # resume the audio
                voice_client.resume()
                await ctx.respond("Resumed playing audio")
            else:
                await ctx.respond("Error: audio is already playing")
        else:
            await ctx.respond("Bot not in a voice channel!")

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Adds the button view to the bot for music controls."""
        self._buttons = PlayerButtons(
            self._toggle_play_pause_audio,
            self._skip_audio_helper,
            self._show_queue_helper,
            self._stop_audio_helper,
        )

        self.bot.add_view(self._buttons)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        """Checks to see if the bot is alone in a voice channel.

        Runs every time a user's voice state changes, such as when they connect or
        disconnect from a voice channel.

        Args:
            member (discord.Member): The user whose voice state changed
            before (discord.VoiceState): the voice state before the user made a change
            after (discord.VoiceState): the voice state after the user made a change
        """
        # don't need to use the 'after' voice state
        del after

        # check to see if the user was previously connected to a voice channel
        if before.channel:
            server = member.guild
            channel = before.channel
            # check to see if the bot is alone in a voice channel
            if len(channel.members) == 1 and channel.members[0] == self.bot.user:
                voice_client = self._getVoiceClient(server)
                # check if a song is playing
                if voice_client and voice_client.is_playing():
                    # stop the audio
                    voice_client.stop()
                    # discord won't recognize the audio has stopped unless
                    # we wait before disconnecting
                    await asyncio.sleep(1)
                # disconnect the bot in this server
                await server.voice_client.disconnect()


def setup(bot: NeilBot) -> None:
    """Attach the Player cog to a Discord bot.

    Args:
        bot (NeilBot): the Discord bot to add the Player cog to
    """
    bot.add_cog(Player(bot))
