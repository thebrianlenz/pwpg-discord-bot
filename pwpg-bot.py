# Work with Python 3.6
# Testing on 3.8.3
import asyncio
import sys
import traceback
import aiosqlite
from configparser import ConfigParser

import discord
from discord.ext import commands
from discord.ext.commands import Bot

BOT_PREFIX = ("!", "$")

config = ConfigParser()
bot = Bot(command_prefix=BOT_PREFIX, case_insensitive=True)

config.read('config.ini')
TOKEN = config.get('main', 'token')

initial_modules = [
    'GroupManager',
    'StatsManager',
    'Reflector'
]


@bot.event
async def on_command_error(context, error):

    if hasattr(context, 'error_being_handled') and context.error_being_handled:
        return

    if isinstance(error, commands.CommandNotFound):
        print(error)
        return
    if isinstance(error, commands.CommandOnCooldown):
        print(error)
        return
    if isinstance(error, commands.CheckFailure):
        print(error)
        print(context.author.name)
        return

    print(error)
    await context.send_help('There was an unhandled problem with: ' + str(context.command.name) + '\n' + str(error))

    # Some other error, let the cooldown reset
    context.command.reset_cooldown(context)


@bot.command(name='about',
             brief='A quick summary about the bot',
             description='Lists some of the core features about the bot')
async def _about(context):
    # docstring should include how the fields are populated (name in the cog definition and docstring for the cog)
    # todo - make a cleaner way to include upcoming features
    embed = discord.Embed(
        title="PWPG Bot", url="https://github.com/thebrianlenz/pwpg-discord-bot", color=0x000000)
    embed.set_thumbnail(
        url="https://cdn.discordapp.com/icons/315995274575085570/49318765d092b19f713ad97f26a5ae12")
    embed.add_field(name="Here are some of the features available:",
                    value='---------', inline=False)
    for cog_name in bot.cogs:
        embed.add_field(name=bot.cogs[cog_name].qualified_name,
                        value=bot.cogs[cog_name].description, inline=True)
    embed.add_field(name="Some upcoming features include:",
                    value="---------", inline=False)
    embed.add_field(
        name="Games", value="Secret Hitler, Trivia?, more?", inline=True)
    embed.add_field(
        name="Polls", value="Create and vote on various things", inline=True)
    embed.set_footer(text="Neat")

    await context.send(embed=embed)


@bot.command(name='load',
             hidden=True,
             brief='Load a new module',
             description='Load a new module without stopping the bot')
async def _load(context, module):
    try:
        bot.load_extension(module)
        await context.message.add_reaction('👍')
    except Exception as e:
        print(f'Failed to load module {module}.', e)
        await context.message.add_reaction('👎')


@bot.command(name='unload', hidden=True)
async def _unload(context, module):
    try:
        bot.unload_extension(module)
        await context.message.add_reaction('👍')
    except Exception as e:
        print(f'Failed to load extension {module}.', e)
        await context.message.add_reaction('👎')


@bot.command(name='reload', aliases=['rl'], hidden=True)
async def _reload(context, module):
    try:
        bot.reload_extension(module)
        await context.message.add_reaction('👍')
    except Exception as e:
        print(f'Failed to load module {module}.', e)
        await context.message.add_reaction('👎')


@bot.command(name='modules', hidden=True)
async def _listModules(context):
    print(str(bot.extensions.keys()))


@bot.command(name='rlsh', hidden=True)
async def _reloadSecretHitler(context):
    try:
        bot.reload_extension('SecretHitler')
        await context.message.add_reaction('👍')
    except Exception as e:
        print(f'Failed to load module SH.', e)
        await context.message.add_reaction('👎')


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    print(discord.__version__)
    for m in initial_modules:
        try:
            bot.load_extension(m)
            print(f'{m} loaded.')
        except Exception as e:
            print(f'Failed to load extension {m}. {e}', file=sys.stderr)
            traceback.print_exc()

bot.run(TOKEN)
