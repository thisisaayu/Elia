import datetime

import discord
from discord.ext import commands

from utils import storage, colors

LOGGING_FILE = "logging_config.json"

DEFAULT_EVENTS = {
    "join": True,
    "leave": True,
    "kick": True,
    "ban": True,
    "unban": True,
    "timeout": True,
    "message_delete": True,
    "message_edit": True,
    "role_update": False,
    "nickname_update": False,
}

EVENT_LABELS = {
    "join": "Member Join",
    "leave": "Member Leave",
    "kick": "Member Kick",
    "ban": "Member Ban",
    "unban": "Member Unban",
    "timeout": "Member Timeout",
    "message_delete": "Message Delete",
    "message_edit": "Message Edit",
    "role_update": "Role Update",
    "nickname_update": "Nickname Update",
}


def get_config(guild_id: int) -> dict:
    all_config = storage.load(LOGGING_FILE, {})
    guild_config = all_config.get(str(guild_id), {})
    events = {**DEFAULT_EVENTS, **guild_config.get("events", {})}
    return {"log_channel_id": guild_config.get("log_channel_id"), "events": events}


def save_config(guild_id: int, config: dict):
    all_config = storage.load(LOGGING_FILE, {})
    all_config[str(guild_id)] = config
    storage.save(LOGGING_FILE, all_config)


