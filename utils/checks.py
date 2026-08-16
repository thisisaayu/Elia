import discord
from discord.ext import commands

from cogs.config import get_mod_role_id


def is_staff(member: discord.Member) -> bool:
    """True if the member is the guild owner, an Administrator, or has the configured mod role."""
    if member.guild.owner_id == member.id:
        return True
    if member.guild_permissions.administrator:
        return True
    mod_role_id = get_mod_role_id(member.guild.id)
    if mod_role_id and any(role.id == mod_role_id for role in member.roles):
        return True
    return False


def has_mod_role():
    """Command check: only allow staff (see is_staff) to run the command."""

    async def predicate(ctx: commands.Context):
        if not ctx.guild:
            return False
        if is_staff(ctx.author):
            return True
        raise commands.CheckFailure("You need the mod role to use this command.")

    return commands.check(predicate)


def can_act_on(actor: discord.Member, target: discord.Member) -> bool:
    """
    Safety check: prevents a mod from acting on someone with an equal or
    higher top role (including themselves). The guild owner can act on anyone
    except themselves.
    """
    if target.id == actor.id:
        return False
    if actor.guild.owner_id == actor.id:
        return True
    if target.guild.owner_id == target.id:
        return False
    return actor.top_role > target.top_role
