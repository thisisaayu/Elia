import discord
from discord.ext import commands

from utils import storage
from utils import colors

CONFIG_FILE = "guild_config.json"


def get_guild_config(guild_id: int) -> dict:
    all_config = storage.load(CONFIG_FILE, {})
    return all_config.get(str(guild_id), {})


def set_guild_config(guild_id: int, key: str, value):
    all_config = storage.load(CONFIG_FILE, {})
    guild_key = str(guild_id)
    if guild_key not in all_config:
        all_config[guild_key] = {}
    all_config[guild_key][key] = value
    storage.save(CONFIG_FILE, all_config)


def get_mod_role_id(guild_id: int):
    return get_guild_config(guild_id).get("mod_role_id")


class Config(commands.Cog):
    """Server configuration commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="setmodrole")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def setmodrole(self, ctx: commands.Context, role: discord.Role):
        """Set the role that counts as 'staff' for moderation commands. (Admin only)"""
        set_guild_config(ctx.guild.id, "mod_role_id", role.id)
        embed = discord.Embed(
            description=f"✅ Mod role set to {role.mention}. Members with this role can now use moderation commands.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="modrole")
    @commands.guild_only()
    async def modrole(self, ctx: commands.Context):
        """Show the currently configured mod role."""
        role_id = get_mod_role_id(ctx.guild.id)
        if not role_id:
            embed = discord.Embed(
                description="⚠️ No mod role set yet. An admin can set one with `,setmodrole @role`.",
                color=discord.Color.orange(),
            )
            return await ctx.send(embed=embed)

        role = ctx.guild.get_role(role_id)
        if not role:
            embed = discord.Embed(
                description="⚠️ The configured mod role no longer exists. Please set a new one with `,setmodrole @role`.",
                color=discord.Color.orange(),
            )
            return await ctx.send(embed=embed)

        embed = discord.Embed(
            description=f"Current mod role: {role.mention}",
            color=colors.EMBED_COLOR,
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Config(bot))
