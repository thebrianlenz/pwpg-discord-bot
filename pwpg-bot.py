# Work with Python 3.6
import discord
from discord.ext.commands import Bot
from discord.ext.commands import HelpFormatter
from discord.ext import commands
from configparser import SafeConfigParser

BOT_PREFIX = ("!","$")

config = SafeConfigParser()
client = Bot(command_prefix=BOT_PREFIX)

config.read('config.ini')
TOKEN = config.get('main', 'token')

async def formatAndSendHelp(context):
    f = HelpFormatter()
    helpPages = await f.format_help_for(context, context.command)
    for p in helpPages:
        await context.send(p)
    # await context.send('Usage is `' + context.command.signature + '`') Maybe use this instead?
    return

@client.event
async def on_command_error(context, error):

    if isinstance(error, commands.CommandNotFound):
        return
    
    await formatAndSendHelp(context)

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

@client.command(name='reload', hidden=True)
async def _reload(context, module):
    try:
        client.unload_extension(module)
        client.load_extension(module)
        await context.message.add_reaction('👍')
    except Exception as e:
        print(f'Failed to load module {module}.', e)
        await context.message.add_reaction('👎')  

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    print(discord.__version__)

client.run(TOKEN)
