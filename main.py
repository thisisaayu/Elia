import os
import asyncio
import logging

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load variables from the .env file (DISCORD_TOKEN=...)
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ---- Basic logging so you can see what's happening in the console ----
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("bot")

# ---- Prefix ----
PREFIX = ","

# ---- Intents ----
# These control what data Discord sends your bot. Turn on only what you need.
# message_content and members must ALSO be enabled in the Developer Portal
# under Bot -> Privileged Gateway Intents.
intents = discord.Intents.default()
intents.message_content = True   # needed to read message text (for prefix commands, automod, autoresponders)
intents.members = True           # needed for welcome messages, member info, moderation

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# List of cogs (feature files) to load on startup.
# As we build more features, we just add their name here.
INITIAL_COGS = [
    "cogs.core",
    "cogs.information",
    "cogs.config",
    "cogs.moderation",
]


@bot.event
async def on_ready():
    log.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    log.info(f"Prefix: {PREFIX}")
    log.info("------")
    await bot.change_presence(
        activity=discord.Game(name=f"{PREFIX}help")
    )


async def load_cogs():
    for cog in INITIAL_COGS:
        try:
            await bot.load_extension(cog)
            log.info(f"Loaded cog: {cog}")
        except Exception as e:
            log.error(f"Failed to load cog {cog}: {e}")


async def main():
    if not TOKEN:
        log.error("No DISCORD_TOKEN found. Make sure it's set in your .env / Environment variables.")
        return
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
