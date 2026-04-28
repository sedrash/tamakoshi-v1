from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Character(db.Model):
    __tablename__ = "characters"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    prompt = db.Column(db.Text, nullable=False)

    hp = db.Column(db.Integer, default=10)

    hunger = db.Column(db.Integer, default=80)
    energy = db.Column(db.Integer, default=80)
    hygiene = db.Column(db.Integer, default=80)

    money = db.Column(db.Integer, default=20)
    food = db.Column(db.Integer, default=1)

    is_alive = db.Column(db.Boolean, default=True)
    death_reason = db.Column(db.String(255), nullable=True)

    feeling = db.Column(db.String(255), default="Je viens de commencer ma vie.")
    last_action = db.Column(db.String(50), nullable=True)

    last_update = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    logs = db.relationship("ActionLog", backref="character", lazy=True)


class ActionLog(db.Model):
    __tablename__ = "action_logs"

    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey("characters.id"), nullable=False)

    action = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)