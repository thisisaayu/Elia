import datetime
import time

import discord
from discord.ext import commands

from utils import storage
from utils.checks import has_mod_role, can_act_on

WARNINGS_FILE = "warnings.json"


def _get_warnings(guild_id: int, user_id: int) -> list:
    all_warnings = storage.load(WARNINGS_FILE, {})
    guild_warnings = all_warnings.get(str(guild_id), {})
    return guild_warnings.get(str(user_id), [])


def _add_warning(guild_id: int, user_id: int, moderator_id: int, reason: str):
    all_warnings = storage.load(WARNINGS_FILE, {})
    guild_key, user_key = str(guild_id), str(user_id)
    all_warnings.setdefault(guild_key, {}).setdefault(user_key, [])
    all_warnings[guild_key][user_key].append({
        "moderator_id": moderator_id,
        "reason": reason,
        "timestamp": time.time(),
    })
    storage.save(WARNINGS_FILE, all_warnings)
    return len(all_warnings[guild_key][user_key])


def _clear_warnings(guild_id: int, user_id: int):
    all_warnings = storage.load(WARNINGS_FILE, {})
    guild_key, user_key = str(guild_id), str(user_id)
    if guild_key in all_warnings and user_key in all_warnings[guild_key]:
        all_warnings[guild_key][user_key] = []
        storage.save(WARNINGS_FILE, all_warnings)


