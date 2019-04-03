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
        playerManager.joinLobby(context.author.id)
        playerManager.makeFakePlayers(4)

    @commands.command(name='playerlist')
    async def playerList(self, context):
        print(playerManager.printPlayerOrder())

    @commands.command(name='role')
    async def assignRole(self, context):
        playerManager.assignPlayerRoles(context)
        await context.send(playerManager.printPlayerOrder())

    @commands.command(name='reset')
    async def resetCommand(self, context):
        await initVotingSequence(context)

    #HELPER COMMAND
    @commands.command(name='testsh')
    async def testingSecretHitlerCommand(self, context):
        joinLobby(context.author.id)
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

class PlayerManager():

    def __init__(self):
        self.currentPosition = -1
        self.playerList = []
        self.lobbyList = []

    def sortPlayerList(self):
        self.playerList.sort(key=lambda x: x.position)

    def joinLobby(self, playerID):
        self.lobbyList.append(playerID)

    def makeFakePlayers(self, num: int):
        for i in range(num):
            self.joinLobby(1 + i)

    def printPlayerOrder(self):
        message = '```'
        for i in range(len(self.playerList)):
            message += 'Player ' + str(i+1) + ': ' + self.playerList[i].name + '\n'
        message += '```'
        return message

    def advancePlayerPosition(self):
        self.currentPosition += 1

        if (self.currentPosition) in range(len(self.playerList)):
            if not self.playerList[self.currentPosition].dead:
                print('in bounds and not dead')
                print('new current is ' + str(self.currentPosition))
                return self.currentPosition
            else:
                print('current is dead, advance')
                advancePlayerPosition()
        else:
            print('reached the end of the player list')
            self.currentPosition += 1 # reset to the start of the list
            advancePlayerPosition()

    # Count the players in lobby and assign all to the playerList with role, party, and position
    def assignPlayerRoles(self, context):
        playerCount = len(self.lobbyList)                                       # Helper for player count
        if playerCount in range(5, 10+1):                                       # Check for valid number of players, 5-10
            roles = roleManager.makeRoleListForAssignment(playerCount)          # Assign the appropriate role distribution
            random.shuffle(roles)                                               # Shuffle to feel better
            positions = list(range(playerCount))                                # Make a position list of the total player count
        
            # For each player in the lobby
            for playerID in self.lobbyList:
                roleAssignment = random.choice(roles)                           # Choose a random role
                positionAssignment = random.choice(positions)                   # Choose a random position
                if roleAssignment is 'Liberal': partyAssignment = 'Liberal'     # Assign the party
                else: partyAssignment = 'Fascist'
            
                
                user = context.bot.get_user(playerID)
                if user is None: name = 'Fake ' + str(playerID)
                else: name = user.name

                # Make and assign the player to playerList
                player = Player(name=name, id=playerID, party=partyAssignment, role=roleAssignment, position=positionAssignment)
                self.playerList.append(player)
                roles.remove(roleAssignment)                                    # Remove the role from temporary list
                positions.remove(positionAssignment)                            # Remove the position from temporary list
            self.sortPlayerList()
        else:
            print('Player count invalid: ' + str(playerCount))

class Player(object):
    def __init__(self, name='Empty', id='-1', party='Unassigned', role='Unassigned', position=-1, ready=False, term_limited=False, dead=False):
        self.name = name
        self.id = id
        self.party = party
        self.role = role
        self.position = position
        self.ready = ready
        self.term_limited = term_limited
        self.dead = dead

class RoleManager():
    
    def __init__(self):
        # For 5 or 6 players, Hitler knows who their Fascist is
        self.ROLE_DISTRIBUTION = {5:  {'Liberal': 3, 'Fascist': 1, 'Hitler': 1},
                                  6:  {'Liberal': 4, 'Fascist': 1, 'Hitler': 1},
                                  7:  {'Liberal': 4, 'Fascist': 2, 'Hitler': 1},
                                  8:  {'Liberal': 5, 'Fascist': 2, 'Hitler': 1},
                                  9:  {'Liberal': 5, 'Fascist': 3, 'Hitler': 1},
                                  10: {'Liberal': 6, 'Fascist': 3, 'Hitler': 1}
                                  }


    # Make a temporary list for assigning roles to each player
    # Takes in playerCount to match to a distribution of roles
    # Returns raw list of Role strings (Liberal, Fascist, Hitler) in correct numbers
    def makeRoleListForAssignment(self, playerCount):
        roleList = []

        # For each roleString in ROLE_DISTRIBUTION, append that string a number of times
        for roleString in self.ROLE_DISTRIBUTION[playerCount]:
            # How many times to add roleString from the size in roleString:value
            for _ in range(self.ROLE_DISTRIBUTION[playerCount][roleString]):
                roleList.append(roleString)
        return roleList
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

