import json
import os
from datetime import datetime

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from .models import Action, ActionLog, Location, db
except ImportError:
    from models import Action, ActionLog, Location, db


SYSTEM_PROMPT_BASE = """
### TON EXISTENCE
Tu es une entité autonome dans un monde dont tu ne connais pas les lois physiques.
Tu connais les noms des actions possibles, mais tu ignores leurs conséquences exactes sur tes statistiques.

### TA MISSION
1. Écoute scrupuleusement la PERSONNALITÉ et les STRATÉGIES dictées par le Joueur.
2. Observe l'historique de tes actions passées pour déduire ce qui est efficace.
3. Si tu échoues ou si tes stats baissent, analyse pourquoi dans ton monologue pour t'améliorer au tour suivant.

### FORMAT DE RÉPONSE STRICT
Réponds uniquement en JSON valide :
{
  "action_id": "ID_CHOISI",
  "inner_monologue": "Ton analyse de la situation et ton intention, en 2 phrases maximum."
}
"""


def clamp(value, minimum=0, maximum=100):
    return max(minimum, min(value, maximum))


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    return OpenAI(api_key=api_key)


def calculate_time_passed(character):
    now = datetime.utcnow()
    delta = now - character.last_update
    return delta.total_seconds() / 3600


def decrease_needs(character, hours_passed):
    character.hunger = clamp(character.hunger - int(10 * hours_passed))
    character.energy = clamp(character.energy - int(5 * hours_passed))
    character.hygiene = clamp(character.hygiene - int(3 * hours_passed))
    character.mental = clamp(character.mental - int(2 * hours_passed))
    character.entertainment = clamp(character.entertainment - int(2 * hours_passed))


def calculate_mental_state(character):
    return (character.hunger + character.energy + character.hygiene) / 3


def build_world_description():
    lines = []
    for location in Location.query.order_by(Location.id.asc()).all():
        action_names = [action.nom for action in location.available_actions]
        lines.append(
            f"- {location.nom} (ID: {location.id}) : "
            f"On peut y faire : {', '.join(action_names) or 'aucune action'}"
        )
    return "\n".join(lines)


def fallback_decision(character, options):
    option_ids = {option["id"] for option in options}

    preferred = []
    if character.hunger <= 25:
        preferred = ["EAT", "SHOP", "WORK"]
    elif character.energy <= 20:
        preferred = ["SLEEP"]
    elif character.hygiene <= 20:
        preferred = ["WASH"]
    elif character.food == 0 and character.money >= 50:
        preferred = ["SHOP"]
    elif character.money <= 10 and character.energy > 30 and character.hunger > 30:
        preferred = ["WORK"]
    elif character.hunger <= 45:
        preferred = ["EAT"]
    elif character.energy <= 40:
        preferred = ["SLEEP"]
    elif character.mental <= 20 or character.entertainment <= 20:
        preferred = ["REST"]
    else:
        preferred = ["IDLE"]

    for action_id in preferred:
        if action_id in option_ids:
            return {
                "action_id": action_id,
                "inner_monologue": "Je choisis selon mes besoins les plus urgents.",
            }

    for action_id in preferred:
        for option_id in option_ids:
            if option_id.startswith("MOVE_") and location_has_action(option_id.replace("MOVE_", ""), action_id):
                return {
                    "action_id": option_id,
                    "inner_monologue": "Je dois me déplacer pour faire l'action qui m'aidera.",
                }

    return {
        "action_id": "IDLE" if "IDLE" in option_ids else next(iter(option_ids), None),
        "inner_monologue": "Je vais attendre un peu et observer ce monde.",
    }


def location_has_action(location_id, action_id):
    location = db.session.get(Location, int(location_id))
    if not location:
        return False
    return any(action.id == action_id for action in location.available_actions)


def get_ai_decision(character, options):
    client = get_openai_client()
    if client is None:
        return fallback_decision(character, options)

    current_location = db.session.get(Location, character.current_location_id)
    mental_state = "LUCIDE"
    if character.energy < 20 or character.hunger < 20 or calculate_mental_state(character) < 30:
        mental_state = "CRITIQUE (tes pensées sont confuses, priorise ta survie)"

    system_message = f"""
Tu es l'esprit de {character.name}, un agent autonome.
Ton état mental actuel est : {mental_state}.

CARTE DU MONDE :
{build_world_description()}

RÈGLES DE DÉPLACEMENT :
- Pour faire une action, tu dois être dans le lieu correspondant.
- Si l'action souhaitée n'est pas disponible ici, tu dois choisir un déplacement MOVE_ID.
- Un déplacement coûte 1 tick et 2 énergie.

OBJECTIF :
Respecter les consignes du joueur tout en restant en vie.
Réponds avec un monologue court, lisible dans une interface de jeu.
"""

    user_context = {
        "consignes_du_joueur": character.prompt,
        "lieu_actuel": current_location.nom if current_location else None,
        "stats_actuelles": {
            "vie": f"{character.hp}/10",
            "faim": f"{character.hunger}/100",
            "energie": f"{character.energy}/100",
            "hygiene": f"{character.hygiene}/100",
            "mental": f"{character.mental}/100",
            "loisir": f"{character.entertainment}/100",
            "argent": character.money,
            "nourriture": character.food,
        },
        "choix_possibles": options,
    }

    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-5-nano"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_BASE + "\n" + system_message},
                {"role": "user", "content": json.dumps(user_context, ensure_ascii=False)},
            ],
            response_format={"type": "json_object"},
        )
        decision = json.loads(response.choices[0].message.content)
    except Exception as exc:
        print(f"Erreur OpenAI : {exc}")
        return fallback_decision(character, options)

    action_id = decision.get("action_id")
    if action_id not in {option["id"] for option in options}:
        return fallback_decision(character, options)

    return {
        "action_id": action_id,
        "inner_monologue": decision.get("inner_monologue", "Je prends une décision."),
    }


