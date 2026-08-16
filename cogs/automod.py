import re
import time
from collections import defaultdict, deque

import discord
from discord.ext import commands

from utils import storage
from utils.checks import is_staff

AUTOMOD_FILE = "automod.json"

INVITE_REGEX = re.compile(r"(discord\.gg|discord(?:app)?\.com/invite)/\S+", re.IGNORECASE)
LINK_REGEX = re.compile(r"https?://\S+", re.IGNORECASE)

DEFAULT_CONFIG = {
    "enabled": False,
    "anti_spam": {"enabled": True, "message_limit": 5, "seconds": 5, "punishment": "timeout", "duration_minutes": 5},
    "mass_mention": {"enabled": True, "limit": 5, "punishment": "timeout", "duration_minutes": 5},
    "banned_words": {"enabled": True, "words": [], "punishment": "delete"},
    "invite_links": {"enabled": False, "punishment": "delete"},
    "excessive_caps": {"enabled": False, "min_length": 10, "percent": 70, "punishment": "delete"},
    "log_channel_id": None,
    "ignored_channel_ids": [],
}


def get_config(guild_id: int) -> dict:
    all_config = storage.load(AUTOMOD_FILE, {})
    guild_config = all_config.get(str(guild_id), {})
    # merge with defaults so new keys added later don't break old configs
    merged = {**DEFAULT_CONFIG, **guild_config}
    for key in ("anti_spam", "mass_mention", "banned_words", "invite_links", "excessive_caps"):
        merged[key] = {**DEFAULT_CONFIG[key], **guild_config.get(key, {})}
    return merged


def save_config(guild_id: int, config: dict):
    all_config = storage.load(AUTOMOD_FILE, {})
    all_config[str(guild_id)] = config
    storage.save(AUTOMOD_FILE, all_config)


