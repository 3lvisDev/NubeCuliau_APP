from discord.ext import commands
from discord import app_commands, Interaction, Embed
import requests
from bs4 import BeautifulSoup

class Estado(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.URL_ESTADO = "https://support.xbox.com/es-CL/xbox-live-status"

    @app_commands.command(name="estado", description="Verifica el estado actual de Xbox Live.")
    async def estado(self, interaction: Interaction):
        try:
            response = requests.get(self.URL_ESTADO)
            soup = BeautifulSoup(response.content, "html.parser")

            estado = soup.find("div", class_="services-list").get_text(strip=True)

            embed = Embed(title="📶 Estado de Xbox Live", color=0x00ff00)
            embed.add_field(name="Estado", value=estado, inline=False)
            embed.add_field(name="Fuente", value=f"[Xbox Live Status]({self.URL_ESTADO})", inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error al obtener estado: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Estado(bot))