cardManager = CardManager(17)
playerManager = PlayerManager()
roleManager = RoleManager()

currentPosition = -1

# Number emoji's
NUMBER_EMOJI = ['1\N{combining enclosing keycap}',
                '2\N{combining enclosing keycap}',
                '3\N{combining enclosing keycap}',
                '4\N{combining enclosing keycap}',
                '5\N{combining enclosing keycap}',
                '6\N{combining enclosing keycap}',
                '7\N{combining enclosing keycap}',
                '8\N{combining enclosing keycap}',
                '9\N{combining enclosing keycap}',
                '\N{keycap ten}'
                ]

# ready player

# start a president selection
# returns the message created
async def prepareChancellorSelectionPrompt(context):
    # send a DM to presidential candidate
    # prompt with all players in the game (including availability (dead or term limit))

    prompt = 'Please select your nomination for chancellor'
    for i in range(len(playerManager.playerList)):
        prompt += '\n' + playerManager.playerList[i].name
        if playerManager.playerList[i].dead:
            prompt += '\t-\t DEAD'
        if playerManager.playerList[i].term_limited:
            prompt += '\t-\t Term-Limited'
        if playerManager.playerList[i].position is playerManager.currentPosition:
            prompt += '\t-\t President Elect'

    msg = await context.send(prompt)
    
    for i in range(len(playerManager.playerList)):
        await msg.add_reaction(NUMBER_EMOJI[i])

    return msg

# Handles evaluation of the Chancellor selection
# Takes argument of the chancellorSelectionPrompt message
# Should be used inside a DM
# Removes the voting prompt after a valid selection
# Returns position of the selected Chancellor as an int
# ::FIX:: need to add confirmation for selection
async def waitForChancellorSelectionReaction(context, msg):
    # Ignore the bot reactions, and ensure the reaction is a number selection
    def check(reaction, user):
        return user != msg.author and reaction.emoji in NUMBER_EMOJI
    print('Waiting for reaction')
    reaction, user = await context.bot.wait_for('reaction_add', check=check)

    # Iterate through keys to determine actual number being represented
    # Check if that player is a valid selection for Chancellor
    for i in range(len(NUMBER_EMOJI)):
        print(str(i))
        if NUMBER_EMOJI[i] == reaction.emoji:
            if i is playerManager.currentPosition:
                await msg.remove_reaction(reaction.emoji, context.author)
                await context.send('You can\'t elect yourself! Please vote again.', delete_after=5)
                return await waitForChancellorSelectionReaction(context, msg)
            elif i is playerManager.playerList[i].dead:
                await msg.remove_reaction(reaction.emoji, context.author)
                await context.send('That player is dead! Please vote again.', delete_after=5)
                return await waitForChancellorSelectionReaction(context, msg)
            elif i is playerManager.playerList[i].term_limited:
                await msg.remove_reaction(reaction.emoji, context.author)
                await context.send('That player is term-limited for this turn. Please vote again.', delete_after=5)
                return await waitForChancellorSelectionReaction(context, msg)
            else:
                await msg.delete()
                return i
    else:
        await context.send('Something has gone horribly wrong')
        return None

async def prepareChancellorVotingPrompt(context, chancellorPos: int):
    # send PMs to all alive players
    # prompt for ja or nein
    # return a list of all messages used

    prompt = 'Voting: ' + str(playerManager.currentPosition) + '\t' + str(playerManager.chancellorPos)
    await context.send(prompt)
    return msgList

async def initVotingSequence(context):
    print(str(playerManager.advancePlayerPosition()))
    msg = await prepareChancellorSelectionPrompt(context)
    selection = await waitForChancellorSelectionReaction(context, msg)

    await context.send('Candidate Number ' + str(selection + 1) + ' selected')

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
