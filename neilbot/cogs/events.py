import discord
from discord.ext import commands


class Events(commands.Cog):
    """Discord Bot cog that includes listeners for Discord events.

    Attributes:
        bot (discord.Bot): the instance of the Discord bot this cog is added to
    """

    def __init__(self, bot: discord.Bot):
        """Inits the Events cog.

        Args:
            bot (discord.Bot): the Discord bot this cog is being added to
        """
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Prints a message when the bot starts up."""
        print(f"{self.bot.user} is ready and online!")

    @commands.Cog.listener()
    async def on_application_command_error(
        self, ctx: discord.ApplicationContext, error: discord.DiscordException
    ) -> None:
        """Handles errors from bot slash commands.

        If the error is caused by a command being on cooldown, then prints an error message.

        Args:
            ctx (discord.ApplicationContext): the Discord application context
            error (discord.DiscordException): the exception raised from a slash command

        Raises:
            error: the slash command exception that is not handled
        """
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond("This command is currently on cooldown!")
        else:
            raise error


def setup(bot: discord.Bot) -> None:
    """Attach the Events cog to a Discord bot.

    Args:
        bot (discord.Bot): the Discord bot to add the Events cog to
    """
    bot.add_cog(Events(bot))
