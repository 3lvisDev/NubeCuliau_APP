import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

async def main():
    load_dotenv()
    TOKEN = os.getenv("DISCORD_TOKEN")

    intents = discord.Intents.default()
    intents.members = True

    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        print(f"✅ Bot conectado como {bot.user}")
        await bot.tree.sync()
        print("🌐 Comandos slash sincronizados.")

    async with bot:
        await bot.load_extension("bot.cogs.dashboard")
        await bot.load_extension("bot.cogs.stream_checker")
        await bot.start(TOKEN)

import asyncio
if __name__ == "__main__":
    asyncio.run(main())
