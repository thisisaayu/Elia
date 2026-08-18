import discord
from discord.ext import commands

from utils import storage
from utils.checks import has_mod_role

AUTORESPONDER_FILE = "autoresponders.json"
MAX_RESPONDERS_PER_GUILD = 50
MAX_TRIGGER_LENGTH = 100
MAX_RESPONSE_LENGTH = 1800  # leaves room for placeholder expansion under Discord's 2000 char limit


def get_guild_responders(guild_id: int) -> dict:
    """Returns {trigger_lower: {"trigger": original_case, "response": str}}"""
    all_data = storage.load(AUTORESPONDER_FILE, {})
    return all_data.get(str(guild_id), {}).get("triggers", {})


def get_guild_settings(guild_id: int) -> dict:
    all_data = storage.load(AUTORESPONDER_FILE, {})
    guild_data = all_data.get(str(guild_id), {})
    return {"enabled": guild_data.get("enabled", True)}


def save_guild_responders(guild_id: int, triggers: dict):
    all_data = storage.load(AUTORESPONDER_FILE, {})
    guild_key = str(guild_id)
    all_data.setdefault(guild_key, {})
    all_data[guild_key]["triggers"] = triggers
    storage.save(AUTORESPONDER_FILE, all_data)


def set_enabled(guild_id: int, enabled: bool):
    all_data = storage.load(AUTORESPONDER_FILE, {})
    guild_key = str(guild_id)
    all_data.setdefault(guild_key, {})
    all_data[guild_key]["enabled"] = enabled
    storage.save(AUTORESPONDER_FILE, all_data)


def expand_placeholders(response: str, message: discord.Message) -> str:
    return (
        response
        .replace("{user}", message.author.mention)
        .replace("{username}", message.author.display_name)
        .replace("{server}", message.guild.name if message.guild else "this server")
        .replace("{channel}", message.channel.mention)
    )


