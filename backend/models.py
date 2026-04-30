from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Location(db.Model):
    __tablename__ = "locations"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    x_coord = db.Column(db.Integer, default=0)
    y_coord = db.Column(db.Integer, default=0)

    available_actions = db.relationship(
        "Action",
        secondary="location_actions",
        back_populates="locations",
    )


class Action(db.Model):
    __tablename__ = "actions"

    id = db.Column(db.String(50), primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    nb_ticks = db.Column(db.Integer, default=1)

    mod_energie = db.Column(db.Integer, default=0)
    mod_argent = db.Column(db.Float, default=0.0)
    mod_hygiene = db.Column(db.Integer, default=0)
    mod_mental = db.Column(db.Integer, default=0)
    mod_divertissement = db.Column(db.Integer, default=0)
    mod_vie = db.Column(db.Integer, default=0)
    mod_faim = db.Column(db.Integer, default=0)
    mod_stockage = db.Column(db.Integer, default=0)

    type_effet = db.Column(db.String(50))

    locations = db.relationship(
        "Location",
        secondary="location_actions",
        back_populates="available_actions",
    )


class LocationAction(db.Model):
    __tablename__ = "location_actions"

    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=False)
    action_id = db.Column(db.String(50), db.ForeignKey("actions.id"), nullable=False)

    __table_args__ = (
        db.UniqueConstraint("location_id", "action_id", name="uq_location_action"),
    )


class Character(db.Model):
    __tablename__ = "characters"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    prompt = db.Column(db.Text, nullable=False)

    hp = db.Column(db.Integer, default=10)

    hunger = db.Column(db.Integer, default=80)
    energy = db.Column(db.Integer, default=80)
    hygiene = db.Column(db.Integer, default=80)
    mental = db.Column(db.Integer, default=80)
    entertainment = db.Column(db.Integer, default=80)

    money = db.Column(db.Integer, default=20)
    food = db.Column(db.Integer, default=1)

    is_alive = db.Column(db.Boolean, default=True)
    death_reason = db.Column(db.String(255), nullable=True)

    feeling = db.Column(db.String(255), default="Je viens de commencer ma vie.")
    last_action = db.Column(db.String(50), nullable=True)

    last_update = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    current_location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), default=1)
    current_action_id = db.Column(db.String(50), nullable=True)
    remaining_ticks = db.Column(db.Integer, default=0)

    logs = db.relationship("ActionLog", backref="character", cascade="all, delete-orphan", lazy=True)
    current_location = db.relationship("Location", foreign_keys=[current_location_id])


class ActionLog(db.Model):
    __tablename__ = "action_logs"

    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey("characters.id"), nullable=False)

    action = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
