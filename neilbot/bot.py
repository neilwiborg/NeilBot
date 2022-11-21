import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
token = str(os.getenv("TOKEN"))

activity = discord.Game(name = "Leetcode")
allowed_mentions = discord.AllowedMentions.all()
intents = discord.Intents(guilds = True, members = True)
bot = discord.Bot(activity = activity, allowed_mentions = allowed_mentions, intents = intents)

# load all cogs into the bot
for filename in os.listdir("./neilbot/cogs"):
    if filename.endswith(".py"):
        # remove the extension from the name
        bot.load_extension(f"cogs.{filename[:-3]}")

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")

@bot.event
async def on_application_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.respond("This command is currently on cooldown!")
    else:
        raise error

bot.run(token)
