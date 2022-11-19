import os
import discord
from dotenv import load_dotenv

load_dotenv()
token = str(os.getenv("TOKEN"))
bot = discord.Bot()



bot.run(token)
