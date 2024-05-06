from typing import cast

import discord
from discord.ext import commands

from neilbot.neilbot import NeilBot


class Leetcode(commands.Cog):
    """Discord Bot cog that includes slash commands for Leetcode problems.

    Attributes:
        bot (NeilBot): the instance of the Discord bot this cog is added to
    """

    def __init__(self, bot: NeilBot):
        """Inits the Leetcode cog.

        Args:
            bot (NeilBot): the Discord bot this cog is being added to
        """
        self.bot = bot

    def _convertThreadName(self, name: str) -> str:
        """Convert a thread name into lowercase and remove periods.

        Args:
            name (str): the thread name to convert

        Returns:
            str: the name in lowercase and stripped of periods
        """
        return name.lower().translate(str.maketrans("", "", "."))

    def _getProblemNumberFromConvertedThreadName(self, name: str) -> int | None:
        """Gets the number of a problem from the full problem name.

        The name passed in must be converted to lowercase and have no periods.

        Args:
            name (str): A problem name that has been converted

        Returns:
            int | None: A problem number, or None if the problem name did not contain
            a number
        """
        # split the name into words
        words = name.split(" ")
        # check if the first word is a number
        if words[0].isdigit():
            # if so, then it should be the problem number
            return int(words[0])
        # no number was found at the beginning of the name
        return None

    def _getProblemNameFromConvertedThreadName(self, name: str) -> str:
        """Gets the name of a problem without the problem number.

        The name passed in must be converted to lowercase and have no periods.

        Args:
            name (str): A problem name that has been converted

        Returns:
            str: A problem name without the problem number
        """
        # check if the problem name contains the problem number, and if so then remove
        # it
        if self._getProblemNumberFromConvertedThreadName(name):
            # split name into words
            words = name.split(" ")
            # remove the first word and reconnect the rest
            name = " ".join(words[1:])
        # if the problem name does not contain the problem number, then just return
        # the name
        return name

    def _findMostSimilarThread(
        self, number: int | None, name: str, threads: list[discord.Thread]
    ) -> discord.Thread | None:
        """Find the single thread most similar to the thread number and thread name.

        If no matching threads were found, then None is returned.

        Args:
            number (int | None): the thread number to search for, or None if the number
            is not known
            name (str): the thread name to search for, or a substring of the name to
            search for
            threads (list[discord.Thread]): a list of threads to search in

        Returns:
            discord.Thread | None: the best matching thread, or None if no matching
            thread was found
        """
        # store all the possible thread matches in a list, since some problems may have
        # multiple thread discussions (duplicate threads)
        matches: list[discord.Thread] = []

        # if we know the number of the problem we are searching for then use that first.
        if number:
            # check every thread in the channel
            for th in threads:
                # convert thread name to lowercase and remove periods, to get the
                # problem number
                threadName = self._convertThreadName(th.name)
                # use the converted thread name to get the thread number, if it has one
                threadProblemNumber = self._getProblemNumberFromConvertedThreadName(
                    threadName
                )
                # the thread is a match if a problem number was found
                if threadProblemNumber and threadProblemNumber == number:
                    matches.append(th)
            if matches:
                # the best matching thread should be the one with the most discussion,
                # i.e. the thread with the most messages
                best_match = max(matches, key=lambda x: cast(int, x.message_count))
                return best_match

        # if we don't know the number of the problem we are searching for or if we
        # didn't find any threads using the problem number, then search by problem name.
        for th in threads:
            # convert the thread name to lowercase for better comparison.
            th_name = self._convertThreadName(th.name)
            # remove the problem number if it exists at the beginning of the problem
            # name
            th_name = self._getProblemNameFromConvertedThreadName(th_name)
            # if the thread name contains the string passed in,
            # then add it to the possible match list
            if name in th_name:
                matches.append(th)

        if matches:
            # the best matching thread should be the one with the shortest name,
            # since threads with more words are likely other problem variants.
            best_match = min(matches, key=lambda x: len(x.name))
            return best_match
        # if no threads matched the one we were looking for
        return None

    async def getArchivedThreads(
        self, channel: discord.TextChannel
    ) -> list[discord.Thread]:
        """Gets all archived threads from a specified channel.

        Args:
            channel (discord.TextChannel): a Discord channel to get threads from

        Returns:
            list[discord.Thread]: a list of all archived threads, or an empty list
            if no archived threads were found
        """
        # store all found threads
        threads: list[discord.Thread] = []
        # iterate over all archived threads
        async for th in channel.archived_threads():
            # add each thread to the list
            threads.append(th)
        # return all archived threads
        return threads

    @discord.slash_command(
        name="lc_thread", description="Find the Leetcode thread for a problem"
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def find_lc_thread(
        self, ctx: discord.ApplicationContext, problem: str
    ) -> None:
        """Finds a Leetcode thread that most closely matches the problem query.

        Args:
            ctx (discord.ApplicationContext): the Discord application context
            problem (str): a query string for a Leetcode problem thread
        """
        # give us 15 minutes instead of 3 seconds to respond
        await ctx.defer(ephemeral=True)

        channel = ctx.channel
        threads = cast(list[discord.Thread], channel.threads)
        archivedThreads = await self.getArchivedThreads(channel)
        threads.extend(archivedThreads)

        # convert to lowercase and remove periods,
        # so that we can get the problem number easily
        problem = self._convertThreadName(problem)
        # get the number for this problem, if the problem name contained a number
        problem_number = self._getProblemNumberFromConvertedThreadName(problem)
        # get just the name of the problem, without the number
        problem = self._getProblemNameFromConvertedThreadName(problem)

        # find the thread that most closely matches the problem number and/or problem
        # name
        best_match = self._findMostSimilarThread(problem_number, problem, threads)
        # if a match was found
        if best_match:
            # if the thread has been archived, then unarchive it because discord
            # has trouble loading messages in archived threads
            await best_match.unarchive()
            # send a url to the matched thread
            await ctx.respond(f"Found problem thread: {best_match.jump_url}")
        else:
            await ctx.respond("Didn't find problem thread")


def setup(bot: NeilBot) -> None:
    """Attach the Leetcode cog to a Discord bot.

    Args:
        bot (NeilBot): the Discord bot to add the Leetcode cog to
    """
    bot.add_cog(Leetcode(bot))
