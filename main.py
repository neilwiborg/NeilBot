import os

from dotenv import load_dotenv

from neilbot.neilbot import NeilBot


def main() -> None:
    """Starts up the Discord bot and sets initial bot values."""

    load_dotenv()
    discord_token = str(os.getenv("DISCORD_TOKEN"))

    bot = NeilBot()
    bot.run(discord_token)


if __name__ == "__main__":
    main()
