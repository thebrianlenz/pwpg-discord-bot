from discord.ext import commands
from discord.ext.commands import Bot
from discord.ext.commands import MemberConverter
from discord.ext.commands import UserConverter
from discord import Status
import discord
import asyncio
import json
import re

GROUP_FILE = 'groupsData.json'

RESERVED_WORDS = ['group', 'groups', 'all']

groupData = {}

class GroupDoesNotExistError(commands.BadArgument): pass
class GroupAlreadyExistsError(commands.BadArgument): pass
class GroupUserAlreadyInGroupError(commands.BadArgument): pass
class GroupUserNotInGroupError(commands.BadArgument): pass

#       √ Remove the 'No Description' message on command repsonses
#       Delete group confirmation
#       √ List all of a single user's groups
#       √ Cooldown on group creation
#           Needs better error management, doesn't feel very clean
#       Case insensitivity when join/leave
#       √ Convert user data to the unique identifier (snowflake?) for save and eval
#       Temporary group mute for a user
#       √ Offline ping preference setting
#           Needs a refactor for more/smarter preferences
#       √ BUG the write loop should be refactored back to on-call writing?
#       Expand on error handling to inclue more information (command causing the error, etc)
class GroupManager(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot
        readGroupData()

    async def cog_command_error(self, context, error):
        if hasattr(context.command, 'on_error'): return # ignore anything with a individual local error handler

        # Marks the context that we are handling the error
        setattr(context, 'error_being_handled', True)

        # Taking care of the error
        if isinstance(error, commands.CommandOnCooldown):
            await context.message.add_reaction('⌛')
            await asyncio.sleep(error.retry_after)
            await context.message.remove_reaction('⌛', context.bot.user)
            return
        if isinstance(error, GroupAlreadyExistsError):
            await context.send('The group `' + str(error) + '` already exists! Use $list to see existing groups.') # Remove $list hardcoding
            context.command.reset_cooldown(context)
            return
        if isinstance(error, GroupDoesNotExistError):
            await context.send('The group `' + str(error) + '` does not exist! Use $create <groupName> to create a new group.') # Remove hardcoding
            context.command.reset_cooldown(context)
            return
        if isinstance(error, GroupUserAlreadyInGroupError):
            await context.send('You are already in `' + str(error) + '`. There is no need to join again! Use $mysubs to see all of your group memberships.') # Remove hardcoding
            context.command.reset_cooldown(context)
            return
        if isinstance(error, GroupUserNotInGroupError):
            await context.send('You are not in group `' + str(error) + '`. Use $sub <groupName> to join a group, or $mysubs to see all of your memberships.') # Remove hardcoding
            context.command.reset_cooldown(context)
            return

        # Finished handling our errors, anything left will go to the generic handler in pwpg-bot
        setattr(context, 'error_being_handled', False)

    # Return full list of all groups with member count (short descr too?)
    @commands.cooldown(1, 5, commands.BucketType.channel)
    @commands.command(name='list',
                      description='List all groups. To see members of a specific group, include the group name.',
                      brief='List all groups, or members of a group.',
                      aliases=['ls'],
                      invoke_without_command=True,
                      rest_is_raw=True,
                      pass_context=True)
    async def listGroupsCommand(self, context, groupName=''):
        messageToSend = ''
        uc = UserConverter()
        groupID = getGroupNameId(groupName)
        if (groupName is None) or (groupName is RESERVED_WORDS) or (groupID is False): # Conditions to list all groups (no name given, reserved words, not in groupData)
            messageToSend += 'There are currently ' + str(len(groupData)) + ' groups on PWPG!\n'
            for id in groupData:
                messageToSend += groupData[id]['title'] + ': '
                if groupData[id]['description'] != 'No Description': messageToSend += groupData[id]['description'] # Add the description if the group has one
                messageToSend += '\n\tMembers: ' + str(len(groupData[id]['members'])) + '\n'
        elif groupID is not False:
            messageToSend += groupData[groupID]['title'] + ' has ' + str(len(groupData[groupID]['members'])) + ' members.\n' # <groupName> has <number> members \n
            if groupData[groupID]['description'] != 'No Description': messageToSend += groupData[groupID]['description'] + '\n' # Add the description if the group has one
            messageToSend += '---------------' + '\n'
            for m in groupData[groupID]['members']: # Add each member
                member = await uc.convert(context, m)
                messageToSend += '\t' + member.name + '\n'
        else:
            print('how did this even happen?')
            messageToSend += 'THIS SHOULD NOT BE SEEN!?'

        await context.send('```' + messageToSend + '```')

    # Returns a user's full list of memberships
    @commands.cooldown(1, 10, commands.BucketType.channel)
    @commands.command(name='mysubs',
                    description='List all of your group subscriptions.',
                    brief='List all of your subs',
                    aliases=['mygroups'],
                    pass_context=True)
    async def listUsersGroups(self, context):
        messageToSend = '```' + context.author.display_name + ' is in:\n'
        for id in groupData:
            if str(context.author.id) in groupData[id]['members']:
                messageToSend += '\t' + groupData[id]['title'] + ':\t Offline Ping: ' + str(groupData[id]['members'][str(context.author.id)]['offlinePing']) + '\n'
        messageToSend += '```'
        await context.send(messageToSend)

    # Joins an existing group and writes to file
    @commands.command(name='sub',
                    description='Subscribe to a group. Belonging ' + 'to a group will include you in pings.\n' + 'Use [list] to find existing groups.',
                    brief='Subscribe to a group.',
                    aliases=['subscribe','join'],
                    rest_is_raw=True)
    async def joinGroupCommand(self, context, groupName):
        if joinGroup(context, groupName):
           await context.send('`' + context.author.display_name + '` has been added to `' + groupName + '`')
        else:
            return

    # Leaves a group the user is a member of
    @commands.command(name='unsub',
                    description='Unsubscribe from a group that you are a part of. Removes you from future ' + 'pings and notifications for this group.',
                    brief='Unsubscribe from a group.',
                    aliases=['unsubscribe', 'leave'],
                    rest_is_raw=True,
                    pass_context=True)
    async def leaveGroupCommand(self, context, groupName):
        if leaveGroup(context, groupName):
            await context.send('`' + context.author.display_name + '` has left `' + groupName + '`')
        else:
            return

    # Ping a group with an optional message
    # Check if user is online, consult property
    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command(name='ping',
                    description='Ping a group. Pinging sends a single message to all users in a group. ' + 'Include an optional message for the ping.',
                    brief='Ping a group',
                    aliases=['poke'],
                    invoke_without_command=True,
                    pass_context=True)
    async def pingGroupCommand(self, context, groupName, *, optionalMessage=None):
        id = getGroupNameId(groupName)
        if id is not False:
            m = MemberConverter()
            messageToSend = f'`{context.author.display_name}` has pinged `{getGroupTitle(groupName)}`.'
            if optionalMessage is not None:
                messageToSend += '\n' + optionalMessage

            # For each member in the group,
            # check user status and preference for offline ping
            # send the message if online or wants offline pings
            for u in groupData[id]['members']:
                user = await m.convert(context, u)
                if groupData[id]['members'][u].get('offlinePing') or (user.status is Status.online or user.status is Status.idle):
                    await user.send(messageToSend)
                else:
                    print('no offline ping and they aren\'t online')
            return True
        else:
            raise GroupDoesNotExistError(groupName)

    # Creates a non-existing group
    # Write to GROUP_FILE
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(name='create',
                      description='Make a group and add yourself to it. Add a short description of the group after the name. Groups can be pinged using [ping] <groupName>.',
                      brief='Create a group',
                      aliases=['make'],
                      pass_context=True)
    async def createGroupCommand(self, context, *, groupName):
        if addGroup(context, groupName):
            await context.send(f'Group `{getGroupTitle(groupName)}` has been created.')
        else:
            return

    # Deletes an existing group
    # Write to GROUP_FILE
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(name='delete',
                    description='Removes an existing group. Confirmation is not implemented yet.',
                    brief='Remove a group',
                    aliases=['remove', 'del', 'rm'],
                    hidden=True,
                    pass_context=True)
    async def deleteGroupCommand(self, context, *, groupName):
        title = getGroupTitle(groupName)
        if removeGroup(groupName):
            await context.send(f'Group `{title}` has been deleted.')
        else:
            return

    # Edits an existing group's description
    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command(name='edit',
                    description='Edit an existing group\'s description. No quotations are needed.',
                    brief='Edit a group description',
                    aliases=['editgroup', 'editdesc'],
                    pass_context=True)
    async def editGroupDescriptionCommand(self, context, groupName, *, description=None):
        if description is None:
            if editGroupDescription(groupName, 'No Description'):
                await context.send(f'The description for `{getGroupTitle(groupName)}` has been removed.')
            return
        else:
            if editGroupDescription(groupName, description):
                await context.send(f'The description for `{getGroupTitle(groupName)}` has been updated.')
            return

    # Edit a user's group preference
    @commands.command(name='myprefs',
                    description='Edit your preferences for a group. Currently includes: \nOffline Ping:\t Receiving Pings when offline',
                    brief='Edit your group preferences',
                    aliases=['mypref'],
                    pass_context=True)
    async def editUsersGroupPreferenceCommand(self, context, groupName, offlinePing=False):
        preferences = {'offlinePing': offlinePing}
        updateUserGroupPreferences(context, groupName, preferences)

    def is_luke(self):
        def predicate(ctx):
            return ctx.message.author.id == 180532524068503552
        return commands.check(predicate)

    @commands.command(name='waffle', hidden=True)
    #@is_luke
    #@commands.guild_only()
    async def _stupidLuke(self, context):
        # if not isinstance(context.channel, (discord.DMChannel,
        # discord.GroupChannel)):
        await context.message.delete()
        await context.send('The word "waffle" first appears in the English language in 1725', delete_after=180)

    @commands.command(name='testid', hidden=True)
    async def testid(self, context):
        rebuildGroupsData()

    @commands.group(name='group',
                      description='Manage group properties: Title, Aliases, or Description',
                      brief='Manage group properties',
                      pass_context=True)
    async def manageGroupCommand(self, context):
        print('group command')
        return

    @manageGroupCommand.group(name='alias',
                                description='Manage group aliases. Use -add or -remove for quick management.',
                                brief='Manage group aliases.',
                                pass_context=True)
    async def aliasCommand(self, context):
        print('alias command')
        return

    @aliasCommand.command(name='-add',
                          description='Add an alias to an existing group.',
                          brief='Add an alias.',
                          aliases=['add','a','-a'],
                          pass_context=True)
    async def aliasCommandAdd(self, context, groupName: str, *, newAlias: str):
        if addAliasToGroup(context, groupName, newAlias):
            await context.send(f'The alias `{newAlias}` has been added to `{getGroupTitle(groupName)}`.')
        return



## Creates a new group entry. Title required
def addGroup(context, groupTitle: str):
    global groupData
    if getGroupNameId(nameCleanUp(groupTitle)) is not False: raise GroupAlreadyExistsError(groupTitle)
    else:
        idList = [int(i) for i in groupData.keys()]
        groupID = max(idList, default=0) + 1
        aliases = []
        aliases.insert(0, nameCleanUp(groupTitle))
        groupData[groupID] = {'title': groupTitle, 'description': 'No Description', 'aliases': aliases, 'members': {}}
        writeGroupData()
    return True

def addAliasToGroup(context, groupName: str, newAlias: str):
    global groupData
    id = getGroupNameId(groupName)
    if id is not False:
        aliasid = getGroupNameId(newAlias)
        if aliasid is not False: raise GroupAlreadyExistsError(newAlias)
        else:
            groupData[id]['aliases'].append(nameCleanUp(newAlias))
    else:
        raise GroupDoesNotExistError(groupName)
    writeGroupData()
    return True

# Checks for a Group Name in all aliases
# Automatically cleans the groupName passed in
# Returns the id of the group if name is already in use
# Returns False if name is unused
def getGroupNameId(groupName: str):
    global groupData
    groupName = nameCleanUp(groupName)
    for id in groupData:
        if groupName in groupData[id]['aliases']:
            return id
    return False

# Checks for a Group Name in all aliases
# Returns the Title of a group if the alias is in use
# Returns False if the name is unused
def getGroupTitle(groupName: str):
    global groupData
    groupName = nameCleanUp(groupName)
    for id in groupData:
        if groupName in groupData[id]['aliases']:
            return groupData[id]['title']
    return False

# Returns a lowercase string without special characters
def nameCleanUp(name: str):
    name = name.lower()
    return re.sub('\W+','',name)

def rebuildGroupsData():
    global groupData
    newData = {}
    i = 0
    for groupObject in groupData:
        #i = max(groupData.keys(), default=0)
        groupAliases = []
        groupAliases.insert(0, groupObject)
        newData[i] = {'title': groupObject, 'description': groupData[groupObject]['description'], 'aliases': groupAliases, 'members': groupData[groupObject]['member']}
        i += 1


    with open('newData.json', 'w') as f:
        json.dump(newData, f, indent=4)
        print('Group Data Written')
    return

# Removes entire entry for a group
# Returns false if group doesn't exist
def removeGroup(groupName: str):
    global groupData
    id = getGroupNameId(groupName)
    if id is not False:
        groupData.pop(id)
        writeGroupData()
        return True
    else:
        raise GroupDoesNotExistError(groupName)
        return False

# Edits an existing group's description
# Returns false if the group doesn't exist
def editGroupDescription(groupName: str, description: str):
    global groupData
    id = getGroupNameId(groupName)

    if id is not False:
        groupData[id]['description'] = description
        writeGroupData()
        return True
    else:
        raise GroupDoesNotExistError(groupName)
        return False

# Add author to a group
# Returns false if no matching group name or in group already
def joinGroup(context, groupName: str):
    global groupData
    userProps = {'offlinePing': False}
    id = getGroupNameId(nameCleanUp(groupName))

    if id is not False:
        if str(context.author.id) in groupData[id]['members']:
            raise GroupUserAlreadyInGroupError(groupName)
            return False
        groupData[id]['members'][str(context.author.id)] = userProps
        writeGroupData()
        return True
    else:
        raise GroupDoesNotExistError(groupName)
        return False

# Remove author from a group
# Returns false if not in the group, or if the group doesn't exist
def leaveGroup(context, groupName: str):
    global groupData
    id = getGroupNameId(groupName)
    if id is not False:
        if str(context.author.id) in groupData[id]['members']:
            groupData[id]['members'].pop(str(context.author.id))
            writeGroupData()
            return True
        else:
            raise GroupUserNotInGroupError(groupName)
            return False
    else:
        raise GroupDoesNotExistError(groupName)
        return False

# Replace user preferences for a group with dictionary
# Returns false if not in group or no matching group
#  throw error if no dict provided (missing arg)
def updateUserGroupPreferences(context, name: str, properties: dict):
    global groupData
    if name in groupData:
        if str(context.author.id) not in groupData[name]['member']:
            print('throw error, not in group')
            return False
        groupData[name]['member'][str(context.author.id)] = properties
        writeGroupData()
        return True
    else:
        raise GroupDoesNotExistError(name)
        return False

# Write groupData dict to GROUP_FILE, return True if sucessful
def writeGroupData():
    with open(GROUP_FILE, 'w') as f:
        json.dump(groupData, f, indent=4)
        print('Group Data Written')
        return True
    return None

# Read GROUP_FILE and assign to groupData dict, return groupData
def readGroupData():
    with open(GROUP_FILE, 'r') as f:
        global groupData
        groupData = json.load(f)
        print('Group Data Loaded')
        return groupData
    return None


def setup(bot):
    bot.add_cog(GroupManager(bot))

def teardown(bot):
    writeGroupData()
    bot.remove_cog('GroupManager')
