from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    discord_id = db.Column(db.String(50), unique=True, nullable=False)
    guilds = db.relationship('Guild', backref='user', lazy=True)
    linked_accounts = db.relationship('LinkedAccount', backref='user', lazy=True)

class Guild(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notification_channel_id = db.Column(db.String(50), nullable=True)

class LinkedAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    platform = db.Column(db.String(20), nullable=False)  # 'twitch' or 'youtube'
    account_name = db.Column(db.String(100), nullable=True)
    channel_id = db.Column(db.String(100), nullable=False)
    encrypted_refresh_token = db.Column(db.LargeBinary, nullable=False)
    is_live = db.Column(db.Boolean, default=False)
