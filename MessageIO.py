import discord
import asyncio

async def promptForInput(context, prompt: str):
    def check(inputMessage):
        return inputMessage.author is context.author

    promptedMessage = await context.send(f'{prompt}')
    try:
        return await context.bot.wait_for("message", check = check, timeout = 60.0)
    except:
        await promptedMessage.delete()
        await context.send(f'Input has timed out, skipping input')
        return False

# Takes in a string and prompts the message
# Adds thumbs up and down
# Waits for a up or down from the user that prompted the message
# Returns True for Up, False for Down
# Also returns false if timed-out
async def promptForThumbs(context, message: str):
    def check(reaction, user):
        return user is context.author and reaction.emoji in ['👍', '👎'] and reaction.message.id == promptedText.id

    promptedText = await context.send(f'{message}')
    await promptedText.add_reaction('👍')
    await promptedText.add_reaction('👎')

    try:
        reaction, _user = await context.bot.wait_for("reaction_add", timeout = 10.0, check = check)
    except asyncio.TimeoutError:
        await promptedText.delete()
        await context.send(f'Please select a response quicker!')
        return False

    if reaction.emoji == '👍':
        await promptedText.clear_reactions()
        return True
    elif reaction.emoji == '👎':
        await promptedText.clear_reactions()
        return False
