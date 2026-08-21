import os
import asyncio
import logging

import discord
from discord.ext import commands
from dotenv import load_dotenv

from utils.webserver import start_webserver

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
    "cogs.devtools",
    "cogs.information",
    "cogs.config",
    "cogs.moderation",
    "cogs.automod",
    "cogs.lockdown",
    "cogs.nuke",
    "cogs.autoresponder",
    "cogs.reactionroles",
    "cogs.embedbuilder",
    "cogs.snipe",
    "cogs.logs",
    "cogs.fun",
    "cogs.economy",
    "cogs.presence",
    "cogs.help",
]


@bot.event
async def on_ready():
    log.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    log.info(f"Prefix: {PREFIX}")
    log.info("------")
    try:
        synced = await bot.tree.sync()
        log.info(f"Synced {len(synced)} slash command(s) globally.")
        log.info("Note: global slash commands can take up to ~1 hour to appear everywhere the first time.")
        log.info("Use ,sync in a server (bot owner only) to make them appear instantly in that server for testing.")
    except discord.HTTPException as e:
        log.error(f"Failed to sync slash commands: {e}")


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

    # Wispbyte's subdomain feature needs something listening on the port shown
    # in its panel. Check "SERVER PORT" there and confirm it matches WEB_PORT below
    # (or set a WEB_PORT variable in Wispbyte's Environment tab to override it).
    web_port = int(os.getenv("WEB_PORT", "14441"))

    async with bot:
        await load_cogs()
        try:
            await start_webserver(bot, host="0.0.0.0", port=web_port)
            log.info(f"Web status page listening on 0.0.0.0:{web_port}")
        except OSError as e:
            log.error(f"Could not start the web server on port {web_port}: {e}")
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
