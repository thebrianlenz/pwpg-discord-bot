from discord.ext import commands
from discord.ext.commands import Bot
from discord.ext.commands import MemberConverter
import asyncio
import json

GROUP_FILE = 'groupsData.json'

RESERVED_WORDS = ['group','groups','all']

groupData = {}

#temp = test['group']['group1']['members']

#groupsJSON = {groupName: {desc:desc, members: [list]}}

# members: [listOfMembers]
# groupName: {description, members}

# TODO schedule file write for saving, listen for event from pwpg-bot?

class GroupManager(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot
        readGroupData()

    @commands.command(name='jsdump', hidden=True)
    async def dump(self, context):
        print(groupData)
        writeGroupData()


    # Return robust list of all groups with member count (short descr too?)
    # Pulls from current groupData
    @commands.command(name='list',
                    description='List all groups. To see members of a specific group, include the group name.',
                    brief='List all groups, or members of a group.',
                    aliases=['ls'],
                    invoke_without_command=True,
                    rest_is_raw=True,
                    pass_context=True
                    )
    async def listGroupsCommand(self, context, groupName=None):
        messageToSend = ''
        if (groupName is None) or (groupName is RESERVED_WORDS) or (groupName not in groupData):
            messageToSend += 'There are currently ' + str(len(groupData)) + ' groups on PWPG!\n'
            for name in groupData:
                messageToSend += name + ': ' + groupData[name]['description'] + '\n\tMembers: ' + str(len(groupData[name]['member'])) + '\n'

        elif groupName in groupData:
            messageToSend += groupName + ' has ' + str(len(groupData[groupName]['member'])) + ' members.\n' + groupData[groupName]['description']
        
        else:
            print('how did this even happen?')
            messageToSend += 'THIS SHOULD NOT BE SEEN!?'

        await context.send('```' + messageToSend + '```')
    
    # TODO docs and command params
    @commands.command(name='members',
                    hidden=True,
                    pass_context=True
                    )
    async def listGroupMembersCommand(self, context, groupName):
        if groupName in groupData:
            print ('print shit for a group')
        else: print ('no group')

    # Joins an existing group and writes to file
    # TODO error calls?
    @commands.command(name='sub',
                    description='Subscribe to a group. Belonging '+
                    'to a group will include you in pings.\n'+
                    'Use [list] to find existing groups.',
                    brief='Subscribe to a group.',
                    aliases=['subscribe','join'],
                    rest_is_raw=True,
                    pass_context=True
                    )
    async def joinGroupCommand(self, context, groupName):
        if joinGroup(context, groupName):
            print('joined')
            await context.send('`'+ str(context.author) + '` has been added to `' + groupName + '`')
        else:
            print('failed')
            await context.send('`'+ str(context.author) + '` could not be added to `' + groupName + '`')

    # TODO leave group
    # Leaves a group the user is a member of
    @commands.command(name='unsub',
                    description='Unsubscribe from a group that you are a part of. Removes you from future '+
                    'pings and notifications for this group.',
                    brief='Unsubscribe from a group.',
                    aliases=['unsubscribe', 'leave'],
                    rest_is_raw=True,
                    pass_context=True
                    )
    async def leaveGroupCommand(self, context, groupName):
        if leaveGroup(context, groupName):
            await context.send('`' + str(context.author) + '` has left `' + groupName + '`')
        else:
            await context.send('`' + str(context.author) + '` could not leave `' + groupName + '`')

    # TODO ping group

    @commands.command(name='ping',
                    description='Ping a group. Pinging sends a single message to all users in a group. '+
                    'Include an optional message for the ping.',
                    brief='Ping a group',
                    aliases=['poke'],
                    invoke_without_command=True,
                    pass_context=True
                    )
    async def pingGroupCommand(self, context, groupName, *, optionalMessage=None):
        if optionalMessage is not None:
            await context.send('NOT IMPLEMENTED\n' + groupName + '\n' + optionalMessage)


    # Creates a non-existing group
    # Syncs with groupData
    # TODO move writing to pwpg-bot loop?
    @commands.command(name='create',
                    description='Make a group and add yourself to it. Groups can be pinged using [ping].',
                    brief='Create a group',
                    aliases=['make'],
                    pass_context=True
                    )
    async def createGroupCommand(self, context, groupName, description=None):
        if addGroup(context, groupName, description):
            print('create group success')
            writeGroupData()
        else:
            print('create group failed')

    # Deletes an existing group
    # Sync to groupData
    # TODO write in bot loop
    @commands.command(name='delete',
                    description='Removes an existing group. Confirmation is not implemented yet.',
                    brief='Remove a group',
                    aliases=['remove', 'del', 'rm'],
                    hidden=True,
                    pass_context=True
                    )
    async def deleteGroupCommand(self, context, groupName):
        if removeGroup(groupName):
            print('group deleted')
            writeGroupData()
        else:
            print('delete group failed')

# Create a group entry with an optional name
# Returns false if group exists
# TODO error throws
def addGroup(context, name: str, description=None):
    global groupData
    if name in groupData:
        print('group exists -> throw error')
        return False
    else:
        if description is None: description='No Description'
        groupData[name] = {'description': description, 'member': {str(context.author):{}}}
        return True

# Removes entire entry for a group
# Returns false if group doesn't exist
# TODO error throws mark file has changes?
def removeGroup(name: str):
    global groupData
    if name in groupData.keys():
        groupData.pop(name)
        return True
    else:
        print('group doesn\'t exist -> throw error')
        return False

# Edits an existing group's description
# Returns false if the group doesn't exist
# TODO error throws
def editGroupDescription(name: str, description: str):
    global groupData
    if name in groupData:
        groupData[name]['description'] = description
        return True
    else:
        print('group doesn\'t exist -> throw error')
        return False

# Add author to a group
# Returns false if no matching group name or in group already
# TODO error throws
def joinGroup(context, name: str):
    global groupData
    if name in groupData:
        if str(context.author) in groupData[name]['member']:
            print('user already in group -> throw error')
            return False
        groupData[name]['member'] = {str(context.author):{}}
        return True
    else:
        print('group doesn\'t exist -> throw error')
        return False

# Remove author from a group
# Returns false if not in the group, or if the group doesn't exist
# TODO error throws
def leaveGroup(context, name: str):
    global groupData
    if name in groupData:
        if str(context.author) in groupData[name]['member']:
            groupData[name]['member'].pop(str(context.author))
            return True
        else:
            print ('not in this group')
            return False
    else:
        print ('group doesn\'t exist -> throw error')
        return False

# Write groupData dict to GROUP_FILE, return True if sucessful
def writeGroupData():
    with open(GROUP_FILE, 'w') as f:
        json.dump(groupData, f, indent=4)
        return True

# Read GROUP_FILE and assign to groupData dict, return groupData
def readGroupData():
    with open(GROUP_FILE, 'r') as f:
        global groupData
        groupData = json.load(f)
        return groupData

def setup(bot):
    bot.add_cog(GroupManager(bot))

def teardown(bot):
    bot.remove_cog('GroupManager')