import discord
from discord.ext import commands

from utils import storage
from utils.checks import has_mod_role
from utils import colors

LOCKDOWN_FILE = "lockdown.json"


def _get_saved_state(guild_id: int, channel_id: int, key: str):
    all_data = storage.load(LOCKDOWN_FILE, {})
    return all_data.get(str(guild_id), {}).get(str(channel_id), {}).get(key, "__unset__")


def _save_state(guild_id: int, channel_id: int, key: str, value):
    all_data = storage.load(LOCKDOWN_FILE, {})
    guild_key, chan_key = str(guild_id), str(channel_id)
    all_data.setdefault(guild_key, {}).setdefault(chan_key, {})
    all_data[guild_key][chan_key][key] = value
    storage.save(LOCKDOWN_FILE, all_data)


def _clear_state(guild_id: int, channel_id: int, key: str):
    all_data = storage.load(LOCKDOWN_FILE, {})
    guild_key, chan_key = str(guild_id), str(channel_id)
    if guild_key in all_data and chan_key in all_data[guild_key] and key in all_data[guild_key][chan_key]:
        del all_data[guild_key][chan_key][key]
        storage.save(LOCKDOWN_FILE, all_data)


class Lockdown(commands.Cog):
    """Channel and server lock/unlock/hide/unhide commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _lock_channel(self, channel: discord.TextChannel, everyone: discord.Role) -> bool:
        """Deny send_messages for @everyone, remembering the prior value. Returns True if changed."""
        overwrite = channel.overwrites_for(everyone)
        if overwrite.send_messages is False:
            return False  # already locked
        _save_state(channel.guild.id, channel.id, "send_messages", overwrite.send_messages)
        overwrite.send_messages = False
        await channel.set_permissions(everyone, overwrite=overwrite, reason="Channel locked")
        return True

    async def _unlock_channel(self, channel: discord.TextChannel, everyone: discord.Role) -> bool:
        overwrite = channel.overwrites_for(everyone)
        if overwrite.send_messages is not False:
            return False  # not locked
        previous = _get_saved_state(channel.guild.id, channel.id, "send_messages")
        overwrite.send_messages = None if previous == "__unset__" else previous
        await channel.set_permissions(everyone, overwrite=overwrite, reason="Channel unlocked")
        _clear_state(channel.guild.id, channel.id, "send_messages")
        return True

    async def _hide_channel(self, channel: discord.TextChannel, everyone: discord.Role) -> bool:
        overwrite = channel.overwrites_for(everyone)
        if overwrite.view_channel is False:
            return False
        _save_state(channel.guild.id, channel.id, "view_channel", overwrite.view_channel)
        overwrite.view_channel = False
        await channel.set_permissions(everyone, overwrite=overwrite, reason="Channel hidden")
        return True

    async def _unhide_channel(self, channel: discord.TextChannel, everyone: discord.Role) -> bool:
        overwrite = channel.overwrites_for(everyone)
        if overwrite.view_channel is not False:
            return False
        previous = _get_saved_state(channel.guild.id, channel.id, "view_channel")
        overwrite.view_channel = None if previous == "__unset__" else previous
        await channel.set_permissions(everyone, overwrite=overwrite, reason="Channel unhidden")
        _clear_state(channel.guild.id, channel.id, "view_channel")
        return True

    # ---------------- LOCK ----------------
    @commands.hybrid_command(name="lock")
    @has_mod_role()
    @commands.guild_only()
    @commands.bot_has_permissions(manage_channels=True)
    async def lock(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Lock a channel (stops @everyone from sending messages). Defaults to the current channel."""
        channel = channel or ctx.channel
        everyone = ctx.guild.default_role
        changed = await self._lock_channel(channel, everyone)
        if changed:
            embed = discord.Embed(description=f"🔒 {channel.mention} has been locked.", color=discord.Color.red())
        else:
            embed = discord.Embed(description=f"⚠️ {channel.mention} is already locked.", color=discord.Color.orange())
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="unlock")
    @has_mod_role()
    @commands.guild_only()
    @commands.bot_has_permissions(manage_channels=True)
    async def unlock(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Unlock a channel, restoring its previous permission state. Defaults to the current channel."""
        channel = channel or ctx.channel
        everyone = ctx.guild.default_role
        changed = await self._unlock_channel(channel, everyone)
        if changed:
            embed = discord.Embed(description=f"🔓 {channel.mention} has been unlocked.", color=discord.Color.green())
        else:
            embed = discord.Embed(description=f"⚠️ {channel.mention} isn't locked.", color=discord.Color.orange())
        await ctx.send(embed=embed)

    # ---------------- HIDE ----------------
    @commands.hybrid_command(name="hide")
    @has_mod_role()
    @commands.guild_only()
    @commands.bot_has_permissions(manage_channels=True)
    async def hide(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Hide a channel from @everyone. Defaults to the current channel."""
        channel = channel or ctx.channel
        everyone = ctx.guild.default_role
        changed = await self._hide_channel(channel, everyone)
        if changed:
            embed = discord.Embed(description=f"🙈 {channel.mention} has been hidden.", color=discord.Color.red())
        else:
            embed = discord.Embed(description=f"⚠️ {channel.mention} is already hidden.", color=discord.Color.orange())
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="unhide")
    @has_mod_role()
    @commands.guild_only()
    @commands.bot_has_permissions(manage_channels=True)
    async def unhide(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Unhide a channel, restoring its previous visibility. Defaults to the current channel."""
        channel = channel or ctx.channel
        everyone = ctx.guild.default_role
        changed = await self._unhide_channel(channel, everyone)
        if changed:
            embed = discord.Embed(description=f"👁️ {channel.mention} is visible again.", color=discord.Color.green())
        else:
            embed = discord.Embed(description=f"⚠️ {channel.mention} isn't hidden.", color=discord.Color.orange())
        await ctx.send(embed=embed)

    # ---------------- SERVER-WIDE ----------------
    @commands.hybrid_command(name="lockdown", aliases=["lockall"])
    @has_mod_role()
    @commands.guild_only()
    @commands.bot_has_permissions(manage_channels=True)
    async def lockdown(self, ctx: commands.Context):
        """Lock every text channel in the server."""
        everyone = ctx.guild.default_role
        count = 0
        msg = await ctx.send(embed=discord.Embed(description="🔒 Locking down the server...", color=discord.Color.orange()))
        for channel in ctx.guild.text_channels:
            try:
                if await self._lock_channel(channel, everyone):
                    count += 1
            except (discord.Forbidden, discord.HTTPException):
                continue
        await msg.edit(embed=discord.Embed(
            description=f"🔒 Server lockdown complete. Locked **{count}** channel(s).",
            color=discord.Color.red(),
        ))

    @commands.hybrid_command(name="unlockdown", aliases=["unlockall"])
    @has_mod_role()
    @commands.guild_only()
    @commands.bot_has_permissions(manage_channels=True)
    async def unlockdown(self, ctx: commands.Context):
        """Unlock every text channel in the server."""
        everyone = ctx.guild.default_role
        count = 0
        msg = await ctx.send(embed=discord.Embed(description="🔓 Lifting lockdown...", color=colors.EMBED_COLOR))
        for channel in ctx.guild.text_channels:
            try:
                if await self._unlock_channel(channel, everyone):
                    count += 1
            except (discord.Forbidden, discord.HTTPException):
                continue
        await msg.edit(embed=discord.Embed(
            description=f"🔓 Lockdown lifted. Unlocked **{count}** channel(s).",
            color=discord.Color.green(),
        ))

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CheckFailure):
            await ctx.send(embed=discord.Embed(description="❌ You need the mod role to use this command.", color=discord.Color.red()))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(embed=discord.Embed(description="❌ Couldn't find that channel.", color=discord.Color.red()))
        else:
            raise error


async def setup(bot: commands.Bot):
    await bot.add_cog(Lockdown(bot))
