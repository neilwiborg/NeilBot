import os
import discord
from dotenv import load_dotenv

load_dotenv()
token = str(os.getenv("TOKEN"))

activity =  discord.Game(name = "Leetcode")
intents = discord.Intents(guilds = True, members = True)
bot = discord.Bot(intents = intents, activity = activity)

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")

@bot.slash_command(name = "hello", description = "Say hello to the bot")
async def hello(ctx):
    await ctx.respond("Hey!")

@bot.slash_command(name = "anyone", description = "Set the anyone target")
async def set_anyone(ctx):
    # get the caller
    member = ctx.author
    # get all server members
    all_members = ctx.guild.members
    # get the 'anyone' role
    role = discord.utils.get(ctx.guild.roles, name="anyone")

    # remove the 'anyone' role from everyone in the server
    for m in all_members:
        await m.remove_roles(role)

    # add the 'anyone' role to the caller
    await member.add_roles(role)
    
    await ctx.respond("Set anyone to you!")

bot.run(token)
