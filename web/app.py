import os
import google_auth_oauthlib.flow
from flask import Flask, redirect, url_for, render_template, request, session
from flask_discord import DiscordOAuth2Session, Unauthorized
from .models import db, User, Guild, LinkedAccount
from .crypto import encrypt, decrypt
from twitchapi.twitch import Twitch
from twitchapi.oauth import UserAuthenticator
from twitchapi.types import AuthScope
from googleapiclient.discovery import build
import google.oauth2.credentials

app = Flask(__name__)

app.config["SECRET_KEY"] = os.urandom(24)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///../database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# Note: You'll need to set these in your .env file
app.config["DISCORD_CLIENT_ID"] = os.getenv("DISCORD_CLIENT_ID")
app.config["DISCORD_CLIENT_SECRET"] = os.getenv("DISCORD_CLIENT_SECRET")
app.config["DISCORD_REDIRECT_URI"] = "http://localhost:5000/callback"
app.config["DISCORD_BOT_TOKEN"] = os.getenv("DISCORD_TOKEN")
app.config["TWITCH_CLIENT_ID"] = os.getenv("TWITCH_CLIENT_ID")
app.config["TWITCH_CLIENT_SECRET"] = os.getenv("TWITCH_CLIENT_SECRET")
app.config["TWITCH_REDIRECT_URI"] = "http://localhost:5000/callback/twitch"
app.config["YOUTUBE_CLIENT_ID"] = os.getenv("YOUTUBE_CLIENT_ID")
app.config["YOUTUBE_CLIENT_SECRET"] = os.getenv("YOUTUBE_CLIENT_SECRET")
app.config["YOUTUBE_REDIRECT_URI"] = "http://localhost:5000/callback/youtube"


# Scopes for the bot invitation
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "true" # !! REMOVE IN PRODUCTION
app.config["DISCORD_BOT_SCOPES"] = ["bot", "applications.commands"]
app.config["DISCORD_BOT_PERMISSIONS"] = 8 # Administrator

discord = DiscordOAuth2Session(app)
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    if discord.authorized:
        return redirect(url_for("dashboard"))
    return render_template('index.html')

@app.route("/login/")
def login():
    return discord.create_session(scope=app.config["DISCORD_BOT_SCOPES"], permissions=app.config["DISCORD_BOT_PERMISSIONS"])

@app.route("/callback/")
def callback():
    data = discord.callback()
    user = discord.fetch_user()

    db_user = User.query.filter_by(discord_id=str(user.id)).first()
    if not db_user:
        db_user = User(discord_id=str(user.id))
        db.session.add(db_user)
        db.session.commit()

    guild_id = data.get("guild_id")
    if guild_id:
        guild = Guild.query.filter_by(guild_id=guild_id).first()
        if not guild:
            guild = Guild(guild_id=guild_id, user_id=db_user.id)
            db.session.add(guild)
            db.session.commit()

    return redirect(url_for("dashboard"))

@app.route("/dashboard/")
def dashboard():
    try:
        user = discord.fetch_user()
        db_user = User.query.filter_by(discord_id=str(user.id)).first()
        linked_accounts = db_user.linked_accounts if db_user else []
        guilds = db_user.guilds if db_user else []
        return render_template('dashboard.html', user=user, linked_accounts=linked_accounts, guilds=guilds)
    except Unauthorized:
        return redirect(url_for("login"))

@app.route("/link/twitch")
async def link_twitch():
    twitch = await Twitch(app.config["TWITCH_CLIENT_ID"], app.config["TWITCH_CLIENT_SECRET"])
    auth = UserAuthenticator(twitch, [AuthScope.USER_READ_EMAIL], url=app.config["TWITCH_REDIRECT_URI"])
    return redirect(auth.get_auth_url())

