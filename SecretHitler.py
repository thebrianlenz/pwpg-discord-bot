from discord.ext import commands
from discord.ext.commands import Bot
from discord.ext.commands import Paginator
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
player assignment
    take number of players and select appropriate distribution and assign
game 'lobby'
    let players join to be included in player assignment
admin commands (start, end)
    after lobby is created
presidential powers
    examine player, bullet, top cards, veto, select next president
president selection conditions (can't pick previous etc)
'''
gameActive = True
players = {}

p = Paginator()

class SecretHitler(commands.Cog, command_attrs=dict(hidden=True)):
    
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    async def makeBoard(self, context):
        t = TileBuilder(10, 10)
        t.initBoard()

        #p.add_line(t.getLineString(0))
        for line in range(len(t.grid)):
            p.add_line(t.getLineString(line))

        for line in p.pages:
            await context.send(line)

        #p.add_line


    @commands.command(name='mkplayer')
    async def makePlayer(self, context, num: int):
        for i in range(num):
            joinPlayerList('player' + str(i))

    @commands.command(name='playerlist')
    async def playerList(self, context):
        await context.send(players)

    @commands.command(name='role')
    async def assignRole(self, context):
        roles = ['Liberal', 'Fascist', 'Hitler']
        if len(players) in range(5, 10):
            for p in players:
                players[p] = str(random.choice(roles))
        else:
            await context.send('Must have between 5 and 10 players')

def joinPlayerList(username):
    players[username] = None

async def displayBoard():
    pass

class TileBuilder:

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = []

    def initBoard(self):
        for y in range(self.height):
            self.grid.append([])
            for x in range(self.width):
                self.grid[y].append(str(y) + str(x))

        #print(self.grid)
    
    def getLineString(self, line: int):
        tempString = ''
        for i in self.grid[line]:
            tempString += i + ' '
        return tempString

# while (gameActive):
#     print(players)

def setup(bot):
    bot.add_cog(SecretHitler(bot))

def teardown(bot):
    bot.remove_cog('SecretHitler')