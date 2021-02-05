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
import sys
import argparse
from discord.ext.commands import Bot
from discord.ext.commands import MemberConverter
from discord.ext.commands import UserConverter
from discord import Status
import discord
import asyncio
import json
import re
import MessageIO

import sqlite3
from datetime import datetime

GROUP_FILE = 'groupsData.json'

RESERVED_WORDS = ['group', 'groups', 'all']

groupData = {}


class GroupDoesNotExistError(commands.BadArgument):
    pass


class GroupAlreadyExistsError(commands.BadArgument):
    pass


class GroupUserAlreadyInGroupError(commands.BadArgument):
    pass


class GroupUserNotInGroupError(commands.BadArgument):
    pass


class GroupEditingOtherThanSelfError(commands.BadArgument):
    pass


class UserNotFound(commands.BadArgument):
    pass


# TODO: Overall Refactor
"""
Major:
    Descriptions
    Better documentation
    Confirmations (probably the reaction method again)
    Temp channels? Probably should be its own module, but it should definitely be hooked somehow
Minor:
    Check a user's group memberships
    User preferences? (offline ping mainly)
    Shortcodes? simple symbols for ping, e.g. - ..<group> <message>
    Temporary group mute for a user

Should exceptions be raised for common errors? (group not existing, duplicate entries, etc)
If exceptions are raised, all calls should likely be wrapped in try blocks to do local handling
    This makes sense for managing individual exceptions differently per *command* rather than per
    operation. Likely would result in more helper methods, as many handlers would be similar.

This could be pushed further to the general database errors. The database errors could raise
the more "unified" exceptions that would be made, and pass the necessary information along.
The actual response to the exception would still need to be handled case by case, at the
command level.
"""
# todo - robust responses for "major" commands (create, delete, join, leave)
# todo - delete group entry, needs some sort of confirmation
# todo - bulk set a user's preferences for pings


