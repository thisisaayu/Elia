import random
import time

import discord
from discord.ext import commands

from utils import storage
from utils import colors

ECONOMY_FILE = "economy.json"

CURRENCY_NAME = "Aurel"
CURRENCY_PLURAL = "Aurels"
CURRENCY_SYMBOL = "₳"
CURRENCY_CODE = "AUR"

STARTING_BALANCE = 500

DAILY_MIN, DAILY_MAX = 200, 400
DAILY_COOLDOWN = 24 * 3600

WORK_MIN, WORK_MAX = 50, 150
WORK_COOLDOWN = 60 * 60

WORK_JOBS = [
    "delivered packages across town",
    "helped debug a server for a client",
    "busked in the town square",
    "walked a dozen dogs",
    "flipped items at the market",
    "worked a shift at the cafe",
    "did some freelance writing",
    "fixed a leaky faucet",
]

SLOT_EMOJIS = ["🍒", "🍋", "🍉", "⭐", "💎", "7️⃣"]
SLOT_WEIGHTS = [30, 25, 20, 15, 7, 3]  # rarer symbols weighted lower
SLOT_PAYOUTS = {  # multiplier applied to bet, keyed by matched emoji
    "🍒": 2, "🍋": 2, "🍉": 3, "⭐": 4, "💎": 8, "7️⃣": 15,
}


def cur(amount: int) -> str:
    return CURRENCY_NAME if amount == 1 else CURRENCY_PLURAL


def fmt(amount: int) -> str:
    return f"{CURRENCY_SYMBOL}{amount:,} {cur(amount)}"


def get_user_data(guild_id: int, user_id: int) -> dict:
    all_data = storage.load(ECONOMY_FILE, {})
    guild_data = all_data.get(str(guild_id), {})
    user_data = guild_data.get(str(user_id))
    if user_data is None:
        user_data = {"balance": STARTING_BALANCE, "last_daily": 0, "last_work": 0}
    return user_data


def save_user_data(guild_id: int, user_id: int, user_data: dict):
    all_data = storage.load(ECONOMY_FILE, {})
    guild_key, user_key = str(guild_id), str(user_id)
    all_data.setdefault(guild_key, {})
    all_data[guild_key][user_key] = user_data
    storage.save(ECONOMY_FILE, all_data)


def get_balance(guild_id: int, user_id: int) -> int:
    return get_user_data(guild_id, user_id)["balance"]


def add_balance(guild_id: int, user_id: int, amount: int):
    data = get_user_data(guild_id, user_id)
    data["balance"] += amount
    save_user_data(guild_id, user_id, data)
    return data["balance"]


