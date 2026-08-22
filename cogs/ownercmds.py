import os
import platform
import time

import discord
from discord.ext import commands

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from utils import colors

# Hardcoded — these are the only user IDs that can use anything in this file,
# regardless of server roles or permissions. Add/remove IDs here directly.
BOT_ADMIN_IDS = {
    690506706853167104,
    1141696019797639208,
    856197301532753970,
}

PROCESS_START = time.time()


def is_bot_admin():
    async def predicate(ctx: commands.Context):
        if ctx.author.id in BOT_ADMIN_IDS:
            return True
        # Deliberately vague failure — don't reveal this command exists to non-admins
        raise commands.CheckFailure("not a bot admin")
    return commands.check(predicate)


def format_uptime(seconds: float) -> str:
    seconds = int(seconds)
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)
    parts = []
    if days: parts.append(f"{days}d")
    if hours: parts.append(f"{hours}h")
    if minutes: parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


class OwnerCommands(commands.Cog):
    """Hidden commands restricted to specific user IDs. Not shown in ,help."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------------- STATS ----------------
    @commands.command(name="stats")
    @is_bot_admin()
    async def stats(self, ctx: commands.Context):
        """Deep system/process stats (bot admins only)."""
        total_users = sum(g.member_count for g in self.bot.guilds)
        uptime = format_uptime(time.time() - PROCESS_START)

        embed = discord.Embed(title="📊 Bot Admin Stats", color=colors.EMBED_COLOR, timestamp=discord.utils.utcnow())
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Users", value=str(total_users), inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)

        embed.add_field(name="Uptime", value=uptime, inline=True)
        embed.add_field(name="Python", value=platform.python_version(), inline=True)
        embed.add_field(name="discord.py", value=discord.__version__, inline=True)

        embed.add_field(name="Cogs Loaded", value=str(len(self.bot.cogs)), inline=True)
        embed.add_field(name="Commands", value=str(len(self.bot.commands)), inline=True)

        if HAS_PSUTIL:
            process = psutil.Process(os.getpid())
            mem_mb = process.memory_info().rss / (1024 * 1024)
            cpu_percent = process.cpu_percent(interval=0.1)
            embed.add_field(name="Memory (RSS)", value=f"{mem_mb:.1f} MB", inline=True)
            embed.add_field(name="CPU", value=f"{cpu_percent:.1f}%", inline=True)
        else:
            embed.add_field(name="Memory/CPU", value="psutil not installed", inline=True)

        await ctx.reply(embed=embed)

    # ---------------- SERVER LIST ----------------
    @commands.command(name="servers")
    @is_bot_admin()
    async def servers(self, ctx: commands.Context):
        """List every server the bot is in (bot admins only)."""
        guilds = sorted(self.bot.guilds, key=lambda g: g.member_count, reverse=True)

        lines = []
        for g in guilds[:25]:
            owner = str(g.owner) if g.owner else "Unknown"
            lines.append(f"**{g.name}** (`{g.id}`) — {g.member_count} members — owner: {owner}")

        embed = discord.Embed(
            title=f"🌐 Servers ({len(guilds)})",
            description="\n".join(lines) or "No servers.",
            color=colors.EMBED_COLOR,
        )
        if len(guilds) > 25:
            embed.set_footer(text=f"Showing top 25 of {len(guilds)} by member count.")
        await ctx.reply(embed=embed)

    # ---------------- LEAVE A SERVER ----------------
    @commands.command(name="leaveguild")
    @is_bot_admin()
    async def leaveguild(self, ctx: commands.Context, guild_id: int):
        """Make the bot leave a specific server by ID (bot admins only)."""
        guild = self.bot.get_guild(guild_id)
        if not guild:
            embed = discord.Embed(description=f"❌ Not in a server with ID `{guild_id}`.", color=discord.Color.red())
            return await ctx.reply(embed=embed)

        name = guild.name
        await guild.leave()
        embed = discord.Embed(description=f"✅ Left **{name}** (`{guild_id}`).", color=discord.Color.green())
        await ctx.reply(embed=embed)

    # ---------------- HOT-RELOAD A COG ----------------
    @commands.command(name="reloadcog")
    @is_bot_admin()
    async def reloadcog(self, ctx: commands.Context, cog_name: str):
        """Reload a single cog without restarting the whole bot: ,reloadcog moderation"""
        extension = f"cogs.{cog_name}"
        try:
            await self.bot.reload_extension(extension)
        except commands.ExtensionNotLoaded:
            try:
                await self.bot.load_extension(extension)
            except Exception as e:
                embed = discord.Embed(description=f"❌ Couldn't load `{extension}`: {e}", color=discord.Color.red())
                return await ctx.reply(embed=embed)
        except Exception as e:
            embed = discord.Embed(description=f"❌ Failed to reload `{extension}`: {e}", color=discord.Color.red())
            return await ctx.reply(embed=embed)

        embed = discord.Embed(description=f"✅ Reloaded `{extension}`.", color=discord.Color.green())
        await ctx.reply(embed=embed)

    # ---------------- SHUTDOWN ----------------
    @commands.command(name="shutdown")
    @is_bot_admin()
    async def shutdown(self, ctx: commands.Context):
        """Gracefully shut down the bot process (bot admins only).
        Note: whether it comes back online depends on your host's auto-restart settings."""
        embed = discord.Embed(description="🛑 Shutting down...", color=discord.Color.orange())
        await ctx.reply(embed=embed)
        await self.bot.close()

    # ---------------- HELP (admins only) ----------------
    @commands.command(name="devhelp")
    @is_bot_admin()
    async def devhelp(self, ctx: commands.Context):
        """Show this list. Bot admins only — not shown anywhere else."""
        embed = discord.Embed(
            title="🔧 Bot Admin Commands",
            description="Restricted to specific user IDs, regardless of server roles.",
            color=colors.EMBED_COLOR,
        )
        embed.add_field(name=f"{ctx.prefix}stats", value="Deep system/process stats.", inline=False)
        embed.add_field(name=f"{ctx.prefix}servers", value="List every server the bot is in.", inline=False)
        embed.add_field(name=f"{ctx.prefix}leaveguild <guild_id>", value="Make the bot leave a specific server.", inline=False)
        embed.add_field(name=f"{ctx.prefix}reloadcog <name>", value="Hot-reload a single cog without a full restart.", inline=False)
        embed.add_field(name=f"{ctx.prefix}shutdown", value="Gracefully shut down the bot process.", inline=False)
        await ctx.reply(embed=embed)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CheckFailure):
            return  # silently ignore — don't reveal these commands exist to non-admins
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(description=f"❌ Missing an argument: `{error.param.name}`", color=discord.Color.red())
            return await ctx.reply(embed=embed)
        raise error


async def setup(bot: commands.Bot):
    await bot.add_cog(OwnerCommands(bot))
