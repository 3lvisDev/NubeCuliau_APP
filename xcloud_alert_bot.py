import discord
import asyncio
import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from bs4 import XMLParsedAsHTMLWarning
import warnings

# Ignorar advertencias XMLParsedAsHTMLWarning
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Cargar variables desde .env
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
ID_CANAL = int(os.getenv("CHANNEL_ID"))

# URL de búsqueda de noticias en Google News
URL_BUSQUEDA = "https://news.google.com/search?q=xcloud+chile&hl=es-419&gl=CL&ceid=CL:es-419"

# Intents de Discord
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ Bot conectado como {client.user}")
    # await buscar_y_enviar_noticia() # Comentado para que no se envíe al iniciar

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!noticias'):
        await buscar_y_enviar_noticia(message.channel)
    elif message.content.startswith('!ayuda'):
        embed = discord.Embed(
            title="Centro de Ayuda de NubeCuliau",
            description="Aquí tienes una lista de los comandos disponibles:",
            color=discord.Color.blue()
        )
        embed.add_field(name="`!noticias`", value="Busca y muestra la última noticia sobre xCloud en Chile.", inline=False)
        embed.add_field(name="`!ayuda`", value="Muestra este mensaje de ayuda.", inline=False)
        embed.set_footer(text="¡Espero que esto te ayude! 😊")
        await message.channel.send(embed=embed)

async def limpiar_mensajes_antiguos(canal):
    try:
        async for mensaje in canal.history(limit=50):
            if mensaje.author == client.user:
                await mensaje.delete()
                await asyncio.sleep(1)  # Evita el rate limit
        print("🧹 Mensajes anteriores eliminados correctamente.")
    except Exception as e:
        print(f"⚠️ Error al eliminar mensajes antiguos: {e}")

async def buscar_y_enviar_noticia(canal):
    try:
        # Limpiar mensajes anteriores del bot
        await limpiar_mensajes_antiguos(canal)

        response = requests.get(URL_BUSQUEDA)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Encontrar el enlace de la primera noticia
        article = soup.find("article")
        if not article:
            print("No se encontraron noticias.")
            return

        link = article.find("a", href=True)
        if not link:
            print("No se encontró el enlace de la noticia.")
            return
        
        # Google News usa URLs relativas, así que las completamos
        url_noticia = "https://news.google.com" + link['href']

        # Extraer información de la noticia
        titulo = link.text.strip()
        fuente_tag = article.find("div", {"class": "SVJrMe"})
        fuente = fuente_tag.text.strip() if fuente_tag else "Fuente no disponible"
        
        fecha = datetime.now().strftime("%d-%m-%Y %H:%M")

        embed = discord.Embed(
            title=f"📢 ¡Nueva Noticia de xCloud en Chile!",
            description=f"📰 **[{titulo}]({url_noticia})**",
            color=discord.Color.green()
        )
        embed.add_field(name="📅 Fecha", value=fecha, inline=True)
        embed.add_field(name="🌐 Fuente", value=f"`{fuente}`", inline=True)
        embed.add_field(name="🔎 Ver más noticias", value=f"[Google News]({URL_BUSQUEDA})", inline=False)
        embed.set_footer(text="🇨🇱 NubeCuliau está al tanto pa’ avisarte 🔔")
        
        await canal.send(embed=embed)
        print("✅ Noticia enviada y canal limpio.")

    except Exception as e:
        print(f"❌ Error al enviar la noticia: {e}")

client.run(TOKEN)

