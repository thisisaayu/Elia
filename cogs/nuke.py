import discord
from discord.ext import commands

from utils import colors
from utils.checks import has_mod_role


class NukeConfirmView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=30)
        self.author_id = author_id
        self.confirmed = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This confirmation isn't yours.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirm Nuke", style=discord.ButtonStyle.red)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.gray)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = False
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    async def on_timeout(self):
        self.confirmed = False


class Nuke(commands.Cog):
    """Clone-and-replace a channel to reset its message history."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="nuke")
    @has_mod_role()
    @commands.guild_only()
    @commands.bot_has_permissions(manage_channels=True)
    async def nuke(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Clone a channel and delete the original — effectively wipes its message history."""
        channel = channel or ctx.channel

        if not isinstance(channel, discord.TextChannel):
            embed = discord.Embed(description="❌ I can only nuke text channels right now.", color=discord.Color.red())
            return await ctx.reply(embed=embed)

        confirm_embed = discord.Embed(
            title="⚠️ Confirm Channel Nuke",
            description=(
                f"This will **delete {channel.mention} and recreate it** with the same name, "
                f"permissions, position, and settings.\n\n"
                f"All message history in this channel will be **permanently lost**. This can't be undone."
            ),
            color=discord.Color.orange(),
        )
        view = NukeConfirmView(ctx.author.id)
        confirm_message = await ctx.reply(embed=confirm_embed, view=view)

        await view.wait()

        if not view.confirmed:
            cancel_embed = discord.Embed(description="❌ Nuke cancelled.", color=colors.EMBED_COLOR)
            try:
                await confirm_message.edit(embed=cancel_embed, view=view)
            except discord.HTTPException:
                pass
            return

        try:
            await confirm_message.edit(
                embed=discord.Embed(description="💣 Nuking...", color=discord.Color.orange()),
                view=view,
            )
        except discord.HTTPException:
            pass

        # Capture everything needed to recreate the channel
        name = channel.name
        topic = channel.topic
        position = channel.position
        nsfw = channel.nsfw
        slowmode_delay = channel.slowmode_delay
        overwrites = channel.overwrites
        category = channel.category
        reason = f"Channel nuked by {ctx.author} ({ctx.author.id})"

        try:
            if category:
                new_channel = await category.create_text_channel(
                    name=name,
                    topic=topic,
                    nsfw=nsfw,
                    slowmode_delay=slowmode_delay,
                    overwrites=overwrites,
                    reason=reason,
                )
            else:
                new_channel = await ctx.guild.create_text_channel(
                    name=name,
                    topic=topic,
                    nsfw=nsfw,
                    slowmode_delay=slowmode_delay,
                    overwrites=overwrites,
                    reason=reason,
                )
        except discord.Forbidden:
            error_embed = discord.Embed(
                description="❌ I don't have permission to create channels here.",
                color=discord.Color.red(),
            )
            try:
                await confirm_message.edit(embed=error_embed, view=None)
            except discord.HTTPException:
                pass
            return
        except discord.HTTPException as e:
            error_embed = discord.Embed(description=f"❌ Failed to create the new channel: {e}", color=discord.Color.red())
            try:
                await confirm_message.edit(embed=error_embed, view=None)
            except discord.HTTPException:
                pass
            return

        try:
            await channel.delete(reason=reason)
        except (discord.Forbidden, discord.HTTPException):
            pass

        try:
            await new_channel.edit(position=position)
        except discord.HTTPException:
            pass

        done_embed = discord.Embed(
            description=f"💥 This channel has been nuked by {ctx.author.mention}.",
            color=discord.Color.orange(),
        )
        await new_channel.send(embed=done_embed)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CheckFailure):
            embed = discord.Embed(description="❌ You need the mod role to use this command.", color=discord.Color.red())
            await ctx.reply(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(description="❌ Couldn't find that channel.", color=discord.Color.red())
            await ctx.reply(embed=embed)
        else:
            raise error


async def setup(bot: commands.Bot):
    await bot.add_cog(Nuke(bot))