class Moderation(commands.Cog):
    """Moderation commands: kick, ban, timeout, warn, clear, slowmode."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CheckFailure):
            embed = discord.Embed(
                description="❌ You need the mod role to use this command.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                description=f"❌ Missing an argument: `{error.param.name}`",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                description="❌ Couldn't find that user/role. Try mentioning them or using their ID.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
        else:
            raise error

    # ---------------- KICK ----------------
    @commands.command(name="kick")
    @has_mod_role()
    @commands.guild_only()
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """Kick a member from the server."""
        if not can_act_on(ctx.author, member):
            embed = discord.Embed(description="❌ You can't act on that member.", color=discord.Color.red())
            return await ctx.send(embed=embed)

        try:
            await member.send(f"You were kicked from **{ctx.guild.name}**.\nReason: {reason}")
        except discord.Forbidden:
            pass  # user has DMs off, ignore

        await member.kick(reason=f"By {ctx.author}: {reason}")

        embed = discord.Embed(
            description=f"👢 **{member}** was kicked.\n**Reason:** {reason}",
            color=discord.Color.orange(),
        )
        await ctx.send(embed=embed)

    # ---------------- BAN ----------------
    @commands.command(name="ban")
    @has_mod_role()
    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """Ban a member from the server."""
        if not can_act_on(ctx.author, member):
            embed = discord.Embed(description="❌ You can't act on that member.", color=discord.Color.red())
            return await ctx.send(embed=embed)

        try:
            await member.send(f"You were banned from **{ctx.guild.name}**.\nReason: {reason}")
        except discord.Forbidden:
            pass

        await member.ban(reason=f"By {ctx.author}: {reason}", delete_message_days=0)

        embed = discord.Embed(
            description=f"🔨 **{member}** was banned.\n**Reason:** {reason}",
            color=discord.Color.red(),
        )
        await ctx.send(embed=embed)

    # ---------------- UNBAN ----------------
    @commands.command(name="unban")
    @has_mod_role()
    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, user_id: int, *, reason: str = "No reason provided"):
        """Unban a user by their ID."""
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=f"By {ctx.author}: {reason}")
        except discord.NotFound:
            embed = discord.Embed(description="❌ That user isn't banned or doesn't exist.", color=discord.Color.red())
            return await ctx.send(embed=embed)

        embed = discord.Embed(
            description=f"✅ **{user}** was unbanned.\n**Reason:** {reason}",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    # ---------------- TIMEOUT ----------------
    @commands.command(name="timeout", aliases=["mute"])
    @has_mod_role()
    @commands.guild_only()
    @commands.bot_has_permissions(moderate_members=True)
    async def timeout(self, ctx: commands.Context, member: discord.Member, minutes: int, *, reason: str = "No reason provided"):
        """Timeout (mute) a member for a number of minutes (max 40320 = 28 days)."""
        if not can_act_on(ctx.author, member):
            embed = discord.Embed(description="❌ You can't act on that member.", color=discord.Color.red())
            return await ctx.send(embed=embed)

        if minutes <= 0 or minutes > 40320:
            embed = discord.Embed(description="❌ Minutes must be between 1 and 40320 (28 days).", color=discord.Color.red())
            return await ctx.send(embed=embed)

        duration = datetime.timedelta(minutes=minutes)
        await member.timeout(duration, reason=f"By {ctx.author}: {reason}")

        embed = discord.Embed(
            description=f"🔇 **{member}** was timed out for **{minutes} minute(s)**.\n**Reason:** {reason}",
            color=discord.Color.orange(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="untimeout", aliases=["unmute"])
    @has_mod_role()
    @commands.guild_only()
    @commands.bot_has_permissions(moderate_members=True)
    async def untimeout(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """Remove a member's timeout."""
        await member.timeout(None, reason=f"By {ctx.author}: {reason}")
        embed = discord.Embed(
            description=f"🔊 **{member}**'s timeout was removed.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    # ---------------- WARN ----------------
    @commands.command(name="warn")
    @has_mod_role()
    @commands.guild_only()
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """Warn a member. Warnings are saved permanently."""
        if not can_act_on(ctx.author, member):
            embed = discord.Embed(description="❌ You can't act on that member.", color=discord.Color.red())
            return await ctx.send(embed=embed)

        count = _add_warning(ctx.guild.id, member.id, ctx.author.id, reason)

        try:
            await member.send(f"You were warned in **{ctx.guild.name}**.\nReason: {reason}")
        except discord.Forbidden:
            pass

        embed = discord.Embed(
            description=f"⚠️ **{member}** has been warned.\n**Reason:** {reason}\n**Total warnings:** {count}",
            color=discord.Color.orange(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="warnings", aliases=["warns"])
    @has_mod_role()
    @commands.guild_only()
    async def warnings_cmd(self, ctx: commands.Context, member: discord.Member):
        """View a member's warning history."""
        warns = _get_warnings(ctx.guild.id, member.id)

        embed = discord.Embed(
            title=f"Warnings for {member}",
            color=discord.Color.blurple(),
        )
        if not warns:
            embed.description = "No warnings on record."
        else:
            for i, w in enumerate(warns, start=1):
                mod = ctx.guild.get_member(w["moderator_id"])
                mod_name = str(mod) if mod else f"ID {w['moderator_id']}"
                when = datetime.datetime.fromtimestamp(w["timestamp"]).strftime("%Y-%m-%d %H:%M")
                embed.add_field(
                    name=f"#{i} — {when}",
                    value=f"**Reason:** {w['reason']}\n**By:** {mod_name}",
                    inline=False,
                )

        await ctx.send(embed=embed)

    @commands.command(name="clearwarnings", aliases=["clearwarns"])
    @has_mod_role()
    @commands.guild_only()
    async def clearwarnings(self, ctx: commands.Context, member: discord.Member):
        """Clear all warnings for a member."""
        _clear_warnings(ctx.guild.id, member.id)
        embed = discord.Embed(
            description=f"🗑️ Cleared all warnings for **{member}**.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    # ---------------- CLEAR / PURGE ----------------
    @commands.command(name="purge", aliases=["c", "clear"])
    @has_mod_role()
    @commands.guild_only()
    @commands.bot_has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, amount: int = None):
        """Bulk-delete a number of recent messages (max 100). Does nothing if no amount is given."""
        if amount is None:
            return  # no number given — silently do nothing

        if amount <= 0 or amount > 100:
            embed = discord.Embed(description="❌ Amount must be between 1 and 100.", color=discord.Color.red())
            return await ctx.send(embed=embed)

        deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message itself

        embed = discord.Embed(
            description=f"🧹 Deleted **{len(deleted) - 1}** messages.",
            color=discord.Color.green(),
        )
        msg = await ctx.send(embed=embed)
        await msg.delete(delay=4)

    # ---------------- SLOWMODE ----------------
    @commands.command(name="slowmode")
    @has_mod_role()
    @commands.guild_only()
    @commands.bot_has_permissions(manage_channels=True)
    async def slowmode(self, ctx: commands.Context, seconds: int):
        """Set slowmode for the current channel (0 to disable, max 21600)."""
        if seconds < 0 or seconds > 21600:
            embed = discord.Embed(description="❌ Seconds must be between 0 and 21600 (6 hours).", color=discord.Color.red())
            return await ctx.send(embed=embed)

        await ctx.channel.edit(slowmode_delay=seconds)

        if seconds == 0:
            embed = discord.Embed(description="✅ Slowmode disabled for this channel.", color=discord.Color.green())
        else:
            embed = discord.Embed(description=f"🐌 Slowmode set to **{seconds} second(s)**.", color=discord.Color.blurple())
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