class AutoMod(commands.Cog):
    """Automatic moderation: spam, mass mentions, banned words, invite links, excessive caps."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # guild_id -> user_id -> deque of message timestamps (for spam detection)
        self.message_log: dict[int, dict[int, deque]] = defaultdict(lambda: defaultdict(lambda: deque(maxlen=20)))

    async def log_action(self, guild: discord.Guild, config: dict, description: str):
        channel_id = config.get("log_channel_id")
        if not channel_id:
            return
        channel = guild.get_channel(channel_id)
        if not channel:
            return
        embed = discord.Embed(description=description, color=discord.Color.orange(), timestamp=discord.utils.utcnow())
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass

    async def punish(self, member: discord.Member, punishment: str, duration_minutes: int, reason: str):
        try:
            if punishment == "timeout":
                import datetime
                await member.timeout(datetime.timedelta(minutes=duration_minutes), reason=reason)
            elif punishment == "kick":
                await member.kick(reason=reason)
            elif punishment == "ban":
                await member.ban(reason=reason, delete_message_days=0)
            # "delete" punishment = message deletion only, handled by caller
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        config = get_config(message.guild.id)
        if not config["enabled"]:
            return
        if message.channel.id in config["ignored_channel_ids"]:
            return
        if is_staff(message.author):
            return  # staff are exempt from automod

        # ---- Banned words ----
        bw = config["banned_words"]
        if bw["enabled"] and bw["words"]:
            content_lower = message.content.lower()
            if any(word.lower() in content_lower for word in bw["words"]):
                try:
                    await message.delete()
                except (discord.Forbidden, discord.NotFound):
                    pass
                await self.log_action(
                    message.guild, config,
                    f"🚫 Blocked banned word from {message.author.mention} in {message.channel.mention}",
                )
                return

        # ---- Invite links ----
        il = config["invite_links"]
        if il["enabled"] and INVITE_REGEX.search(message.content):
            try:
                await message.delete()
            except (discord.Forbidden, discord.NotFound):
                pass
            await self.log_action(
                message.guild, config,
                f"🔗 Blocked invite link from {message.author.mention} in {message.channel.mention}",
            )
            return

        # ---- Mass mentions ----
        mm = config["mass_mention"]
        if mm["enabled"]:
            mention_count = len(message.mentions) + len(message.role_mentions)
            if mention_count >= mm["limit"]:
                try:
                    await message.delete()
                except (discord.Forbidden, discord.NotFound):
                    pass
                await self.punish(
                    message.author, mm["punishment"], mm["duration_minutes"],
                    reason="Automod: mass mention",
                )
                await self.log_action(
                    message.guild, config,
                    f"📢 {message.author.mention} mass-mentioned ({mention_count} mentions) — punished with `{mm['punishment']}`",
                )
                return

        # ---- Excessive caps ----
        ec = config["excessive_caps"]
        if ec["enabled"] and len(message.content) >= ec["min_length"]:
            letters = [c for c in message.content if c.isalpha()]
            if letters:
                caps_percent = (sum(1 for c in letters if c.isupper()) / len(letters)) * 100
                if caps_percent >= ec["percent"]:
                    try:
                        await message.delete()
                    except (discord.Forbidden, discord.NotFound):
                        pass
                    await self.log_action(
                        message.guild, config,
                        f"🔠 Blocked excessive caps from {message.author.mention} in {message.channel.mention}",
                    )
                    return

        # ---- Anti-spam ----
        sp = config["anti_spam"]
        if sp["enabled"]:
            log = self.message_log[message.guild.id][message.author.id]
            now = time.time()
            log.append(now)
            recent = [t for t in log if now - t <= sp["seconds"]]
            if len(recent) >= sp["message_limit"]:
                await self.punish(
                    message.author, sp["punishment"], sp["duration_minutes"],
                    reason="Automod: spam",
                )
                await self.log_action(
                    message.guild, config,
                    f"💨 {message.author.mention} was punished for spam (`{sp['punishment']}`)",
                )
                log.clear()


class AutoModConfig(commands.Cog, name="AutoMod Config"):
    """Admin commands to configure automod."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(name="automod", invoke_without_command=True)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def automod(self, ctx: commands.Context):
        """Show current automod configuration."""
        config = get_config(ctx.guild.id)
        embed = discord.Embed(title="🛡️ AutoMod Configuration", color=discord.Color.blurple())
        embed.add_field(name="Enabled", value="✅ Yes" if config["enabled"] else "❌ No", inline=False)
        embed.add_field(
            name="Anti-Spam",
            value=f"{'✅' if config['anti_spam']['enabled'] else '❌'} {config['anti_spam']['message_limit']} msgs / {config['anti_spam']['seconds']}s → `{config['anti_spam']['punishment']}`",
            inline=False,
        )
        embed.add_field(
            name="Mass Mention",
            value=f"{'✅' if config['mass_mention']['enabled'] else '❌'} limit {config['mass_mention']['limit']} → `{config['mass_mention']['punishment']}`",
            inline=False,
        )
        embed.add_field(
            name="Banned Words",
            value=f"{'✅' if config['banned_words']['enabled'] else '❌'} {len(config['banned_words']['words'])} word(s)",
            inline=False,
        )
        embed.add_field(
            name="Invite Links",
            value=f"{'✅' if config['invite_links']['enabled'] else '❌'}",
            inline=False,
        )
        embed.add_field(
            name="Excessive Caps",
            value=f"{'✅' if config['excessive_caps']['enabled'] else '❌'} {config['excessive_caps']['percent']}% threshold",
            inline=False,
        )
        log_ch = ctx.guild.get_channel(config["log_channel_id"]) if config["log_channel_id"] else None
        embed.add_field(name="Log Channel", value=log_ch.mention if log_ch else "Not set", inline=False)
        embed.set_footer(text=f"Use {ctx.prefix}help and select AutoMod for the full command list.")
        await ctx.send(embed=embed)

    @automod.command(name="toggle")
    @commands.has_permissions(administrator=True)
    async def automod_toggle(self, ctx: commands.Context, on_off: str):
        """Turn automod on or off entirely. Usage: ,automod toggle on / ,automod toggle off"""
        config = get_config(ctx.guild.id)
        config["enabled"] = on_off.lower() in ("on", "true", "enable", "enabled", "1")
        save_config(ctx.guild.id, config)
        state = "enabled ✅" if config["enabled"] else "disabled ❌"
        await ctx.send(embed=discord.Embed(description=f"AutoMod {state}.", color=discord.Color.green()))

    @automod.command(name="feature")
    @commands.has_permissions(administrator=True)
    async def automod_feature(self, ctx: commands.Context, feature: str, on_off: str):
        """Toggle a specific feature. Features: spam, mentions, words, invites, caps"""
        mapping = {
            "spam": "anti_spam",
            "mentions": "mass_mention",
            "words": "banned_words",
            "invites": "invite_links",
            "caps": "excessive_caps",
        }
        key = mapping.get(feature.lower())
        if not key:
            return await ctx.send(embed=discord.Embed(
                description=f"❌ Unknown feature. Choose from: {', '.join(mapping.keys())}",
                color=discord.Color.red(),
            ))
        config = get_config(ctx.guild.id)
        config[key]["enabled"] = on_off.lower() in ("on", "true", "enable", "enabled", "1")
        save_config(ctx.guild.id, config)
        state = "enabled ✅" if config[key]["enabled"] else "disabled ❌"
        await ctx.send(embed=discord.Embed(description=f"`{feature}` {state}.", color=discord.Color.green()))

    @automod.command(name="addword")
    @commands.has_permissions(administrator=True)
    async def automod_addword(self, ctx: commands.Context, *, word: str):
        """Add a word/phrase to the banned words list."""
        config = get_config(ctx.guild.id)
        if word.lower() not in [w.lower() for w in config["banned_words"]["words"]]:
            config["banned_words"]["words"].append(word)
            save_config(ctx.guild.id, config)
        await ctx.send(embed=discord.Embed(description=f"✅ Added `{word}` to the banned words list.", color=discord.Color.green()))

    @automod.command(name="removeword")
    @commands.has_permissions(administrator=True)
    async def automod_removeword(self, ctx: commands.Context, *, word: str):
        """Remove a word/phrase from the banned words list."""
        config = get_config(ctx.guild.id)
        config["banned_words"]["words"] = [w for w in config["banned_words"]["words"] if w.lower() != word.lower()]
        save_config(ctx.guild.id, config)
        await ctx.send(embed=discord.Embed(description=f"🗑️ Removed `{word}` from the banned words list.", color=discord.Color.green()))

    @automod.command(name="wordlist")
    @commands.has_permissions(administrator=True)
    async def automod_wordlist(self, ctx: commands.Context):
        """Show the current banned words list."""
        config = get_config(ctx.guild.id)
        words = config["banned_words"]["words"]
        desc = ", ".join(f"`{w}`" for w in words) if words else "No banned words set."
        await ctx.send(embed=discord.Embed(title="Banned Words", description=desc, color=discord.Color.blurple()))

    @automod.command(name="logchannel")
    @commands.has_permissions(administrator=True)
    async def automod_logchannel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Set (or clear, if no channel given) the automod log channel."""
        config = get_config(ctx.guild.id)
        config["log_channel_id"] = channel.id if channel else None
        save_config(ctx.guild.id, config)
        desc = f"✅ Log channel set to {channel.mention}." if channel else "✅ Log channel cleared."
        await ctx.send(embed=discord.Embed(description=desc, color=discord.Color.green()))

    @automod.command(name="ignorechannel")
    @commands.has_permissions(administrator=True)
    async def automod_ignorechannel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Toggle whether automod ignores a channel entirely."""
        config = get_config(ctx.guild.id)
        ids = config["ignored_channel_ids"]
        if channel.id in ids:
            ids.remove(channel.id)
            desc = f"✅ {channel.mention} is no longer ignored."
        else:
            ids.append(channel.id)
            desc = f"✅ {channel.mention} is now ignored by automod."
        save_config(ctx.guild.id, config)
        await ctx.send(embed=discord.Embed(description=desc, color=discord.Color.green()))

    @automod.command(name="spamsettings")
    @commands.has_permissions(administrator=True)
    async def automod_spamsettings(self, ctx: commands.Context, message_limit: int, seconds: int, punishment: str, duration_minutes: int = 5):
        """Configure anti-spam: message_limit, seconds, punishment (delete/timeout/kick/ban), duration_minutes."""
        if punishment not in ("delete", "timeout", "kick", "ban"):
            return await ctx.send(embed=discord.Embed(description="❌ Punishment must be one of: delete, timeout, kick, ban", color=discord.Color.red()))
        config = get_config(ctx.guild.id)
        config["anti_spam"].update({
            "message_limit": message_limit, "seconds": seconds,
            "punishment": punishment, "duration_minutes": duration_minutes,
        })
        save_config(ctx.guild.id, config)
        await ctx.send(embed=discord.Embed(
            description=f"✅ Anti-spam set: {message_limit} messages / {seconds}s → `{punishment}`",
            color=discord.Color.green(),
        ))

    @automod.command(name="mentionsettings")
    @commands.has_permissions(administrator=True)
    async def automod_mentionsettings(self, ctx: commands.Context, limit: int, punishment: str, duration_minutes: int = 5):
        """Configure mass-mention detection: limit, punishment (delete/timeout/kick/ban), duration_minutes."""
        if punishment not in ("delete", "timeout", "kick", "ban"):
            return await ctx.send(embed=discord.Embed(description="❌ Punishment must be one of: delete, timeout, kick, ban", color=discord.Color.red()))
        config = get_config(ctx.guild.id)
        config["mass_mention"].update({"limit": limit, "punishment": punishment, "duration_minutes": duration_minutes})
        save_config(ctx.guild.id, config)
        await ctx.send(embed=discord.Embed(
            description=f"✅ Mass mention set: limit {limit} → `{punishment}`",
            color=discord.Color.green(),
        ))

    @automod.command(name="capssettings")
    @commands.has_permissions(administrator=True)
    async def automod_capssettings(self, ctx: commands.Context, percent: int, min_length: int = 10):
        """Configure excessive caps detection: percent (0-100), min_length."""
        if not (0 <= percent <= 100):
            return await ctx.send(embed=discord.Embed(description="❌ Percent must be between 0 and 100.", color=discord.Color.red()))
        config = get_config(ctx.guild.id)
        config["excessive_caps"].update({"percent": percent, "min_length": min_length})
        save_config(ctx.guild.id, config)
        await ctx.send(embed=discord.Embed(
            description=f"✅ Excessive caps set: {percent}% threshold, min length {min_length}",
            color=discord.Color.green(),
        ))


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoMod(bot))
    await bot.add_cog(AutoModConfig(bot))
