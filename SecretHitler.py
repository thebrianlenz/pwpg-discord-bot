from discord.ext import commands
from discord.ext.commands import Bot
from discord.ext.commands import Paginator
from discord import Message
from discord import Client
import asyncio
import discord
import random

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

# For 5 or 6 players, Hitler knows who their Fascist is
ROLE_DISTRIBUTION = {5:  {'Liberal': 3, 'Fascist': 1, 'Hitler': 1},
                     6:  {'Liberal': 4, 'Fascist': 1, 'Hitler': 1},
                     7:  {'Liberal': 4, 'Fascist': 2, 'Hitler': 1},
                     8:  {'Liberal': 5, 'Fascist': 2, 'Hitler': 1},
                     9:  {'Liberal': 5, 'Fascist': 3, 'Hitler': 1},
                     10: {'Liberal': 6, 'Fascist': 3, 'Hitler': 1}
                     }

# add players to player list (lobby)
# let players ready up
# count number of players and evaluate
# assign roles randomly
# assign player order (random?)
# assign first president

# Makes a player, with assosciated properties
def makePlayerProps(name='Empty', party='Unassigned', role='Unassigned', position=-1, ready=False, tl=False, dead=False):
    props = {'Name': name,
             'Party': party,
             'Role': role,
             'Position': position,
             'Ready': ready,
             'Term-Limited': tl,
             'Dead': dead
             }
    return props

# Adds the author of the command to the active lobby as 'unready'
def joinActiveLobby(context):
    #playerList[context.author.id] = makePlayerProps(name=context.author.name)
    lobbyList.append(context.author.id)

# TEMPORARY HELPER FOR TESTING
def makeFakePlayers(context, num: int):
    for i in range(num):
        lobbyList.append(1 + i)

# Sets the author in the active lobby to 'ready'
# Author must already be in lobby
def readyActiveLobby(context):
    if context.author.id in playerList:
        playerList[context.author.id]['Ready'] = True
    else:
        print('Player not in lobby')

def _makeRoleListForAssignment(roleLayout: dict):
    roleList = []
    for i in roleLayout:
        for _ in range(roleLayout[i]):
            roleList.append(i)
    return roleList

# Count the players in lobby and assign all to the playerList with role, party, and position
def evaluateAndAssignPlayerRoles(context):
    playerCount = len(lobbyList)                                            # Helper for player count
    if playerCount in range(5, 10+1):                                       # Check for valid number of players, 5-10
        roles = _makeRoleListForAssignment(ROLE_DISTRIBUTION[playerCount])  # Assign the appropriate role distribution
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
            if user is None: name = 'Fake Player: ' + str(playerID)
            else: name = user.name
            playerList[playerID] = makePlayerProps(name=name,
                                                    party=partyAssignment,
                                                    role=roleAssignment,
                                                    position=positionAssignment
                                                    )
            roles.remove(roleAssignment)                                    # Remove the role
            positions.remove(positionAssignment)                            # Remove the position
            print(playerList[playerID])
    else:
        print('Player count invalid: ' + str(playerCount))

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

class SecretHitler(commands.Cog, command_attrs=dict(hidden=True)):

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def makeBoard(self, context):
        b = Board(50, 10)
        b.clearBoard('X')

        # shape = AsciiShape(0, 0, 5, 5)
        # shape.fillLetterToShape('x')
        # b.drawShape(shape)

        # shape2 = AsciiShape(3, 3, 5, 5)
        # shape2.fillLetterToShape('y')
        # b.drawShape(shape2)

        # shape3 = AsciiShape(2, 1, 5, 2)
        # shape3.stringToShape('teststests')
        # b.drawShape(shape3)

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
        makeFakePlayers(context, 9)
        print(lobbyList)

    @commands.command(name='playerlist')
    async def playerList(self, context):
        print(playerList)

    @commands.command(name='role')
    async def assignRole(self, context):
        evaluateAndAssignPlayerRoles(context)

    @commands.command(name='startsh')
    async def startSecretHitler(self, context):
        global isLoaded
        isLoaded = True
        await mainLoop(context, TICK_RATE)

    @commands.command(name='endsh')
    async def endSecretHitler(self, context):
        global isLoaded
        isLoaded = False

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

def setup(bot):
    global isLoaded
    isLoaded = True
    bot.add_cog(SecretHitler(bot))
    #bot.loop.create_task(mainLoop(bot.context, TICK_RATE))

def teardown(bot):
    global isLoaded
    isLoaded = False
    bot.remove_cog('SecretHitler')