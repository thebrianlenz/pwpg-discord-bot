from discord.ext import commands
from discord.ext.commands import Bot
from discord.ext.commands import MemberConverter
import asyncio
import json

class Grouping(commands.Cog):

    def __init__(self, bot):
        #print('init')
        self.bot = bot

    # Joins an existing group and writes to file
    @commands.command(name='sub',
                    description='Subscribe to a group. Belonging '+
                    'to a group will include you in pings.\n'+
                    'Use [list] to find existing groups.',
                    brief='Subscribe to a group.',
                    aliases=['subscribe','join'],
                    rest_is_raw=True,
                    pass_context=True
                    )
    async def joinGroup(self, context, groupName):    
        # if no group is provided, reference on_command_error
        groupList = retrieveGroupList() # update group list
        username = str(context.message.author) # helper for author's username
        
        if groupName in groupList: # check for group existance
            userList = getUserList(groupName, groupList) # create userlist

            # user already in group
            if username in userList:
                await context.send('`' + username + '` is already in `' + groupName + '`.')
                return

            userList.append(username) # add new user
            groupList[groupName] = userList # set userList to the group
            writeGroupList(groupList) # write to file
            await context.send('Username `' + str(context.message.author) + '` has been added to the group `' +
                            groupName + '`.')
            await context.send('`' + groupName + '` now has ' + str(len(userList)) + ' members.')
        else:
            await context.send('The group `' + groupName + '` doesn\'t exist.\n' +
                            'Use `!create <name>` to create a group')

    # Leaves a group the user is a member of
    @commands.command(name='unsub',
                    description='Unsubscribe from a group that you are a part of. Removes you from future '+
                    'pings and notifications for this group.',
                    brief='Unsubscribe from a group.',
                    aliases=['unsubscribe', 'leave'],
                    rest_is_raw=True,
                    pass_context=True
                    )
    async def leaveGroup(self, context, groupName):
        # if no group is provided, reference on_command_error
        groupList = retrieveGroupList()
        username = str(context.message.author)

        userList = getUserList(groupName, groupList)

        if username in userList:
            userList.remove(username)
            print('userlist \n' + str(userList))
            groupList[groupName] = userList
            print('grouplist \n' + str(groupList))
            writeGroupList(groupList)
            await context.send('`' + username + '` has been removed from `' + groupName + '`.')
        else:
            await context.send('`' + username + '` is not a part of the `' + groupName + '` group.')

    # Retrieves current group or member list 
    @commands.command(name='list',
                    description='List all groups. To see members of a specific group, include the group name.',
                    brief='List all groups, or members of a group.',
                    aliases=['ls'],
                    invoke_without_command=True,
                    rest_is_raw=True,
                    pass_context=True
                    )
    async def listGroups(self, context, groupName=None):

        groupList = retrieveGroupList()

        # If no groupName is provided, list all groups
        if (groupName is None) or (groupName == 'group') or (groupName == 'groups'):
            groupList = retrieveGroupList()
            temp = ''
            for tempgroup in groupList:
                temp += '\n' + tempgroup
            await context.send('There are `' + str(len(groupList)) + '` groups.```' + temp + '```')
            return

        elif groupName in groupList:
            userList = getUserList(groupName, groupList)
            
            # List the members of the given group name
            if userList:
                temp = ''
                for tempuser in userList:
                    temp += tempuser + '\n'
                await context.send('The group `' + groupName + '` has `' + str(len(userList)) + '` members.```' +
                                temp + '```')
            else:
                await context.send('The group `' + groupName + '` is empty! Use `!join <groupName>` to join.')

        # The groupName doesn't exist
        else:
            await context.send('The group `' + groupName + '` doesn\'t exist.\n' +
                            'Use `!create <name>` to create a group')
            
    # Creates a non-existing group and writes to file
    @commands.command(name='create',
                    description='Make a group and add yourself to it. Groups can be pinged using [ping].',
                    brief='Create a group',
                    aliases=['make'],
                    pass_context=True
                    )
    async def createGroup(self, context, groupName):
        groupList = retrieveGroupList()
        if groupName in groupList:
            await context.send('The group `' + groupName + '` already exists.\n' +
                            'Use `!join ' + groupName + '` to join the group')
            return
        else:
            groupList[groupName] = [str(context.message.author),]
            writeGroupList(groupList)
            await context.send('The group `' + groupName + '` has been created.\n' +
                            'User `' + str(context.message.author) + '` has been added.')

    @commands.command(name='play',
                    description='Start a lobby to play. [WIP]',
                    brief='[WIP]',
                    pass_context=True
                    )
    async def createGameLobby(self, context, groupName):
        # make active game
        # need to list active games
        # description? (gamemmode)
        # 
        return

    @commands.command(name='ping',
                    description='Ping a group. Pinging sends a single message to all users in a group. '+
                    'Include an optional message for the ping.',
                    brief='Ping a group',
                    aliases=['poke'],
                    invoke_without_command=True,
                    pass_context=True
                    )
    async def pingGroup(self, context, groupName, *, optionalMessage=None):
        groupList = retrieveGroupList()
        memConverter = MemberConverter()

        message = '`' + context.author.display_name + '` has pinged `' + groupName + '`.'

        if optionalMessage != None:
            message = message + '```' + optionalMessage + '```'            

        if groupName in groupList:
            for user in getUserList(groupName, groupList):
                member = await memConverter.convert(context, user)
                await member.send(message)
        else:
            await context.send('The group `' + groupName + '` doesn\'t exist.\n Use `' + context.createGroup.signature + '`')

def setup(bot):
    bot.add_cog(Grouping(bot))

def teardown(bot):
    bot.remove_cog('Grouping')

# Helper function
# Reload the Group List from file
def retrieveGroupList():
    with open('groups.json', 'r') as f:
        return json.load(f)
        
# Helper function
# Write the Current Group List to file
def writeGroupList(data):
    with open('groups.json', 'w') as f:
            json.dump(data, f, indent=4) 

# Helper function
# Retrieves current userList
def getUserList(groupName, groupList):
    if groupName in groupList:
        return groupList.get(groupName)
    else:
        return False