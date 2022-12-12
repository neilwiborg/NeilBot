import discord
from discord.ext import commands


class Leetcode(commands.Cog):
    """Discord Bot cog that includes slash commands for Leetcode problems.

    Attributes:
        bot (discord.Bot): the instance of the Discord bot this cog is added to
    """

    def __init__(self, bot: discord.Bot):
        """Inits the Leetcode cog.

        Args:
            bot (discord.Bot): the Discord bot this cog is being added to
        """
        self.bot = bot

    @discord.slash_command(name="lc_thread", description="Find the Leetcode thread for a problem")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def find_lc_thread(self, ctx: discord.ApplicationContext, problem: str) -> None:
        """Finds a Leetcode thread that most closely matches the problem query.

        Args:
            ctx (discord.ApplicationContext): the Discord application context
            problem (str): a query string for a Leetcode problem thread
        """
        # give us 15 minutes instead of 3 seconds to respond
        await ctx.defer(ephemeral=True)

        channel = ctx.channel
        threads = channel.threads
        # convert to lowercase and remove periods, so that we can get the problem number easily
        problem = problem.lower().translate(str.maketrans("", "", "."))
		# split the problem string into words
        problem_words = problem.split(" ")

        # store all the possible thread matches in a list, since some problems may have
        # multiple thread discussions (duplicate threads)
        problem_threads = []

		# the first word will either be the problem number or just a word. If it's a number,
        # then we can compare that number with thread numbers.
        problem_number = problem_words[0] if problem_words[0].isdigit() else None
        if problem_number:
			# remove the problem number from the list of words
            problem_words = problem_words[1:]
			# recombine the words without the problem number
            problem = " ".join(problem_words)

            # check every thread in the channel
            for th in threads:
                # convert the thread name to lowercase and remove periods, so that we can get
                # the problem number easily. The 0th index will either be the problem number or
                # just a word.
                th_name_words = th.name.lower().translate(
                    str.maketrans("", "", ".")).split(" ")
                # if the thread name starts with a problem number and is the same number as
                # the string passed in, then add it to the possible match list
                if problem_number == th_name_words[0]:
                    problem_threads.append(th)

            if problem_threads:
                # the best matching thread should be the one with the most discussion,
                # i.e. the thread with the most messages
                best_match = max(problem_threads, key=lambda x: x.message_count)
                # if the thread has been archived, then unarchive it because discord
                # has trouble loading messages in archived threads
                await best_match.unarchive()
                # send a url to the matched thread
                await ctx.respond(f"Found problem thread: {best_match.jump_url}")
                return

        # check every thread in the channel
        for th in threads:
            # convert the thread name to lowercase for better comparison.
            th_name = th.name.lower()
            # if the thread name contains the string passed in,
            # then add it to the possible match list
            if problem in th_name:
                problem_threads.append(th)

        if problem_threads:
            # the best matching thread should be the one with the shortest name,
            # since threads with more words are likely other problem variants.
            best_match = min(problem_threads, key=lambda x: len(x.name))
            # if the thread has been archived, then unarchive it because discord
            # has trouble loading messages in archived threads
            await best_match.unarchive()
            # send a url to the matched thread
            await ctx.respond(f"Found problem thread: {best_match.jump_url}")
        else:
            await ctx.respond("Didn't find problem thread")


def setup(bot: discord.Bot) -> None:
    """Attach the Leetcode cog to a Discord bot.

    Args:
        bot (discord.Bot): the Discord bot to add the Leetcode cog to
    """
    bot.add_cog(Leetcode(bot))
