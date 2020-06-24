"""		Overview
	Managing statistics and various information about the bot, commands,
	and other usages.
"""
import sqlite3
import asyncio
import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot

from datetime import datetime

"""		Things needed
	Watch and record command executions
	Record reactions
	Dump results
"""

class StatsManager(commands.Cog):
	# TODO: finish docstrings

	# TODO: data retrieval for stats

	def __init__(self, bot: Bot):
		self.bot = bot
		self.command_batch = []
		self.reaction_batch = []
		self.stats_db = sqlite3.connect('stats.db')
		self.bulk_insert_loop.start()

	def cog_unload(self):
		self.bulk_insert()
		self.bulk_insert_loop.stop()

	#=======================
	# Data Insertion
	#=======================

	@tasks.loop(seconds=10.0)
	async def bulk_insert_loop(self):
		"""Calls bulk_insert() as a loop.
		
		Loop is started on the cog's creation, and ended on unload.
		"""
		self.bulk_insert()

	def bulk_insert(self):
		"""Inserts all data into loaded database
		
		Executes SQL to insert the command and reaction batch lists into the stats_db
		"""
		if self.command_batch:
			try:
				self.stats_db.executemany("""INSERT INTO commands VALUES
				(:guild_id, :channel_id, :author_id, :message_id, :timestamp, :prefix, :command, :args, :failed)""", self.command_batch)
				self.stats_db.commit()
			except Exception as error:
				print(error)
			self.command_batch.clear()

		if self.reaction_batch:
			try:
				self.stats_db.executemany("""INSERT INTO reactions VALUES
					(:guild_id, :channel_id, :user_id, :message_id, :timestamp, :reaction, :type)""", self.reaction_batch)
				self.stats_db.commit()
			except Exception as error:
				print(error)
			self.reaction_batch.clear()
		pass
	
	#=======================
	# Commands
	#=======================

	@commands.Cog.listener()
	async def on_command_completion(self, context):
		"""Listens for any commands and passes the context to log_command()
		
		Parameters
		----------
		context : context
			The context which called a command
		"""
		self.log_command(context)

	def log_command(self, context):
		"""Appends the command and related data to the command_batch list
		
		Parameters
		----------
		context : context
			The context which called a command
		"""
		self.command_batch.append({
			'guild_id': context.guild.id,
			'channel_id': context.channel.id,
			'author_id': context.author.id, 
			'message_id': context.message.id,
			'timestamp': context.message.created_at.isoformat(),
			'prefix': context.prefix,
			'command': context.command.qualified_name,
			'args': context.message.content.lstrip(context.prefix.join(context.invoked_with)).lstrip(),
			'failed': context.command_failed
		})

	#=======================
	# Reactions
	#=======================
		
	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload):
		"""Listens for any reaction changes and passes the payload to log_reaction()
		
		Parameters
		----------
		payload : payload
			The payload which includes the data of the reaction that was added or removed
		"""
		self.log_reaction(payload)

	def log_reaction(self, payload):
		"""Appends the reaction and related data to the reaction_batch list
		
		Parameters
		----------
		payload : payload
			The payload which includes the data of the reaction that was added or removed
		"""
		self.reaction_batch.append({
				'guild_id': payload.guild_id,
				'channel_id': payload.channel_id,
				'user_id': payload.user_id,
				'message_id': payload.message_id,
				'timestamp': datetime.utcnow().isoformat(),
				'reaction': payload.emoji.name,
				'type': payload.event_type
			})

def setup(bot):
	bot.add_cog(StatsManager(bot))

def teardown(bot):
	bot.remove_cog('StatsManager')