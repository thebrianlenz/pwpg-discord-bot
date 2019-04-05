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

    @commands.command(name='fake')
    async def makeFakePlayers(self, context, num=4):
        playerManager.makeFakePlayers(num)

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
    async def testingSecretHitlerCommand(self, context, num=4):
        playerManager.joinLobby(context.author.id)
        playerManager.makeFakePlayers(num)
        playerManager.assignPlayerRoles(context)

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
    """Manages all Player related components.

    This manager is used as a single container for keeping
    track of players. This includes the current position,
    president, and chancellor.

    Attributes
    ----------
    currentPosition : int
        the current position in the playerList
    playerList : list
        contains a list of Player objects that have been
        assigned their attributes (role, position, etc)
    lobbyList : list
        contains a list of user_ids that are ready to be
        added to a game
    candidate_pre : int
        the position of the Presidential Candidate (voting phase)
    candidate_cha : int
        the position of the Chancellor Candidate (voting phase)
    president : int
        the position of the elected President (play phase)
    chancellor : int
        the position of the elected Chancellor (play phase)

    """

    def __init__(self):
        self.currentPosition = -1
        self.playerList = []
        self.lobbyList = []
        self.candidate_pre = -1
        self.candidate_cha = -1
        self.president = -1
        self.chancellor = -1
        self.votes_recorded = 0

    def sortPlayerList(self):
        """Sort the playerList by the Player's positions"""

        self.playerList.sort(key=lambda x: x.position)

    def joinLobby(self, playerID):
        """Append a playerID to the lobbyList"""

        self.lobbyList.append(playerID)

    def makeFakePlayers(self, num: int):
        """Temporary helper function for populating playerList."""

        for i in range(num):
            self.joinLobby(1 + i)

    def printPlayerOrder(self):
        """Creates a simple string including all players in playerList and their name"""

        message = '```'
        for i in range(len(self.playerList)):
            message += 'Player ' + str(i+1) + ': ' + self.playerList[i].name + '\n'
        message += '```'
        return message

    def advancePlayerPosition(self):
        """Advances the current position by one, and returns the new position"""

        self.currentPosition += 1 # Increase current position

        if (self.currentPosition) in range(len(self.playerList)):
            if not self.playerList[self.currentPosition].dead:
                print('New Current Position: ' + str(self.currentPosition))
                return self.currentPosition
            else:
                advancePlayerPosition()
        else:
            self.currentPosition = -1 # reset to the start of the list
            advancePlayerPosition()

    def assignPlayerRoles(self, context):
        """Takes all users in the lobbyList and turns them into Players for the playerList"""

        playerCount = len(self.lobbyList)                                       # Helper for player count
        if playerCount in range(5, 10+1):                                       # Check for valid number of players, 5-10
            self.playerList.clear()                                             # Clear any old playerList
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
            self.lobbyList.clear()
        else:
            print('Player count invalid: ' + str(playerCount))

    def setElectionCandidates(self, president: int, chancellor: int):
        """Set the presidential and chancellor candidates"""

        self.candidate_pre = president
        self.candidate_cha = chancellor

class Player(object):
    """Acts as a container for all attributes required for a Player"""

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

bind these commands to specific channels
perhaps have a designated channel for bot displays (board, votes, etc)
maybe look into having player votes and selections done not in dms, but "private" channels
    mainly for easier access, instead of having to jump into and out of the DM windows

