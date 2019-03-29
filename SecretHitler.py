from discord.ext import commands
from discord.ext.commands import Bot
from discord.ext.commands import Paginator
from discord import Message
from discord import Client
import asyncio
import discord
import random

class SecretHitler(commands.Cog, command_attrs=dict(hidden=True)):

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def makeBoard(self, context):
        b = Board(50, 10)
        b.clearBoard('X')

        shapeCard = AsciiShape(5, 5, 5, 4)
        shapeCard.stringToShape(b.CARD_SPRITE)
        b.drawShape(shapeCard)

        shapeCard = AsciiShape(10, 5, 5, 4)
        shapeCard.stringToShape(b.CARD_SPRITE)
        b.drawShape(shapeCard)

        shapeCard = AsciiShape(15, 5, 5, 4)
        shapeCard.stringToShape(b.CARD_SPRITE)
        b.drawShape(shapeCard)

        shapeCard = AsciiShape(20, 5, 5, 4)
        shapeCard.stringToShape(b.CARD_SPRITE)
        b.drawShape(shapeCard)

        shapeCard = AsciiShape(25, 5, 5, 4)
        shapeCard.stringToShape(b.CARD_SPRITE)
        b.drawShape(shapeCard)
        
        for line in b.assemblePage():
            await context.send(line)

    @commands.command(name='joinSH')
    async def makePlayer(self, context):
        joinActiveLobby(context)
        makeFakePlayers(context, 4)
        print(lobbyList)

    @commands.command(name='playerlist')
    async def playerList(self, context):
        print(playerList)

    @commands.command(name='role')
    async def assignRole(self, context):
        evaluateAndAssignPlayerRoles(context)
        await context.send(printPlayerOrder())

    @commands.command(name='startsh')
    async def startSecretHitler(self, context):
        global isLoaded
        isLoaded = True
        await mainLoop(context, TICK_RATE)

    @commands.command(name='endsh')
    async def endSecretHitler(self, context):
        global isLoaded
        isLoaded = False

    @commands.command(name='next')
    async def nextPlayer(self, context):
        advanceAndGetCurrentPlayer()
        await context.send(playerList[currentPosition]['name'])

    @commands.command(name='reset')
    async def resetCommand(self, context):
        await initVotingSequence(context)

    @commands.command(name='makeDeck')
    async def createNewDeckCommand(self, context):
        print('Deck Created')
        cardManager.createDeck(11, 6)

    @commands.command(name='deal')
    async def dealCards(self, context):
        print(cardManager.drawCards(3))


    #HELPER COMMAND
    @commands.command(name='testsh')
    async def testingSecretHitlerCommand(self, context):
        joinActiveLobby(context)
        makeFakePlayers(context, 4)
        evaluateAndAssignPlayerRoles(context)
        await context.send(printPlayerOrder())

class AsciiShape(object):

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.tile = []
        self.initTile()

    def initTile(self):
        for y in range(self.height):
            self.tile.append([])
            for _ in range(self.width):
                self.tile[y].append(' ')

    def fillLetterToShape(self, letter=' '):
        for y in range(self.height):
            for x in range(self.width):
                self.tile[y][x] = letter

    def stringToShape(self, strShape: str):
        if len(strShape) is (self.width * self.height):
            for y in range(self.height):
                for x in range(self.width):
                    self.tile[y][x] = strShape[y*self.width + x]
        else:
            print('size mismatch')

class Board:

    CARD_SPRITE=(" ___ "
                 "|   |"
                 "|   |"
                 "|___|")

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = []
        self.initGrid()

    def initGrid(self):
        for y in range(self.height):
            self.grid.append([])
            for _ in range(self.width):
                self.grid[y].append(' ')

    def clearBoard(self, letter=' '):
        for y in range(self.height):
            for x in range(self.width):
                self.grid[y][x] = letter

        #print(self.grid)

    def assemblePage(self):
        p = Paginator()
        for line in self.grid:
            p.add_line(''.join(line))
        return p.pages

    def drawShape(self, shape: AsciiShape):
        for h in range(shape.height):
            for w in range(shape.width):
                self.grid[shape.y+h][shape.x+w] = shape.tile[h][w]
        return

