# Work with Python 3.6
import asyncio
import sys
import traceback
from configparser import SafeConfigParser

import discord
from discord.ext import commands
from discord.ext.commands import Bot
import GroupManager

BOT_PREFIX = ("!","$")

config = SafeConfigParser()
client = Bot(command_prefix=BOT_PREFIX, case_insensitive=True)

config.read('config.ini')
TOKEN = config.get('main', 'token')

initial_modules = [
        'GroupManager'
        ]

@client.event
async def on_command_error(context, error):

    if hasattr(context, 'error_being_handled') and context.error_being_handled: return

    if isinstance(error, commands.CommandNotFound):
        print('Command not found')
        print(error)
        return
    if isinstance(error, commands.CommandOnCooldown):
        print(error)
        return
    if isinstance(error, commands.CheckFailure):
        print(error)
        print(context.author.name)
        return


    print (error)
    await context.send_help('There was an unhandled problem with: ' + str(context.command.name) + '\n' + str(error))

    # Some other error, let the cooldown reset
    context.command.reset_cooldown(context)

@client.command(name='load', 
                hidden=True,
                brief='Load a new module',
                description='Load a new module without stopping the bot')
async def _load(context, module):
    try:
        client.load_extension(module)
        await context.message.add_reaction('👍')
    except Exception as e:
        print(f'Failed to load module {module}.', e)
        await context.message.add_reaction('👎')

@client.command(name='unload', hidden=True)
async def _unload(context, module):
    try:
        client.unload_extension(module)
        await context.message.add_reaction('👍')
    except Exception as e:
        print(f'Failed to load extension {module}.', e)
        await context.message.add_reaction('👎')

@client.command(name='reload', aliases=['rl'], hidden=True)
async def _reload(context, module):
    try:
        client.reload_extension(module)
        await context.message.add_reaction('👍')
    except Exception as e:
        print(f'Failed to load module {module}.', e)
        await context.message.add_reaction('👎')

@client.command(name='modules', hidden=True)
async def _listModules(context):
    print (str(client.extensions.keys()))

@client.command(name='rlsh', hidden=True)
async def _reloadSecretHitler(context):
    try:
        client.reload_extension('SecretHitler')
        await context.message.add_reaction('👍')
    except Exception as e:
        print(f'Failed to load module SH.', e)
        await context.message.add_reaction('👎')

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    print(discord.__version__)
    for m in initial_modules:
            try:
                client.load_extension(m)
                print(f'{m} loaded.')
            except Exception as e:
                print(f'Failed to load extension {m}. {e}', file=sys.stderr)
                traceback.print_exc()

client.run(TOKEN)
