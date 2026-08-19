import discord
from discord.ext import commands

from utils import colors


class EmbedState:
    """Holds the in-progress embed's data while the user builds it."""

    def __init__(self, author: discord.Member):
        self.author = author
        self.title = None
        self.description = None
        self.color = colors.EMBED_COLOR
        self.footer_text = None
        self.footer_icon = None
        self.image_url = None
        self.thumbnail_url = None
        self.author_name = None
        self.author_icon = None
        self.fields = []  # list of (name, value, inline)

    def build(self) -> discord.Embed:
        embed = discord.Embed(
            title=self.title,
            description=self.description,
            color=self.color,
        )
        if self.footer_text:
            if self.footer_icon:
                embed.set_footer(text=self.footer_text, icon_url=self.footer_icon)
            else:
                embed.set_footer(text=self.footer_text)
        if self.image_url:
            embed.set_image(url=self.image_url)
        if self.thumbnail_url:
            embed.set_thumbnail(url=self.thumbnail_url)
        if self.author_name:
            if self.author_icon:
                embed.set_author(name=self.author_name, icon_url=self.author_icon)
            else:
                embed.set_author(name=self.author_name)
        for name, value, inline in self.fields:
            embed.add_field(name=name, value=value, inline=inline)
        if not self.title and not self.description and not self.fields:
            embed.description = "*(empty — use the buttons below to add content)*"
        return embed


# ---------------- MODALS ----------------
class TitleDescriptionModal(discord.ui.Modal, title="Title & Description"):
    def __init__(self, state: EmbedState, view: "EmbedBuilderView"):
        super().__init__()
        self.state = state
        self.view = view
        self.title_input = discord.ui.TextInput(
            label="Title", required=False, max_length=256, default=state.title or ""
        )
        self.description_input = discord.ui.TextInput(
            label="Description", style=discord.TextStyle.paragraph, required=False,
            max_length=4000, default=state.description or ""
        )
        self.add_item(self.title_input)
        self.add_item(self.description_input)

    async def on_submit(self, interaction: discord.Interaction):
        self.state.title = self.title_input.value or None
        self.state.description = self.description_input.value or None
        await self.view.refresh(interaction)


class ColorModal(discord.ui.Modal, title="Embed Color"):
    def __init__(self, state: EmbedState, view: "EmbedBuilderView"):
        super().__init__()
        self.state = state
        self.view = view
        self.color_input = discord.ui.TextInput(
            label="Hex color (e.g. #5865F2 or FF0000)", required=True, max_length=7,
        )
        self.add_item(self.color_input)

    async def on_submit(self, interaction: discord.Interaction):
        raw = self.color_input.value.strip().lstrip("#")
        try:
            value = int(raw, 16)
            if not (0 <= value <= 0xFFFFFF):
                raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ Invalid hex color. Example: `#5865F2`", ephemeral=True)
            return
        self.state.color = discord.Color(value)
        await self.view.refresh(interaction)


class FooterModal(discord.ui.Modal, title="Footer"):
    def __init__(self, state: EmbedState, view: "EmbedBuilderView"):
        super().__init__()
        self.state = state
        self.view = view
        self.text_input = discord.ui.TextInput(label="Footer text", required=False, max_length=2048, default=state.footer_text or "")
        self.icon_input = discord.ui.TextInput(label="Footer icon URL (optional)", required=False, default=state.footer_icon or "")
        self.add_item(self.text_input)
        self.add_item(self.icon_input)

    async def on_submit(self, interaction: discord.Interaction):
        self.state.footer_text = self.text_input.value or None
        self.state.footer_icon = self.icon_input.value or None
        await self.view.refresh(interaction)


class ImageModal(discord.ui.Modal, title="Image & Thumbnail"):
    def __init__(self, state: EmbedState, view: "EmbedBuilderView"):
        super().__init__()
        self.state = state
        self.view = view
        self.image_input = discord.ui.TextInput(label="Image URL (large, bottom)", required=False, default=state.image_url or "")
        self.thumb_input = discord.ui.TextInput(label="Thumbnail URL (small, corner)", required=False, default=state.thumbnail_url or "")
        self.add_item(self.image_input)
        self.add_item(self.thumb_input)

    async def on_submit(self, interaction: discord.Interaction):
        self.state.image_url = self.image_input.value or None
        self.state.thumbnail_url = self.thumb_input.value or None
        await self.view.refresh(interaction)


