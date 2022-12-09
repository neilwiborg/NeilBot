from io import BytesIO
from typing import Optional
import aiohttp
import discord
from discord.ext import commands


class Photo(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
    
    async def _download_photo(self, url: str) -> Optional[BytesIO]:
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

    @discord.slash_command(name="photo_uwb", description="Take a photograph of UW Bothell")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def take_photo_uwb(self, ctx: discord.ApplicationContext) -> None:
        # save the URL used for accessing the UWB webcam
        UWB_WEBCAM_URL = "http://69.91.192.220/netcam.jpg"

        # give us 15 minutes instead of 3 seconds to respond
        await ctx.defer(ephemeral=False)

        image = await self._download_photo(UWB_WEBCAM_URL)
        if image:
            await ctx.respond("UWB rn:", file=discord.File(image, filename="netcam.jpg"))
        else:
            await ctx.respond("Error: unable to download photo")


def setup(bot: discord.Bot):
    bot.add_cog(Photo(bot))
