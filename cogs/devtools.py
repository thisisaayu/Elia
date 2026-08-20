import discord
from discord.ext import commands

from utils import colors


class DevTools(commands.Cog):
    """Bot-owner-only development utilities."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="sync")
    @commands.is_owner()
    async def sync(self, ctx: commands.Context, scope: str = "guild"):
        """Sync slash commands. ,sync guild = instant in this server (for testing).
        ,sync global = sync everywhere (can take up to ~1 hour to fully propagate)."""
        if scope == "guild":
            if not ctx.guild:
                embed = discord.Embed(description="❌ Run this inside a server to sync it instantly.", color=discord.Color.red())
                return await ctx.reply(embed=embed)
            self.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await self.bot.tree.sync(guild=ctx.guild)
            embed = discord.Embed(
                description=f"✅ Synced **{len(synced)}** slash command(s) instantly to this server.",
                color=discord.Color.green(),
            )
        elif scope == "global":
            synced = await self.bot.tree.sync()
            embed = discord.Embed(
                description=f"✅ Synced **{len(synced)}** slash command(s) globally. Can take up to ~1 hour to fully appear everywhere.",
                color=discord.Color.green(),
            )
        else:
            embed = discord.Embed(description="❌ Use `,sync guild` or `,sync global`.", color=discord.Color.red())

        await ctx.reply(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(DevTools(bot))