def format_cooldown(seconds_left: int) -> str:
    hours, remainder = divmod(int(seconds_left), 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds and not hours:
        parts.append(f"{seconds}s")
    return " ".join(parts) if parts else "a few seconds"


class Economy(commands.Cog):
    """Economy system: balance, daily/work income, pay, leaderboard, gambling."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------------- BALANCE ----------------
    @commands.command(name="balance", aliases=["bal", "aurels"])
    @commands.guild_only()
    async def balance(self, ctx: commands.Context, member: discord.Member = None):
        """Check your (or someone else's) balance."""
        member = member or ctx.author
        bal = get_balance(ctx.guild.id, member.id)

        embed = discord.Embed(
            title=f"{CURRENCY_SYMBOL} {member.display_name}'s Wallet",
            description=f"**{fmt(bal)}**",
            color=colors.EMBED_COLOR,
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=CURRENCY_CODE)
        await ctx.reply(embed=embed)

    # ---------------- DAILY ----------------
    @commands.command(name="daily")
    @commands.guild_only()
    async def daily(self, ctx: commands.Context):
        """Claim your daily reward."""
        data = get_user_data(ctx.guild.id, ctx.author.id)
        now = time.time()
        elapsed = now - data["last_daily"]

        if elapsed < DAILY_COOLDOWN:
            remaining = DAILY_COOLDOWN - elapsed
            embed = discord.Embed(
                description=f"⏳ You've already claimed your daily. Come back in **{format_cooldown(remaining)}**.",
                color=discord.Color.orange(),
            )
            return await ctx.reply(embed=embed)

        reward = random.randint(DAILY_MIN, DAILY_MAX)
        data["balance"] += reward
        data["last_daily"] = now
        save_user_data(ctx.guild.id, ctx.author.id, data)

        embed = discord.Embed(
            description=f"🎁 You claimed your daily reward of **{fmt(reward)}**!\nNew balance: **{fmt(data['balance'])}**",
            color=discord.Color.green(),
        )
        await ctx.reply(embed=embed)

    # ---------------- WORK ----------------
    @commands.command(name="work")
    @commands.guild_only()
    async def work(self, ctx: commands.Context):
        """Work for some quick Aurels."""
        data = get_user_data(ctx.guild.id, ctx.author.id)
        now = time.time()
        elapsed = now - data["last_work"]

        if elapsed < WORK_COOLDOWN:
            remaining = WORK_COOLDOWN - elapsed
            embed = discord.Embed(
                description=f"⏳ You're tired from your last shift. Rest for **{format_cooldown(remaining)}**.",
                color=discord.Color.orange(),
            )
            return await ctx.reply(embed=embed)

        reward = random.randint(WORK_MIN, WORK_MAX)
        job = random.choice(WORK_JOBS)
        data["balance"] += reward
        data["last_work"] = now
        save_user_data(ctx.guild.id, ctx.author.id, data)

        embed = discord.Embed(
            description=f"💼 You {job} and earned **{fmt(reward)}**!\nNew balance: **{fmt(data['balance'])}**",
            color=discord.Color.green(),
        )
        await ctx.reply(embed=embed)

    # ---------------- PAY ----------------
    @commands.command(name="pay", aliases=["give"])
    @commands.guild_only()
    async def pay(self, ctx: commands.Context, member: discord.Member, amount: int):
        """Pay another member some Aurels."""
        if member.bot:
            embed = discord.Embed(description="❌ You can't pay a bot.", color=discord.Color.red())
            return await ctx.reply(embed=embed)
        if member.id == ctx.author.id:
            embed = discord.Embed(description="❌ You can't pay yourself.", color=discord.Color.red())
            return await ctx.reply(embed=embed)
        if amount <= 0:
            embed = discord.Embed(description="❌ Amount must be positive.", color=discord.Color.red())
            return await ctx.reply(embed=embed)

        sender_data = get_user_data(ctx.guild.id, ctx.author.id)
        if sender_data["balance"] < amount:
            embed = discord.Embed(
                description=f"❌ You don't have enough. Your balance: **{fmt(sender_data['balance'])}**",
                color=discord.Color.red(),
            )
            return await ctx.reply(embed=embed)

        sender_data["balance"] -= amount
        save_user_data(ctx.guild.id, ctx.author.id, sender_data)
        add_balance(ctx.guild.id, member.id, amount)

        embed = discord.Embed(
            description=f"✅ **{ctx.author.display_name}** paid **{member.display_name}** {fmt(amount)}.",
            color=discord.Color.green(),
        )
        await ctx.reply(embed=embed)

    # ---------------- LEADERBOARD ----------------
    @commands.command(name="leaderboard", aliases=["lb"])
    @commands.guild_only()
    async def leaderboard(self, ctx: commands.Context):
        """Show the top 10 richest members in this server."""
        all_data = storage.load(ECONOMY_FILE, {})
        guild_data = all_data.get(str(ctx.guild.id), {})

        entries = []
        for user_id_str, data in guild_data.items():
            member = ctx.guild.get_member(int(user_id_str))
            if member:
                entries.append((member, data.get("balance", 0)))

        entries.sort(key=lambda x: x[1], reverse=True)
        top = entries[:10]

        embed = discord.Embed(
            title=f"{CURRENCY_SYMBOL} Leaderboard — {ctx.guild.name}",
            color=colors.EMBED_COLOR,
        )
        if not top:
            embed.description = "No one has any Aurels yet."
        else:
            medals = ["🥇", "🥈", "🥉"]
            lines = []
            for i, (member, bal) in enumerate(top):
                rank = medals[i] if i < 3 else f"#{i + 1}"
                lines.append(f"{rank} **{member.display_name}** — {fmt(bal)}")
            embed.description = "\n".join(lines)

        await ctx.reply(embed=embed)

    # ---------------- GAMBLING: COINFLIP ----------------
    @commands.command(name="cf", aliases=["coinflipbet"])
    @commands.guild_only()
    async def coinflip_bet(self, ctx: commands.Context, amount: int, side: str = None):
        """Bet on a coinflip: ,cf <amount> <heads/tails>"""
        if side is None or side.lower() not in ("heads", "tails"):
            embed = discord.Embed(description="❌ Choose a side: `,cf <amount> heads` or `,cf <amount> tails`", color=discord.Color.red())
            return await ctx.reply(embed=embed)
        if amount <= 0:
            embed = discord.Embed(description="❌ Bet must be positive.", color=discord.Color.red())
            return await ctx.reply(embed=embed)

        data = get_user_data(ctx.guild.id, ctx.author.id)
        if data["balance"] < amount:
            embed = discord.Embed(description=f"❌ You don't have enough. Your balance: **{fmt(data['balance'])}**", color=discord.Color.red())
            return await ctx.reply(embed=embed)

        side = side.lower()
        result = random.choice(["heads", "tails"])
        won = result == side

        if won:
            data["balance"] += amount
            color = discord.Color.green()
            outcome = f"🪙 It landed on **{result}**! You won **{fmt(amount)}**!"
        else:
            data["balance"] -= amount
            color = discord.Color.red()
            outcome = f"🪙 It landed on **{result}**. You lost **{fmt(amount)}**."

        save_user_data(ctx.guild.id, ctx.author.id, data)

        embed = discord.Embed(description=f"{outcome}\nNew balance: **{fmt(data['balance'])}**", color=color)
        await ctx.reply(embed=embed)

    # ---------------- GAMBLING: SLOTS ----------------
    @commands.command(name="slots")
    @commands.guild_only()
    async def slots(self, ctx: commands.Context, amount: int):
        """Play the slot machine: ,slots <amount>"""
        if amount <= 0:
            embed = discord.Embed(description="❌ Bet must be positive.", color=discord.Color.red())
            return await ctx.reply(embed=embed)

        data = get_user_data(ctx.guild.id, ctx.author.id)
        if data["balance"] < amount:
            embed = discord.Embed(description=f"❌ You don't have enough. Your balance: **{fmt(data['balance'])}**", color=discord.Color.red())
            return await ctx.reply(embed=embed)

        reels = random.choices(SLOT_EMOJIS, weights=SLOT_WEIGHTS, k=3)
        reel_display = " | ".join(reels)

        if reels[0] == reels[1] == reels[2]:
            multiplier = SLOT_PAYOUTS[reels[0]]
            winnings = amount * multiplier
            data["balance"] += winnings
            color = discord.Color.green()
            outcome = f"🎰 **JACKPOT!** All three match! You won **{fmt(winnings)}** ({multiplier}x)!"
        elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
            winnings = amount  # break-even on a partial match
            color = discord.Color.orange()
            outcome = f"🎰 Two match! You broke even, **{fmt(winnings)}** returned."
        else:
            data["balance"] -= amount
            color = discord.Color.red()
            outcome = f"🎰 No match. You lost **{fmt(amount)}**."

        save_user_data(ctx.guild.id, ctx.author.id, data)

        embed = discord.Embed(
            title=reel_display,
            description=f"{outcome}\nNew balance: **{fmt(data['balance'])}**",
            color=color,
        )
        await ctx.reply(embed=embed)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(description=f"❌ Missing an argument: `{error.param.name}`", color=discord.Color.red())
            await ctx.reply(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(description="❌ Couldn't parse that argument. Check your command usage.", color=discord.Color.red())
            await ctx.reply(embed=embed)
        else:
            raise error


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
