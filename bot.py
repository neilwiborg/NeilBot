import os
import random
import discord
from discord.ext import commands
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

@bot.event
async def on_application_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.respond("This command is currently on cooldown!")
    else:
        raise error

async def _anyone_helper(ctx, all_members, member, role):
    try:
        # remove the 'anyone' role from everyone in the server
        for m in all_members:
            await m.remove_roles(role)

        # add the 'anyone' role to the random user
        await member.add_roles(role)
        
        await ctx.respond(f"Set {role.mention} to {member.mention}!")
    except discord.Forbidden:
        await ctx.respond("Error: please give me permission to manage roles!")
    except discord.HTTPException:
        await ctx.respond("Error: unable to execute command, please try later!")

@bot.slash_command(name = "anyone_me", description = "Set the @anyone target to yourself")
@commands.cooldown(1, 10, commands.BucketType.user) 
async def set_anyone_me(ctx):
    # get the caller
    member = ctx.author
    # get the server
    server = ctx.guild

    # if the bot is not in the server
    if server:
        # get all server members
        all_members = server.members
        # get the 'anyone' role
        role = discord.utils.get(server.roles, name="anyone")

        await _anyone_helper(ctx, all_members, member, role)
    else:
        await ctx.respond("Error: please add me to the server first!")

@bot.slash_command(name = "anyone_rand", description = "Set the @anyone target to a random user")
@commands.cooldown(1, 10, commands.BucketType.user) 
async def set_anyone_rand(ctx):
    # get the server
    server = ctx.guild

    # if the bot is not in the server
    if server:
        # get all server members
        all_members = server.members
        # get a random user
        member = random.choice(all_members)
        # get the 'anyone' role
        role = discord.utils.get(ctx.guild.roles, name="anyone")

        await _anyone_helper(ctx, all_members, member, role)
    else:
        await ctx.respond("Error: please add me to the server first!")

bot.run(token)
