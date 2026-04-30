import os
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from sqlalchemy import inspect, text

try:
    from .game_engine import run_tick
    from .models import Action, ActionLog, Character, Location, LocationAction, db
except ImportError:
    from game_engine import run_tick
    from models import Action, ActionLog, Character, Location, LocationAction, db

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"
SQLITE_DATABASE_URI = f"sqlite:///{BASE_DIR / 'tamakoshi.db'}"
MARIADB_DATABASE_URI = "mysql+pymysql://tamakoshi_user:password123@localhost/tamakoshi_db"


def load_env_file():
    env_path = PROJECT_DIR / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file()


def get_database_uri():
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL")
    if os.getenv("TAMAKOSHI_DATABASE", "").lower() == "sqlite":
        return SQLITE_DATABASE_URI
    return MARIADB_DATABASE_URI


def create_app(test_config=None):
    app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
    CORS(app)

    app.config.update(
        SQLALCHEMY_DATABASE_URI=get_database_uri(),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JSON_SORT_KEYS=False,
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    register_routes(app)

    with app.app_context():
        db.create_all()
        ensure_character_columns()
        seed_world()

    return app


def isoformat(value):
    return value.isoformat() if value else None

def character_to_json(character):
    current_action = db.session.get(Action, character.current_action_id) if character.current_action_id else None
    current_location = db.session.get(Location, character.current_location_id) if character.current_location_id else None

    return {
        "id": character.id,
        "name": character.name,
        "prompt": character.prompt,
        "hp": character.hp,
        "hunger": character.hunger,
        "energy": character.energy,
        "hygiene": character.hygiene,
        "mental": character.mental,
        "entertainment": character.entertainment,
        "money": character.money,
        "food": character.food,
        "isAlive": character.is_alive,
        "deathReason": character.death_reason,
        "feeling": character.feeling,
        "situationTitle": situation_title(character, current_action, current_location),
        "lastAction": character.last_action,
        "currentAction": current_action.nom if current_action else None,
        "actionTicksLeft": character.remaining_ticks or 0,
        "currentLocation": current_location.nom if current_location else None,
        "currentLocationId": character.current_location_id,
        "lastUpdate": isoformat(character.last_update),
        "createdAt": isoformat(character.created_at),
    }


def situation_title(character, current_action=None, current_location=None):
    if not character.is_alive:
        return character.death_reason or "Personnage mort"

    critical_stats = []
    for label, value in (
        ("faim", character.hunger),
        ("energie", character.energy),
        ("hygiene", character.hygiene),
        ("mental", character.mental),
        ("loisir", character.entertainment),
    ):
        if value is not None and value <= 25:
            critical_stats.append(label)

    if critical_stats:
        return f"Priorite : {', '.join(critical_stats)}"

    if current_action:
        return f"{current_action.nom} en cours"

    location_name = current_location.nom if current_location else "Lieu inconnu"
    return f"{location_name} - situation stable"


def action_to_json(action):
    return {
        "slug": action.id,
        "name": action.nom,
        "effects": {
            "hp": action.mod_vie,
            "hunger": action.mod_faim,
            "energy": action.mod_energie,
            "hygiene": action.mod_hygiene,
            "mental": action.mod_mental,
            "entertainment": action.mod_divertissement,
            "money": action.mod_argent,
            "food": action.mod_stockage,
        },
        "duration": action.nb_ticks,
    }


def actions_to_json():
    return [action_to_json(action) for action in Action.query.order_by(Action.nom.asc()).all()]


def find_character_or_404(character_id):
    character = db.session.get(Character, character_id)
    if character is None:
        return None, (jsonify({"error": "Character not found"}), 404)
    return character, None


def register_routes(app):
    @app.route("/", methods=["GET"])
    def home():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.route("/api", methods=["GET"])
    def api_home():
        return jsonify({
            "message": "Tamakoshi backend is running",
            "database": app.config["SQLALCHEMY_DATABASE_URI"],
        })

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"})

    @app.route("/api/actions", methods=["GET"])
    def get_actions():
        return jsonify(actions_to_json())

    @app.route("/api/characters", methods=["POST"])
    def create_character():
        data = request.get_json(silent=True)

        if not data:
            return jsonify({"error": "JSON body is required"}), 400

        name = str(data.get("name", "")).strip()
        prompt = str(data.get("prompt", "")).strip()

        if not name or not prompt:
            return jsonify({"error": "name and prompt are required"}), 400

        character = Character(
            name=name[:100],
            prompt=prompt,
            hp=10,
            hunger=80,
            energy=80,
            hygiene=80,
            mental=80,
            entertainment=80,
            money=20,
            food=1,
            current_location_id=1,
            remaining_ticks=0,
            is_alive=True,
            feeling="Je viens de commencer ma vie.",
            last_action="spawn",
        )

        db.session.add(character)
        db.session.flush()
        db.session.add(
            ActionLog(
                character_id=character.id,
                action="spawn",
                message=f"{character.name} commence sa vie.",
            )
        )
        db.session.commit()

        return jsonify(character_to_json(character)), 201

    @app.route("/api/characters", methods=["GET"])
    def get_all_characters():
        characters = Character.query.order_by(Character.created_at.desc()).all()
        return jsonify([character_to_json(character) for character in characters])

    @app.route("/api/characters/<int:character_id>", methods=["GET"])
    def get_character(character_id):
        character, error = find_character_or_404(character_id)
        if error:
            return error
        return jsonify(character_to_json(character))

    @app.route("/api/characters/<int:character_id>", methods=["DELETE"])
    def delete_character(character_id):
        character, error = find_character_or_404(character_id)
        if error:
            return error

        db.session.delete(character)
        db.session.commit()
        return "", 204

    @app.route("/api/characters/<int:character_id>/logs", methods=["GET"])
    def get_character_logs(character_id):
        character, error = find_character_or_404(character_id)
        if error:
            return error

        try:
            limit = min(max(int(request.args.get("limit", 20)), 1), 100)
        except ValueError:
            return jsonify({"error": "limit must be an integer"}), 400

        logs = (
            ActionLog.query.filter_by(character_id=character.id)
            .order_by(ActionLog.created_at.desc())
            .limit(limit)
            .all()
        )

        return jsonify([
            {
                "id": log.id,
                "action": log.action,
                "message": log.message,
                "createdAt": isoformat(log.created_at),
            }
            for log in logs
        ])

    @app.route("/api/characters/<int:character_id>/status", methods=["GET"])
    def get_character_status(character_id):
        character, error = find_character_or_404(character_id)
        if error:
            return error
        return jsonify(character_to_json(character))

    @app.route("/api/characters/<int:character_id>/tick", methods=["POST"])
    def manual_tick(character_id):
        character, error = find_character_or_404(character_id)
        if error:
            return error

        updated_character = run_tick(character)
        return jsonify({
            "message": "Tick executed",
            "character": character_to_json(updated_character),
        })

    @app.route("/api/characters/<int:character_id>/ticks", methods=["POST"])
    def manual_ticks(character_id):
        character, error = find_character_or_404(character_id)
        if error:
            return error

        data = request.get_json(silent=True) or {}
        try:
            count = min(max(int(data.get("count", 1)), 1), 100)
        except (TypeError, ValueError):
            return jsonify({"error": "count must be an integer"}), 400

        for _ in range(count):
            character = run_tick(character)
            if not character.is_alive:
                break

        return jsonify({
            "message": "Ticks executed",
            "character": character_to_json(character),
        })

    @app.route("/<path:path>", methods=["GET"])
    def frontend_assets(path):
        return send_from_directory(FRONTEND_DIR, path)


def ensure_character_columns():
    inspector = inspect(db.engine)
    if not inspector.has_table("characters"):
        return

    existing_columns = {column["name"] for column in inspector.get_columns("characters")}
    missing_columns = {
        "mental": "INTEGER DEFAULT 80",
        "entertainment": "INTEGER DEFAULT 80",
        "current_location_id": "INTEGER DEFAULT 1",
        "current_action_id": "VARCHAR(50)",
        "remaining_ticks": "INTEGER DEFAULT 0",
    }

    for column_name, column_type in missing_columns.items():
        if column_name not in existing_columns:
            db.session.execute(text(f"ALTER TABLE characters ADD COLUMN {column_name} {column_type}"))
            db.session.execute(text(f"UPDATE characters SET {column_name} = 80 WHERE {column_name} IS NULL"))
    db.session.commit()


def seed_world():
    if Location.query.first() or Action.query.first():
        return

    home = Location(id=1, nom="Maison", description="Lieu de repos et de soins.", x_coord=0, y_coord=0)
    work = Location(id=2, nom="Travail", description="Lieu pour gagner de l'argent.", x_coord=2, y_coord=0)
    market = Location(id=3, nom="Marché", description="Lieu pour acheter de la nourriture.", x_coord=1, y_coord=1)
    park = Location(id=4, nom="Parc", description="Lieu pour récupérer mentalement.", x_coord=0, y_coord=2)

    actions = {
        "IDLE": Action(id="IDLE", nom="Attendre", nb_ticks=1, mod_faim=-2, mod_energie=-1, mod_divertissement=-1, type_effet="IDLE"),
        "EAT": Action(id="EAT", nom="Manger", nb_ticks=1, mod_faim=30, mod_energie=-5, mod_stockage=-1, type_effet="EAT"),
        "SLEEP": Action(id="SLEEP", nom="Dormir", nb_ticks=4, mod_faim=-10, mod_energie=25, type_effet="SLEEP"),
        "WASH": Action(id="WASH", nom="Se laver", nb_ticks=1, mod_energie=-5, mod_hygiene=40, type_effet="WASH"),
        "WORK": Action(id="WORK", nom="Travailler", nb_ticks=3, mod_faim=-15, mod_energie=-20, mod_hygiene=-10, mod_mental=-8, mod_divertissement=-8, mod_argent=50, type_effet="WORK"),
        "SHOP": Action(id="SHOP", nom="Acheter à manger", nb_ticks=1, mod_energie=-5, mod_argent=-50, mod_stockage=5, type_effet="SHOP"),
        "REST": Action(id="REST", nom="Se reposer", nb_ticks=2, mod_faim=-5, mod_energie=10, mod_mental=25, mod_divertissement=25, type_effet="REST"),
    }

    home.available_actions.extend([actions["IDLE"], actions["EAT"], actions["SLEEP"], actions["WASH"]])
    work.available_actions.extend([actions["IDLE"], actions["WORK"]])
    market.available_actions.extend([actions["IDLE"], actions["SHOP"]])
    park.available_actions.extend([actions["IDLE"], actions["REST"]])

    db.session.add_all([home, work, market, park, *actions.values()])
    db.session.commit()


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