class Logging(commands.Cog):
    """Server event logging: joins, leaves, message edits/deletes, mod actions."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _send_log(self, guild: discord.Guild, event_key: str, embed: discord.Embed):
        config = get_config(guild.id)
        if not config["log_channel_id"] or not config["events"].get(event_key, False):
            return
        channel = guild.get_channel(config["log_channel_id"])
        if not channel:
            return
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass

    async def _find_audit_entry(self, guild: discord.Guild, action: discord.AuditLogAction, target_id: int, within_seconds: int = 8):
        """Best-effort lookup of a recent audit log entry for a given target. Returns None if not found/no permission."""
        try:
            async for entry in guild.audit_logs(action=action, limit=5):
                if entry.target and getattr(entry.target, "id", None) == target_id:
                    age = (discord.utils.utcnow() - entry.created_at).total_seconds()
                    if age <= within_seconds:
                        return entry
        except discord.Forbidden:
            return None
        return None

    # ---------------- MEMBER JOIN / LEAVE / KICK ----------------
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        account_age = (discord.utils.utcnow() - member.created_at).days
        embed = discord.Embed(
            description=f"📥 {member.mention} joined the server.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Account Age", value=f"{account_age} day(s)", inline=True)
        embed.add_field(name="Member Count", value=str(member.guild.member_count), inline=True)
        embed.set_footer(text=f"ID: {member.id}")
        await self._send_log(member.guild, "join", embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        kick_entry = await self._find_audit_entry(member.guild, discord.AuditLogAction.kick, member.id)

        if kick_entry:
            embed = discord.Embed(
                description=f"👢 **{member}** was kicked.",
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow(),
            )
            embed.add_field(name="Moderator", value=str(kick_entry.user), inline=True)
            embed.add_field(name="Reason", value=kick_entry.reason or "No reason provided", inline=True)
            embed.set_footer(text=f"ID: {member.id}")
            await self._send_log(member.guild, "kick", embed)
        else:
            embed = discord.Embed(
                description=f"📤 **{member}** left the server.",
                color=discord.Color.dark_gray(),
                timestamp=discord.utils.utcnow(),
            )
            embed.set_footer(text=f"ID: {member.id}")
            await self._send_log(member.guild, "leave", embed)

    # ---------------- BAN / UNBAN ----------------
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.abc.User):
        entry = await self._find_audit_entry(guild, discord.AuditLogAction.ban, user.id)
        embed = discord.Embed(
            description=f"🔨 **{user}** was banned.",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow(),
        )
        if entry:
            embed.add_field(name="Moderator", value=str(entry.user), inline=True)
            embed.add_field(name="Reason", value=entry.reason or "No reason provided", inline=True)
        embed.set_footer(text=f"ID: {user.id}")
        await self._send_log(guild, "ban", embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.abc.User):
        entry = await self._find_audit_entry(guild, discord.AuditLogAction.unban, user.id)
        embed = discord.Embed(
            description=f"✅ **{user}** was unbanned.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow(),
        )
        if entry:
            embed.add_field(name="Moderator", value=str(entry.user), inline=True)
        embed.set_footer(text=f"ID: {user.id}")
        await self._send_log(guild, "unban", embed)

    # ---------------- MEMBER UPDATE (timeout, nickname, roles) ----------------
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        # Timeout applied/removed
        if before.timed_out_until != after.timed_out_until:
            entry = await self._find_audit_entry(after.guild, discord.AuditLogAction.member_update, after.id)
            if after.timed_out_until and (after.timed_out_until > discord.utils.utcnow()):
                embed = discord.Embed(
                    description=f"🔇 **{after}** was timed out until {discord.utils.format_dt(after.timed_out_until, style='f')}.",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow(),
                )
            else:
                embed = discord.Embed(
                    description=f"🔊 **{after}**'s timeout was removed.",
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow(),
                )
            if entry:
                embed.add_field(name="Moderator", value=str(entry.user), inline=True)
                if entry.reason:
                    embed.add_field(name="Reason", value=entry.reason, inline=True)
            embed.set_footer(text=f"ID: {after.id}")
            await self._send_log(after.guild, "timeout", embed)

        # Nickname change
        if before.nick != after.nick:
            embed = discord.Embed(
                description=f"✏️ **{after}**'s nickname changed.",
                color=colors.EMBED_COLOR,
                timestamp=discord.utils.utcnow(),
            )
            embed.add_field(name="Before", value=before.nick or "*(none)*", inline=True)
            embed.add_field(name="After", value=after.nick or "*(none)*", inline=True)
            embed.set_footer(text=f"ID: {after.id}")
            await self._send_log(after.guild, "nickname_update", embed)

        # Role changes
        before_roles = set(before.roles)
        after_roles = set(after.roles)
        added = after_roles - before_roles
        removed = before_roles - after_roles
        if added or removed:
            embed = discord.Embed(
                description=f"🎭 **{after}**'s roles changed.",
                color=colors.EMBED_COLOR,
                timestamp=discord.utils.utcnow(),
            )
            if added:
                embed.add_field(name="Added", value=", ".join(r.mention for r in added), inline=False)
            if removed:
                embed.add_field(name="Removed", value=", ".join(r.mention for r in removed), inline=False)
            embed.set_footer(text=f"ID: {after.id}")
            await self._send_log(after.guild, "role_update", embed)

    # ---------------- MESSAGE DELETE / EDIT ----------------
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        embed = discord.Embed(
            description=f"🗑️ Message by {message.author.mention} deleted in {message.channel.mention}.",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow(),
        )
        if message.content:
            embed.add_field(name="Content", value=message.content[:1000], inline=False)
        if message.attachments:
            embed.add_field(name="Attachments", value=str(len(message.attachments)), inline=False)
        embed.set_footer(text=f"Author ID: {message.author.id}")
        await self._send_log(message.guild, "message_delete", embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or not before.guild or before.content == after.content:
            return
        embed = discord.Embed(
            description=f"✏️ Message by {before.author.mention} edited in {before.channel.mention}. [Jump]({after.jump_url})",
            color=colors.EMBED_COLOR,
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="Before", value=(before.content or "*(empty)*")[:1000], inline=False)
        embed.add_field(name="After", value=(after.content or "*(empty)*")[:1000], inline=False)
        embed.set_footer(text=f"Author ID: {before.author.id}")
        await self._send_log(before.guild, "message_edit", embed)

    # ---------------- CONFIG COMMANDS ----------------
    @commands.group(name="logs", invoke_without_command=True)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def logs(self, ctx: commands.Context):
        """Show the current logging configuration."""
        config = get_config(ctx.guild.id)
        channel = ctx.guild.get_channel(config["log_channel_id"]) if config["log_channel_id"] else None

        embed = discord.Embed(title="📋 Logging Configuration", color=colors.EMBED_COLOR)
        embed.add_field(name="Log Channel", value=channel.mention if channel else "Not set", inline=False)

        status_lines = []
        for key, label in EVENT_LABELS.items():
            enabled = config["events"].get(key, False)
            status_lines.append(f"{'✅' if enabled else '❌'} {label}")
        embed.add_field(name="Events", value="\n".join(status_lines), inline=False)

        await ctx.reply(embed=embed)

    @logs.command(name="setchannel")
    async def logs_setchannel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Set (or clear, if no channel given) the log channel."""
        config = get_config(ctx.guild.id)
        config["log_channel_id"] = channel.id if channel else None
        save_config(ctx.guild.id, config)
        if channel:
            embed = discord.Embed(description=f"✅ Logs will now be sent to {channel.mention}.", color=discord.Color.green())
        else:
            embed = discord.Embed(description="✅ Log channel cleared. Logging is now off.", color=discord.Color.green())
        await ctx.reply(embed=embed)

    @logs.command(name="toggle")
    async def logs_toggle(self, ctx: commands.Context, event: str, state: str):
        """Toggle a specific event: ,logs toggle message_delete on"""
        event = event.lower()
        if event not in EVENT_LABELS:
            valid = ", ".join(EVENT_LABELS.keys())
            embed = discord.Embed(description=f"❌ Unknown event. Choose from: {valid}", color=discord.Color.red())
            return await ctx.reply(embed=embed)

        value = state.lower() in ("on", "true", "yes", "enable", "enabled")
        config = get_config(ctx.guild.id)
        config["events"][event] = value
        save_config(ctx.guild.id, config)

        embed = discord.Embed(
            description=f"✅ **{EVENT_LABELS[event]}** logging {'enabled' if value else 'disabled'}.",
            color=discord.Color.green(),
        )
        await ctx.reply(embed=embed)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CheckFailure):
            embed = discord.Embed(description="❌ You need Administrator to manage logging.", color=discord.Color.red())
            await ctx.reply(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(description=f"❌ Missing an argument: `{error.param.name}`", color=discord.Color.red())
            await ctx.reply(embed=embed)
        else:
            raise error


async def setup(bot: commands.Bot):
    await bot.add_cog(Logging(bot))
