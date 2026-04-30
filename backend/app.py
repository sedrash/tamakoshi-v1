import os
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from sqlalchemy import inspect, text

try:
    from .game_engine import run_tick
    from .models import ActionLog, Character, db
except ImportError:
    from game_engine import run_tick
    from models import ActionLog, Character, db

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"
SQLITE_DATABASE_URI = f"sqlite:///{BASE_DIR / 'tamakoshi.db'}"
MARIADB_DATABASE_URI = "mysql+pymysql://tamakoshi_user:password123@localhost/tamakoshi_db"


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

    return app


def isoformat(value):
    return value.isoformat() if value else None

def character_to_json(character):
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
        "lastAction": character.last_action,
        "currentAction": None,
        "actionTicksLeft": 0,
        "lastUpdate": isoformat(character.last_update),
        "createdAt": isoformat(character.created_at),
    }


def actions_to_json():
    return [
        {
            "slug": "eat",
            "name": "Manger",
            "effects": {"hp": 0, "hunger": 30, "energy": -5, "hygiene": 0, "mental": 0, "entertainment": 0, "money": 0, "food": -1},
            "duration": 1,
        },
        {
            "slug": "sleep",
            "name": "Dormir",
            "effects": {"hp": 0, "hunger": -40, "energy": 80, "hygiene": 0, "mental": 0, "entertainment": 0, "money": 0, "food": 0},
            "duration": 1,
        },
        {
            "slug": "work",
            "name": "Travailler",
            "effects": {"hp": 0, "hunger": -15, "energy": -20, "hygiene": -10, "mental": 0, "entertainment": 0, "money": 50, "food": 0},
            "duration": 1,
        },
        {
            "slug": "shop",
            "name": "Courses",
            "effects": {"hp": 0, "hunger": 0, "energy": -5, "hygiene": 0, "mental": 0, "entertainment": 0, "money": -50, "food": 5},
            "duration": 1,
        },
        {
            "slug": "wash",
            "name": "Se laver",
            "effects": {"hp": 0, "hunger": 0, "energy": -5, "hygiene": 40, "mental": 0, "entertainment": 0, "money": 0, "food": 0},
            "duration": 1,
        },
        {
            "slug": "rest",
            "name": "Se reposer",
            "effects": {"hp": 0, "hunger": -5, "energy": 10, "hygiene": 0, "mental": 25, "entertainment": 25, "money": 0, "food": 0},
            "duration": 1,
        },
    ]


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
    }

    for column_name, column_type in missing_columns.items():
        if column_name not in existing_columns:
            db.session.execute(text(f"ALTER TABLE characters ADD COLUMN {column_name} {column_type}"))
            db.session.execute(text(f"UPDATE characters SET {column_name} = 80 WHERE {column_name} IS NULL"))
    db.session.commit()


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