'''

# One loop every TICK_RATE seconds
TICK_RATE = 2

cardManager = CardManager(17)
playerManager = PlayerManager()
roleManager = RoleManager()

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
# needs to be forced as a DM to the Presidential Candidate
async def prepareChancellorSelectionPrompt(context):
    """Creates and sends the Chancellor Selection Prompt for the Presidential Candidate.
    Returns the created message."""

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
            prompt += '\t-\t Presidential Candidate'

    msg = await context.send(prompt)
    
    for i in range(len(playerManager.playerList)):
        await msg.add_reaction(NUMBER_EMOJI[i])

    return msg

# Handles evaluation of the Chancellor selection
# Takes argument of the chancellorSelectionPrompt message
# msg should be from inside a DM
# Removes the voting prompt after a valid selection
# Returns position of the selected Chancellor as an int
# ::FIX:: need to add confirmation for selection
async def waitForChancellorSelectionReaction(context, msg):
    """Waits for a reaction on the designated message and returns it as an int"""

    # Ignore the bot reactions, and ensure the reaction is a number selection
    def check(reaction, user):
        return not user.bot and reaction.emoji in NUMBER_EMOJI
    reaction, user = await context.bot.wait_for('reaction_add', check = check)

    # Iterate through keys to determine actual number being represented
    # Check if that player is a valid selection for Chancellor
    for i in range(len(NUMBER_EMOJI)):
        if NUMBER_EMOJI[i] == reaction.emoji:
            if i is playerManager.currentPosition:
                await msg.remove_reaction(reaction.emoji, user)
                await context.send('You can\'t elect yourself! Please vote again.', delete_after = 5)
                return await waitForChancellorSelectionReaction(context, msg)
            elif i is playerManager.playerList[i].dead:
                await msg.remove_reaction(reaction.emoji, user)
                await context.send('That player is dead! Please vote again.', delete_after = 5)
                return await waitForChancellorSelectionReaction(context, msg)
            elif i is playerManager.playerList[i].term_limited:
                await msg.remove_reaction(reaction.emoji, user)
                await context.send('That player is term-limited for this turn. Please vote again.', delete_after = 5)
                return await waitForChancellorSelectionReaction(context, msg)
            else:
                await msg.delete()
                return i
    else:
        await context.send('Something has gone horribly wrong')
        return None

async def prepareChancellorVotingPrompt(context):
    """Creates and sends a message to all living players with a voting ballot
    
    Returns a list of all Messages created"""

    prompt = 'Voting for Candidates: President - ' + str(playerManager.candidate_pre) + '\tChancellor - ' + str(playerManager.candidate_cha)
    msgList = []
    # Iterate through Players in playerList
    for p in playerManager.playerList:
        if not p.dead: 
            # If they are alive, give them a voting ballot ::FIX:: move this to DMs?
            msgList.insert(p.position, await context.send(p.name + ' vote ballot\n' + prompt))
            await msgList[p.position].add_reaction('👍')
            await msgList[p.position].add_reaction('👎')
        else: print(p.name + ' is dead. No vote.')
    return msgList

async def waitForCandidateVoteReaction(context, msg):
    """Waits for a reaction to a Candidate vote on a ballot.
    
    ::FIX:: Needs to return the vote choice, possibly the message/voter
    Alter to wait for simply the confirmation and then count vote"""

    def check(reaction, user):
        return not user.bot and reaction.emoji in ['👍', '👎'] and reaction.message.id == msg.id

    reaction, user = await context.bot.wait_for("reaction_add", check = check)
    playerManager.votes_recorded += 1
    await context.send('Votes recorded: {}'.format(playerManager.votes_recorded))


    confirmMessage = await context.send('confirm selection {} {}'.format(reaction.emoji, user.name))
    await confirmMessage.add_reaction('👍')
    await confirmMessage.add_reaction('👎')
    def check2(reaction, user):
        return not user.bot and reaction.emoji in ['👍', '👎'] and reaction.message.id == confirmMessage.id

    await context.bot.wait_for("reaction_add", check = check2)
    print('Confirmed vote')

    return reaction, user

async def initVotingSequence(context):
    """Includes entire sequence of voting functions.
    
        1. Advances playerPosition
        2. Creates the Selection Prompt for Chancellor
        3. Waits for the Chancellor Selection
        4. Sets the Candidates
        5. Creates the Voting Prompts for the Candidates
        6. Waits on all reactions from voting
    """

    print(str(playerManager.advancePlayerPosition()))
    chancellorSelectMessage = await prepareChancellorSelectionPrompt(context)
    chancellorCandidatePosition = await waitForChancellorSelectionReaction(context, chancellorSelectMessage)
    playerManager.setElectionCandidates(playerManager.currentPosition, chancellorCandidatePosition)
    chancellorVotingList = await prepareChancellorVotingPrompt(context)
    tasks = []
    for m in chancellorVotingList:
        tasks.append(waitForCandidateVoteReaction(context, m))

    results = await asyncio.gather(*tasks)

    print(results[0])

    print('Voting finished')

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