class AutoResponder(commands.Cog):
    """Custom trigger -> response autoresponders."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------------- LISTENER ----------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        # don't trigger on actual bot commands
        if message.content.startswith(self.bot.command_prefix):
            return

        settings = get_guild_settings(message.guild.id)
        if not settings["enabled"]:
            return

        triggers = get_guild_responders(message.guild.id)
        if not triggers:
            return

        content_lower = message.content.lower()
        for trigger_lower, data in triggers.items():
            if trigger_lower in content_lower:
                response = expand_placeholders(data["response"], message)
                try:
                    await message.reply(response, mention_author=False)
                except discord.Forbidden:
                    pass
                return  # only fire the first matching trigger per message

    # ---------------- CONFIG COMMANDS ----------------
    @commands.group(name="autoresponder", aliases=["ar"], invoke_without_command=True)
    @commands.guild_only()
    async def autoresponder(self, ctx: commands.Context):
        """List all autoresponders configured for this server."""
        triggers = get_guild_responders(ctx.guild.id)
        settings = get_guild_settings(ctx.guild.id)

        embed = discord.Embed(
            title="💬 Autoresponders",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Status", value="✅ Enabled" if settings["enabled"] else "❌ Disabled", inline=False)

        if not triggers:
            embed.description = "No autoresponders set up yet."
        else:
            lines = []
            for data in list(triggers.values())[:25]:
                trigger = data["trigger"]
                response = data["response"]
                preview = response if len(response) <= 60 else response[:57] + "..."
                lines.append(f"**{trigger}** → {preview}")
            embed.add_field(name=f"Triggers [{len(triggers)}]", value="\n".join(lines), inline=False)
            if len(triggers) > 25:
                embed.set_footer(text=f"Showing 25 of {len(triggers)} triggers.")

        await ctx.reply(embed=embed)

    @autoresponder.command(name="add")
    @has_mod_role()
    async def autoresponder_add(self, ctx: commands.Context, *, args: str):
        """Add an autoresponder: ,ar add <trigger> | <response>
        Placeholders you can use in the response: {user} {username} {server} {channel}"""
        if "|" not in args:
            embed = discord.Embed(
                description="❌ Use the format: `,ar add <trigger> | <response>`\nExample: `,ar add hello | Hey there {user}!`",
                color=discord.Color.red(),
            )
            return await ctx.reply(embed=embed)

        trigger, response = args.split("|", 1)
        trigger = trigger.strip()
        response = response.strip()

        if not trigger or not response:
            embed = discord.Embed(description="❌ Both a trigger and a response are required.", color=discord.Color.red())
            return await ctx.reply(embed=embed)

        if len(trigger) > MAX_TRIGGER_LENGTH:
            embed = discord.Embed(description=f"❌ Trigger must be under {MAX_TRIGGER_LENGTH} characters.", color=discord.Color.red())
            return await ctx.reply(embed=embed)

        if len(response) > MAX_RESPONSE_LENGTH:
            embed = discord.Embed(description=f"❌ Response must be under {MAX_RESPONSE_LENGTH} characters.", color=discord.Color.red())
            return await ctx.reply(embed=embed)

        triggers = get_guild_responders(ctx.guild.id)

        if len(triggers) >= MAX_RESPONDERS_PER_GUILD and trigger.lower() not in triggers:
            embed = discord.Embed(
                description=f"❌ Limit of {MAX_RESPONDERS_PER_GUILD} autoresponders reached. Remove one first.",
                color=discord.Color.red(),
            )
            return await ctx.reply(embed=embed)

        triggers[trigger.lower()] = {"trigger": trigger, "response": response}
        save_guild_responders(ctx.guild.id, triggers)

        embed = discord.Embed(
            description=f"✅ Autoresponder added.\n**Trigger:** {trigger}\n**Response:** {response}",
            color=discord.Color.green(),
        )
        await ctx.reply(embed=embed)

    @autoresponder.command(name="remove", aliases=["delete"])
    @has_mod_role()
    async def autoresponder_remove(self, ctx: commands.Context, *, trigger: str):
        """Remove an autoresponder: ,ar remove <trigger>"""
        triggers = get_guild_responders(ctx.guild.id)
        trigger_lower = trigger.strip().lower()

        if trigger_lower not in triggers:
            embed = discord.Embed(description=f"❌ No autoresponder found for `{trigger}`.", color=discord.Color.red())
            return await ctx.reply(embed=embed)

        del triggers[trigger_lower]
        save_guild_responders(ctx.guild.id, triggers)

        embed = discord.Embed(description=f"🗑️ Removed autoresponder for `{trigger}`.", color=discord.Color.green())
        await ctx.reply(embed=embed)

    @autoresponder.command(name="clear")
    @has_mod_role()
    async def autoresponder_clear(self, ctx: commands.Context):
        """Remove ALL autoresponders for this server."""
        save_guild_responders(ctx.guild.id, {})
        embed = discord.Embed(description="🗑️ All autoresponders have been cleared.", color=discord.Color.green())
        await ctx.reply(embed=embed)

    @autoresponder.command(name="toggle")
    @has_mod_role()
    async def autoresponder_toggle(self, ctx: commands.Context, state: str):
        """Enable or disable all autoresponders: ,ar toggle on/off"""
        value = state.lower() in ("on", "true", "yes", "enable", "enabled")
        set_enabled(ctx.guild.id, value)
        embed = discord.Embed(
            description=f"✅ Autoresponders {'enabled' if value else 'disabled'}.",
            color=discord.Color.green(),
        )
        await ctx.reply(embed=embed)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CheckFailure):
            embed = discord.Embed(description="❌ You need the mod role to use this command.", color=discord.Color.red())
            await ctx.reply(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(description=f"❌ Missing an argument: `{error.param.name}`", color=discord.Color.red())
            await ctx.reply(embed=embed)
        else:
            raise error


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoResponder(bot))
