""" Heck the Groups, we goin' roles

    Have determined conventions for naming schemes

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

    todo - perm checks for create/delete
    todo - checks/creation of categorical roles
"""
import discord
from discord.ext import commands
from discord.ext.commands import Bot
from discord.utils import get
from operator import attrgetter
import asyncio

GROUP_CATEGORY_NAME = """- Groups -"""
COSMETIC_CATEGORY_NAME = """- Colors -"""


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
    async def command_rolecall(self, context):
        """Lists all the joinable roles on the guild.

        Args:
            context (context): The context of the invoking command
        """
        print(self._fetch_category_roles(context))
        print(self._fetch_category_roles(context, COSMETIC_CATEGORY_NAME))

    # =======================
    # List commands
    # =======================

    @commands.group(name='list',
                    aliases=['ls'],
                    brief='List all roles available.',
                    description='List all the roles available to be joined within the RoleManager module.',
                    invoke_without_command=True)
    async def command_list(self, context):
        # TODO - make this do something different than the regular list group
        await context.send(embed=self._build_group_list_embed(context))

    @command_list.command(name='groups',
                          aliases=['group', 'grps', 'grp'],
                          brief='List available groups.',
                          description='Lists the groups available to join.')
    async def subcommand_list_groups(self, context):
        await context.send(embed=self._build_group_list_embed(context))

    @command_list.command(name='colors',
                          aliases=['colours', 'color', 'clr', 'clrs'],
                          brief='List available colors.',
                          description='Lists the colors available to be assigned')
    async def subcommand_list_colors(self, context):
        await context.send(embed=self._build_color_list_embed(context))

    # =======================
    # Create commands
    # =======================

    @commands.group(name='create',
                    brief='Creates a role.',
                    description='Creates a new role in the current guild.',
                    invoke_without_command=True,
                    pass_context=True)
    async def command_create(self, context):
        """Used to create a new role for the current guild.

        Use the subcommand `group` or `color` to indicate the desired role type.
        """
        # await self._create_new_role(context, name, target=GROUP_CATEGORY_NAME)
        print('main create')

    @command_create.command(name='group',
                            brief='Creates a new group',
                            description='Creates a new group in the current guild.',
                            pass_context=True,
                            rest_is_raw=True)
    async def subcommand_create_group(self, context, name: str):
        print('group create')

    @command_create.command(name='color',
                            brief='Creates a new color',
                            description='Creates a new color in the current guild.',
                            pass_context=True,
                            rest_is_raw=True)
    async def subcommand_create_color(self, context, name: str):
        print('color create')

    # =======================
    # Delete commands
    # =======================

    @commands.command(name='delete',
                      brief='Deletes a role.',
                      description='Deletes the specified role in the current guild.',
                      rest_is_raw=True)
    async def command_delete_role(self, context, name: str):
        # todo - delete the specified role
        self._delete_role(context, name)
        pass

    def _build_group_list_embed(self, context):
        """Creates an embed for all roles in the Group Category

        Args:
            context (context): The context of the invoking command

        Returns:
            discord.Embed: An embed containing all the roles as fields
        """
        embed = discord.Embed(
            title=f"Roles on {context.guild.name}", color=0x000000)
        for role in self._fetch_category_roles(context):
            embed.add_field(
                name=role.name, value=f"{len(role.members)} {self.plural_selector('member','members', len(role.members))}")

        embed.set_footer(
            text=f'Use {context.prefix}assign to join a role or {context.prefix}help for more information')

        return embed

    def _build_color_list_embed(self, context):
        """Create a message for all roles in the Cosmetic Category

        Args:
            context (context): The context of the invoking command

        Returns:
            str: A message containing all the cosmetic roles
        """

        embed = discord.Embed(
            title=f"Cosmetic roles on {context.guild.name}", description=f'Users should only have *one* color role selected.\
            \nOnly the highest role will be used to display color.\nUse {context.prefix}assign `role name` to add the role.', color=0x000000)
        for role in self._fetch_category_roles(context, COSMETIC_CATEGORY_NAME):
            embed.add_field(
                name=f"{role.name}", value=f"{role.mention}", inline=False)

        embed.set_footer(
            text=f'Use {context.prefix}assign to join a role or {context.prefix}help for more information')

        return embed

    async def _build_group_reaction_embed(self, context):
        # needs to build the message embed for the available groups to join
        # assign reactions to each group and add corresponding reactions to the message for interaction

        # likely will need a parallel function for the cosmetic roles
        pass

    async def _create_new_role(self, context, name: str, target=GROUP_CATEGORY_NAME, channel=False, color: discord.Color = None):
        """Create a new role and position within the heirarchy based on the target category

        Args:
            context (context): The context of the invoking command
            name (str): The name to assign to the new role
            target (str, optional): The category to sort the role under. Defaults to GROUP_CATEGORY_NAME.
            channel (bool, optional): Unimplemented. Defaults to False.
            color (discord.Color, optional): Unimplemented. Defaults to None.
        """
        # todo - sanitize input, preventing "-" specifically
        target_role = get(context.guild.roles, name=target)
        target_position = target_role.position

        new_role = await context.guild.create_role(
            name=name, mentionable=True, reason=f"Role created by {context.author}")

        await context.guild.edit_role_positions(positions={new_role: target_position})

    def _fetch_category_roles(self, context, category_target=GROUP_CATEGORY_NAME):
        """Fetch all roles sorted below a Category Role. Stops at the next category, or at the bottom of the role heirarchy

        Args:
            context (context): The context of the invoking command
            category_target (str): The category to search for in the role list. Defaults to GROUP_CATEGORY_NAME.

        Returns:
            Role[]: A list of roles
        """
        try:
            # ask for a specific category
            roles_list = context.guild.roles  # preload roles list
            # find the target category's role
            category_role = get(roles_list, name=category_target)
            # preload the position of the category
            target_category_position = category_role.position

            category_role_list = []

            for i in range(target_category_position - 1, 0, -1):
                if roles_list[i].name.startswith('-') or roles_list[i].name is None:
                    break
                else:
                    category_role_list.append(roles_list[i])

            return category_role_list
        except Exception as error:
            print(f"Errored when fetching roles in {category_target}\n{error}")

    def _delete_role(self, context, name: str):
        # todo - deletes a role
        # todo - needs confirmation
        # todo - needs to ensure it's not deleting a role it shouldn't (namely anything not joinable)
        role = get(context.guild.roles, name=name)
        print('name: ' + role.name)
        print(f'tags: {role.tags}')
        print(f'managed: {role.managed}')

        pass

    def plural_selector(self, singular: str, plural: str, count: int):
        # todo - docstring and likely move to a helper class? maybe messageIO
        return singular if abs(count) == 1 else plural


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