class CardManager():
    
    deck = []
    hand = []
    discardPile = []
    gameBoard = []

    def __init__(self, deckSize: int):
        self.deckSize = deckSize

    def createDeck(self, numFascist, numLiberal):
        deck = []
        for i in range(numFascist):
            self.deck.append('Fascist')
        for i in range(numLiberal):
            self.deck.append('Liberal')

        random.shuffle(self.deck)
        return self.deck

    # Remove from deck, place in hand
    # If less than three cards, merge and reshuffle?
    # Returns hand
    def drawCards(self, numCards: int):
        for _ in range(numCards):
            card = self.deck.pop()
            self.hand.append(card)
        return self.hand

    # Select a card to discard from hand
    # Returns remaining cards in hand
    def selectCard(self, pos: int):
        card = self.hand.pop(pos)
        self.discardPile.append(card)
        return self.hand

    # Select a card to play to the game board from hand
    # Moves remaining cards in hand to the discard pile
    # Returns the game board
    def playCard(self, pos: int):
        card = self.hand.pop(pos)
        self.gameBoard.append(card)
        self.dicardPile.extend(self.hand)
        return gameBoard

# Soon
'''
display "board"
    ascii or photos?
    needs to be editable for multiple conditions
player turns
    cycle through the player list to pass presidental control around
player votes
    vote with reactions? through pm most likely for secrecy
deck management
    control deck of liberal/fascist cards, dealing, discarding, and playing
play cards
    select from choices to play to table
win conditions
    number of cards played, hitler voted in after certain turns
game 'lobby'
    let players join to be included in player assignment
admin commands (start, end)
    after lobby is created
presidential powers
    examine player, bullet, top cards, veto, select next president
president selection conditions (can't pick previous etc)

player assignment
    take number of players and select appropriate distribution and assign
determine player order
'''
# One loop every TICK_RATE seconds

TICK_RATE = 2

gameActive = True
playerList = {}
lobbyList = []
cardManager = CardManager(17)

currentPosition = 0

# For 5 or 6 players, Hitler knows who their Fascist is
ROLE_DISTRIBUTION = {5:  {'Liberal': 3, 'Fascist': 1, 'Hitler': 1},
                     6:  {'Liberal': 4, 'Fascist': 1, 'Hitler': 1},
                     7:  {'Liberal': 4, 'Fascist': 2, 'Hitler': 1},
                     8:  {'Liberal': 5, 'Fascist': 2, 'Hitler': 1},
                     9:  {'Liberal': 5, 'Fascist': 3, 'Hitler': 1},
                     10: {'Liberal': 6, 'Fascist': 3, 'Hitler': 1}
                     }

# Number emoji's
NUMBER_EMOJI = {1: '1\N{combining enclosing keycap}',
                2: '2\N{combining enclosing keycap}',
                3: '3\N{combining enclosing keycap}',
                4: '4\N{combining enclosing keycap}',
                5: '5\N{combining enclosing keycap}',
                6: '6\N{combining enclosing keycap}',
                7: '7\N{combining enclosing keycap}',
                8: '8\N{combining enclosing keycap}',
                9: '9\N{combining enclosing keycap}',
                10: '\N{keycap ten}'
                }

# let players ready up

# Makes a player, with assosciated properties
def makePlayerProps(name='Empty', uniqID='-1', party='Unassigned', role='Unassigned', position=-1, ready=False, tl=False, dead=False):
    props = {'name': name,
             'id': uniqID,
             'party': party,
             'role': role,
             'position': position,
             'ready': ready,
             'term-limited': tl,
             'dead': dead
             }
    return props

def joinActiveLobby(context):
    lobbyList.append(context.author.id)

def makeFakePlayers(context, num: int):
    for i in range(num):
        lobbyList.append(1 + i)

def printPlayerOrder():
    message = '```'
    for i in range(len(playerList)):
        print(playerList[i])
        message += 'Player ' + str(i+1) + ': ' + playerList[i]['name'] + '\n'
    message += '```'
    return message

# Sets the author in the active lobby to 'ready'
# Author must already be in lobby
def readyActiveLobby(context):
    if context.author.id in playerList:
        playerList[context.author.id]['Ready'] = True
    else:
        print('Player not in lobby')

# Make a temporary list for assigning roles to each player
# Takes in dictionary of Role Count -- ROLE_DISTRIBUTION[i]
def makeRoleListForAssignment(roleLayout: dict):
    roleList = []
    for i in roleLayout:
        for _ in range(roleLayout[i]):
            roleList.append(i)
    return roleList

