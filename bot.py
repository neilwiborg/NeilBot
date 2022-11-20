import os
import random
import discord
from dotenv import load_dotenv

load_dotenv()
token = str(os.getenv("TOKEN"))

activity = discord.Game(name = "Leetcode")
allowed_mentions = discord.AllowedMentions.all()
intents = discord.Intents(guilds = True, members = True)
bot = discord.Bot(activity = activity, allowed_mentions = allowed_mentions, intents = intents)

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")

@bot.slash_command(name = "anyone_me", description = "Set the @anyone target to yourself")
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
    
    await ctx.respond(f"Set {role.mention} to {member.mention}!")

@bot.slash_command(name = "anyone_rand", description = "Set the @anyone target to a random user")
async def set_anyone(ctx):
    # get all server members
    all_members = ctx.guild.members
    # get the 'anyone' role
    role = discord.utils.get(ctx.guild.roles, name="anyone")

    # remove the 'anyone' role from everyone in the server
    for m in all_members:
        await m.remove_roles(role)
    
    # get a random user
    member = random.choice(all_members)

    # add the 'anyone' role to the random user
    await member.add_roles(role)
    
    await ctx.respond(f"Set {role.mention} to {member.mention}!")

bot.run(token)
