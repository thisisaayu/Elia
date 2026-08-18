import discord
from discord.ext import commands, tasks

# Change this to your own Twitch/YouTube URL if you want — Discord only renders the
# "Streaming" badge correctly for twitch.tv or youtube.com links.
STREAM_URL = "https://twitch.tv/discord"

ROTATE_SECONDS = 15


class Presence(commands.Cog):
    """Rotates the bot's status/activity on a timer."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.index = 0
        self.rotate_presence.start()

    def cog_unload(self):
        self.rotate_presence.cancel()

    def build_statuses(self):
        prefix = self.bot.command_prefix
        return [
            discord.Streaming(name=f"{prefix}help", url=STREAM_URL),
            discord.Activity(type=discord.ActivityType.competing, name=f"{prefix}ping"),
            discord.Activity(type=discord.ActivityType.watching, name=f"{prefix}Revenge of the Sith"),
            discord.Game(name=f"{prefix}help"),
            discord.Activity(type=discord.ActivityType.listening, name="duel of the fates"),
        ]

    @tasks.loop(seconds=ROTATE_SECONDS)
    async def rotate_presence(self):
        statuses = self.build_statuses()
        activity = statuses[self.index % len(statuses)]
        self.index += 1
        await self.bot.change_presence(status=discord.Status.dnd, activity=activity)

    @rotate_presence.before_loop
    async def before_rotate(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(Presence(bot))
