import asyncio
from typing import Any, cast

import aiohttp
import discord
import validators
import yt_dlp
from discord import FFmpegPCMAudio
from discord.ext import commands


class Player(commands.Cog):
    """Discord Bot cog that includes slash commands for playing audio.

    Attributes:
        bot (discord.Bot): the instance of the Discord bot this cog is added to
    """

    def __init__(self, bot: discord.Bot):
        """Inits the Player cog.

        Args:
            bot (discord.Bot): the Discord bot this cog is being added to
        """
        self.bot = bot

        # setup options for YouTube downloader
        self.YDL_OPTIONS = {
            "format": "bestaudio",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "outtmpl": "song.%(ext)s",
        }

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

    async def _validYouTubeVideo(self, url: str) -> bool:
        """Checks whether a YouTube URL loads to a valid YouTube video.

        Assumes that url is a valid url to the YouTube website.

        Args:
            url (str): A valid url to YouTube.com

        Returns:
            bool: whether or not the url leads to a valid YouTube video.
        """
        # start an aiohttp client session
        async with aiohttp.ClientSession() as session:
            # send a get request to the url
            async with session.get(url) as resp:
                # check if response is OK
                if resp.status == 200:
                    # read the response stream
                    content = await resp.text()
                    return "Video unavailable" not in content
        return False

    async def _downloadFromYouTube(self, url_or_search: str) -> dict[str, Any] | None:
        """Takes either a YouTube video url or a search query and downloads the video.

        If a search query is given, the first result is downloaded. If no video is
        found, then None is returned.

        Args:
            url_or_search (str): A YouTube url or search query

        Returns:
            dict[str, Any] | None: A dictionary with information about the video.
            If no video was found, then None is returned.
        """
        video: dict[str, Any] | None = None

        with yt_dlp.YoutubeDL(self.YDL_OPTIONS) as ydl:
            if validators.url(url_or_search):
                # url is valid, need to check if url is valid YouTube video still
                if (
                    "youtube.com" in url_or_search.lower()
                    and await self._validYouTubeVideo(url_or_search)
                ):
                    # we can download the video
                    video = ydl.extract_info(url_or_search, download=False)
                # if it is a url but not a valid video, do not attempt to download
            else:
                # url_or_search is a search query
                search_results = ydl.sanitize_info(
                    ydl.extract_info(f"ytsearch:{url_or_search}", download=False)
                )["entries"]
                # if search query returned results
                if search_results:
                    video = search_results[0]
            # if we found a matching video, then download it
            if video:
                ydl.download(video["webpage_url"])
        return video

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

        # get the server
        server = ctx.guild
        # get all voice channels on the server
        voice_channels = server.voice_channels

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
            await ctx.respond(f"Disconnected from {botVoiceChannel.name}")
        else:
            await ctx.respond("Error: not connected to voice channel")

    @discord.slash_command(
        name="play", description="Play the YouTube video url or first search result"
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def play_audio(
        self, ctx: discord.ApplicationContext, url_or_search: str
    ) -> None:
        """Play audio from YouTube from either a URL or a search query.

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

        # only play music if the bot is in or was able to join a voice channel
        if botVoiceChannel:
            video = await self._downloadFromYouTube(url_or_search)
            if video:
                # get the server voice client
                voice_client = self._getVoiceClient(server)
                # check if a song is already playing
                if voice_client and not voice_client.is_playing():
                    # play the downloaded song
                    voice_client.play(FFmpegPCMAudio("song.mp3"))
                    await ctx.respond(f"Now playing **{video['title']}**")
                else:
                    await ctx.respond("Already playing song")
            else:
                await ctx.respond("Error: unable to find any matching videos")

    @discord.slash_command(name="stop", description="Stop the currently playing audio")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def stop_audio(self, ctx: discord.ApplicationContext) -> None:
        """Stop any audio currently playing from the bot.

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

        # only stop the music if the bot is in a voice channel
        if botVoiceChannel:
            # get the server voice client
            voice_client = self._getVoiceClient(server)
            # check if a song is playing
            if voice_client and voice_client.is_playing():
                # stop the audio
                voice_client.stop()
                await ctx.respond("Stopped playing audio")
            else:
                await ctx.respond("Error: no audio is playing")
        else:
            await ctx.respond("Bot not in a voice channel!")

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


def setup(bot: discord.Bot) -> None:
    """Attach the Player cog to a Discord bot.

    Args:
        bot (discord.Bot): the Discord bot to add the Player cog to
    """
    bot.add_cog(Player(bot))
