from discord.ext import commands
from discord import app_commands, Interaction, Embed
import requests
from bs4 import BeautifulSoup

class Noticias(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.URL_BUSQUEDA = "https://news.google.com/search?q=xcloud%20chile&hl=es-419&gl=CL&ceid=CL:es-419"

    @app_commands.command(name="noticias", description="Muestra las últimas noticias sobre xCloud en Chile.")
    async def noticias(self, interaction: Interaction):
        try:
            res = requests.get(self.URL_BUSQUEDA)
            soup = BeautifulSoup(res.text, "html.parser")
            noticia = soup.find("article")
            titulo = noticia.text
            link = "https://news.google.com" + noticia.find("a")["href"][1:]

            embed = Embed(title="📰 Última noticia de xCloud en Chile", description=titulo, color=0xf1c40f)
            embed.add_field(name="Ver más", value=f"[Leer noticia]({link})", inline=False)
            embed.set_footer(text="🇨🇱 NubeCuliau está al tanto pa’ avisarte 🔔")

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error al buscar noticias: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Noticias(bot))

