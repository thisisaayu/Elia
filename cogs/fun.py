import hashlib
import random

import aiohttp
import discord
from discord.ext import commands

# nekos.best is a free, no-key-required API for anime reaction gifs.
# Each entry: command name -> (API action, caption template using {a} = author, {t} = target)
GIF_ACTIONS = {
    "hug":      ("hug",      "🤗 **{a}** hugs **{t}**!"),
    "pat":      ("pat",      "🖐️ **{a}** pats **{t}**!"),
    "slap":     ("slap",     "👋 **{a}** slaps **{t}**! That looks like it hurt..."),
    "kiss":     ("kiss",     "😘 **{a}** kisses **{t}**!"),
    "cuddle":   ("cuddle",   "🥰 **{a}** cuddles up with **{t}**!"),
    "poke":     ("poke",     "👉 **{a}** pokes **{t}**!"),
    "tickle":   ("tickle",   "🤭 **{a}** tickles **{t}**!"),
    "punch":    ("punch",    "👊 **{a}** punches **{t}**!"),
    "bite":     ("bite",     "😬 **{a}** bites **{t}**!"),
    "highfive": ("highfive", "🙌 **{a}** high-fives **{t}**!"),
    "wave":     ("wave",     "👋 **{a}** waves at **{t}**!"),
    "feed":     ("feed",     "🍽️ **{a}** feeds **{t}**!"),
}

# Actions used for the ,fuck joke command — subverts expectations with a comedic beatdown instead
BEATDOWN_ACTIONS = ["punch", "slap", "kick", "bite"]
BEATDOWN_CAPTIONS = [
    "💥 **{a}** absolutely wrecks **{t}**! Bet you thought this was gonna be something else...",
    "💀 **{a}** just ended **{t}**'s whole career. Nothing sexual about it.",
    "🥊 **{a}** unleashes pure violence on **{t}**! Get your mind out of the gutter.",
    "⚡ **{a}** delivers a devastating combo to **{t}**! That's the only kind of action you're getting here.",
]

EIGHTBALL_RESPONSES = [
    "It is certain.", "Without a doubt.", "Yes, definitely.", "You may rely on it.",
    "As I see it, yes.", "Most likely.", "Outlook good.", "Yes.",
    "Signs point to yes.", "Reply hazy, try again.", "Ask again later.",
    "Better not tell you now.", "Cannot predict now.", "Concentrate and ask again.",
    "Don't count on it.", "My reply is no.", "My sources say no.",
    "Outlook not so good.", "Very doubtful.",
]

JOKES = [
    "Why don't scientists trust atoms? Because they make up everything.",
    "I told my computer I needed a break, and it said no problem — it froze immediately.",
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "How do you comfort a JavaScript bug? You console it.",
    "Why did the developer go broke? Because they used up all their cache.",
    "I would tell you a UDP joke, but you might not get it.",
    "There are 10 types of people: those who understand binary and those who don't.",
    "Why did the scarecrow win an award? He was outstanding in his field.",
    "What do you call a fish with no eyes? A fsh.",
    "I'm reading a book on anti-gravity. It's impossible to put down.",
]

FACTS = [
    "Honey never spoils — archaeologists have found 3000-year-old honey that's still edible.",
    "Bananas are berries, but strawberries aren't.",
    "Octopuses have three hearts and blue blood.",
    "A day on Venus is longer than a year on Venus.",
    "Wombat poop is cube-shaped.",
    "The Eiffel Tower can grow taller in summer due to heat expansion.",
    "Sea otters hold hands while sleeping so they don't drift apart.",
    "Sharks existed before trees.",
    "There are more possible chess games than atoms in the observable universe.",
    "A group of flamingos is called a 'flamboyance'.",
]

WYR_QUESTIONS = [
    "Would you rather have the ability to fly or be invisible?",
    "Would you rather always be 10 minutes late or 20 minutes early?",
    "Would you rather fight one horse-sized duck or 100 duck-sized horses?",
    "Would you rather never use social media again or never watch another movie/show?",
    "Would you rather have unlimited books or unlimited games, but never get any new ones again?",
    "Would you rather be able to talk to animals or speak every human language?",
    "Would you rather lose all your money or all your photos?",
]

RPS_EMOJI = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
RPS_BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}


