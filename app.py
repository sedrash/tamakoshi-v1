from flask import Flask, request, jsonify
from flask_cors import CORS

from models import db, Character, ActionLog
from game_engine import run_tick

app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://tamakoshi_user:password123@localhost/tamakoshi_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


def character_to_json(character):
    return {
        "id": character.id,
        "name": character.name,
        "prompt": character.prompt,
        "hp": character.hp,
        "hunger": character.hunger,
        "energy": character.energy,
        "hygiene": character.hygiene,
        "money": character.money,
        "food": character.food,
        "isAlive": character.is_alive,
        "deathReason": character.death_reason,
        "feeling": character.feeling,
        "lastAction": character.last_action,
        "lastUpdate": character.last_update.isoformat(),
        "createdAt": character.created_at.isoformat()
    }


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Tamakoshi backend is running"
    })


@app.route("/characters", methods=["POST"])
def create_character():
    data = request.get_json()

    if not data:
        return jsonify({"error": "JSON body is required"}), 400

    name = data.get("name")
    prompt = data.get("prompt")

    if not name or not prompt:
        return jsonify({"error": "name and prompt are required"}), 400

    character = Character(
        name=name,
        prompt=prompt,
        hp=10,
        hunger=80,
        energy=80,
        hygiene=80,
        money=20,
        food=1,
        is_alive=True,
        feeling="Je viens de commencer ma vie."
    )

    db.session.add(character)
    db.session.commit()

    return jsonify(character_to_json(character)), 201


@app.route("/characters", methods=["GET"])
def get_all_characters():
    characters = Character.query.all()
    return jsonify([character_to_json(character) for character in characters])


@app.route("/characters/<int:character_id>", methods=["GET"])
def get_character(character_id):
    character = Character.query.get(character_id)

    if not character:
        return jsonify({"error": "Character not found"}), 404

    updated_character = run_tick(character)

    return jsonify(character_to_json(updated_character))


@app.route("/characters/<int:character_id>/logs", methods=["GET"])
def get_character_logs(character_id):
    character = Character.query.get(character_id)

    if not character:
        return jsonify({"error": "Character not found"}), 404

    logs = ActionLog.query.filter_by(character_id=character_id).order_by(ActionLog.created_at.desc()).all()

    return jsonify([
        {
            "id": log.id,
            "action": log.action,
            "message": log.message,
            "createdAt": log.created_at.isoformat()
        }
        for log in logs
    ])


@app.route("/characters/<int:character_id>/status", methods=["GET"])
def get_character_status(character_id):
    character = Character.query.get(character_id)

    if not character:
        return jsonify({"error": "Character not found"}), 404

    return jsonify({
        "id": character.id,
        "name": character.name,
        "isAlive": character.is_alive,
        "deathReason": character.death_reason,
        "feeling": character.feeling,
        "lastAction": character.last_action
    })


@app.route("/characters/<int:character_id>/tick", methods=["POST"])
def manual_tick(character_id):
    character = Character.query.get(character_id)

    if not character:
        return jsonify({"error": "Character not found"}), 404

    updated_character = run_tick(character)

    return jsonify({
        "message": "Tick executed",
        "character": character_to_json(updated_character)
    })


if __name__ == "__main__":
    app.run(debug=True)