class GroupManager(commands.Cog, name='Group Manager'):
    """Join groups for easy pings and text chats."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.groups_db = sqlite3.connect('data/groups.db')

    async def cog_command_error(self, context, error):
        """This command fires whenever a local Cog error is thrown

        Args:
            context (context): The context of the error being thrown
            error (Exception): The error being thrown
        """
        # Flags the context that the cog is handling the error
        setattr(context, 'error_being_handled', True)
        print('Cog Command Error in Group Manager')
        print(context.command)  # Individual error types would be handled here
        # The cog error handling didn't catch the error, passes to main bot error handling
        setattr(context, 'error_being_handled', False)

    def _database_error_handler(self, context, error, data: {}):
        """Usually is called during try:catch when dealing with the sqlite3 databases

        Args:
            context (context): The context of the error
            error (Exception): Generally should be sqlite3 exceptions
            data (dictionary): Dataset that likely caused the error
        """
        if isinstance(error, sqlite3.IntegrityError):
            error_check = error.args[0].split(": ")
            if error_check[0] == "UNIQUE constraint failed":
                conflicts = error_check[1].split(", ")
                print(f'Unique error. {conflicts}')
            else:
                print(f'Unhandled Integrity Error - {error}')
            self.groups_db.rollback()
        elif isinstance(error, sqlite3.OperationalError):
            print(f'Operational error - {error}')
            self.groups_db.rollback()

    @commands.command(name='create',
                      brief='Create a new group',
                      description='Creates a group for users to join and interact with.',
                      rest_is_raw=True)
    async def command_create_group(self, context, group_title: str):
        """Creates a group entry with the given title. TODO: allow a description
        to be given to be associated with the group.

        Args:
            context (context): The context of the invoking command
            group_title (str): A title for the group
        """

        description = 'descr'
        group_id = self._create_group_entry(context, group_title, description)
        if group_id != -1:
            # todo expand response (suggest commands?, give info on created group)
            await context.send(f'A new group was created!')

    @commands.command(name='join',
                      brief='Join a group',
                      description='Adds the user to the specified group.',
                      rest_is_raw=True)
    async def command_join_group(self, context, group_name: str):
        """Adds the invoking user to the group entry with the given name.

        Args:
            context (context): The context of the invoking command
            group_name (str): The group to join
        """
        # todo better response

        options = 0
        if self._add_group_user_entry(context, group_name, options):
            await context.message.add_reaction('👍')
            await context.send(f'{context.author} has been added to `{group_name}`')
        else:
            await context.message.add_reaction('👎')
            await context.send(f'{context.author} could not be added to `{group_name}`')

    @commands.command(name='leave',
                      brief='Leave a group',
                      description='Removes the user from the specified group.')
    async def command_leave_group(self, context, group_name: str):
        """Removes the invoking user from the group provided

        Args:
            context (context): The context of the invoking command
            group_name (str): The group to leave
        """
        # todo better response
        if await MessageIO.prompt_with_thumbs(context, f'Confirm attempt to leave {group_name}?', True):
            if self._delete_group_user_entry(context, group_name):
                await context.message.add_reaction('👍')
            else:
                await context.message.add_reaction('👎')
        else:
            await context.message.add_reaction('👎')

    @commands.command(name='lookup',
                      brief='Lookup a group id',
                      description='Searches for a group\'s id using it\'s name',
                      rest_is_raw=True,
                      hidden=True)
    async def command_group_lookup(self, context, group_name: str):
        """Simple helper to lookup a group's id

        Args:
            context (context): The context of the invoking command
            group_name (str): The group to search for
        """
        print(
            f'Lookup command found {self._get_group_id(context, group_name)}')

    @commands.command(name='info',
                      brief='Lookup and dump user join dates',
                      hidden=True)
    async def command_info_server(self, context):
        """A temporary command for retrieving and dumping user join dates

        Args:
            context (context): The context of the invoking command
        """
        print(context.guild.owner)
        list = await context.guild.fetch_members().flatten()
        temp = sorted(list, key=lambda x: getattr(x, 'joined_at'))
        for mem in temp:
            print("{} joined at {}".format(mem.name, mem.joined_at))

    @commands.group(name='list',
                    brief='List the user\'s groups.',
                    description='Lists all of the group memberships for the user.',
                    invoke_without_command=True)
    async def command_list(self, context):
        """Lists the memberships of the invoking user.

        Args:
            context (context): The context of the invoking command
        """
        results = self._get_user_memberships(context, context.author.id)
        member_count = self._get_group_member_counts(context)

        embed = discord.Embed(title='Group Memberships',
                              description=f'`{context.author.display_name}` belongs to these groups on `{context.guild.name}`:')
        embed.set_thumbnail(url=context.guild.icon_url_as(size=32))

        for group in results:
            if group[1] == context.guild.id:
                embed.add_field(
                    name=group[0], value=f'{member_count[group[3]]} {self.plural_selector("member","members",member_count[group[3]])}')

        embed.set_footer(text='Use the help command to see other uses')
        await context.send(embed=embed)

    # todo - probably should include aliases of the group
    @command_list.command(name='group',
                          brief='Lists members of a specified group',
                          description='Lists all members that have joined a specific group.')
    async def command_list_group(self, context, *, group_name: str):
        """Lists all the members in a specified group

        Args:
            context (context): The context of the invoking command
            group_name (str): The group of the members to list
        """
        group_members = self._get_group_member_list(context, group_name)
        embed = discord.Embed(
            title=f'{group_members[0][0]}', description=f'{len(group_members)} {self.plural_selector("member is ", "members are ", len(group_members))} in this group!')

        temp = ''
        mc = commands.MemberConverter()
        for member in group_members:
            member_object = await mc.convert(context, str(member[2]))
            temp += f'{member_object.name}\n'

        embed.add_field(name='Members include:', value=f'{temp}')
        await context.send(embed=embed)

    # todo - list group aliases here?
    @command_list.command(name='all',
                          brief='Lists all groups of the guild',
                          description='List the names and descriptions of all groups on the active guild.')
    async def command_list_all(self, context):
        groups_list = self._get_all_groups(context)

        embed = discord.Embed(
            title=f'There {self.plural_selector("is", "are", len(groups_list))} {len(groups_list)} {self.plural_selector("group","groups",len(groups_list))} on {context.guild.name}!')

        for group in groups_list:
            embed.add_field(name=group[1], value=group[2], inline=True)

        await context.send(embed=embed)

    @command_list.command(name='user',
                          description='Lists the memberships of a specified user. Use with a mention of the desired user.',
                          hidden=True)
    async def command_list_user(self, context, *, username):

        user = await commands.UserConverter().convert(context, username)
        results = self._get_user_memberships(context, user.id)
        member_count = self._get_group_member_counts(context)

        embed = discord.Embed(title='Group Memberships',
                              description=f'`{user.display_name}` belongs to these groups on `{context.guild.name}`:')
        embed.set_thumbnail(url=context.guild.icon_url_as(size=32))

        for group in results:
            if group[1] == context.guild.id:
                embed.add_field(
                    name=group[0], value=f'{member_count[group[3]]} {self.plural_selector("member","members",member_count[group[3]])}')

        await context.send(embed=embed)

    @commands.command(name="ping",
                      brief='Ping the members of a group',
                      description='Sends a direct message to all group members and provides a link to the active text channel.')
    async def command_ping_group(self, context, group_name: str, *, message=''):
        """Send a message to a group's members.

        Args:
            context (context): The context of the invoking command
            group_name (str): The name of the group to ping
            message (str): A message to be added to the ping
        """

        member_list = self._get_group_member_list(context, group_name)

        channel_embed = discord.Embed(
            title=f'Attempting to ping group `{member_list[0][0]}`!', description="... waiting ...")
        channel_message = await context.send(embed=channel_embed)

        message_to_send = f"[Jump to the channel!]({channel_message.jump_url})\n{message}"

        dm_embed = discord.Embed(
            title=f'`{context.author.name}` has pinged group `{member_list[0][0]}`!', description=message_to_send)
        dm_embed.set_thumbnail(url=context.guild.icon_url_as(size=32))
        dm_embed.set_footer(text='Powered by PWPG',
                            icon_url=context.bot.user.avatar_url_as(size=32))

        message_counter = 0

        for member_data in member_list:
            member = await commands.MemberConverter().convert(context, str(member_data[2]))
            if member_data[3] == 1:
                await member.send(embed=dm_embed)
                message_counter += 1
            elif member_data[3] == 0:
                if member.status is Status.online or member.status is Status.idle:
                    await member.send(embed=dm_embed)
                    message_counter += 1
                else:
                    print(
                        f'Ignoring member {member.mention}, not online or idle')
            elif member_data[3] == -1:
                print(f'Ignoring member {member.mention}')
            else:
                print('Invalid options_key')

        channel_embed.title = f'Pings sent to `{member_list[0][0]}`!'
        channel_embed.description = f'Total members: {len(member_list)}\nMembers pinged: {message_counter}'

        await channel_message.edit(embed=channel_embed)

    @commands.command(name='update',
                      brief='Update your options for a group',
                      description='Sets the options key for a specific group')
    async def command_update_group_user_options_key(self, context, group_name: str, new_key):
        """Update a user's preferences for offline pings for a specific group

        Args:
            context (context): The context of the invoking command
            group_name (str): The group to be updated
            new_key (int): The new key to be used
        """
        # todo - allow the user to "select" the option for the group
        #       could be through messageIO, or just different ways to pass in the value
        #       instead of using the -1/0/1
        self._set_group_user_options_key(context, group_name, new_key)

    @commands.command(name='init',
                      brief='Initializes the groups.db table',
                      description='Creates the initial tables for the database of groups. This should not typically need to be called.',
                      hidden=True)
    async def command_init_tables(self, context):
        """Temporary command for initializing the groups.db tables

        Args:
            context (context): The context of the invoking command
        """
        self._database_creation()

    @commands.command()
    async def connect(self, ctx, *, channel: discord.VoiceChannel = None):
        """
        Connect to a voice channel
        This command also handles moving the bot to different channels.

        Params:
        - channel: discord.VoiceChannel [Optional]
            The channel to connect to. If a channel is not specified, an attempt to join the voice channel you are in
            will be made.
        """
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                raise discord.InvalidVoiceChannel(
                    'No channel to join. Please either specify a valid channel or join one.')

        vc = ctx.voice_client

        if vc:
            if vc.channel.id == channel.id:
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                raise discord.VoiceConnectionError(
                    f'Moving to channel: <{channel}> timed out.')
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                raise discord.VoiceConnectionError(
                    f'Connecting to channel: <{channel}> timed out.')

        await ctx.send(f'Connected to: {channel}', delete_after=20)

    def _set_group_user_options_key(self, context, group_name: str, new_option_key: int):
        """Set the options key for the invoking user for a specified group

        Args:
            context (context): The context of the invoking command
            group_name (str): The group to be updated
            new_option_key (int): The new key to be used

        Raises:
            non: [description] # todo - raise non existing group

        Returns:
            bool: Returns True if the key was updated successfully
        """
        group_id = self._get_group_id(context, group_name)

        if group_id == -1:
            print(f'The group {group_name} was not found.')
            # TODO raise non-existant group
            return False

        data = {
            'group_id': group_id,
            'options_key': new_option_key,
            'user_id': context.author.id
        }

        query = """UPDATE group_user_registry
                SET options_key = :options_key
                WHERE user_id = :user_id AND group_id = :group_id"""

        try:
            self.groups_db.execute(query, data)
        except Exception as error:
            self._database_error_handler(context, error, data)
            return False
        else:
            self.groups_db.commit()
            print(
                f'Updated {data["user_id"]} options key to {data["options_key"]} for the group id {data["group_id"]}')
            return True

    def _get_group_member_list(self, context, group_name: str):
        """Retrieves all members of a group

        Args:
            context (context): The context of the invoking command
            group_name (str): The name of the group to fetch members

        Raises:
            non: TODO: Raise a non-existing group error

        Returns:
            list of (group_title, group_id, user_id, options_key): List of tuples containing member information
        """
        # takes in an alias, and returns the member list including option key
        group_id = self._get_group_id(context, group_name)
        if group_id == -1:
            return False

        data = {'group_id': group_id}

        query = """SELECT
                    group_registry.group_title,
                    group_user_registry.group_id,
                    group_user_registry.user_id,
                    group_user_registry.options_key
                FROM group_user_registry
                INNER JOIN group_registry ON
                    group_user_registry.group_id = group_registry.group_id
                WHERE group_user_registry.group_id=(:group_id)"""

        try:
            member_list = self.groups_db.execute(query, data).fetchall()
        except Exception as error:
            self._database_error_handler(context, error, data)
            return None

        return member_list

    def _get_group_member_counts(self, context):
        """Count the total users of each group_id and return as a dictionary

        Args:
            context (context): The context of the invoking command

        Returns:
            dictionary of (group_id:member_count): Member counts of each group_id
        """
        data = {}
        query = """SELECT group_id, COUNT(*) FROM group_user_registry GROUP BY group_id"""

        try:
            member_counts = self.groups_db.execute(query).fetchall()
        except Exception as error:
            self._database_error_handler(context, error, data)
            return None

        return dict(member_counts)

    def _get_user_memberships(self, context, user_id):
        """Retrieves all memberships of a specific user_id.

        Args:
            context (context): The context of the invoking command
            user_id (int): The id of a specific user to search

        Returns:
            list of (group_title, guild_id, description, group_id, options_key): A list of a user's memberships by group_id as a tuple.
        """

        data = {'user_id': user_id}

        query = """SELECT
                        group_registry.group_title,
                        group_registry.guild_id,
                        group_registry.description,
                        group_user_registry.group_id,
                        group_user_registry.options_key
                    FROM group_registry
                    INNER JOIN group_user_registry ON
                        group_registry.group_id = group_user_registry.group_id
                    WHERE group_user_registry.user_id=(:user_id)"""

        try:
            groups_list = self.groups_db.execute(query, data).fetchall()
        except Exception as error:
            self._database_error_handler(context, error, data)
            return None

        return groups_list

    def _get_all_groups(self, context):
        """Fetches a list of tuples for all groups in the current guild.

        Args:
            context (context): The context of the invoking command

        Returns:
            list of (group_id: int, group_title: str, group_description: str): The results of the database query for all groups in the current guild.
                Returned as a list of tuples.
        """
        data = {'guild_id': context.guild.id}

        try:
            groups_list = self.groups_db.execute(
                """SELECT group_id, group_title, description FROM group_registry WHERE guild_id=(:guild_id)""", data).fetchall()
        except Exception as error:
            self._database_error_handler(context, error, data)

        return groups_list

    def _get_group_id(self, context, alias_to_search: str):
        """Fetches the group_id using a title or alias in the context's guild.

        Args:
            context (context): The context of the invoking command
            alias_to_search (str): The title or alias to search

        Returns:
            int: A group_id matching the search
        """
        data = {'alias': alias_to_search, 'guild_id': context.guild.id}

        try:
            group_id = self.groups_db.execute(
                """SELECT group_id FROM group_alias_registry WHERE alias LIKE (:alias) AND guild_id = (:guild_id)""", data).fetchall()[0][0]
        except Exception as error:
            self._database_error_handler(context, error, data)
            return -1
        else:
            return group_id

    def _get_group_by_id(self, context, group_id_to_search: int):
        """Fetches a group and associated information through an ID lookup.

        Args:
            context (context): The contxet of the invoking command
            group_id (int): The ID of a group to search for
        """
        data = {'group_id': group_id_to_search, 'guild': context.guild.id}

        try:
            group = self.groups_db.execute(
                """SELECT 
                        group_id,
                        group_title,
                        guild_id,
                        datetime_created,
                        description
                    FROM group_registry
                    WHERE group_id=(:group_id)"""
            )
        except Exception as error:
            self._database_error_handler(context, error, data)
            return None

        # todo: probably want it returned as a dict, and including aliases
        return group

    def _create_group_entry(self, context, group_title: str, description: str):
        """Creates an entry for the group_registry table in the groups database.

        Args:
            context (context): The context of the invoking command
            group_title (str): The title of the group to be added
            description (str): A related description of the group being added

        Returns:
            int: The group_id of the group created. Returns -1 if unsuccessful.
        """
        data = {
            'group_title': group_title,
            'guild_id': context.guild.id,
            'datetime_created': datetime.utcnow().isoformat(),
            'description': description
        }
        group_id = -1

        try:
            group_id = self.groups_db.execute(
                """INSERT INTO group_registry VALUES (NULL, :group_title, :guild_id, :datetime_created, :description)""", data).lastrowid
        except Exception as error:
            print(f'The group {group_title} could not be created')
            self._database_error_handler(context, error, data)
        else:
            self._add_group_alias(context, group_id, group_title)
            self.groups_db.commit()
            print(
                f'A new group {group_title} has been created with the id {group_id}')

        return group_id

    def _add_group_alias(self, context, group_id: int, alias: str):
        """Adds an alias to an existing group. Aliases allow multiple names to refer to the same group_id.

        Args:
            context (context): Context of the invoking command
            group_id (int): The group to be aliased
            alias (str): The name to be added as an alias
        """

        data = {'group_id': group_id,
                'guild_id': context.guild.id, 'alias': alias}
        try:
            self.groups_db.execute("""INSERT INTO group_alias_registry VALUES
                (:group_id, :guild_id, :alias)""", data)
        except Exception as error:
            self._database_error_handler(context, error, data)
            print(
                f'The alias {alias} could not be added to the group id {group_id}')
        else:
            self.groups_db.commit()
            print(
                f'An alias of {alias} seems to have been added to group id {group_id}.')

    def _add_group_user_entry(self, context, group_name: str, options_key: int):
        """Adds the invoking user to a specified group.

        Args:
            context (context): The context of the invoking command
            group_name (str): The group for the user entry to be associated with
            # todo options key init
            options_key (int): An options key to be associated with the user (not implemented yet)

        Returns:
            int: The id of the target group. -1 if none is found
        """
        group_id = self._get_group_id(context, group_name)
        if group_id == -1:
            # todo - Raise exception here for group not existing?
            return group_id

        data = {'group_id': group_id, 'user_id': context.author.id,
                'options_key': options_key}

        try:
            self.groups_db.execute("""INSERT INTO group_user_registry VALUES
                (:group_id, :user_id, :options_key)""", data)
        except Exception as error:
            self._database_error_handler(context, error, data)
            print(
                f'User id {data["user_id"]} could not be added to {group_id}')
            return -1
        else:
            self.groups_db.commit()
            print(f'Added user id {data["user_id"]} to group id {group_id}')
            return group_id

    def _delete_group_user_entry(self, context, group_name: str):
        """Removes the invoking user from the specified group

        Args:
            context (context): The context of the invoking command
            group_name (str): The group to be removed from

        Raises:
            exception: # todo raise no group exception

        Returns:
            bool: Returns True if the user was removed successfully
        """
        group_id = self._get_group_id(context, group_name)
        if group_id == -1:
            # TODO raise exception
            return False

        data = {'group_id': group_id, 'user_id': context.author.id}
        query = """DELETE FROM group_user_registry
                WHERE group_id = :group_id AND user_id = :user_id"""

        try:
            self.groups_db.execute(query, data)
        except Exception as error:
            self._database_error_handler(context, error, data)
            print(
                f'There was an issue removing {data["user_id"]} from group {data["group_id"]}')
            return False
        else:
            self.groups_db.commit()
            print(
                f'The user id {data["user_id"]} was removed from group {data["group_id"]}')
            return True

    def _database_creation(self):
        """Initializes the group database tables.
        """
        sql_group_registry = """CREATE TABLE IF NOT EXISTS group_registry (
                                group_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                                group_title TEXT COLLATE NOCASE,
                                guild_id INTEGER,
                                datetime_created TEXT,
                                description TEXT,
                                UNIQUE(group_title, guild_id)
                            );"""

        sql_group_user_registry = """CREATE TABLE IF NOT EXISTS group_user_registry (
                                    group_id INTEGER NOT NULL,
                                    user_id INTEGER NOT NULL,
                                    options_key INTEGER,
                                    FOREIGN KEY(group_id) REFERENCES group_registry(group_id) ON DELETE CASCADE,
                                    UNIQUE(group_id, user_id)
                                );"""

        sql_group_alias_registry = """CREATE TABLE IF NOT EXISTS group_alias_registry (
                                    group_id INTEGER NOT NULL,
                                    guild_id INTEGER NOT NULL,
                                    alias TEXT COLLATE NOCASE,
                                    FOREIGN KEY(group_id) REFERENCES group_registry(group_id) ON DELETE CASCADE,
                                    UNIQUE(guild_id, alias)
                                );"""

        self.groups_db.execute(sql_group_registry)
        self.groups_db.execute(sql_group_user_registry)
        self.groups_db.execute(sql_group_alias_registry)
        print('Tables should be initialized')

    def plural_selector(self, singular: str, plural: str, count: int):
        # todo - docstring and likely move to a helper class? maybe messageIO
        return singular if abs(count) == 1 else plural

    def cog_unload(self):
        """Called when the Cog is removed from the bot. Ensures that the database is closed properly.
        """
        print('unloading GroupManager cog')
        self.groups_db.close()

# =======================
# Bot Management
# =======================


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
    # TODO ensure there are no open database connections?
    bot.remove_cog('GroupDatabaseManager')
