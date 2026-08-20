from collections import defaultdict, deque
import time

import discord
from discord.ext import commands

from utils import colors

MAX_SNIPES_PER_CHANNEL = 10
SNIPE_EXPIRY_SECONDS = 3600  # 1 hour — after this, a snipe is considered too stale to show


class SnipedMessage:
    def __init__(self, author: discord.abc.User, content: str, attachment_url: str = None):
        self.author = author
        self.content = content
        self.attachment_url = attachment_url
        self.timestamp = time.time()


class SnipedEdit:
    def __init__(self, author: discord.abc.User, before: str, after: str):
        self.author = author
        self.before = before
        self.after = after
        self.timestamp = time.time()


class Snipe(commands.Cog):
    """Recover recently deleted or edited messages."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # channel_id -> deque of SnipedMessage, most recent first
        self.deleted = defaultdict(lambda: deque(maxlen=MAX_SNIPES_PER_CHANNEL))
        # channel_id -> deque of SnipedEdit, most recent first
        self.edited = defaultdict(lambda: deque(maxlen=MAX_SNIPES_PER_CHANNEL))

    # ---------------- LISTENERS ----------------
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        if not message.content and not message.attachments:
            return  # nothing worth showing

        attachment_url = None
        for att in message.attachments:
            if att.content_type and att.content_type.startswith("image/"):
                attachment_url = att.url
                break

        sniped = SnipedMessage(message.author, message.content, attachment_url)
        self.deleted[message.channel.id].appendleft(sniped)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        # Intentionally not recorded — purges shouldn't be recoverable via snipe.
        pass

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or not before.guild:
            return
        if before.content == after.content:
            return  # e.g. an embed loaded, not an actual content edit

        sniped = SnipedEdit(before.author, before.content, after.content)
        self.edited[before.channel.id].appendleft(sniped)

    # ---------------- COMMANDS ----------------
    @commands.hybrid_command(name="snipe", aliases=["s"])
    @commands.guild_only()
    async def snipe(self, ctx: commands.Context, index: int = 1):
        """Show a recently deleted message in this channel. ,snipe 2 shows the 2nd most recent."""
        history = self.deleted.get(ctx.channel.id)
        if not history:
            embed = discord.Embed(description="There's nothing to snipe in this channel.", color=colors.EMBED_COLOR)
            return await ctx.reply(embed=embed)

        if index < 1 or index > len(history):
            embed = discord.Embed(
                description=f"❌ Invalid index. There are **{len(history)}** sniped message(s) available here.",
                color=discord.Color.red(),
            )
            return await ctx.reply(embed=embed)

        sniped = history[index - 1]
        age = time.time() - sniped.timestamp
        if age > SNIPE_EXPIRY_SECONDS:
            embed = discord.Embed(description="That message is too old to snipe anymore.", color=colors.EMBED_COLOR)
            return await ctx.reply(embed=embed)

        embed = discord.Embed(
            description=sniped.content or "*(no text content)*",
            color=colors.EMBED_COLOR,
            timestamp=discord.utils.utcnow(),
        )
        embed.set_author(name=str(sniped.author), icon_url=sniped.author.display_avatar.url)
        if sniped.attachment_url:
            embed.set_image(url=sniped.attachment_url)
        embed.set_footer(text=f"Deleted message {index}/{len(history)} • Requested by {ctx.author}")
        await ctx.reply(embed=embed)

    @commands.hybrid_command(name="editsnipe", aliases=["es"])
    @commands.guild_only()
    async def editsnipe(self, ctx: commands.Context, index: int = 1):
        """Show a recently edited message in this channel. ,editsnipe 2 shows the 2nd most recent."""
        history = self.edited.get(ctx.channel.id)
        if not history:
            embed = discord.Embed(description="There's nothing to editsnipe in this channel.", color=colors.EMBED_COLOR)
            return await ctx.reply(embed=embed)

        if index < 1 or index > len(history):
            embed = discord.Embed(
                description=f"❌ Invalid index. There are **{len(history)}** edited message(s) available here.",
                color=discord.Color.red(),
            )
            return await ctx.reply(embed=embed)

        sniped = history[index - 1]
        age = time.time() - sniped.timestamp
        if age > SNIPE_EXPIRY_SECONDS:
            embed = discord.Embed(description="That edit is too old to snipe anymore.", color=colors.EMBED_COLOR)
            return await ctx.reply(embed=embed)

        embed = discord.Embed(color=colors.EMBED_COLOR, timestamp=discord.utils.utcnow())
        embed.set_author(name=str(sniped.author), icon_url=sniped.author.display_avatar.url)
        embed.add_field(name="Before", value=sniped.before or "*(empty)*", inline=False)
        embed.add_field(name="After", value=sniped.after or "*(empty)*", inline=False)
        embed.set_footer(text=f"Edited message {index}/{len(history)} • Requested by {ctx.author}")
        await ctx.reply(embed=embed)

    @commands.hybrid_command(name="clearsnipe", aliases=["cs"])
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def clearsnipe(self, ctx: commands.Context):
        """Clear the snipe history for this channel."""
        self.deleted[ctx.channel.id].clear()
        self.edited[ctx.channel.id].clear()
        embed = discord.Embed(description="🗑️ Snipe history cleared for this channel.", color=discord.Color.green())
        await ctx.reply(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Snipe(bot))
