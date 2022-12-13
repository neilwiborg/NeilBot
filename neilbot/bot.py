import os

import discord
from dotenv import load_dotenv


def main() -> None:
    """Starts up the Discord bot and sets initial bot values."""

    load_dotenv()
    discord_token = str(os.getenv("DISCORD_TOKEN"))

    activity = discord.Game(name="Leetcode")
    allowed_mentions = discord.AllowedMentions.all()
    intents = discord.Intents(guilds=True, members=True, voice_states=True)
    bot = discord.Bot(
        activity=activity, allowed_mentions=allowed_mentions, intents=intents
    )

    # load all cogs into the bot
    for filename in os.listdir("./neilbot/cogs"):
        if filename.endswith(".py"):
            # remove the extension from the name
            bot.load_extension(f"neilbot.cogs.{filename[:-3]}")

    bot.run(discord_token)


if __name__ == "__main__":
    main()
