import discord
from discord.ext import commands
import yt_dlp

class Player(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

def setup(bot):
	bot.add_cog(Player(bot))