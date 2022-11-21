import random
import discord
from discord.ext import commands

class Anyone(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	async def _anyone_helper(self, ctx, all_members, member, role):
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

	@discord.slash_command(name = "anyone_me", description = "Set the @anyone target to yourself")
	@commands.cooldown(1, 10, commands.BucketType.user) 
	async def set_anyone_me(self, ctx):
		# give us 15 minutes instead of 3 seconds to respond
		await ctx.defer(ephemeral = False)

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
			if role:
				await self._anyone_helper(ctx, all_members, member, role)
			else:
				ctx.respond("Error: unable to find role 'anyone'")

		else:
			await ctx.respond("Error: please add me to the server first!")

	@discord.slash_command(name = "anyone_rand", description = "Set the @anyone target to a random user")
	@commands.cooldown(1, 10, commands.BucketType.user) 
	async def set_anyone_rand(self, ctx):
		# give us 15 minutes instead of 3 seconds to respond
		await ctx.defer(ephemeral = False)

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
			if role:
				await self._anyone_helper(ctx, all_members, member, role)
			else:
				ctx.respond("Error: unable to find role 'anyone'")

		else:
			await ctx.respond("Error: please add me to the server first!")

def setup(bot):
	bot.add_cog(Anyone(bot))