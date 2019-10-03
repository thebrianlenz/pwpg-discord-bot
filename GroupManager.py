"""Used for creating, accessing, and managing groups.
    
    GroupManager functions as an extension for a Discord.py bot. This 
    includes the GroupManager Cog, which handles all associated commands 
    and are registered with the bot that loads this extension.

    This extension creates and reads from a file for Groups of users seperated
    by Guild ID. This file is saved as groupsData.json in the local directory.
    These groups can be accessed by users to alert other members of a group, 
    usually for playing games. Requires asyncio and discord.py libraries.

    This extension should likely not be loaded as a Python module.
"""

from discord.ext import commands
from discord.ext.commands import Bot
from discord.ext.commands import MemberConverter
from discord.ext.commands import UserConverter
from discord import Status
import discord
import asyncio
import json
import re
from MessageIO import *

GROUP_FILE = 'groupsData.json'

RESERVED_WORDS = ['group', 'groups', 'all']

groupData = {}

class GroupDoesNotExistError(commands.BadArgument): pass
class GroupAlreadyExistsError(commands.BadArgument): pass
class GroupUserAlreadyInGroupError(commands.BadArgument): pass
class GroupUserNotInGroupError(commands.BadArgument): pass
class GroupEditingOtherThanSelfError(commands.BadArgument): pass
class UserNotFound(commands.BadArgument): pass

#       Delete group confirmation
#       Temporary group mute for a user
#       √ Offline ping preference setting
#           Needs a refactor for more/smarter preferences
#       Expand on error handling to inclue more information (command causing the error, etc)

