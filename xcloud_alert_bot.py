import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    await bot.tree.sync()
    print("🌐 Comandos slash sincronizados.")

@bot.tree.command(name="ayuda", description="Muestra todos los comandos disponibles")
async def ayuda_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Comandos de NubeCuliau 🕹️",
        description="Aquí tienes lo que puedes hacer:",
        color=discord.Color.green()
    )
    embed.add_field(name="/estado", value="Verifica el estado de los servicios de Xbox.", inline=False)
    embed.add_field(name="/juegos", value="Lista los juegos disponibles de Game Pass para PC.", inline=False)
    embed.add_field(name="/noticias", value="Busca noticias sobre xCloud en Chile.", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Cargar los cogs
async def main():
    await bot.load_extension("bot.cogs.estado")
    await bot.load_extension("bot.cogs.juegos")
    await bot.load_extension("bot.cogs.noticias")
    await bot.start(TOKEN)

import asyncio
asyncio.run(main())

