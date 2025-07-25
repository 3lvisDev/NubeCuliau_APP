from discord.ext import commands
from discord import app_commands, Interaction, Embed
import requests

class Juegos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="juegos", description="Muestra algunos juegos del Game Pass.")
    async def juegos(self, interaction: Interaction):
        try:
            response = requests.get("https://catalog.gamepass.com/api/v1/Products?market=cl&language=es-cl")
            data = response.json()

            juegos = [j['ProductTitle'] for j in data[:10]]  # top 10 juegos
            lista = "\n".join(f"🎮 {j}" for j in juegos)

            embed = Embed(title="🎮 Juegos disponibles en Game Pass", description=lista, color=0x3498db)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error al obtener juegos: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Juegos(bot))