class GroupManager(commands.Cog):
    """
    """
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
            print(error)
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
        if isinstance(error, UserNotFound):
            print('User id is not on this server, or is invalid.' + str(error))
            return
        if isinstance(error, GroupEditingOtherThanSelfError):
            print('Trying to edit a group other than itself' + str(error))
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
    async def listCommand(self, context, groupName=''):
        # Temp string to build the message
        messageToSend = ''
        
        # Retrieves the passed in group name's id
        selected_group_id = getGroupNameId(context, groupName)

        # Conditions to list all groups (no name given, reserved words, not in groupData)
        if (groupName is None) or (groupName is RESERVED_WORDS) or (selected_group_id is False):
            messageToSend += f'There are currently {str(len(groupData[str(context.guild.id)]))} groups on {context.guild.name}!\n'
            
            # Add each group and the number of members
            for group_id in groupData[str(context.guild.id)]:
                messageToSend += groupData[str(context.guild.id)][group_id]['title'] + ': '
                
                # Add the description if the group has one
                if groupData[str(context.guild.id)][group_id]['description'] != 'No Description':
                    messageToSend += groupData[str(context.guild.id)][group_id]['description']
                
                messageToSend += f'\n\tAlternate Names: {groupData[str(context.guild.id)][group_id]["aliases"]}'
                messageToSend += '\n\tMembers: ' + str(len(groupData[str(context.guild.id)][group_id]['members'])) + '\n'
        
        # If we find a valid group id, print all members
        elif selected_group_id is not False:
             # <groupName> has <number> members \n
            messageToSend += (
                            f"{groupData[str(context.guild.id)][selected_group_id]['title']} has "
                            f"{str(len(groupData[str(context.guild.id)][selected_group_id]['members']))} members.\n"
                            )
            
            # Add the description if the group has one
            if groupData[str(context.guild.id)][selected_group_id]['description'] != 'No Description':
                messageToSend += groupData[str(context.guild.id)][selected_group_id]['description'] + '\n'
            
            messageToSend += '---------------' + '\n'
            
            # Add each member
            for m in groupData[str(context.guild.id)][selected_group_id]['members']:
                messageToSend += '\t' + await getUserNameFromID(context, m) + '\n'
        
        else:
            print('how did this even happen?')
            messageToSend += 'THIS SHOULD NOT BE SEEN!?'

        await context.send('```' + messageToSend + '```')

    # Returns a user's full list of memberships
    @commands.cooldown(1, 10, commands.BucketType.channel)
    @commands.command(name='me',
                    description='List all of your group subscriptions.',
                    brief='List all of your subs',
                    aliases=['mysubs, mygroups'],
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
    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command(name='ping',
                    description='Ping a group. Pinging sends a single message to all users in a group. ' + 'Include an optional message for the ping.',
                    brief='Ping a group',
                    aliases=['poke'],
                    invoke_without_command=True,
                    pass_context=True)
    async def pingGroupCommand(self, context, groupName, *, optionalMessage=None):
        group_id = getGroupNameId(context, groupName)
        if group_id is not False:
            m = MemberConverter()
            messageToSend = f'`{context.author.display_name}` has pinged `{getGroupTitle(context, groupName)}`.'
            if optionalMessage is not None:
                messageToSend += '\n' + optionalMessage

            # For each member in the group,
            # check user status and preference for offline ping
            # send the message if online or wants offline pings
            for u in groupData[str(context.guild.id)][group_id]['members']:
                user = await m.convert(context, u)
                if groupData[str(context.guild.id)][group_id]['members'][u].get('offlinePing') or (user.status is Status.online or user.status is Status.idle):
                    await user.send(messageToSend)
                else:
                    print('no offline ping and they aren\'t online')
            return True
        else:
            raise GroupDoesNotExistError(groupName)

    # Creates a group
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(name='create',
                      description='Make a group. Add a short description of the group after the name. Groups can be pinged using [ping] <groupName>.',
                      brief='Create a group',
                      aliases=['make'],
                      pass_context=True)
    async def createGroupCommand(self, context, *, groupName):
        if addGroup(context, groupName):
            await context.send(f'Group `{getGroupTitle(context, groupName)}` has been created.')
        else:
            return

    # Deletes an existing group
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(name='delete',
                    description='Removes an existing group. Confirmation is not implemented yet.',
                    brief='Remove a group',
                    aliases=['remove', 'del', 'rm'],
                    hidden=True,
                    pass_context=True)
    async def deleteGroupCommand(self, context, *, groupName):
        title = getGroupTitle(context, groupName)
        if removeGroup(context, groupName):
            await context.send(f'Group `{title}` has been deleted.')
        else:
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

    @commands.command(name='testadd', hidden=True)
    async def testadd(self, context, groupName):
        #rebuildGroupsData()
        #await promptForGroupDetails(context, groupName)
        await promptForAliasAddition(context, groupName)

    @commands.command(name='testdelete', hidden=True)
    async def testdelete(self, context, groupName):
        #rebuildGroupsData()
        #await promptForGroupDetails(context, groupName)
        await promptForAliasDeletion(context, groupName)

    @commands.group(name='group',
                      description='Manage all of a group\'s properties: Title, Aliases, or Description. Use flags before the group name to edit individual properties',
                      brief='Manage group properties',
                      invoke_without_command=True,
                      pass_context=True)
    async def manageGroupCommand(self, context, groupName: str):
        await promptForGroupDetails(context, groupName)
        return

    @manageGroupCommand.group(name='-title',
                                description='Change a group\'s title. Capitilization and spacing will be preserved for display.',
                                brief='Edit a group\'s title',
                                pass_context=True)
    async def editGroupTitleCommand(self, context, groupName: str, *, newTitle: str):
        await editGroupTitle(context, groupName, newTitle)
        return

    @manageGroupCommand.group(name='-description',
                                description='Change a group\'s description. Capitilization and spacing will be preserved.',
                                brief='Edit a group\'s description',
                                aliases=['-desc'],
                                pass_context=True)
    async def editGroupDescriptionCommand(self, context, groupName: str, *, newTitle: str):
        await editGroupDescription(context, groupName, newTitle)
        return

    @manageGroupCommand.group(name='-alias',
                                description='Manage a group\'s aliases. Enter a group name to prompt bulk addition and removal. Use -add or -delete for quick management.',
                                brief='Manage a group\'s aliases.',
                                invoke_without_command=True,
                                pass_context=True)
    async def aliasCommand(self, context, groupName: str):
        await promptForAliasManagement(context, groupName)
        return

    @aliasCommand.command(name='-add',
                          description='Add a single alias to an existing group.',
                          brief='Add an alias to a group.',
                          aliases=['-a'],
                          pass_context=True)
    async def aliasCommandAdd(self, context, groupName: str, *, newAlias: str):
        if addAliasToGroup(context, groupName, newAlias):
           await context.send(f'The alias `{newAlias}` has been added to `{getGroupTitle(context, groupName)}`.')
        return

    @aliasCommand.command(name='-delete',
                          description='Delete a single alias from an existing group.',
                          brief='Delete an alias from a group.',
                          aliases=['-del'],
                          pass_context=True)
    async def aliasCommandDelete(self, context, groupName: str, *, newAlias: str):
        if deleteAliasFromGroup(context, groupName, newAlias):
            await context.send(f'The alias `{newAlias}` has been deleted from `{getGroupTitle(context, groupName)}`.')
        return


async def promptForNewTitle(context, groupName: str):
    """Creates a prompt for a new Title for the given Group.
    
    This command includes prompts for ensuring the correct group is being edited, 
    acceptance of a new group title, 
    and confirmation of the new name
    
    Parameters
    ----------
    context : context
        The context from the invoked command
    groupName : str
        The name of the group being edited
    """
    if await promptForThumbs(context, f'Edit the Title of the group?\nCurrent title is: `{getGroupTitle(context, groupName)}`'):
        newTitleInput = await promptAndWaitForInput(context, 'Please enter a new Title. Capitilization and spacing is preserved', True)

        if newTitleInput is not False:
            try:
                if editGroupTitle(context, groupName, newTitleInput):
                    await context.send(f'New title, `{newTitleInput}`, has been confirmed')
                    return newTitleInput
                else: print('Something went crazy when prompting for new title')
            except GroupAlreadyExistsError:
                await context.send(f'{newTitleInput} is already in use.')
                return await promptForNewTitle(context, groupName)
        else: return False
    else:
        return False

async def promptForNewDescription(context, groupName: str):
    """Creates a prompt for a new Description for the given Group.
    
    This command includes prompts for ensuring the correct group is being edited, 
    acceptance of a new group description, 
    and confirmation of the new description
    
    Parameters
    ----------
    context : context
        The context from the invoked command
    groupName : str
        The name of the group being edited

    Returns
    -------
    newDescriptionInput : str
        The newly entered text. Returns False if cancelled or failed
    """
    currentDescription = groupData[str(context.guild.id)][getGroupNameId(context, groupName)]['description']
    if await promptForThumbs(context, f'Edit the Description of `{getGroupTitle(context, groupName)}`?\n'
                                            f'Current Description is `{currentDescription}`'):
        newDescriptionInput = await promptAndWaitForInput(context, 'Please enter a new Description')
        if newDescriptionInput is False:
            await context.send(f'Description editing has been cancelled')
            return False
        if editGroupDescription(context, groupName, newDescriptionInput):
            await context.send(f'New description, `{newDescriptionInput}`, has been confirmed')
            return newDescriptionInput     
        elif await promptForThumbs(context, f'Try again?'):
           return await promptForNewDescription(context, groupName)
        else:
            return False
    else:
        return False

async def promptForAliasAddition(context, groupName: str):
    """Creates the prompts for adding new Aliases to a group.
    
    This command includes prompts for ensuring the correct group is being edited, 
    acceptance of aliases to be added to the group, 
    and confirmation of the aliases to be added.

    Confirms the aliases that were successfully added.
    
    Parameters
    ----------
    context : context
        The context from the invoked command
    groupName : str
        The name of the group being edited
    """
    if groupNameInUse(context, groupName):
        responseMessage = await promptForInput(context, f'Enter new aliases for `{getGroupTitle(context, groupName)}` seperated by commas. Spacing, symbols, and capitilzation are ignored.')
        aliasList = [x.strip() for x in responseMessage.content.split(',')]
        if await promptForThumbs(context, f'Attempting to add aliases to `{getGroupTitle(context, groupName)}`:\n`{aliasList}`\nConfirm?'):
            addedAliases = []
            for a in aliasList:
                if addAliasToGroup(context, groupName, nameCleanUp(a)):
                    addedAliases.append(a)
        else:
            await context.send('Operation cancelled')
    else: raise GroupDoesNotExistError(groupName)
    await context.send(f'Aliases `{addedAliases}` have been added to `{getGroupTitle(context, groupName)}`')

async def promptForAliasDeletion(context, groupName: str):
    """Creates the prompts for deleting Aliases from a group.
    
    This command includes prompts for ensuring the correct group is being edited, 
    acceptance of aliases to be deleted from the group, 
    and confirmation of the aliases to be deleted.

    Confirms the aliases that were successfully deleted.
    
    Parameters
    ----------
    context : context
        The context from the invoked command
    groupName : str
        The name of the group being edited
    """
    if groupNameInUse(context, groupName):
        responseMessage = await promptForInput(context, f'Enter aliases to delete from `{getGroupTitle(context, groupName)}` seperated by commas. Spacing, symbols, and capitilzation are ignored.'
                                                        f'\nCurrent aliases are: `{getGroupAliases(context, groupName)}`')
        aliasList = [x.strip() for x in responseMessage.content.split(',')]
        if await promptForThumbs(context, f'Attempting delete aliases from `{getGroupTitle(context, groupName)}`:\n`{aliasList}`\nConfirm?'):
            removedAliases = []
            for a in aliasList:
                if deleteAliasFromGroup(context, groupName, nameCleanUp(a)):
                    removedAliases.append(a)
        else:
            await context.send('Operation cancelled')
    else: raise GroupDoesNotExistError(groupName)
    await context.send(f'Aliases `{removedAliases}` have been deleted from `{getGroupTitle(context, groupName)}`')

async def promptForAliasManagement(context, groupName: str):
    """Creates the prompts for both adding and removing Aliases.
    
    This is a simple helper that calls both promptForAliasAddition and promptForAliasDeletion.

    Asks if the user wants to use the prompts.
    
    Parameters
    ----------
    context : context
        The context from the invoked command
    groupName : str
        The name of the group being edited
    """
    if await promptForThumbs(context, f'Add or remove aliases?\n'
                                        f'Current aliases for `{getGroupTitle(context, groupName)}` are `{getGroupAliases(context, groupName)}`.'):
        if await promptForThumbs(context, f'Add new aliases?'):
            await promptForAliasAddition(context, groupName)
        if await promptForThumbs(context, f'Delete existing aliases?'):
            await promptForAliasDeletion(context, groupName)

async def promptForGroupDetails(context, groupName: str):
    """Wraps all associated group editing prompts into a single method.

    Ensures the groupName is in use, asks if the user wishes to edit the group, 
    then asks and prompts for editing: Title, Description, and Aliases
    
    Parameters
    ----------
    context : context
        The context from the invoked command
    groupName : str
        The name of the group being edited
    """
    if groupNameInUse(context, groupName) is False: raise GroupDoesNotExistError(groupName)
    else:
        # confirm group title to edit
        question = f'Would you like to edit `{getGroupTitle(context, groupName)}`?'
        if await promptForThumbs(context, question):

            newTitleResult = await promptForNewTitle(context, groupName)

            if newTitleResult is not False:
                    groupName = newTitleResult
            
            await promptForNewDescription(context, groupName)

            await promptForAliasManagement(context, groupName)
        else:
            await context.send('Editing cancelled')

async def promptAndWaitForInput(context, prompt: str, validateGroupExistence = False):
    """Provides a prompt that includes validating a group's existance before confirmation.

    This likely should be deprecated and replaced with a more generic command usage. 
    As it stands, this passes through to promptForInput from MessageIO, then can perform 
    a basic check for usage and reprompting.
    
    Parameters
    ----------
    context : context
        The context from the invoked command
    prompt : str
        The prompt to be presented to the user
    validateGroupExistence : bool, optional
        Flags usage of a group existence check. If failed, it will reprompt before continuing.
        (default is False)
    """
    inputMessage = await promptForInput(context, prompt)

    if validateGroupExistence and groupNameInUse(context, inputMessage.content):
        await context.send(f'The name `{inputMessage.content}` is already in use. Please try again')
        return await promptAndWaitForInput(context, prompt, validateGroupExistence)

    confirmText = f'`{inputMessage.content}` - Please confirm, {context.author.name}'
    if await promptForThumbs(context, confirmText):
        return inputMessage.content
    else:
        if await promptForThumbs(context, "Try again?"):
            return await promptAndWaitForInput(context, prompt, validateGroupExistence)
        else:
            return False

# Edits the description of a group
# Edits an existing group's description
# Returns false if the group doesn't exist
def editGroupDescription(context, groupName: str, description: str):
    global groupData
    group_id = getGroupNameId(context, groupName)

    if group_id is not False:
        groupData[str(context.guild.id)][group_id]['description'] = description
        writeGroupData()
        return True
    else:
        raise GroupDoesNotExistError(groupName)

# Replaces the title of a group with another
# Also updates alias list to reflect new title
# Writes to groupData
def editGroupTitle(context, groupName: str, newTitle: str):
    global groupData
    group_id = getGroupNameId(context, groupName)
    if group_id is False:
        raise GroupDoesNotExistError(groupName)
    elif getGroupNameId(context, newTitle) is not False:
        raise GroupAlreadyExistsError(newTitle)
    else:
        groupData[str(context.guild.id)][group_id]['title'] = newTitle
        addAliasToGroup(context, groupName, newTitle)
        deleteAliasFromGroup(context, groupName, groupName)
        writeGroupData()
    return True

# Creates a new group entry. Title required
# Checks for an existing group using the Title (includes aliases)
# Assigns a unique groupID
# Adds the Title to it's own list of aliases
# Writes groupData to file
def addGroup(context, groupName: str):
    global groupData
    if getGroupNameId(context, groupName) is not False: raise GroupAlreadyExistsError(groupName)
    else:
        idList = [int(i) for i in groupData[str(context.guild.id)].keys()]
        groupID = max(idList, default=0) + 1
        aliases = []
        aliases.insert(0, nameCleanUp(groupName))
        groupData[str(context.guild.id)][groupID] = {'title':groupName, 'description': 'No Description', 'aliases': aliases, 'members': {}}
        writeGroupData()
    return True

# Adds an alias to a specific group
# Checks to be sure the group exists
# Checks to be sure that the alias isn't already in use
# Appends a cleaned version of newAlias to aliases
# Writes groupData to file
def addAliasToGroup(context, groupName: str, newAlias: str):
    guild = groupData[str(context.guild.id)]
    group_id = getGroupNameId(context, groupName)
    alias_id = getGroupNameId(context, newAlias)

    if group_id is False: return False
    elif alias_id is not False: return False
    else:
        guild[group_id]['aliases'].append(nameCleanUp(newAlias))
        writeGroupData()
        return True

# Deletes an alias from a group
# Passes in a groupName to be sure we aren't deleting from a different group
# Checks to be sure the group and alias exist
# Disallow deletion of the title alias TODO: add an error message for trying to remove title
# Writes groupData to file
def deleteAliasFromGroup(context, groupName: str, aliasToDelete: str):
    guild = groupData[str(context.guild.id)]
    group_id = getGroupNameId(context, groupName)
    alias_id = getGroupNameId(context, aliasToDelete)

    if group_id is False: raise GroupDoesNotExistError(groupName)
    elif alias_id is False: return False
    elif group_id != alias_id: raise GroupEditingOtherThanSelfError(aliasToDelete, alias_id)
    elif nameCleanUp(aliasToDelete) == nameCleanUp(getGroupTitle(context, groupName)):
        print('cant delete title alias')
        return False
    else:
        guild[alias_id]['aliases'].remove(nameCleanUp(aliasToDelete))
        writeGroupData()
        return True

# Checks for a Group Name in all aliases in current guild
# Returns the id of the group if name is already in use
# Returns False if name is unused
def getGroupNameId(context, groupName: str):
    d = groupData[str(context.guild.id)]
    for group_id in d:
        if nameCleanUp(groupName) in d[group_id]['aliases']:
            return group_id
    return False

# Checks for a Group Name in all aliases in current guild
# Returns the Title of a group if the alias is in use
# Returns False if the name is unused
def getGroupTitle(context, groupName: str):
    d = groupData[str(context.guild.id)]
    for group_id in d:
        if nameCleanUp(groupName) in d[group_id]['aliases']:
            return d[group_id]['title']
    return False

# Finds a group in current guild
# Returns a list of all aliases for the guild
# Returns False if the group does not exist
def getGroupAliases(context, groupName:str):
    d = groupData[str(context.guild.id)]
    for group_id in d:
        if nameCleanUp(groupName) in d[group_id]['aliases']:
            return d[group_id]['aliases']
    return False

# Simple helper
# Checks if a group name is used in any aliases
# Returns bool
def groupNameInUse(context, groupName: str):
    d = groupData[str(context.guild.id)]
    name = nameCleanUp(groupName)
    for group_id in d:
        if name in d[group_id]['aliases']:
            return True
    return False

# Returns a lowercase string without special characters
def nameCleanUp(name: str):
    name = name.lower()
    return re.sub('\W+','',name)

# Removes entire entry for a group
# Returns false if group doesn't exist
def removeGroup(context, groupName: str):
    global groupData
    group_id = getGroupNameId(context, groupName)
    if group_id is not False:
        groupData[str(context.guild.id)].pop(group_id)
        writeGroupData()
        return True
    else:
        raise GroupDoesNotExistError(groupName)

# Add author to a group
# Returns false if no matching group name or in group already
def joinGroup(context, groupName: str):
    global groupData
    userProps = {'offlinePing': False}
    group_id = getGroupNameId(context, nameCleanUp(groupName))

    if group_id is not False:
        if str(context.author.id) in groupData[str(context.guild.id)][group_id]['members']:
            raise GroupUserAlreadyInGroupError(groupName)
        groupData[str(context.guild.id)][group_id]['members'][str(context.author.id)] = userProps
        writeGroupData()
        return True
    else:
        raise GroupDoesNotExistError(groupName)

# Remove author from a group
# Returns false if not in the group, or if the group doesn't exist
def leaveGroup(context, groupName: str):
    global groupData
    group_id = getGroupNameId(context, groupName)

    if group_id is not False:
        if str(context.author.id) in groupData[str(context.guild.id)][group_id]['members']:
            groupData[str(context.guild.id)][group_id]['members'].pop(str(context.author.id))
            writeGroupData()
            return True
        else:
            raise GroupUserNotInGroupError(groupName)
    else:
        raise GroupDoesNotExistError(groupName)

# Replace user preferences for a group with dictionary
# Returns false if not in group or no matching group
#  throw error if no dict provided (missing arg)
def updateUserGroupPreferences(context, groupName: str, properties: dict):
    global groupData
    group_id = getGroupNameId(context, groupName)

    if group_id is not False:
        if str(context.author.id) not in groupData[str(context.guild.id)][group_id]['member']:
            print('throw error, not in group')
        groupData[str(context.guild.id)][group_id]['member'][str(context.author.id)] = properties
        writeGroupData()
        return True
    else:
        raise GroupDoesNotExistError(groupName)

# Takes a string of a user's id
# Returns a string of the associated name, or a default message
async def getUserNameFromID(context, id: str):
    uc = UserConverter()
    try:
        member = await uc.convert(context, id)
        return member.name
    except commands.BadArgument:
        return f'ID `{id}` not in server'

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
