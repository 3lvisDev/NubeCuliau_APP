import asyncio
from discord.ext import tasks, commands
from web.models import db, User, LinkedAccount, Guild
from web.crypto import decrypt
from twitchapi.twitch import Twitch, AuthScope
from googleapiclient.discovery import build
import os
from web.app import app
import google.oauth2.credentials

class StreamChecker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.twitch = None
        self.check_streams.start()

    async def cog_load(self):
        self.twitch = await Twitch(os.getenv("TWITCH_CLIENT_ID"), os.getenv("TWITCH_CLIENT_SECRET"))

    @tasks.loop(minutes=1)
    async def check_streams(self):
        if not self.twitch:
            await self.cog_load()

        with app.app_context():
            accounts = LinkedAccount.query.all()
            for account in accounts:
                is_live = False
                try:
                    if account.platform == 'twitch':
                        live_streams = await self.twitch.get_streams(user_id=[account.channel_id])
                        if live_streams['data']:
                            is_live = True

                    elif account.platform == 'youtube':
                        refresh_token = decrypt(account.encrypted_refresh_token)
                        credentials = google.oauth2.credentials.Credentials(
                            None,
                            refresh_token=refresh_token,
                            token_uri="https://oauth2.googleapis.com/token",
                            client_id=os.getenv("YOUTUBE_CLIENT_ID"),
                            client_secret=os.getenv("YOUTUBE_CLIENT_SECRET"),
                        )
                        youtube = build('youtube', 'v3', credentials=credentials)
                        search_response = youtube.search().list(
                            channelId=account.channel_id,
                            type='video',
                            eventType='live',
                            part='id',
                            maxResults=1
                        ).execute()
                        if search_response.get('items'):
                            is_live = True

                    if is_live and not account.is_live:
                        account.is_live = True
                        db.session.commit()

                        user = User.query.get(account.user_id)
                        for guild in user.guilds:
                            if guild.notification_channel_id:
                                channel = self.bot.get_channel(int(guild.notification_channel_id))
                                if channel:
                                    await channel.send(f"🎉 Hey @everyone! {account.account_name} is now live on {account.platform.capitalize()}! 🎉\nWatch here: https://www.{account.platform}.com/{account.account_name}")

                    elif not is_live and account.is_live:
                        account.is_live = False
                        db.session.commit()

                except Exception as e:
                    print(f"Error checking stream for {account.account_name} on {account.platform}: {e}")

    @check_streams.before_loop
    async def before_check_streams(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(StreamChecker(bot))
