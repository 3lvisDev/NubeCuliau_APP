import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Cargar variables desde .env
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
ID_CANAL = int(os.getenv("CHANNEL_ID"))

# Intents de Discord
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

# Cargar cogs
initial_extensions = [
    'bot.cogs.noticias',
    'bot.cogs.juegos',
    'bot.cogs.estado'
]

if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)

@bot.command(name='ayuda')
async def ayuda(ctx):
    embed = discord.Embed(
        title="Centro de Ayuda de NubeCuliau",
        description="Aquí tienes una lista de los comandos disponibles:",
        color=discord.Color.blue()
    )
    embed.add_field(name="`!noticias`", value="Busca y muestra la última noticia sobre xCloud en Chile.", inline=False)
    embed.add_field(name="`!juegos`", value="Muestra la lista de juegos de PC disponibles en xCloud.", inline=False)
    embed.add_field(name="`!juegos_consola`", value="Muestra la lista de juegos de consola disponibles en xCloud.", inline=False)
    embed.add_field(name="`!estado`", value="Verifica el estado de los servicios de Xbox.", inline=False)
    embed.add_field(name="`!ayuda`", value="Muestra este mensaje de ayuda.", inline=False)
    embed.set_footer(text="¡Espero que esto te ayude! 😊")
    await ctx.send(embed=embed)

bot.run(TOKEN)
bot/cogs/noticias.py

import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
from datetime import datetime

class Noticias(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.URL_BUSQUEDA = "https://news.google.com/search?q=xcloud+chile&hl=es-419&gl=CL&ceid=CL:es-419"

    @commands.command(name='noticias')
    async def buscar_noticias(self, ctx):
        """Busca y muestra la última noticia sobre xCloud en Chile."""
        try:
            await self.limpiar_mensajes_antiguos(ctx.channel)
            response = requests.get(self.URL_BUSQUEDA)
            soup = BeautifulSoup(response.text, 'html.parser')

            article = soup.find("article")
            if not article:
                await ctx.send("No se encontraron noticias.")
                return

            link = article.find("a", href=True)
            if not link:
                await ctx.send("No se encontró el enlace de la noticia.")
                return

            google_news_url = "https://news.google.com" + link['href']
            response_noticia = requests.get(google_news_url)
            
            url_noticia = response_noticia.url
            
            soup_noticia = BeautifulSoup(response_noticia.text, 'html.parser')
            
            titulo = soup_noticia.find('h1').text.strip() if soup_noticia.find('h1') else "Título no disponible"
            fuente_tag = article.find("div", {"class": "SVJrMe"})
            fuente = fuente_tag.text.strip() if fuente_tag else "Fuente no disponible"
            fecha = datetime.now().strftime("%d-%m-%Y %H:%M")

            embed = discord.Embed(
                title=titulo,
                url=url_noticia,
                color=discord.Color.green()
            )
            embed.set_author(name=fuente)
            embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/Xbox_one_logo.svg/1200px-Xbox_one_logo.svg.png")
            embed.add_field(name="Fecha", value=fecha, inline=True)
            embed.add_field(name="Ver más", value=f"[en Google News]({self.URL_BUSQUEDA})", inline=True)
            embed.set_footer(text="🇨🇱 NubeCuliau está al tanto pa’ avisarte 🔔")
            
            await ctx.send(embed=embed)
            print("✅ Noticia enviada y canal limpio.")

        except Exception as e:
            print(f"❌ Error al enviar la noticia: {e}")
            await ctx.send("❌ Hubo un error al buscar las noticias.")

    async def limpiar_mensajes_antiguos(self, canal):
        try:
            async for mensaje in canal.history(limit=50):
                if mensaje.author == self.bot.user:
                    await mensaje.delete()
            print("🧹 Mensajes anteriores eliminados correctamente.")
        except Exception as e:
            print(f"⚠️ Error al eliminar mensajes antiguos: {e}")

def setup(bot):
    bot.add_cog(Noticias(bot))
bot/cogs/juegos.py

import discord
from discord.ext import commands
import requests

class Juegos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='juegos')
    async def listar_juegos_pc(self, ctx):
        """Muestra la lista de juegos disponibles en xCloud para PC."""
        await self.listar_juegos(ctx, "PC")

    @commands.command(name='juegos_consola')
    async def listar_juegos_consola(self, ctx):
        """Muestra la lista de juegos disponibles en xCloud para Consola."""
        await self.listar_juegos(ctx, "Console")

    async def listar_juegos(self, ctx, plataforma):
        """Muestra la lista de juegos disponibles en xCloud para una plataforma específica."""
        try:
            URL_JUEGOS = f"https://catalog.gamepass.com/v2/products?market=US&language=en-US&platform={plataforma}"
            response = requests.get(URL_JUEGOS)
            juegos = response.json()

            embed = discord.Embed(
                title=f"🎮 Juegos Disponibles en xCloud ({plataforma})",
                description="Aquí tienes una lista de los juegos disponibles actualmente:",
                color=discord.Color.purple()
            )

            lista_juegos = ""
            for juego in juegos.get('Products', [])[:20]:
                lista_juegos += f"- {juego.get('LocalizedProperties', [{}])[0].get('ProductTitle', 'Nombre no disponible')}\n"

            if lista_juegos:
                embed.add_field(name="Juegos", value=lista_juegos, inline=False)
            else:
                embed.add_field(name="Juegos", value="No se encontraron juegos.", inline=False)

            await ctx.send(embed=embed)

        except Exception as e:
            print(f"❌ Error al listar los juegos: {e}")
            await ctx.send("❌ Hubo un error al obtener la lista de juegos.")

def setup(bot):
    bot.add_cog(Juegos(bot))
bot/cogs/estado.py

import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup

class Estado(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.URL_ESTADO = "https://support.xbox.com/es-CL/xbox-live-status"

    @commands.command(name='estado')
    async def verificar_estado(self, ctx):
        """Verifica el estado de los servicios de Xbox."""
        try:
            response = requests.get(self.URL_ESTADO)
            soup = BeautifulSoup(response.text, 'html.parser')

            status_element = soup.find("h2", class_="c-heading-3")
            status = status_element.text.strip() if status_element else "No se pudo obtener el estado."

            embed = discord.Embed(
                title="☁️ Estado de los Servicios de Xbox",
                description=f"El estado actual de los servicios es: **{status}**",
                color=discord.Color.orange()
            )
            embed.add_field(name="Fuente", value=f"[Página de estado de Xbox]({self.URL_ESTADO})", inline=False)
            
            await ctx.send(embed=embed)

        except Exception as e:
            print(f"❌ Error al verificar el estado: {e}")
            await ctx.send("❌ Hubo un error al verificar el estado de los servicios.")

def setup(bot):
    bot.add_cog(Estado(bot))
