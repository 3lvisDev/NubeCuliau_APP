import discord
from discord.ext import commands, tasks
import json
import nmap
import requests
import asyncio
import logging

logging.basicConfig(level=logging.INFO)

class LanWatcher(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = self.load_config()
        self.known_hosts = self.load_known_hosts()
        self.nm = nmap.PortScanner()
        if self.config.get('enabled', True):
            self.scan_network_task.start()

    def cog_unload(self):
        self.scan_network_task.cancel()

    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error("El archivo config.json no fue encontrado. Creando uno con valores por defecto.")
            default_config = {
                "network": "192.168.1.0/24",
                "intervalSeconds": 60,
                "discordWebhookUrl": "https://discord.com/api/webhooks/ID/TOKEN",
                "knownFile": "known_hosts.json",
                "enabled": True
            }
            with open('config.json', 'w') as f:
                json.dump(default_config, f, indent=4)
            return default_config

    def load_known_hosts(self):
        try:
            with open(self.config['knownFile'], 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.info(f"El archivo {self.config['knownFile']} no fue encontrado. Se creará uno nuevo.")
            return {}
        except json.JSONDecodeError:
            logging.warning(f"Error al leer {self.config['knownFile']}. El archivo podría estar corrupto. Empezando con una lista vacía.")
            return {}

    def save_known_hosts(self):
        with open(self.config['knownFile'], 'w') as f:
            json.dump(self.known_hosts, f, indent=4)

    async def notify_discord(self, message):
        webhook_url = self.config.get('discordWebhookUrl')
        if not webhook_url or 'ID/TOKEN' in webhook_url:
            logging.warning("El webhook de Discord no está configurado. Omitiendo notificación.")
            return

        data = {"content": message}
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                lambda: requests.post(webhook_url, json=data)
            )
        except Exception as e:
            logging.error(f"Error al notificar a Discord: {e}")

    def scan_network(self):
        try:
            self.nm.scan(hosts=self.config['network'], arguments='-sn')
            hosts = {}
            for host in self.nm.all_hosts():
                ip = host
                mac = self.nm[host]['addresses'].get('mac', 'desconocida')
                vendor = self.nm[host]['vendor'].get(mac, 'desconocido') if mac != 'desconocida' else 'desconocido'
                hosts[ip] = {'ip': ip, 'mac': mac, 'vendor': vendor}
            return hosts
        except Exception as e:
            logging.error(f"Error durante el escaneo de red con nmap: {e}")
            return {}

    @tasks.loop(minutes=5)
    async def scan_network_task(self):
        logging.info("Iniciando escaneo de red...")
        loop = asyncio.get_running_loop()
        try:
            current_hosts = await loop.run_in_executor(None, self.scan_network)

            for ip, info in current_hosts.items():
                if ip not in self.known_hosts:
                    msg = (
                        f"🔔 **Nuevo dispositivo detectado en la red**\n"
                        f"**IP:** `{info['ip']}`\n"
                        f"**MAC:** `{info['mac']}`\n"
                        f"**Fabricante:** `{info['vendor']}`"
                    )
                    logging.info(f"Nuevo dispositivo: {info['ip']} ({info['mac']})")
                    await self.notify_discord(msg)
                    self.known_hosts[ip] = info

            self.save_known_hosts()
            logging.info(f"Escaneo de red completado. Hosts conocidos: {len(self.known_hosts)}")

        except Exception as e:
            logging.error(f"Ocurrió un error en la tarea de escaneo: {e}")

    @scan_network_task.before_loop
    async def before_scan_network_task(self):
        logging.info("Esperando que el bot esté listo para iniciar el escáner de red...")
        await self.bot.wait_until_ready()

    @commands.hybrid_group(name="lan", description="Comandos para el monitor de red.")
    async def lan(self, ctx):
        await ctx.send_help(ctx.command)

    @lan.command(name="scan", description="Realiza un escaneo de la red en busca de nuevos dispositivos.")
    @commands.is_owner()
    async def scan_command(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        logging.info(f"Escaneo manual de red iniciado por {ctx.author}.")

        loop = asyncio.get_running_loop()
        try:
            current_hosts = await loop.run_in_executor(None, self.scan_network)
            new_devices_found = 0

            for ip, info in current_hosts.items():
                if ip not in self.known_hosts:
                    new_devices_found += 1
                    msg = (
                        f"🔔 **Nuevo dispositivo detectado en la red (escaneo manual)**\n"
                        f"**IP:** `{info['ip']}`\n"
                        f"**MAC:** `{info['mac']}`\n"
                        f"**Fabricante:** `{info['vendor']}`"
                    )
                    logging.info(f"Nuevo dispositivo: {info['ip']} ({info['mac']})")
                    await self.notify_discord(msg)
                    self.known_hosts[ip] = info

            self.save_known_hosts()

            if new_devices_found > 0:
                await ctx.send(f"✅ Escaneo completado. Se encontraron {new_devices_found} nuevos dispositivos.", ephemeral=True)
            else:
                await ctx.send("✅ Escaneo completado. No se encontraron nuevos dispositivos.", ephemeral=True)

        except Exception as e:
            logging.error(f"Error en el escaneo manual: {e}")
            await ctx.send(f"❌ Ocurrió un error al escanear la red: {e}", ephemeral=True)

    @lan.command(name="known", description="Muestra la lista de dispositivos conocidos en la red.")
    @commands.is_owner()
    async def known_command(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        if not self.known_hosts:
            await ctx.send("No hay dispositivos conocidos en la lista.", ephemeral=True)
            return

        embed = discord.Embed(title="Dispositivos Conocidos en la Red", color=discord.Color.blue())
        description = ""
        for ip, info in self.known_hosts.items():
            description += f"**IP:** `{info['ip']}` | **MAC:** `{info['mac']}` | **Fabricante:** `{info.get('vendor', 'desconocido')}`\n"

        # Discord embed descriptions have a limit of 4096 characters.
        if len(description) > 4096:
            description = description[:4090] + "..."

        embed.description = description
        await ctx.send(embed=embed, ephemeral=True)

    @lan.command(name="status", description="Muestra el estado del monitor de red.")
    @commands.is_owner()
    async def status_command(self, ctx: commands.Context):
        status = "✅ Activo" if self.scan_network_task.is_running() else "❌ Inactivo"
        next_iteration = discord.utils.format_dt(self.scan_network_task.next_iteration, style='R') if self.scan_network_task.is_running() else "N/A"

        embed = discord.Embed(title="Estado del Monitor de Red", color=discord.Color.green())
        embed.add_field(name="Servicio", value=status, inline=True)
        embed.add_field(name="Próximo escaneo", value=next_iteration, inline=True)
        embed.add_field(name="Hosts conocidos", value=str(len(self.known_hosts)), inline=True)
        embed.add_field(name="Red", value=f"`{self.config['network']}`", inline=False)

        await ctx.send(embed=embed, ephemeral=True)


async def setup(bot):
    import subprocess
    # nmap debe estar instalado en el sistema para que este cog funcione.
    try:
        subprocess.run(['nmap', '-V'], check=True, capture_output=True)
        await bot.add_cog(LanWatcher(bot))
    except (subprocess.CalledProcessError, FileNotFoundError):
        logging.error("="*50)
        logging.error("NMAP NO ESTÁ INSTALADO O NO SE ENCUENTRA EN EL PATH.")
        logging.error("Este cog ('LanWatcher') no se cargará.")
        logging.error("Por favor, instala nmap en tu sistema.")
        logging.error("En Debian/Ubuntu: sudo apt install nmap")
        logging.error("En Windows, descárgalo desde https://nmap.org")
        logging.error("="*50)