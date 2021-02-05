"""Used for easily converting timezones.

    GroupManager functions as an extension for a Discord.py bot. This
    includes the GroupManager Cog, which handles all associated commands
    and are registered with the bot that loads this extension.

    This extension creates and reads from a file for Groups of users seperated
    by Guild ID. This file is saved as groupsData.json in the local directory.
    These groups can be accessed by users to alert other members of a group,
    usually for playing games. Requires asyncio and discord.py libraries.

    This extension is generally accessed through adding the GroupManager
    as a cog to an existing Discord.py Bot.
    This extension should likely not be loaded as a Python module.
"""
from discord.ext import commands
from discord.ext.commands import Bot
import dateutil
from dateutil import parser


class TimeManager(commands.Cog, name="Time Manager"):
    """Easily convert timezones and schedule things"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(
        name="convert",
        brief="Converts a timezones",
        description="converts a time from a specific timezone to another timezone",
        rest_is_raw=True,
        pass_context=True,
    )
    async def command_convert(self, context, *, time_query: str):
        """Converts a time from a specific timezone to another timezone

        Args:
            context (context): The context of the invoking command
            time_query (str): the query, in the following format: [time] [timezone-from] -> [timezone-to]
        """
        try:
            t_from, tz_to = map(str.strip, time_query.strip().split("->"))
            t = parser.parse(t_from)
            if t.tzinfo is None:
                await context.send(
                    "You either forgot to supply a timezone, or"
                    "I didn't understand it. You can check this list here:"
                    "https://en.wikipedia.org/wiki/List_of_tz_database_time_zones"
                    ".")
                raise Exception
            tz_to = dateutil.tz.gettz(tz_to)
            if tz_to is None:
                await context.send(
                    "I didn't understand your TO timezone. Check this list here:"
                    "https://en.wikipedia.org/wiki/List_of_tz_database_time_zones"
                )
                raise Exception

            t = t.astimezone(dateutil.tz.gettz(tz_to))
            await context.send(f"{tz_to}: {t.strftime('%Y-%m-%d %H:%M')}")

        except ValueError as e:
            await context.send(
                "I did not understand your query. Are you sure"
                "you used the format: schedule [time] [timezone-from] ->"
                "[timezone-to] ?")
            print(f"Errored in command_convert: {e}")


def setup(bot):
    """Initial setup for the TimeManager cog.
    This is called when a cog is added to the client.
    """
    bot.add_cog(TimeManager(bot))


def teardown(bot):
    """Removes the cog from the bot.
    This is called when a cog is removed from the client. A final data write is
    called before the cog is removed.
    """
    bot.remove_cog("TimeManager")
