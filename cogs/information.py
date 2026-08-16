import platform
import time

import discord
from discord.ext import commands


class Information(commands.Cog):
    """Info commands: server, user, bot, avatar."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = time.time()

    @commands.command(name="serverinfo", aliases=["si"])
    @commands.guild_only()
    async def serverinfo(self, ctx: commands.Context):
        """Show information about the current server."""
        guild = ctx.guild

        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        total_members = guild.member_count
        humans = sum(1 for m in guild.members if not m.bot)
        bots = sum(1 for m in guild.members if m.bot)

        embed = discord.Embed(
            title=guild.name,
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="Owner", value=str(guild.owner) if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Server ID", value=str(guild.id), inline=True)
        embed.add_field(name="Created", value=discord.utils.format_dt(guild.created_at, style="R"), inline=True)

        embed.add_field(name="Members", value=f"{total_members} total\n{humans} humans, {bots} bots", inline=True)
        embed.add_field(name="Channels", value=f"{text_channels} text\n{voice_channels} voice", inline=True)
        embed.add_field(name="Roles", value=str(len(guild.roles)), inline=True)

        embed.add_field(name="Boost Level", value=f"Level {guild.premium_tier}", inline=True)
        embed.add_field(name="Boosts", value=str(guild.premium_subscription_count or 0), inline=True)
        embed.add_field(name="Verification", value=str(guild.verification_level).title(), inline=True)

        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.reply(embed=embed)

    @commands.command(name="userinfo", aliases=["ui", "whois"])
    @commands.guild_only()
    async def userinfo(self, ctx: commands.Context, member: discord.Member = None):
        """Show information about a user (defaults to yourself)."""
        member = member or ctx.author

        roles = [role.mention for role in reversed(member.roles) if role.name != "@everyone"]
        roles_str = " ".join(roles) if roles else "None"
        if len(roles_str) > 1024:
            roles_str = f"{len(roles)} roles (too many to display)"

        embed = discord.Embed(
            title=str(member),
            color=member.color if member.color.value != 0 else discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(name="User ID", value=str(member.id), inline=True)
        embed.add_field(name="Nickname", value=member.nick or "None", inline=True)
        embed.add_field(name="Bot?", value="Yes" if member.bot else "No", inline=True)

        embed.add_field(
            name="Account Created",
            value=discord.utils.format_dt(member.created_at, style="R"),
            inline=True,
        )
        if member.joined_at:
            embed.add_field(
                name="Joined Server",
                value=discord.utils.format_dt(member.joined_at, style="R"),
                inline=True,
            )
        embed.add_field(name="Top Role", value=member.top_role.mention, inline=True)

        embed.add_field(name=f"Roles [{len(roles)}]", value=roles_str, inline=False)

        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.reply(embed=embed)

    @commands.command(name="avatar", aliases=["av", "pfp"])
    async def avatar(self, ctx: commands.Context, member: discord.Member = None):
        """Show a user's avatar (defaults to yourself)."""
        member = member or ctx.author

        embed = discord.Embed(
            title=f"{member}'s Avatar",
            color=discord.Color.blurple(),
        )
        embed.set_image(url=member.display_avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.reply(embed=embed)

    @commands.command(name="botinfo", aliases=["bi", "stats"])
    async def botinfo(self, ctx: commands.Context):
        """Show information about the bot itself."""
        uptime_seconds = int(time.time() - self.start_time)
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"

        total_members = sum(g.member_count for g in self.bot.guilds)

        embed = discord.Embed(
            title=f"{self.bot.user.name} — Bot Info",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Users", value=str(total_members), inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)

        embed.add_field(name="Uptime", value=uptime_str, inline=True)
        embed.add_field(name="discord.py", value=discord.__version__, inline=True)
        embed.add_field(name="Python", value=platform.python_version(), inline=True)

        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.reply(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Information(bot))