class AuthorModal(discord.ui.Modal, title="Author"):
    def __init__(self, state: EmbedState, view: "EmbedBuilderView"):
        super().__init__()
        self.state = state
        self.view = view
        self.name_input = discord.ui.TextInput(label="Author name", required=False, max_length=256, default=state.author_name or "")
        self.icon_input = discord.ui.TextInput(label="Author icon URL (optional)", required=False, default=state.author_icon or "")
        self.add_item(self.name_input)
        self.add_item(self.icon_input)

    async def on_submit(self, interaction: discord.Interaction):
        self.state.author_name = self.name_input.value or None
        self.state.author_icon = self.icon_input.value or None
        await self.view.refresh(interaction)


class FieldModal(discord.ui.Modal, title="Add Field"):
    def __init__(self, state: EmbedState, view: "EmbedBuilderView"):
        super().__init__()
        self.state = state
        self.view = view
        self.name_input = discord.ui.TextInput(label="Field name", required=True, max_length=256)
        self.value_input = discord.ui.TextInput(label="Field value", style=discord.TextStyle.paragraph, required=True, max_length=1024)
        self.inline_input = discord.ui.TextInput(label="Inline? (yes/no)", required=False, default="yes")
        self.add_item(self.name_input)
        self.add_item(self.value_input)
        self.add_item(self.inline_input)

    async def on_submit(self, interaction: discord.Interaction):
        if len(self.state.fields) >= 25:
            await interaction.response.send_message("❌ Embeds can have at most 25 fields.", ephemeral=True)
            return
        inline = self.inline_input.value.strip().lower() not in ("no", "false", "0")
        self.state.fields.append((self.name_input.value, self.value_input.value, inline))
        await self.view.refresh(interaction)


# ---------------- MAIN VIEW ----------------
class EmbedBuilderView(discord.ui.View):
    def __init__(self, state: EmbedState, target_channel: discord.TextChannel):
        super().__init__(timeout=600)
        self.state = state
        self.target_channel = target_channel
        self.message: discord.Message = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.state.author.id:
            await interaction.response.send_message("This builder isn't yours.", ephemeral=True)
            return False
        return True

    async def refresh(self, interaction: discord.Interaction):
        embed = self.state.build()
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    @discord.ui.button(label="Title/Desc", style=discord.ButtonStyle.blurple, row=0)
    async def title_desc_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TitleDescriptionModal(self.state, self))

    @discord.ui.button(label="Color", style=discord.ButtonStyle.blurple, row=0)
    async def color_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ColorModal(self.state, self))

    @discord.ui.button(label="Author", style=discord.ButtonStyle.blurple, row=0)
    async def author_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AuthorModal(self.state, self))

    @discord.ui.button(label="Footer", style=discord.ButtonStyle.blurple, row=1)
    async def footer_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FooterModal(self.state, self))

    @discord.ui.button(label="Image/Thumbnail", style=discord.ButtonStyle.blurple, row=1)
    async def image_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ImageModal(self.state, self))

    @discord.ui.button(label="Add Field", style=discord.ButtonStyle.blurple, row=1)
    async def field_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FieldModal(self.state, self))

    @discord.ui.button(label="Clear Fields", style=discord.ButtonStyle.gray, row=2)
    async def clear_fields_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.state.fields = []
        await self.refresh(interaction)

    @discord.ui.button(label="Send", style=discord.ButtonStyle.green, row=2)
    async def send_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = self.state.build()
        try:
            await self.target_channel.send(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to send in that channel.", ephemeral=True)
            return

        for item in self.children:
            item.disabled = True
        confirm_embed = discord.Embed(
            description=f"✅ Embed sent to {self.target_channel.mention}.",
            color=discord.Color.green(),
        )
        await interaction.response.edit_message(embed=confirm_embed, view=self)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, row=2)
    async def cancel_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        cancel_embed = discord.Embed(description="❌ Embed builder cancelled.", color=discord.Color.red())
        await interaction.response.edit_message(embed=cancel_embed, view=self)
        self.stop()


class EmbedBuilder(commands.Cog):
    """Interactive embed builder."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="embed")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def embed(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Open the interactive embed builder. Optionally specify a channel to send the finished embed to."""
        target_channel = channel or ctx.channel
        state = EmbedState(ctx.author)
        view = EmbedBuilderView(state, target_channel)

        embed = state.build()
        message = await ctx.reply(embed=embed, view=view)
        view.message = message


async def setup(bot: commands.Bot):
    await bot.add_cog(EmbedBuilder(bot))
