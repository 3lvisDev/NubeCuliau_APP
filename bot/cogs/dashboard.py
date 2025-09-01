import discord
from discord.ext import commands
from discord import app_commands

class Dashboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="dashboard", description="Get a link to your web dashboard.")
    async def dashboard(self, interaction: discord.Interaction):
        # In a real application, you would get this URL from a config file
        # For now, we'll just hardcode it.
        await interaction.response.send_message(
            "Click here to access your dashboard: http://localhost:5000/",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Dashboard(bot))
