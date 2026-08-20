import discord
from discord.ext import commands

from utils.help_data import MODULES
from utils import colors


def build_home_embed(bot: commands.Bot) -> discord.Embed:
    total_commands = sum(len(m["commands"]) for m in MODULES.values())
    embed = discord.Embed(
        title=f"@{bot.user.name} | Help",
        description=(
            f"Prefix: `{bot.command_prefix}`\n"
            f"{len(MODULES)} modules • {total_commands} commands\n\n"
            "Use the dropdown below to browse a module's commands.\n"
            "`<>` = required argument, `[]` = optional argument."
        ),
        color=colors.EMBED_COLOR,
    )
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    return embed


def build_module_embed(bot: commands.Bot, module_name: str) -> discord.Embed:
    module = MODULES[module_name]
    embed = discord.Embed(
        title=f"{module['emoji']} {module_name}",
        description=module["description"],
        color=colors.EMBED_COLOR,
    )
    for name, desc in module["commands"]:
        embed.add_field(name=f"`{bot.command_prefix}{name}`", value=desc, inline=False)
    return embed


class HelpSelect(discord.ui.Select):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        options = [
            discord.SelectOption(label="Home", description="Go back to the home screen.", emoji="🏠", value="__home__")
        ]
        for name, data in MODULES.items():
            options.append(
                discord.SelectOption(label=name, description=data["description"][:100], emoji=data["emoji"], value=name)
            )
        super().__init__(placeholder="Select a module...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        if selected == "__home__":
            embed = build_home_embed(self.bot)
        else:
            embed = build_module_embed(self.bot, selected)
        await interaction.response.edit_message(embed=embed)


class HelpView(discord.ui.View):
    def __init__(self, bot: commands.Bot, author_id: int):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.add_item(HelpSelect(bot))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This help menu isn't yours — run `,help` to get your own.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


class Help(commands.Cog):
    """Interactive dropdown help menu."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="help", aliases=["h"])
    async def help_command(self, ctx: commands.Context):
        """Show the interactive help menu."""
        embed = build_home_embed(self.bot)
        view = HelpView(self.bot, ctx.author.id)
        await ctx.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
