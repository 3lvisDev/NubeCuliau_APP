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

# URL de la noticia
URL = "https://pisapapeles.net/xbox-cloud-gaming-tendria-su-primer-servidor-en-chile-y-el-mismo-debutaria-pronto/"

# Intents de Discord
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ Bot conectado como {client.user}")
    await enviar_noticia()

async def limpiar_mensajes_antiguos(canal):
    try:
        async for mensaje in canal.history(limit=50):
            if mensaje.author == client.user:
                await mensaje.delete()
                await asyncio.sleep(1)  # Evita el rate limit
        print("🧹 Mensajes anteriores eliminados correctamente.")
    except Exception as e:
        print(f"⚠️ Error al eliminar mensajes antiguos: {e}")

async def enviar_noticia():
    try:
        canal = client.get_channel(ID_CANAL)
        if canal is None:
            print(f"⚠️ Canal con ID {ID_CANAL} no encontrado.")
            return

        # Limpiar mensajes anteriores del bot
        await limpiar_mensajes_antiguos(canal)

        response = requests.get(URL)
        soup = BeautifulSoup(response.text, 'html.parser')

        titulo_tag = soup.title
        titulo = titulo_tag.string.strip() if titulo_tag and titulo_tag.string else "Título no disponible"

        resumen_tag = soup.find("meta", property="og:description")
        resumen = resumen_tag["content"] if resumen_tag else "Resumen no disponible."

        fecha = datetime.now().strftime("%d-%m-%Y %H:%M")
        fuente = "Pisapapeles"

        mensaje = (
            f"📢 **¡Nueva Noticia de xCloud en Chile!**\n\n"
            f"📰 **Título:** [{titulo}]({URL})\n"
            f"📅 **Fecha:** {fecha}\n"
            f"🌐 **Fuente:** `{fuente}`\n"
            f"📝 **Resumen:** {resumen}\n\n"
            f"[🔎 Ver más noticias en Google News](https://news.google.com/search?q=xcloud+chile&hl=es-419&gl=CL&ceid=CL:es-419)\n"
            f"\n🇨🇱 NubeCuliau está al tanto pa’ avisarte 🔔"
        )

        await canal.send(mensaje)
        print("✅ Noticia enviada y canal limpio.")

    except Exception as e:
        print(f"❌ Error al enviar la noticia: {e}")

client.run(TOKEN)

