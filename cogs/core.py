import time
import discord
from discord.ext import commands


class Core(commands.Cog):
    """Basic bot commands: ping, help."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        """Check the bot's latency."""
        start = time.monotonic()
        message = await ctx.send("Pinging...")
        end = time.monotonic()

        api_latency = round(self.bot.latency * 1000)  # websocket latency
        round_trip = round((end - start) * 1000)      # message round-trip

        embed = discord.Embed(
            title="🏓 Pong!",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Websocket", value=f"{api_latency}ms", inline=True)
        embed.add_field(name="Round-trip", value=f"{round_trip}ms", inline=True)

        await message.edit(content=None, embed=embed)





async def setup(bot: commands.Bot):
    await bot.add_cog(Core(bot))
