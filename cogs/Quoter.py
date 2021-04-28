import discord
import asyncio
from discord.ext import commands
from discord.ext.commands import Bot

import aiosqlite
from datetime import datetime

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
            'timestamp': context.message.created_at.isoformat()
        }
        print(quoted_user)

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


def setup(bot):
    bot.add_cog(Quoter(bot))


def teardown(bot):
    bot.remove_cog('Quoter')
