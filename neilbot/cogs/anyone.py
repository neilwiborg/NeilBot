import random
from typing import cast

import discord
from discord.ext import commands

from neilbot.neilbot import NeilBot


class Anyone(commands.Cog):
    """Discord Bot cog that includes slash commands for setting the Anyone role.

    Attributes:
        bot (NeilBot): the instance of the Discord bot this cog is added to
    """

    def __init__(self, bot: NeilBot):
        """Inits the Anyone cog.

        Args:
            bot (NeilBot): the Discord bot this cog is being added to
        """
        self.bot = bot

    async def _anyone_helper(
        self,
        ctx: discord.ApplicationContext,
        all_members: list[discord.Member],
        member: discord.Member,
        role: discord.Role,
    ) -> None:
        """Remove a role from all server members and add a role to one member.

        Args:
            ctx (discord.ApplicationContext): the Discord application context
            all_members (list[discord.Member]): all server members
            member (discord.Member): a specific server member to add a role to
            role (discord.Role): the role to add to one member
        """
        try:
            # remove the 'anyone' role from everyone in the server
            for m in all_members:
                await m.remove_roles(cast(discord.abc.Snowflake, role))

            # add the 'anyone' role to the random user
            await member.add_roles(cast(discord.abc.Snowflake, role))

            await ctx.respond(f"Set {role.mention} to {member.mention}!")
        except discord.Forbidden:
            await ctx.respond("Error: please give me permission to manage roles!")
        except discord.HTTPException:
            await ctx.respond("Error: unable to execute command, please try later!")

    @discord.slash_command(
        name="anyone_me", description="Set the @anyone target to yourself"
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def set_anyone_me(self, ctx: discord.ApplicationContext) -> None:
        """Sets the @anyone role to the user calling this slash command.

        Args:
            ctx (discord.ApplicationContext): the Discord application context
        """
        # give us 15 minutes instead of 3 seconds to respond
        await ctx.defer(ephemeral=False)

        # get the caller
        member = ctx.author
        # get the server
        server = ctx.guild

        # if the bot is not in the server
        if server:
            # get all server members
            all_members = server.members
            # get the 'anyone' role
            role: discord.Role | None = discord.utils.get(server.roles, name="anyone")
            if role:
                await self._anyone_helper(ctx, all_members, member, role)
            else:
                await ctx.respond("Error: unable to find role 'anyone'")

        else:
            await ctx.respond("Error: please add me to the server first!")

    @discord.slash_command(
        name="anyone_rand", description="Set the @anyone target to a random user"
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def set_anyone_rand(self, ctx: discord.ApplicationContext) -> None:
        """Sets the @anyone role to a random user on the server.

        Args:
            ctx (discord.ApplicationContext): the Discord application context
        """
        # give us 15 minutes instead of 3 seconds to respond
        await ctx.defer(ephemeral=False)

        # get the server
        server = ctx.guild

        # if the bot is not in the server
        if server:
            # get all server members
            all_members = server.members
            # get a random user
            member = random.choice(all_members)
            # get the 'anyone' role
            role: discord.Role | None = discord.utils.get(
                ctx.guild.roles, name="anyone"
            )
            if role:
                await self._anyone_helper(ctx, all_members, member, role)
            else:
                await ctx.respond("Error: unable to find role 'anyone'")

        else:
            await ctx.respond("Error: please add me to the server first!")


def setup(bot: NeilBot) -> None:
    """Attach the Anyone cog to a Discord bot.

    Args:
        bot (NeilBot): the Discord bot to add the Anyone cog to
    """
    bot.add_cog(Anyone(bot))
