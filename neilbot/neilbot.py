import os

import aiohttp
import discord


class NeilBot(discord.Bot):
    """Custom Discord bot with useful features.

    Contains clients for easily interacting with other services.
    """

    def __init__(self) -> None:
        """Inits a new new instance of the NeilBot Discord bot.

        Loads additional cog components from the cogs/ directory.
        """
        activity = discord.Game(name="Leetcode")
        allowed_mentions = discord.AllowedMentions.all()
        intents = discord.Intents(guilds=True, members=True, voice_states=True)
        super().__init__(
            activity=activity, allowed_mentions=allowed_mentions, intents=intents
        )

        # load all cogs into the bot
        for filename in os.listdir("./neilbot/cogs"):
            # if a filename starts with an underscore then it is a private helper
            # and not a cog
            if not filename.startswith("_") and filename.endswith(".py"):
                # remove the extension from the name
                self.load_extension(f"neilbot.cogs.{filename[:-3]}")

    async def on_ready(self) -> None:
        """Setup class members potentially needed for more than one component."""
        # create client for making HTTP requests
        self.httpClient = aiohttp.ClientSession()
