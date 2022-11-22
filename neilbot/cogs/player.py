import asyncio
import discord
from discord.ext import commands
import yt_dlp


class Player(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _getVoiceChannel(self, voice_channels):
        # iterate through every voice channel on the server
        for vc in voice_channels:
            # iterate through every member currently connected to the voice channel
            for m in vc.members:
                # check if the member is the bot
                if m == self.bot.user:
                    # set the status so we know the bot was found and stop looking
                    return vc
        return None

    @discord.slash_command(name="join", description="Have NeilBot join your voice channel")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def join_voice(self, ctx):
        # give us 15 minutes instead of 3 seconds to respond
        await ctx.defer(ephemeral=False)

        # check if the member is connected to a voice channel
        if ctx.author.voice and ctx.author.voice.channel:
            # get the voice channel the member is connected to
            channel = ctx.author.voice.channel
            try:
                # attempt to connect to the same voice channel as the member
                await channel.connect()

                await ctx.respond(f"Connected to {channel.name}")
            except discord.ClientException:
                await ctx.respond(f"Already connected to {channel.name}!")
            except (asyncio.TimeoutError, discord.opus.OpusNotLoaded):
                await ctx.respond(f"Unable to connect to {channel.name}, please try again later")
        else:
            await ctx.respond("Please join a voice channel first!")

    @discord.slash_command(name="leave", description="Have NeilBot leave your voice channel")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def leave_voice(self, ctx):
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
            # disconnect the bot in this server
            await server.voice_client.disconnect()
            await ctx.respond(f"Disconnected from {botVoiceChannel.name}")
        else:
            await ctx.respond("Error: not connected to voice channel")

    @discord.slash_command(name="play", description="Play the YouTube video url")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def play_audio(self, ctx, url):
		# setup options for YouTube downloader
        YDL_OPTIONS = {
            'format': 'bestaudio',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': 'song.%(ext)s',
        }

        # give us 15 minutes instead of 3 seconds to respond
        await ctx.defer(ephemeral=False)

        # get the server
        server = ctx.guild
        # get all voice channels on the server
        voice_channels = server.voice_channels

        # the voice channel we found the bot in
        botVoiceChannel = await self._getVoiceChannel(voice_channels)

		# only play music if the bot is in a voice channel
        if botVoiceChannel:
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
				# download the song from the url
                ydl.download(url)
			# get the server voice client
            voice_client = discord.utils.get(
                self.bot.voice_clients, guild=server)
			# check if a song is already playing
            if not voice_client.is_playing():
				# play the downloaded song
                voice_client.play(discord.FFmpegPCMAudio("song.mp3"))
                await ctx.respond(f"Now playing {url}")
            else:
                await ctx.respond("Already playing song")
        else:
            ctx.respond("Bot not in a voice channel!")


def setup(bot):
    bot.add_cog(Player(bot))
