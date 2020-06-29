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
from MessageIO import *

import sqlite3
from datetime import datetime

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

# TODO: Overall Refactor
"""
Major:
	List all groups
	List members in a group
	Ping a group
	Descriptions
	Better documentation
	Confirmations (probably the reaction method again)
Minor:
	Check a user's group memberships
	User preferences? (offline ping mainly)
	Shortcodes? simple symbols for ping, e.g. - ..<group> <message>

Should exceptions be raised for common errors? (group not existing, duplicate entries, etc)
If exceptions are raised, all calls should likely be wrapped in try blocks to do local handling
	This makes sense for managing individual exceptions differently per *command* rather than per
	operation. Likely would result in more helper methods, as many handlers would be similar.

This could be pushed further to the general database errors. The database errors could raise
the more "unified" exceptions that would be made, and pass the necessary information along.
The actual response to the exception would still need to be handled case by case, at the
command level.


"""
class GroupDatabaseManager(commands.Cog):

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
		print(context.command) # Individual error types would be handled here
		# The cog error handling didn't catch the error, passes to main bot error handling
		setattr(context, 'error_being_handled', False)

	def _database_error_handler(self, context, error, data:{}):
		if isinstance(error, sqlite3.IntegrityError):
			error_check = error.args[0].split(": ")
			if error_check[0] == "UNIQUE constraint failed":
				conflicts = error_check[1].split(", ")
				#temp = error_check[1].split(".")
				print(f'Unique error. {conflicts}')
			else:
				print(f'Unhandled Integrity Error - {error}')
			self.groups_db.rollback()
		elif isinstance(error, sqlite3.OperationalError):
			print(f'Operational error - {error}')
			self.groups_db.rollback()

	@commands.command(name='create', rest_is_raw=True)
	async def command_create_group(self, context, group_title=''):
		"""Creates a group entry with the title given. TODO: allow a description
		to be given to be associated with the group.

		Args:
			context (context): The context of the command being invoked
			group_title (str, optional): A title for the group. Defaults to ''.
		"""
		description = 'descr'
		self._create_group_entry(context, group_title, description)

	@commands.command(name='join', rest_is_raw=True)
	async def command_join_group(self, context, name=''):
		options = -1
		group_id = self._get_group_id(context, name)
		self._add_group_user_entry(context, group_id, options)

	@commands.command(name='lookup', rest_is_raw=True)
	async def command_group_lookup(self, context, name=''):
		print(f'Lookup command found {self._get_group_id(context, name)}')
	
	@commands.command(name='info', hidden=True)
	async def command_info_server(self, context):
		print(context.guild.owner)
		list = await context.guild.fetch_members().flatten()
		temp = sorted(list, key=lambda x: getattr(x, 'joined_at'))
		for mem in temp:
			print("{} joined at {}".format(mem.name, mem.joined_at))

	# list all available groups
	# list specified group
	# list a user's groups
	@commands.command(name='list')
	async def command_list_group(self, context):
		# retrieve the associated groups
		# create embed?
		# post
		print(self._get_all_groups(context))

	@commands.command(name='init')
	async def command_init_tables(self, context):
		self._database_creation()

	def _get_all_groups(self, context):
		"""Fetches a list of tuples for all groups in the current guild.

		Args:
			context (context): The context of the invoking command

		Returns:
			list of (group_id, group_title, group_description): The results of the database query for all groups in the current guild. 
				Returned as a list of tuples.
		"""
		data = { 'guild_id': context.guild.id }

		try:
			groups_list = self.groups_db.execute("""SELECT uid, group_title, description FROM group_registry WHERE guild_id=(:guild_id)""", data).fetchall()
		except Exception as error:
			self._database_error_handler(context, error, data)

		print(groups_list)
		return groups_list

	def _get_group_id(self, context, alias_to_search: str):
		"""Fetches a group_id using a title or alias.

		Args:
			context (context): The context of the invoking command
			alias_to_search (str): The title or alias to search

		Returns:
			int: A group_id matching the search
		"""		
		data = { 'alias': alias_to_search, 'guild_id': context.guild.id }

		try:
			group_id = self.groups_db.execute("""SELECT group_id FROM group_alias_registry WHERE alias LIKE (:alias) AND guild_id = (:guild_id)""", data).fetchall()[0][0]
		except Exception as error:
			self._database_error_handler(context, error, data)
			return -1
		else:
			return group_id

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
			group_id = self.groups_db.execute("""INSERT INTO group_registry VALUES (NULL, :group_title, :guild_id, :datetime_created, :description)""", data).lastrowid
		except Exception as error:
			print(f'The group {group_title} could not be created')
			self._database_error_handler(context, error, data)
		else:
			self._add_group_alias(context, group_id, group_title)
			self.groups_db.commit()
			print(f'A new group {group_title} has been created with the id {group_id}')

		return group_id

	def _add_group_alias(self, context, group_id: int, alias: str):
		"""Adds an alias to an existing group. Aliases allow multiple names to refer to the same group_id.

		Args:
			context (context): Context of the invoking command
			group_id (int): The group_id to be aliased
			alias (str): The name to be added as an alias
		"""		
		data = { 'group_id': group_id, 'guild_id': context.guild.id, 'alias': alias }
		try:
			self.groups_db.execute("""INSERT INTO group_alias_registry VALUES
				(:group_id, :guild_id, :alias)""", data)
		except Exception as error:
			self._database_error_handler(context, error, data)
			print(f'The alias {alias} could not be added to the group id {group_id}')
		else:
			self.groups_db.commit()
			print(f'An alias of {alias} seems to have been added to group id {group_id}.')
		pass

	def _add_group_user_entry(self, context, group_id: int, options_key: int):
		"""Adds the invoking user to a group_id.

		Args:
			context (context): The context of the invoking command
			group_id (int): The group_id for the user entry to be associated with
			options_key (int): An options key to be associated with the user (not implemented yet)

		Returns:
			bool: Whether the user addition was successful
		"""		
		if group_id == -1:
			# todo - Raise exception here for group not existing?
			return False

		data = { 'group_id': group_id, 'user_id': context.author.id, 'options_key': options_key }

		try:
			self.groups_db.execute("""INSERT INTO group_user_registry VALUES
				(:group_id, :user_id, :options_key)""", data)
		except Exception as error:
			self._database_error_handler(context, error, data)
			print(f'User id {data["user_id"]} could not be added to {group_id}')
			return False
		else:
			self.groups_db.commit()
			print(f'Added user id {data["user_id"]} to group id {group_id}')
			return True

	def _database_creation(self):
		"""Initializes the group database tables.
		"""		
		sql_group_registry = """CREATE TABLE IF NOT EXISTS group_registry (
								uid INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
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
									FOREIGN KEY(group_id) REFERENCES group_registry(uid) ON DELETE CASCADE,
									UNIQUE(group_id, user_id)
								);"""

		sql_group_alias_registry = """CREATE TABLE IF NOT EXISTS group_alias_registry (
									group_id INTEGER NOT NULL,
									guild_id INTEGER NOT NULL,
									alias TEXT COLLATE NOCASE,
									FOREIGN KEY(group_id) REFERENCES group_registry(uid) ON DELETE CASCADE,
									UNIQUE(guild_id, alias)
								);"""

		self.groups_db.execute(sql_group_registry)
		self.groups_db.execute(sql_group_user_registry)
		self.groups_db.execute(sql_group_alias_registry)
		print('Tables should be initialized')

	def cog_unload(self):
		"""Called when the Cog is removed from the bot. Ensures that the database is closed properly.
		"""
		print('unloading cog')
		self.groups_db.close()

#=======================
# Bot Management
#=======================

def setup(bot):
	"""Initial setup for the GroupManager cog.

	This is called when a cog is added to the client.
	"""
	bot.add_cog(GroupDatabaseManager(bot))

def teardown(bot):
	"""Removes the cog from the bot.

	This is called when a cog is removed from the client. A final data write is
	called before the cog is removed.
	"""
	# TODO ensure there are no open database connections?
	bot.remove_cog('GroupDatabaseManager')