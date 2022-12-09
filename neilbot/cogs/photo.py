from io import BytesIO
import aiohttp
import discord
from discord.ext import commands


class Photo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="photo_uwb", description="Take a photograph of UW Bothell")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def take_photo_uwb(self, ctx: discord.ApplicationContext) -> None:
        # save the URL used for accessing the UWB webcam
        UWB_WEBCAM_URL = "http://69.91.192.220/netcam.jpg"

        # start an aiohttp client session
        async with aiohttp.ClientSession() as session:
            # send a get request to the webcam
            async with session.get(UWB_WEBCAM_URL) as resp:
                # check if response is OK
                if resp.status == 200:
                    # read the response stream
                    image = BytesIO(await resp.read())
                    await ctx.respond("UWB rn:", file=discord.File(image, filename="netcam.jpg"))
                else:
                    await ctx.respond("Error: unable to download photo")


def setup(bot):
    bot.add_cog(Photo(bot))
