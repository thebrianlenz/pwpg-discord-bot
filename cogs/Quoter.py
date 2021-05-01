import discord
import asyncio
from discord.ext import commands
from discord.ext.commands import Bot

import aiosqlite
from datetime import datetime
import random

QUOTE_DB_PATH = "data/quotes.db"


class Quoter(commands.Cog, name='Quoter'):
    """Manages quotes for users"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(name='quote',
                      brief='Quote a message',
                      description='Quote a message',
                      pass_context=True)
    async def command_quote(self, context, quote: str, quoted_user: discord.User):
        """Quote a message

        Args:
            context (context): The context of the invoking command
            quote (str): The quote to record
            quoted_user (user): The user being quoted
        """

        payload = {
            'guild_id': context.guild.id,
            'channel_id': context.channel.id,
            'invoking_user': context.author.id,
            'quoted_user': quoted_user.id,
            'message_id': context.message.id,
            'quoted_content': quote,
            'timestamp': datetime.now().strftime("%B %d, %Y")
        }

        async with aiosqlite.connect(QUOTE_DB_PATH) as quotes_db:
            print('Connecting to quote database...')
            try:
                await quotes_db.execute("""INSERT INTO quotes VALUES
                    (:guild_id, :channel_id, :invoking_user, :quoted_user, :message_id, :quoted_content, :timestamp)""", payload)
                await quotes_db.commit()
                print('Quote written to database.')
            except Exception as error:
                print(error)

    @command_quote.error
    async def command_quote_error(self, context, error):
        setattr(context, 'error_being_handled', True)
        if isinstance(error, commands.BadArgument):
            print('Bad argument caught in the command_quote in Quoter.')
            await context.send("Could not find that user. Either ensure the user was spelled correctly, or just mention them.")
            return
        setattr(context, 'error_being_handled', False)

    @commands.command(name='my-quotes',
                      brief='Fetch quotes you have said.',
                      description='Fetches the quotes attributed to the invoking user.',
                      pass_context=True)
    async def command_my_quotes(self, context):

        payload = {'guild_id': context.guild.id,
                   'quoted_user': context.author.id}

        query = """SELECT
                        quoted_user,
                        invoking_user,
                        message_id,
                        quoted_content,
                        timestamp
                    FROM quotes
                    WHERE guild_id=(:guild_id) AND
                    quoted_user=(:quoted_user)"""

        async with aiosqlite.connect(QUOTE_DB_PATH) as quotes_db:
            print('Connecting to quote database...')
            try:
                cursor = await quotes_db.execute(query, payload)
                results = await cursor.fetchall()
                print('Quotes fetched')
            except Exception as error:
                print(error)
        message = "```"
        for q in results:
            message += f'\"{q[3]}\"\n\t - {self.bot.get_user(q[0]).display_name}\t{q[4]}\n\n'
        message += '```'

        await context.send(message)

    @commands.command(name='random-quote',
                      brief='Fetch and print a random quote',
                      description='Fetches a random quote from the active guild.',
                      pass_context=True)
    async def command_random_quote(self, context):
        payload = {'guild_id': context.guild.id}

        query = """SELECT
                    quoted_user,
                    invoking_user,
                    quoted_content,
                    timestamp
                FROM quotes
                WHERE guild_id=(:guild_id)"""

        async with aiosqlite.connect(QUOTE_DB_PATH) as quotes_db:
            print('Connecting to quote database...')
            try:
                cursor = await quotes_db.execute(query, payload)
                results = await cursor.fetchall()
                print('Quotes fetched')
            except Exception as error:
                print(error)

        q = random.choice(results)

        # Formats as:
        # "QUOTED_CONTENT"
        #       - QUOTED_USER TIMESTAMP
        # Recorded by: INVOKING_USER
        message = f'```\"{q[2]}\"\n\t- {self.bot.get_user(q[0]).display_name}\t{q[3]}\n\nRecorded by: {self.bot.get_user(q[1]).display_name}```'
        await context.send(message)


def setup(bot):
    bot.add_cog(Quoter(bot))


def teardown(bot):
    bot.remove_cog('Quoter')