def add_log(character, action, message):
    db.session.add(
        ActionLog(
            character_id=character.id,
            action=action or "idle",
            message=message,
        )
    )


def check_death(character):
    if character.hunger <= 0:
        character.hp -= 2
    if character.energy <= 0:
        character.hp -= 1
    if character.hygiene <= 20:
        character.hp -= 1
    if character.mental <= 0:
        character.hp -= 1

    character.hp = max(character.hp, 0)

    if character.hp <= 0:
        character.is_alive = False
        character.death_reason = "Épuisement général des fonctions vitales."
        return True
    return False


def apply_action_effect(character, action):
    character.hunger = clamp(character.hunger + action.mod_faim)
    character.energy = clamp(character.energy + action.mod_energie)
    character.hygiene = clamp(character.hygiene + action.mod_hygiene)
    character.mental = clamp(character.mental + action.mod_mental)
    character.entertainment = clamp(character.entertainment + action.mod_divertissement)
    character.hp = clamp(character.hp + action.mod_vie, 0, 10)
    character.money = max(0, int(character.money + action.mod_argent))
    character.food = max(0, int(character.food + action.mod_stockage))


def get_current_options(character):
    current_location = db.session.get(Location, character.current_location_id)
    if current_location is None:
        current_location = Location.query.order_by(Location.id.asc()).first()
        if current_location:
            character.current_location_id = current_location.id

    options = []
    if current_location:
        options.extend(
            {"id": action.id, "nom": action.nom}
            for action in current_location.available_actions
        )

    for location in Location.query.order_by(Location.id.asc()).all():
        if location.id != character.current_location_id:
            options.append({"id": f"MOVE_{location.id}", "nom": f"Aller à : {location.nom}"})

    return options


def run_tick(character):
    if not character.is_alive:
        return character

    now = datetime.utcnow()
    decrease_needs(character, calculate_time_passed(character))

    if character.remaining_ticks and character.remaining_ticks > 0:
        if character.current_action_id and character.current_action_id.startswith("MOVE_"):
            character.energy = max(0, character.energy - 2)
            character.remaining_ticks -= 1
            message = "En déplacement..."
            log_action = "move"
        else:
            action = db.session.get(Action, character.current_action_id)
            if action:
                apply_action_effect(character, action)
                character.remaining_ticks -= 1
                message = f"{character.name} fait l'action : {action.nom}. Ticks restants : {character.remaining_ticks}"
                log_action = action.nom
            else:
                character.remaining_ticks = 0
                message = "Action inconnue."
                log_action = "unknown"

        if character.remaining_ticks <= 0:
            character.current_action_id = None

        character.last_action = log_action
        add_log(character, log_action, message)
    else:
        options = get_current_options(character)
        decision = get_ai_decision(character, options)
        choice = decision.get("action_id")
        character.feeling = decision.get("inner_monologue")

        if choice and choice.startswith("MOVE_"):
            destination_id = int(choice.replace("MOVE_", ""))
            destination = db.session.get(Location, destination_id)
            character.current_location_id = destination_id
            character.current_action_id = choice
            character.remaining_ticks = 1
            character.last_action = f"Aller à {destination.nom if destination else destination_id}"
            add_log(character, "move", f"{character.name} se déplace vers {destination.nom if destination else destination_id}.")
            return run_tick(character)

        action = db.session.get(Action, choice)
        if action:
            character.current_action_id = action.id
            character.remaining_ticks = max(action.nb_ticks, 1)
            character.last_action = action.nom
            add_log(character, action.nom, f"{character.name} décide de faire : {action.nom}.")
            return run_tick(character)

        character.last_action = "idle"
        add_log(character, "idle", f"{character.name} attend et observe son environnement.")

    if check_death(character):
        character.last_action = "death"
        character.feeling = character.death_reason
        add_log(character, "death", character.death_reason)

    character.last_update = now
    db.session.commit()
    return character