@app.route("/callback/twitch")
async def callback_twitch():
    try:
        user = discord.fetch_user()
        db_user = User.query.filter_by(discord_id=str(user.id)).first()
        if not db_user:
            return "Discord user not found", 404

        code = request.args.get("code")
        twitch = await Twitch(app.config["TWITCH_CLIENT_ID"], app.config["TWITCH_CLIENT_SECRET"])
        auth = UserAuthenticator(twitch, [AuthScope.USER_READ_EMAIL], url=app.config["TWITCH_REDIRECT_URI"])
        token, refresh_token = await auth.authenticate(user_token=code)

        await twitch.set_user_authentication(token, [AuthScope.USER_READ_EMAIL], refresh_token)

        twitch_user_info = await twitch.get_users()
        account_name = twitch_user_info['data'][0]['display_name']
        channel_id = twitch_user_info['data'][0]['id']


        encrypted_token = encrypt(refresh_token)

        new_linked_account = LinkedAccount(
            user_id=db_user.id,
            platform='twitch',
            account_name=account_name,
            channel_id=channel_id,
            encrypted_refresh_token=encrypted_token
        )
        db.session.add(new_linked_account)
        db.session.commit()

        return redirect(url_for("dashboard"))
    except Unauthorized:
        return redirect(url_for("login"))

@app.route('/link/youtube')
def link_youtube():
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        {
            "web": {
                "client_id": app.config["YOUTUBE_CLIENT_ID"],
                "client_secret": app.config["YOUTUBE_CLIENT_SECRET"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": [app.config["YOUTUBE_REDIRECT_URI"]],
            }
        },
        scopes=['https://www.googleapis.com/auth/youtube.readonly'],
        redirect_uri=app.config["YOUTUBE_REDIRECT_URI"])
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')
    session['state'] = state
    return redirect(authorization_url)

@app.route('/callback/youtube')
def callback_youtube():
    state = session['state']
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        {
            "web": {
                "client_id": app.config["YOUTUBE_CLIENT_ID"],
                "client_secret": app.config["YOUTUBE_CLIENT_SECRET"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": [app.config["YOUTUBE_REDIRECT_URI"]],
            }
        },
        scopes=['https://www.googleapis.com/auth/youtube.readonly'],
        state=state,
        redirect_uri=app.config["YOUTUBE_REDIRECT_URI"])
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    refresh_token = credentials.refresh_token

    user = discord.fetch_user()
    db_user = User.query.filter_by(discord_id=str(user.id)).first()
    if not db_user:
        return "Discord user not found", 404

    youtube = build('youtube', 'v3', credentials=credentials)
    channels = youtube.channels().list(part='snippet,id', mine=True).execute()
    account_name = channels['items'][0]['snippet']['title']
    channel_id = channels['items'][0]['id']

    encrypted_token = encrypt(refresh_token)

    new_linked_account = LinkedAccount(
        user_id=db_user.id,
        platform='youtube',
        account_name=account_name,
        channel_id=channel_id,
        encrypted_refresh_token=encrypted_token
    )
    db.session.add(new_linked_account)
    db.session.commit()

    return redirect(url_for('dashboard'))

@app.route('/configure_guild/<guild_id>', methods=['POST'])
def configure_guild(guild_id):
    try:
        user = discord.fetch_user()
        db_user = User.query.filter_by(discord_id=str(user.id)).first()
        guild = Guild.query.filter_by(guild_id=guild_id, user_id=db_user.id).first()
        if not guild:
            return "Guild not found or you do not have permission to configure it.", 404

        channel_id = request.form.get('channel_id')
        guild.notification_channel_id = channel_id
        db.session.commit()

        return redirect(url_for('dashboard'))
    except Unauthorized:
        return redirect(url_for("login"))

@app.route('/remove_account/<int:account_id>')
def remove_account(account_id):
    try:
        user = discord.fetch_user()
        db_user = User.query.filter_by(discord_id=str(user.id)).first()
        account = LinkedAccount.query.filter_by(id=account_id, user_id=db_user.id).first()
        if not account:
            return "Account not found or you do not have permission to remove it.", 404

        db.session.delete(account)
        db.session.commit()

        return redirect(url_for('dashboard'))
    except Unauthorized:
        return redirect(url_for("login"))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
