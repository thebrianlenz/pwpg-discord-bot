""" Heck the Groups, we goin' roles

    Create a role


    create a role with determined perms
        place within the role heirarchy (within categories?)

    - command based
    create role selection message
        list all joinable roles

    - emoji based
    on add reaction to message
        searches the message for connected emoji->role
        adds user to the connected role

    create the role selection message
        populate message with selectable roles
            create corresponding emojis
"""
import discord
from discord.ext import commands
from discord.ext.commands import Bot
from operator import attrgetter
import asyncio


class RoleManager(commands.Cog, name="Role Manager"):
    """Manages roles within a Guild"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(name='assign',
                      brief='Assign a role.',
                      description='Assigns the specified role to the invoking user.',
                      rest_is_raw=True)
    async def command_assign_role(self, context, role: str):
        """Assigns a specified role to the invoking user.

        Args:
            context (context): The context of the invoking command
            role (str): The name of the role to assign
        """
        try:
            await context.author.add_roles(discord.utils.get(
                context.guild.roles, name=role))
            await context.message.add_reaction('👍')
        except Exception as e:
            await context.message.add_reaction('👎')
            await context.send('Role could not be assigned')
            print(f'Errored in command_assign_role.', e)

    @commands.command(name='unassign',
                      brief='Unassign a role.',
                      description='Unassigns the specified role from the invoking user.',
                      rest_is_raw=True)
    async def command_unassign_role(self, context, role: str):
        """Unassigns the specified role from the invoking user

        Args:
            context (context): The context of the invoking command
            role (str): The name of the role to unassign
        """
        try:
            await context.author.remove_roles(discord.utils.get(context.guild.roles, name=role))
            await context.message.add_reaction('👍')
        except Exception as e:
            await context.message.add_reaction('👎')
            await context.send('Role could not be unassigned')
            print(f'Errored in command_unassign_role.', e)

    @commands.command(name='rolecall',
                      brief='List all roles.',
                      description='Lists all the joinable roles?',
                      rest_is_raw=True)
    async def command_rolecall(self, context, category: str):
        """Lists all the joinable roles on the guild.

        Args:
            context (context): The context of the invoking command
        """
        print(self._fetch_role_category(context, category))

    def _fetch_split_roles_list(self, context):
        """Returns a list of tuples, separated by the categories provided.

        Args:
            context (context): The context of the invoking command

        Returns:
            List of (str, [Role]): List of tuples for categories of roles
        """
        categories = ('- Colors -', '- Games -')
        roles_list = context.guild.roles
        roles_list.reverse()

        # Find the index for each split to be made
        indices = []
        for role in roles_list:
            if role.name in categories:
                split = roles_list.index(role)
                indices.append(split)

        # Create a new lists for the split lists
        split_lists = []
        start = 0
        for i in indices:
            split_lists.append(roles_list[start:i])
            start = i
        split_lists.append(roles_list[start:])

        # Assemble role grouping into tuples with category name
        final_lists = []
        for category in split_lists:
            if category[0].name.startswith('-'):
                category_name = category.pop(0).name.strip('- ')
                final_lists.append((category_name, category))
            else:
                final_lists.append(('Uncategorized', category))
        return final_lists

    def _fetch_role_category(self, context, category: str):
        # pull out desired roles within that category?
        # return the list of roles

        roles_list = context.guild.roles
        roles_list.reverse()

        # categories_list.sort(key=attrgetter('position'), reverse=True)
        # for role in categories_list:
        #     if role.name.strip('- ').lower == category.lower:

        for i, role in enumerate(roles_list):
            if role.name.strip('- ').lower() == category.lower():
                index_start = i
                print(f'index start: {index_start}')
                break
            else:
                index_start = 0

        for i, role in enumerate(roles_list[index_start+1:]):
            if role.name.startswith('-'):
                index_end = i
                print(f'index end: {index_end}')
                break
        else:
            index_end = len(roles_list) - 1
            print(f'index end: {index_end}')

        # make a list of the roles from the start of the category by position
        # to the start of the next category - 1 by position
        roles_in_category = []
        roles_in_category.append(roles_list[index_start:index_end])

        return roles_in_category


"""Find the category boundaries within the role list (start and beginning)
    Place category name along with the list of roles as a tuple
        If there is no category, "uncategorized" for tuple
    Remove category role"""


def setup(bot):
    """Initial setup for the RoleManager cog.

    This is called when a cog is added to the client.
    """
    bot.add_cog(RoleManager(bot))


def teardown(bot):
    """Removes the cog from the bot.

    This is called when a cog is removed from the client. A final data write is
    called before the cog is removed.
    """
    bot.remove_cog('RoleManager')
