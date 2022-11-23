import discord
from discord.ext import commands


class Leetcode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="lc_thread", description="Find the Leetcode thread for a problem")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def find_lc_thread(self, ctx, problem):
        # give us 15 minutes instead of 3 seconds to respond
        await ctx.defer(ephemeral=True)

        channel = ctx.channel
        threads = channel.threads
        # convert to lowercase and remove periods, so that we can get the problem number easily
        problem_converted = problem.lower().translate(str.maketrans("", "", "."))
        # the first word will either be the problem number or just a word. If it's a number,
        # then we can compare that number with thread numbers.
        problem_first_word = problem_converted.split(" ")[0]

        # store all the possible thread matches in a list, since some problems may have
        # multiple thread discussions (duplicate threads)
        problem_threads = []
        # check every thread in the channel
        for th in threads:
            # convert to lowercase and check if our problem is in the thread name
            if problem_converted in th.name.lower():
                # convert the thread name to lowercase and remove periods, so that we can get
                # the problem number easily. The 0th index will either be the problem number or
                # just a word.
                th_name_words = th.name.lower().translate(
                    str.maketrans("", "", ".")).split(" ")
                # if both strings start with a problem number, then only add to the list if the numbers are equal
                if th_name_words[0].isdigit() and problem_first_word.isdigit() and th_name_words[0] != problem_first_word:
                    continue
                    # add the possible match to our list
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
        else:
            await ctx.respond("Didn't find problem thread")


def setup(bot):
    bot.add_cog(Leetcode(bot))
