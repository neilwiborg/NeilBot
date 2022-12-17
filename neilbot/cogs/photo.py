from io import BytesIO

import aiohttp
import discord
from discord.ext import commands


class Photo(commands.Cog):
    """Discord Bot cog that includes slash commands for taking photographs.

    Attributes:
        bot (discord.Bot): the instance of the Discord bot this cog is added to
    """

    def __init__(self, bot: discord.Bot):
        """Inits the Photo cog.

        Args:
            bot (discord.Bot): the Discord bot this cog is being added to
        """
        self.bot = bot

    async def _download_photo(self, url: str) -> BytesIO | None:
        """Download a photo from the provided URL. Assumes that the
        URL is a valid URL to a photo.

        Args:
            url (str): the URL to download from

        Returns:
            BytesIO | None: the image in bytes. If an error occurred while
            downloading, then None is returned.
        """
        # start an aiohttp client session
        async with aiohttp.ClientSession() as session:
            # send a get request to the url
            async with session.get(url) as resp:
                # check if response is OK
                if resp.status == 200:
                    # read the response stream
                    image = BytesIO(await resp.read())
                    return image
        return None

    @discord.slash_command(
        name="photo_uws", description="Take a photograph of UW Seattle"
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def take_photo_uws(self, ctx: discord.ApplicationContext) -> None:
        """Downloads and posts a photo of the UW Seattle campus.

        Downloads a photo of the UW Seattle campus from within the last 5 minutes
        and posts the photo. If an error occurs while downloading the
        photo, then an error message is sent instead.

        Args:
            ctx (discord.ApplicationContext): the Discord application context
        """
        # save the URL used for accessing the UWB webcam
        UWS_WEBCAM_URL = "https://www.washington.edu/cambots/camera1_l.jpg"

        # give us 15 minutes instead of 3 seconds to respond
        await ctx.defer(ephemeral=False)

        image = await self._download_photo(UWS_WEBCAM_URL)
        if image:
            await ctx.respond(
                "UWS (Red Square) rn:",
                file=discord.File(image, filename="camera1_l.jpg"),
            )
        else:
            await ctx.respond("Error: unable to download photo")

    @discord.slash_command(
        name="photo_uwb", description="Take a photograph of UW Bothell"
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def take_photo_uwb(self, ctx: discord.ApplicationContext) -> None:
        """Downloads and posts a photo of the UW Bothell campus.

        Downloads a photo of the UW Bothell campus at the time the command is
        executed and posts the photo. If an error occurs while downloading the
        photo, then an error message is sent instead.

        Args:
            ctx (discord.ApplicationContext): the Discord application context
        """
        # save the URL used for accessing the UWB webcam
        UWB_WEBCAM_URL = "http://69.91.192.220/netcam.jpg"

        # give us 15 minutes instead of 3 seconds to respond
        await ctx.defer(ephemeral=False)

        image = await self._download_photo(UWB_WEBCAM_URL)
        if image:
            await ctx.respond(
                "UWB rn:", file=discord.File(image, filename="netcam.jpg")
            )
        else:
            await ctx.respond("Error: unable to download photo")


def setup(bot: discord.Bot) -> None:
    """Attach the Photo cog to a Discord bot.

    Args:
        bot (discord.Bot): the Discord bot to add the Photo cog to
    """
    bot.add_cog(Photo(bot))
