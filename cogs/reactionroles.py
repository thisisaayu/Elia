import discord
from discord.ext import commands

from utils import storage, colors

REACTION_ROLES_FILE = "reaction_roles.json"


def get_message_mappings(guild_id: int, message_id: int) -> dict:
    """Returns {emoji_str: role_id} for a given message."""
    all_data = storage.load(REACTION_ROLES_FILE, {})
    guild_data = all_data.get(str(guild_id), {})
    return guild_data.get(str(message_id), {})


def set_mapping(guild_id: int, message_id: int, emoji_str: str, role_id: int):
    all_data = storage.load(REACTION_ROLES_FILE, {})
    guild_key, msg_key = str(guild_id), str(message_id)
    all_data.setdefault(guild_key, {}).setdefault(msg_key, {})
    all_data[guild_key][msg_key][emoji_str] = role_id
    storage.save(REACTION_ROLES_FILE, all_data)


def remove_mapping(guild_id: int, message_id: int, emoji_str: str) -> bool:
    all_data = storage.load(REACTION_ROLES_FILE, {})
    guild_key, msg_key = str(guild_id), str(message_id)
    if guild_key in all_data and msg_key in all_data[guild_key] and emoji_str in all_data[guild_key][msg_key]:
        del all_data[guild_key][msg_key][emoji_str]
        if not all_data[guild_key][msg_key]:
            del all_data[guild_key][msg_key]
        storage.save(REACTION_ROLES_FILE, all_data)
        return True
    return False


def get_all_guild_mappings(guild_id: int) -> dict:
    """Returns {message_id: {emoji_str: role_id}} for the whole guild."""
    all_data = storage.load(REACTION_ROLES_FILE, {})
    return all_data.get(str(guild_id), {})


class ReactionRoles(commands.Cog):
    """React to a message to get a role; remove the reaction to lose it."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------------- LISTENERS ----------------
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.guild_id is None:
            return
        if payload.member and payload.member.bot:
            return

        mappings = get_message_mappings(payload.guild_id, payload.message_id)
        if not mappings:
            return

        emoji_str = str(payload.emoji)
        role_id = mappings.get(emoji_str)
        if not role_id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        role = guild.get_role(role_id)
        member = payload.member or guild.get_member(payload.user_id)
        if not role or not member:
            return

        try:
            await member.add_roles(role, reason="Reaction role")
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.guild_id is None:
            return

        mappings = get_message_mappings(payload.guild_id, payload.message_id)
        if not mappings:
            return

        emoji_str = str(payload.emoji)
        role_id = mappings.get(emoji_str)
        if not role_id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        role = guild.get_role(role_id)
        try:
            member = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
        except discord.NotFound:
            return
        if not role or not member or member.bot:
            return

        try:
            await member.remove_roles(role, reason="Reaction role removed")
        except discord.Forbidden:
            pass

    # ---------------- CONFIG COMMANDS ----------------
    @commands.hybrid_group(name="reactionrole", aliases=["rr"], invoke_without_command=True)
    @commands.guild_only()
    async def reactionrole(self, ctx: commands.Context):
        """List all reaction role setups in this server."""
        all_mappings = get_all_guild_mappings(ctx.guild.id)
        if not all_mappings:
            embed = discord.Embed(description="No reaction roles set up yet.", color=colors.EMBED_COLOR)
            return await ctx.reply(embed=embed)

        embed = discord.Embed(title="🎭 Reaction Roles", color=colors.EMBED_COLOR)
        for message_id, emoji_map in all_mappings.items():
            lines = []
            for emoji_str, role_id in emoji_map.items():
                role = ctx.guild.get_role(role_id)
                role_text = role.mention if role else f"deleted role ({role_id})"
                lines.append(f"{emoji_str} → {role_text}")
            embed.add_field(name=f"Message ID: {message_id}", value="\n".join(lines), inline=False)

        await ctx.reply(embed=embed)

    @reactionrole.command(name="add")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_roles=True, add_reactions=True)
    async def reactionrole_add(self, ctx: commands.Context, message_id: int, emoji: str, role: discord.Role):
        """Add a reaction role: ,rr add <message_id> <emoji> <@role>
        The command must be run in the same channel as the target message."""
        if role >= ctx.guild.me.top_role:
            embed = discord.Embed(
                description="❌ I can't assign that role — it's higher than or equal to my own top role. Move my role above it in Server Settings.",
                color=discord.Color.red(),
            )
            return await ctx.reply(embed=embed)

        try:
            message = await ctx.channel.fetch_message(message_id)
        except discord.NotFound:
            embed = discord.Embed(
                description="❌ Couldn't find that message in this channel. Run this command in the same channel as the message.",
                color=discord.Color.red(),
            )
            return await ctx.reply(embed=embed)

        try:
            partial_emoji = discord.PartialEmoji.from_str(emoji)
            await message.add_reaction(partial_emoji)
        except (discord.HTTPException, discord.NotFound):
            embed = discord.Embed(description="❌ I couldn't react with that emoji. Make sure it's a valid emoji I have access to.", color=discord.Color.red())
            return await ctx.reply(embed=embed)

        set_mapping(ctx.guild.id, message_id, str(partial_emoji), role.id)

        embed = discord.Embed(
            description=f"✅ Reacting with {emoji} on that message now gives {role.mention}.",
            color=discord.Color.green(),
        )
        await ctx.reply(embed=embed)

    @reactionrole.command(name="remove")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def reactionrole_remove(self, ctx: commands.Context, message_id: int, emoji: str):
        """Remove a reaction role: ,rr remove <message_id> <emoji>"""
        partial_emoji = discord.PartialEmoji.from_str(emoji)
        removed = remove_mapping(ctx.guild.id, message_id, str(partial_emoji))

        if removed:
            embed = discord.Embed(description=f"🗑️ Removed the reaction role for {emoji} on that message.", color=discord.Color.green())
        else:
            embed = discord.Embed(description="❌ No reaction role found for that message/emoji combination.", color=discord.Color.red())
        await ctx.reply(embed=embed)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(description=f"❌ Missing an argument: `{error.param.name}`", color=discord.Color.red())
            await ctx.reply(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(description="❌ Couldn't find that message ID or role. Double check them.", color=discord.Color.red())
            await ctx.reply(embed=embed)
        elif isinstance(error, commands.CheckFailure):
            embed = discord.Embed(description="❌ You need Administrator to manage reaction roles.", color=discord.Color.red())
            await ctx.reply(embed=embed)
        else:
            raise error


async def setup(bot: commands.Bot):
    await bot.add_cog(ReactionRoles(bot))