class Fun(commands.Cog):
    """Fun/entertainment commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session: aiohttp.ClientSession | None = None

    async def cog_load(self):
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        if self.session:
            await self.session.close()

    async def _fetch_gif(self, action: str) -> str | None:
        """Fetch a random gif URL for the given nekos.best action. Returns None on failure."""
        try:
            async with self.session.get(f"https://nekos.best/api/v2/{action}") as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                results = data.get("results")
                if not results:
                    return None
                return results[0].get("url")
        except (aiohttp.ClientError, TimeoutError):
            return None

    @commands.command(name="8ball")
    async def eightball(self, ctx: commands.Context, *, question: str = None):
        """Ask the magic 8-ball a question."""
        if not question:
            embed = discord.Embed(description="❌ You need to ask a question. Example: `,8ball will it rain today?`", color=discord.Color.red())
            return await ctx.send(embed=embed)

        answer = random.choice(EIGHTBALL_RESPONSES)
        embed = discord.Embed(title="🎱 Magic 8-Ball", color=discord.Color.blurple())
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=answer, inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="coinflip", aliases=["flip", "coin"])
    async def coinflip(self, ctx: commands.Context):
        """Flip a coin."""
        result = random.choice(["Heads", "Tails"])
        emoji = "🪙"
        embed = discord.Embed(description=f"{emoji} The coin landed on **{result}**!", color=discord.Color.blurple())
        await ctx.send(embed=embed)

    @commands.command(name="roll", aliases=["dice"])
    async def roll(self, ctx: commands.Context, dice: str = "1d6"):
        """Roll dice. Format: NdM (e.g. 2d20 rolls two 20-sided dice)."""
        try:
            num, sides = dice.lower().split("d")
            num, sides = int(num), int(sides)
        except (ValueError, AttributeError):
            embed = discord.Embed(description="❌ Invalid format. Use e.g. `,roll 2d20`.", color=discord.Color.red())
            return await ctx.send(embed=embed)

        if not (1 <= num <= 20) or not (2 <= sides <= 1000):
            embed = discord.Embed(description="❌ Number of dice must be 1-20, sides must be 2-1000.", color=discord.Color.red())
            return await ctx.send(embed=embed)

        rolls = [random.randint(1, sides) for _ in range(num)]
        embed = discord.Embed(title="🎲 Dice Roll", color=discord.Color.blurple())
        embed.add_field(name="Rolls", value=", ".join(str(r) for r in rolls), inline=False)
        embed.add_field(name="Total", value=str(sum(rolls)), inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="rps")
    async def rps(self, ctx: commands.Context, choice: str = None):
        """Play rock-paper-scissors against the bot."""
        if not choice or choice.lower() not in RPS_BEATS:
            embed = discord.Embed(description="❌ Choose one: `rock`, `paper`, or `scissors`. Example: `,rps rock`", color=discord.Color.red())
            return await ctx.send(embed=embed)

        choice = choice.lower()
        bot_choice = random.choice(list(RPS_BEATS.keys()))

        if choice == bot_choice:
            result = "It's a tie!"
            color = discord.Color.orange()
        elif RPS_BEATS[choice] == bot_choice:
            result = "You win! 🎉"
            color = discord.Color.green()
        else:
            result = "I win! 😎"
            color = discord.Color.red()

        embed = discord.Embed(title="🪨📄✂️ Rock Paper Scissors", color=color)
        embed.add_field(name="You", value=f"{RPS_EMOJI[choice]} {choice.title()}", inline=True)
        embed.add_field(name="Me", value=f"{RPS_EMOJI[bot_choice]} {bot_choice.title()}", inline=True)
        embed.add_field(name="Result", value=result, inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="choose", aliases=["pick"])
    async def choose(self, ctx: commands.Context, *, options: str = None):
        """Let the bot choose between options, separated by commas. Example: ,choose pizza, tacos, sushi"""
        if not options or "," not in options:
            embed = discord.Embed(description="❌ Give me at least two options separated by commas. Example: `,choose pizza, tacos`", color=discord.Color.red())
            return await ctx.send(embed=embed)

        choices = [c.strip() for c in options.split(",") if c.strip()]
        if len(choices) < 2:
            embed = discord.Embed(description="❌ Give me at least two options.", color=discord.Color.red())
            return await ctx.send(embed=embed)

        pick = random.choice(choices)
        embed = discord.Embed(description=f"🤔 I choose... **{pick}**", color=discord.Color.blurple())
        await ctx.send(embed=embed)

    @commands.command(name="ship")
    @commands.guild_only()
    async def ship(self, ctx: commands.Context, user1: discord.Member, user2: discord.Member = None):
        """Ship two users together (compatibility is deterministic per pair, for fun)."""
        user2 = user2 or ctx.author
        # Deterministic "random" percentage based on the pair of IDs, so it's the same result every time
        pair_key = "-".join(sorted([str(user1.id), str(user2.id)]))
        digest = hashlib.md5(pair_key.encode()).hexdigest()
        percent = int(digest, 16) % 101

        bar_filled = "❤️" * (percent // 10)
        bar_empty = "🤍" * (10 - percent // 10)

        embed = discord.Embed(title="💘 Ship Calculator", color=discord.Color.pink())
        embed.description = f"{user1.mention} + {user2.mention}"
        embed.add_field(name="Compatibility", value=f"{bar_filled}{bar_empty}\n**{percent}%**", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="joke")
    async def joke(self, ctx: commands.Context):
        """Get a random joke."""
        embed = discord.Embed(description=f"😄 {random.choice(JOKES)}", color=discord.Color.blurple())
        await ctx.send(embed=embed)

    @commands.command(name="fact")
    async def fact(self, ctx: commands.Context):
        """Get a random fun fact."""
        embed = discord.Embed(description=f"🧠 {random.choice(FACTS)}", color=discord.Color.blurple())
        await ctx.send(embed=embed)

    @commands.command(name="wyr", aliases=["wouldyourather"])
    async def wyr(self, ctx: commands.Context):
        """Get a random 'would you rather' question."""
        embed = discord.Embed(title="🤔 Would You Rather", description=random.choice(WYR_QUESTIONS), color=discord.Color.blurple())
        await ctx.send(embed=embed)

    # ---------------- Interaction commands (with anime reaction GIFs) ----------------
    async def _send_interaction(self, ctx: commands.Context, action: str, member: discord.Member = None):
        member = member or ctx.author
        _, template = GIF_ACTIONS[action]
        caption = template.format(a=ctx.author.display_name, t=member.display_name)

        gif_url = await self._fetch_gif(action)

        embed = discord.Embed(description=caption, color=discord.Color.blurple())
        if gif_url:
            embed.set_image(url=gif_url)
        else:
            embed.set_footer(text="(couldn't load a gif right now)")
        await ctx.send(embed=embed)

    @commands.command(name="hug")
    async def hug(self, ctx: commands.Context, member: discord.Member = None):
        """Hug someone."""
        await self._send_interaction(ctx, "hug", member)

    @commands.command(name="pat")
    async def pat(self, ctx: commands.Context, member: discord.Member = None):
        """Pat someone."""
        await self._send_interaction(ctx, "pat", member)

    @commands.command(name="slap")
    async def slap(self, ctx: commands.Context, member: discord.Member = None):
        """Slap someone (playfully)."""
        await self._send_interaction(ctx, "slap", member)

    @commands.command(name="kiss")
    async def kiss(self, ctx: commands.Context, member: discord.Member = None):
        """Kiss someone."""
        await self._send_interaction(ctx, "kiss", member)

    @commands.command(name="cuddle")
    async def cuddle(self, ctx: commands.Context, member: discord.Member = None):
        """Cuddle someone."""
        await self._send_interaction(ctx, "cuddle", member)

    @commands.command(name="poke")
    async def poke(self, ctx: commands.Context, member: discord.Member = None):
        """Poke someone."""
        await self._send_interaction(ctx, "poke", member)

    @commands.command(name="tickle")
    async def tickle(self, ctx: commands.Context, member: discord.Member = None):
        """Tickle someone."""
        await self._send_interaction(ctx, "tickle", member)

    @commands.command(name="punch")
    async def punch(self, ctx: commands.Context, member: discord.Member = None):
        """Punch someone (playfully)."""
        await self._send_interaction(ctx, "punch", member)

    @commands.command(name="bite")
    async def bite(self, ctx: commands.Context, member: discord.Member = None):
        """Bite someone."""
        await self._send_interaction(ctx, "bite", member)

    @commands.command(name="highfive")
    async def highfive(self, ctx: commands.Context, member: discord.Member = None):
        """High-five someone."""
        await self._send_interaction(ctx, "highfive", member)

    @commands.command(name="wave")
    async def wave(self, ctx: commands.Context, member: discord.Member = None):
        """Wave at someone."""
        await self._send_interaction(ctx, "wave", member)

    @commands.command(name="feed")
    async def feed(self, ctx: commands.Context, member: discord.Member = None):
        """Feed someone."""
        await self._send_interaction(ctx, "feed", member)

    @commands.command(name="fuck")
    async def fuck(self, ctx: commands.Context, member: discord.Member = None):
        """Not what you think. 😈"""
        member = member or ctx.author
        action = random.choice(BEATDOWN_ACTIONS)
        caption = random.choice(BEATDOWN_CAPTIONS).format(a=ctx.author.display_name, t=member.display_name)

        gif_url = await self._fetch_gif(action)

        embed = discord.Embed(description=caption, color=discord.Color.dark_red())
        if gif_url:
            embed.set_image(url=gif_url)
        else:
            embed.set_footer(text="(couldn't load a gif right now)")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))
