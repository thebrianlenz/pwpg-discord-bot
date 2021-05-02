import discord
import asyncio
import datetime
from discord.ext import commands
from discord.ext.commands import Bot


class Extras(commands.Cog, name='Extras'):
    """Additional commands and utilities"""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.channel_chatters = {}

    @commands.command(name='no',
                      brief='No',
                      description='No',
                      hidden=True,
                      pass_context=True)
    async def command_no(self, context):
        await context.send(file=discord.File('data/isildur_no.gif'))
        print("No sent")

    @commands.Cog.listener()
    async def on_typing(self, channel, user, when):
        print(f'saw {user} typing in {channel} at {when}')
        self.chatter_expiration_check(when)

        if channel.id not in self.channel_chatters:
            self.channel_chatters[channel.id] = {}

        expires = when + datetime.timedelta(seconds=10)
        self.channel_chatters[channel.id][user.id] = expires

        await self.chatter_count_check()

    def chatter_expiration_check(self, current_time):
        for c in list(self.channel_chatters.keys()):
            for u, e in list(self.channel_chatters[c].items()):
                if e < current_time:
                    self.channel_chatters[c].pop(u, None)

    async def chatter_count_check(self):
        for channel in self.channel_chatters:
            if len(self.channel_chatters[channel]) >= 4:
                guild_channel = self.bot.get_channel(channel)
                await guild_channel.send(file=discord.File('data/several_people.gif'), delete_after=3)
                self.channel_chatters[channel].clear()
                print('several people are typing?')


def setup(bot):
    bot.add_cog(Extras(bot))


def teardown(bot):
    bot.remove_cog('Extras')