# Count the players in lobby and assign all to the playerList with role, party, and position
def evaluateAndAssignPlayerRoles(context):
    playerCount = len(lobbyList)                                            # Helper for player count
    if playerCount in range(5, 10+1):                                       # Check for valid number of players, 5-10
        roles = makeRoleListForAssignment(ROLE_DISTRIBUTION[playerCount])   # Assign the appropriate role distribution
        random.shuffle(roles)                                               # Shuffle to feel better
        positions = list(range(playerCount))                                # Make a position list of the total player count
        
        # For each player in the lobby
        for playerID in lobbyList:
            roleAssignment = random.choice(roles)                           # Choose a random role
            positionAssignment = random.choice(positions)                   # Choose a random position
            if roleAssignment is 'Liberal': partyAssignment = 'Liberal'     # Assign the party
            else: partyAssignment = 'Fascist'
            
            # Make and assign the player to playerList
            user = context.bot.get_user(playerID)
            if user is None: name = 'Fake ' + str(playerID)
            else: name = user.name
            playerList[positionAssignment] = makePlayerProps(name=name,
                                                    uniqID=playerID,
                                                    party=partyAssignment,
                                                    role=roleAssignment,
                                                    position=positionAssignment
                                                    )
            roles.remove(roleAssignment)                                    # Remove the role from temporary list
            positions.remove(positionAssignment)                            # Remove the position from temporary list
    else:
        print('Player count invalid: ' + str(playerCount))

# Set the global var of current player
# Helper function so global doesn't need to be declared
def setCurrentPlayer(pos: int):
    global currentPosition
    currentPosition = pos
    return currentPosition

# Advancing the current player happens first, logic occurs after to see if it's acceptable
def advanceAndGetCurrentPlayer():
    setCurrentPlayer(currentPosition+1)

    if (currentPosition) in range(len(playerList)):
        if not playerList[currentPosition]['dead']:
            print('in bounds and not dead')
            print('new current is ' + str(currentPosition))
            return currentPosition
        else:
            print('current is dead, advance')
            advanceAndGetCurrentPlayer()
    else:
        print('reached the end of the player list')
        setCurrentPlayer(0) # reset to the start of the list
        advanceAndGetCurrentPlayer()

# start a president selection
# returns the message created
async def prepareChancellorSelectionPrompt(context):
    # send a DM to presidential candidate
    # prompt with all players in the game (including availability (dead or term limit))

    prompt = 'Please select your nomination for chancellor'
    for i in range(len(playerList)):
        prompt += '\n' + playerList[i]['name']
        if playerList[i]['dead']:
            prompt += '\t-\t DEAD'
        if playerList[i]['term-limited']:
            prompt += '\t-\t Term-Limited'

    msg = await context.send(prompt)
    
    for i in range(len(playerList)):
        await msg.add_reaction(NUMBER_EMOJI[i+1])

    return msg


# Handles evaluation of the Chancellor selection
# Takes in a numbered reaction from NUMBER_EMOJI
# Should be used inside a DM
# Removes the voting prompt after a valid selection
# ::FIX:: need to add confirmation for selection
async def waitForChancellorSelectionReaction(context, msg):
    # Ignore the bot reactions, and ensure the reaction is a number selection
    def check(reaction, user):
        return user != msg.author and reaction.emoji in NUMBER_EMOJI.values()
    print('Waiting for reaction')
    reaction, user = await context.bot.wait_for('reaction_add', check=check)

    # Iterate through keys to determine actual number being represented
    # Check if that player is a valid selection for Chancellor
    for i in NUMBER_EMOJI.keys():
        if NUMBER_EMOJI[i] == reaction.emoji:
            if i is currentPosition:
                await msg.remove_reaction(reaction.emoji, context.author)
                await context.send('You can\'t elect yourself! Please vote again.', delete_after=5)
                return await waitForChancellorSelectionReaction(context, msg)
            elif i is playerList[i]['dead']:
                await msg.remove_reaction(reaction.emoji, context.author)
                await context.send('That player is dead! Please vote again.', delete_after=5)
                return await waitForChancellorSelectionReaction(context, msg)
            elif i is playerList[i]['term-limited']:
                await msg.remove_reaction(reaction.emoji, context.author)
                await context.send('That player is term-limited for this turn. Please vote again.', delete_after=5)
                return await waitForChancellorSelectionReaction(context, msg)
            else:
                await msg.delete()
                return i
    else:
        await context.send('Something has gone horribly wrong')
        return None

async def initVotingSequence(context):
    print(str(advanceAndGetCurrentPlayer()))
    msg = await prepareChancellorSelectionPrompt(context)
    selection = await waitForChancellorSelectionReaction(context, msg)

    await context.send('Candidate Number ' + str(selection) + ' selected')



# Main loop for Secret Hitler
# Handle display drawing
async def mainLoop(context, tickRate: int):
    gameBoardMessage = None
    count = 0
    while isLoaded:
        if gameBoardMessage is None:
            gameBoardMessage = await context.send('Here is the base message for SH')
        else:
            await gameBoardMessage.edit(content=str(count))
            count += 1
        await asyncio.sleep(tickRate)

def setup(bot):
    global isLoaded
    isLoaded = True
    bot.add_cog(SecretHitler(bot))

def teardown(bot):
    global isLoaded
    isLoaded = False
    bot.remove_cog('SecretHitler')
