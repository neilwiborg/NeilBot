import os
import discord
from dotenv import load_dotenv

load_dotenv()
token = str(os.getenv("TOKEN"))
bot = discord.Bot()

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")

@bot.slash_command(name = "hello", description = "Say hello to the bot")
async def hello(ctx):
    await ctx.respond("Hey!")

@bot.slash_command(name = "anyone", description = "Set the anyone target")
async def set_anyone(ctx):
    user = ctx.author
    role = discord.utils.get(ctx.guild.roles, name="anyone")
    await user.add_roles(role)
    await ctx.respond("Set anyone to you!")

bot.run(token)
