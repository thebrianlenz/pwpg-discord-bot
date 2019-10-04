"""Used for creating, accessing, and managing groups.

    GroupManager functions as an extension for a Discord.py bot. This
    includes the GroupManager Cog, which handles all associated commands
    and are registered with the bot that loads this extension.

    This extension creates and reads from a file for Groups of users seperated
    by Guild ID. This file is saved as groupsData.json in the local directory.
    These groups can be accessed by users to alert other members of a group,
    usually for playing games. Requires asyncio and discord.py libraries.

    This extension is generally accessed through adding the GroupManager
    as a cog to an existing Discord.py Bot.
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
        selected_group_id = getGroupID(context, groupName)

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
                    aliases=['mysubs', 'mygroups'],
                    pass_context=True)
    async def listUsersGroups(self, context):
        guild = groupData[str(context.guild.id)]
        messageToSend = '```' + context.author.display_name + ' is in:\n'
        for id in guild:
            if str(context.author.id) in guild[id]['members']:
                messageToSend += '\t' + guild[id]['title'] + ':\t Offline Ping: ' + str(guild[id]['members'][str(context.author.id)]['offlinePing']) + '\n'
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
        group_id = getGroupID(context, groupName)
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

#=======================
# Prompts
#=======================

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
    currentDescription = groupData[str(context.guild.id)][getGroupID(context, groupName)]['description']
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
            return await context.send('Operation cancelled')
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
            return await context.send('Operation cancelled')
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


#=======================
# Group Manipulation
#=======================

def addGroup(context, groupName: str):
    """Creates a group for users to join

    Adds a group to the groupData and writes to file. If the groupName
    provided is already in use, GroupAlreadyExistsError is raised.
    The new group will only be added to the active guild. A unique ID for
    the group is created and used. Properties for the group include: Title,
    Description, Aliases, and Members. Aliases is automatically populated with
    a stripped version of the Title. If the group is added successfully,
    True is returned.

    Parameters
    ----------
    context : context
        The context from the invoked command
    groupName : str
        The name of the group that will be created

    Returns
    -------
    bool
        True if the group is successfully created

    Raises
    ------
    GroupAlreadyExistsError
        Raised if the group name provided is already in use

    """
    guild = groupData[str(context.guild.id)]

    if getGroupID(context, groupName) is not False: raise GroupAlreadyExistsError(groupName)
    else:
        idList = [int(i) for i in guild.keys()]
        groupID = max(idList, default=0) + 1
        aliases = []
        aliases.insert(0, nameCleanUp(groupName))
        guild[groupID] = {'title':groupName, 'description': 'No Description', 'aliases': aliases, 'members': {}}
        writeGroupData()
    return True

def removeGroup(context, groupName: str):
    """Removes a group and all accompanying data

    Removes an entire group from the active guild. This command
    does not have a confirmation, so implementation of one is
    encouraged.

    Parameters
    ----------
    context : context
        The context from the invoked command
    groupName : str
        The group to be removed

    Returns
    -------
    bool
        True if the group is successfully removed

    Raises
    ------
    GroupDoesNotExistError
        Raised if the groupName is invalid
    """
    guild = groupData[str(context.guild.id)]
    group_id = getGroupID(context, groupName)

    if group_id is not False:
        guild.pop(group_id)
        writeGroupData()
        return True
    else:
        raise GroupDoesNotExistError(groupName)

def joinGroup(context, groupName: str):
    """Adds the user to groupName

    Adds the command invoker to groupName. If the groupName is unused,
    GroupDoesNotExistError is raised. If the user is already in groupName,
    GroupUserAlreadyInGroupError is raised. Otherwise, the command invoker's
    unique ID is appended to the groupData file. A default version of necessary
    user properties is also added as a dictionary.
    If the join is successful, will return True.

    Parameters
    ----------
    context : context
        The context from the invoked command
    groupName : str
        The name of the group that will be joined

    Returns
    -------
    bool
        True if the group is successfully joined

    Raises
    ------
    GroupDoesNotExistError
        Raised if the group name provided is not valid
    GroupUserAlreadyInGroupError
        Raised if the user is trying to join a group they already are in
    """
    guild = groupData[str(context.guild.id)]

    userProps = {'offlinePing': False}
    group_id = getGroupID(context, nameCleanUp(groupName))

    if group_id is not False:
        if str(context.author.id) in guild[group_id]['members']:
            raise GroupUserAlreadyInGroupError(groupName)
        guild[group_id]['members'][str(context.author.id)] = userProps
        writeGroupData()
        return True
    else:
        raise GroupDoesNotExistError(groupName)

def leaveGroup(context, groupName: str):
    """Leaves a group that the user is a part of.

    Removes a user and associated properties from a group. Will raise
    GroupUserNotInGroupError, if the user is not in groupName, and will
    raise GroupDoesNotExistError if the groupName is invalid. Otherwise,
    the command invoker and all user properties with the group will be
    deleted, and changes will be written to file. Returns True if successful.

    Parameters
    ----------
    context : context
        The context from the invoked command
    groupName : str
        The name of the group that will be left

    Returns
    -------
    bool
        True if the group is successfully left

    Raises
    ------
    GroupDoesNotExistError
        Raised if the group name is invalid
    GroupUserNotInGroupError
        Raised if the user is trying to leave a group they are not in
    """
    global groupData
    group_id = getGroupID(context, groupName)

    if group_id is not False:
        if str(context.author.id) in groupData[str(context.guild.id)][group_id]['members']:
            groupData[str(context.guild.id)][group_id]['members'].pop(str(context.author.id))
            writeGroupData()
            return True
        else:
            raise GroupUserNotInGroupError(groupName)
    else:
        raise GroupDoesNotExistError(groupName)

def editGroupDescription(context, groupName: str, description: str):
    """Replaces the existing Description for a Group with a provided one.

    Finds a group within the guild and replaces the exsting description
    with one passed in. The group data file is then written with the
    updated description. Returns True if successful or raises
    GroupDoesNotExistError

    Parameters
    ----------
    context : context
        The context from the invoked command
    groupName : str
        The name of the group that will be edited
    description : str
        The new description to be used for groupName

    Returns
    -------
    bool
        True if the description is successfully set

    Raises
    ------
    GroupDoesNotExistError
        Raised if the group name provided does not exist

    """
    guild = groupData[str(context.guild.id)]
    group_id = getGroupID(context, groupName)

    if group_id is not False:
        guild[group_id]['description'] = description
        writeGroupData()
        return True
    else:
        raise GroupDoesNotExistError(groupName)

def editGroupTitle(context, groupName: str, newTitle: str):
    """Replaces the existing Title for a Group with a provided one.

    Finds a group within the guild of groupName and sets the Title to
    newTitle. If successful, data is written to groupData file and returns True.
    If the groupName to be edited does not exist, raises GroupDoesNotExistError.
    If the newTitle to be used already is in use, raises GroupAlreadyExistsError.

    Parameters
    ----------
    context : context
        The context from the invoked command
    groupName : str
        The name of the group that will be edited
    newTitle : str
        The new title to be used groupName

    Returns
    -------
    bool
        True if the title is successfully set

    Raises
    ------
    GroupDoesNotExistError
        Raised if groupName does not exist
    GroupAlreadyExistsError
        Raised if the newTitle is already in use

    """
    global groupData
    group_id = getGroupID(context, groupName)
    if group_id is False:
        raise GroupDoesNotExistError(groupName)
    elif getGroupID(context, newTitle) is not False:
        raise GroupAlreadyExistsError(newTitle)
    else:
        groupData[str(context.guild.id)][group_id]['title'] = newTitle
        addAliasToGroup(context, groupName, newTitle)
        deleteAliasFromGroup(context, groupName, groupName)
        writeGroupData()
    return True

def addAliasToGroup(context, groupName: str, newAlias: str):
    """Adds a new Alias to a Group

    Takes newAlias and adds it to the list of aliases for groupName. If the groupName
    is not in use, or, the newAlias is already in use, returns False. Otherwise, if the
    alias is added successfully, True is returned and groupData is written to file.

    Parameters
    ----------
    context : context
        The context from the invoked command
    groupName : str
        The name of the group that will be edited
    newAlias : str
        The alias to be added to groupName

    Returns
    -------
    bool
        True if the alias is successfully added
        False if the groupName is not valid, or newAlias is already in use.
    """
    guild = groupData[str(context.guild.id)]
    group_id = getGroupID(context, groupName)
    alias_id = getGroupID(context, newAlias)

    if group_id is False: return False
    elif alias_id is not False: return False
    else:
        guild[group_id]['aliases'].append(nameCleanUp(newAlias))
        writeGroupData()
        return True

# TODO: error message for title removal
def deleteAliasFromGroup(context, groupName: str, aliasToDelete: str):
    """Deletes an Alias from a Group

    Takes newAlias and adds it to the list of aliases for groupName. If the groupName
    is not in use, or, the newAlias is already in use, returns False. Otherwise, if the
    alias is added successfully, True is returned and groupData is written to file.

    If the groupName is in use, and the aliasToDelete is used within that same group, deletes
    the provided aliasToDelete. If the groupName is unused, raises GroupDoesNotExistError. If the
    aliasToDelete is unused, returns False. If the ID of the groups for groupName and aliasToDelete
    do not match, raises GroupEditingOtherThanSelfError. The alias created from the title of the group
    is also an invalid alias to delete and returns False.

    Otherwise, the aliasToDelete is removed from groupName and is written to file, then returns True

    Parameters
    ----------
    context : context
        The context from the invoked command
    groupName : str
        The name of the group that will be edited
    aliasToDelete : str
        The alias to be deleted from groupName

    Returns
    -------
    bool
        True if the alias is successfully deleted
        False if the alias does not exist or is the same as the title alias

    Raises
    ------
    GroupDoesNotExistError
        Raised if the groupName does not exist
    GroupEditingOtherThanSelfError
        Raised if the alias and group being edited are not the same ID
    """
    guild = groupData[str(context.guild.id)]
    group_id = getGroupID(context, groupName)
    alias_id = getGroupID(context, aliasToDelete)

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

# Replace user preferences for a group with dictionary
# Returns false if not in group or no matching group
#  throw error if no dict provided (missing arg)
def updateUserGroupPreferences(context, groupName: str, properties: dict):
    """Updates the properties for the user

    IN PROGRESS:
    Would update all properties included in a single group's user entry

    Parameters
    ----------
    context : context
        The context from the invoked command
    groupName : str
        The name of the group where a user's properties will be edited
    properties : dict
        A dictionary of all properties for a group

    Returns
    -------
    bool
        True if the properties are successfully updated

    Raises
    ------
    GroupDoesNotExistError
        Raised if the group name is invalid
    """
    global groupData
    group_id = getGroupID(context, groupName)

    if group_id is not False:
        if str(context.author.id) not in groupData[str(context.guild.id)][group_id]['member']:
            print('throw error, not in group')
        groupData[str(context.guild.id)][group_id]['member'][str(context.author.id)] = properties
        writeGroupData()
        return True
    else:
        raise GroupDoesNotExistError(groupName)


#=======================
# Simple Helpers
#=======================

def getGroupID(context, groupName: str):
    """Returns the ID of groupName

    Searches through the active guild for a valid groupName. Returns the
    ID associated, or False if not found.

    Parameters
    ----------
    context : context
        The context from the invoked command
    groupName : str
        The name of a group to get an ID

    Returns
    -------
    group_id : str
        The unique ID of a group
    bool
        False if no valid group is found
    """
    d = groupData[str(context.guild.id)]
    for group_id in d:
        if nameCleanUp(groupName) in d[group_id]['aliases']:
            return group_id
    return False

def getGroupTitle(context, groupName: str):
    """Returns the full Title of groupName

    Searches through the active guild for a valid groupName. Returns the
    full Title associated, or False if none is found.

    Parameters
    ----------
    context : context
        The context from the invoked command
    groupName : str
        The name of a group to get a Title

    Returns
    -------
    str
        The full Title of a group
    bool
        False if no valid group is found
    """
    d = groupData[str(context.guild.id)]
    for group_id in d:
        if nameCleanUp(groupName) in d[group_id]['aliases']:
            return d[group_id]['title']
    return False

def getGroupAliases(context, groupName:str):
    """Returns a list of aliases for the groupName

    Searches through the active guild for a valid groupName. Returns
    a list of strings containing all aliases associated with it, or False if no
    group is found.

    Parameters
    ----------
    context : context
        The context from the invoked command
    groupName : str
        The name of a group

    Returns
    -------
    list
        List containing strings of all aliases for groupName
    bool
        False if no valid group is found
    """
    d = groupData[str(context.guild.id)]
    for group_id in d:
        if nameCleanUp(groupName) in d[group_id]['aliases']:
            return d[group_id]['aliases']
    return False

def groupNameInUse(context, groupName: str):
    """Checks if the groupName is in use.

    Searches through the active guild for a valid groupName. If
    the groupName is in use, returns True, otherwise returns False.

    Parameters
    ----------
    context : context
        The context from the invoked command
    groupName : str
        The name of a group

    Returns
    -------
    bool
        True if the groupName is in use, else returns False
    """
    d = groupData[str(context.guild.id)]
    name = nameCleanUp(groupName)
    for group_id in d:
        if name in d[group_id]['aliases']:
            return True
    return False

def nameCleanUp(name: str):
    """Returns a string as lowercase and without special characters

    Strips the provided name of all special characters and converts
    to lower case.

    Parameters
    ----------
    name : str
        A name to sanitize of extra characters

    Returns
    -------
    str
        A sanitized version of name
    """
    name = name.lower()
    return re.sub('\W+','',name)

async def getUserNameFromID(context, id: str):
    """Retrieves a user's name from their ID

    Takes a string of a user's ID and converts it to the local name.
    If the user ID cannot be identified, a BadArgument is caught and returns
    a string of the ID that failed to be identified.

    Parameters
    ----------
    context : context
        The context from the invoked command
    id : str
        The unique ID of a user to identify

    Returns
    -------
    str
        The user's name in the active guild
    """
    uc = UserConverter()
    try:
        member = await uc.convert(context, id)
        return member.name
    except commands.BadArgument:
        return f'ID `{id}` not in server'

#=======================
# File Management
#=======================

def writeGroupData():
    """Writes the groupData to GROUP_FILE

    Dumps the current groupData object into the GROUP_FILE as
    a JSON object. Returns True after writing. If opening the file
    fails, None is returned.

    Returns
    -------
    bool
        True if write is successful
    """
    with open(GROUP_FILE, 'w') as f:
        json.dump(groupData, f, indent=4)
        print('Group Data Written')
        return True
    return None

def readGroupData():
    """Reads the GROUP_FILE and assigns to groupData.

    Dumps the current groupData object into the GROUP_FILE as
    a json object. Returns True after writing. If opening the file
    fails, None is returned.

    Pulls JSON from GROUP_FILE and dumps into groupData. The resulting groupData
    object is returned if successful. If the file fails to open, returns None.

    Returns
    -------
    bool
        True if write is successful
    """
    with open(GROUP_FILE, 'r') as f:
        global groupData
        groupData = json.load(f)
        print('Group Data Loaded')
        return groupData
    return None

#=======================
# Bot Management
#=======================

def setup(bot):
    """Initial setup for the GroupManager cog.

    This is called when a cog is added to the client.
    """
    bot.add_cog(GroupManager(bot))

def teardown(bot):
    """Removes the cog from the bot.

    This is called when a cog is removed from the client. A final data write is
    called before the cog is removed.
    """
    writeGroupData()
    bot.remove_cog('GroupManager')
