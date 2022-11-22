import asyncio
import discord
from discord.ext import commands
import yt_dlp

class Player(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
	
	@discord.slash_command(name = "join", description = "Have NeilBot join your voice channel")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def join_voice(self, ctx):
		# give us 15 minutes instead of 3 seconds to respond
		await ctx.defer(ephemeral = False)

		if ctx.author.voice and ctx.author.voice.channel:
			channel = ctx.author.voice.channel
			try:
				await channel.connect()

				await ctx.respond(f"Connected to {channel.name}")
			except discord.ClientException:
				await ctx.respond(f"Already connected to {channel.name}!")
			except (asyncio.TimeoutError, discord.opus.OpusNotLoaded):
				await ctx.respond(f"Unable to connect to {channel.name}, please try again later")
		else:
			await ctx.respond("Please join a choice channel first!")
	
	@discord.slash_command(name = "leave", description = "Have NeilBot leave your voice channel")
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def leave_voice(self, ctx):
		# give us 15 minutes instead of 3 seconds to respond
		await ctx.defer(ephemeral = False)

		server = ctx.guild

		voice_channels = server.voice_channels

		foundVoiceChannel = None
		for vc in voice_channels:
			for m in vc.members:
				if m == self.bot.user:
					foundVoiceChannel = vc
					break
		
		if foundVoiceChannel:
			await server.voice_client.disconnect()
			await ctx.respond(f"Disconnected from {foundVoiceChannel.name}")
		else:
			await ctx.respond("Error: not connected to voice channel")	

def setup(bot):
	bot.add_cog(Player(bot))