from datetime import datetime
from models import db, ActionLog


# -------------------------
# TIME SYSTEM
# -------------------------

def calculate_time_passed(character):
    now = datetime.utcnow()
    delta = now - character.last_update
    return delta.total_seconds() / 3600


def decrease_needs(character, hours_passed):
    """
    Natural loss over time.
    The character continues to lose needs even when the player is offline.
    """

    hunger_loss = int(10 * hours_passed)
    energy_loss = int(5 * hours_passed)
    hygiene_loss = int(3 * hours_passed)

    character.hunger = max(character.hunger - hunger_loss, 0)
    character.energy = max(character.energy - energy_loss, 0)
    character.hygiene = max(character.hygiene - hygiene_loss, 0)


# -------------------------
# DECISION SYSTEM
# -------------------------

def choose_action(character):
    """
    Choose the best action according to survival priorities.
    Priority:
    1. Hunger
    2. Energy
    3. Hygiene
    4. Food stock
    5. Money
    6. Idle
    """

    if character.hunger <= 25:
        if character.food > 0:
            return "eat", "hunger_critical"
        if character.money >= 50:
            return "shop", "no_food_but_money"
        return "work", "no_food_no_money"

    if character.energy <= 20:
        return "sleep", "energy_critical"

    if character.hygiene <= 20:
        return "wash", "hygiene_critical"

    if character.food == 0 and character.money >= 50:
        return "shop", "food_stock_empty"

    if character.money <= 10 and character.energy > 30 and character.hunger > 30:
        return "work", "money_low"

    if character.hunger <= 45 and character.food > 0:
        return "eat", "hunger_low"

    if character.energy <= 40:
        return "sleep", "energy_low"

    return "idle", "no_urgent_need"


# -------------------------
# BUSINESS LOGIC
# -------------------------

def apply_action(character, action):
    """
    Apply action effects on character stats.
    """

    if action == "eat":
        if character.food <= 0:
            return "failed", f"{character.name} voulait manger, mais il n’avait plus de nourriture."

        character.hunger = min(character.hunger + 30, 100)
        character.food -= 1
        character.energy = max(character.energy - 5, 0)

        return "eat", f"{character.name} a mangé pour récupérer de la satiété."

    if action == "sleep":
        character.energy = min(character.energy + 80, 100)
        character.hunger = max(character.hunger - 40, 0)

        return "sleep", f"{character.name} a dormi pour récupérer de l’énergie."

    if action == "work":
        if character.energy <= 10:
            return "failed", f"{character.name} était trop épuisé pour travailler."

        character.money += 50
        character.energy = max(character.energy - 20, 0)
        character.hunger = max(character.hunger - 15, 0)
        character.hygiene = max(character.hygiene - 10, 0)

        return "work", f"{character.name} a travaillé pour gagner de l’argent."

    if action == "shop":
        if character.money < 50:
            return "failed", f"{character.name} voulait faire les courses, mais il n’avait pas assez d’argent."

        character.food += 5
        character.money -= 50
        character.energy = max(character.energy - 5, 0)

        return "shop", f"{character.name} a fait les courses et a acheté 5 repas."

    if action == "wash":
        character.hygiene = min(character.hygiene + 40, 100)
        character.energy = max(character.energy - 5, 0)

        return "wash", f"{character.name} s’est lavé pour améliorer son hygiène."

    character.hunger = max(character.hunger - 2, 0)
    character.energy = max(character.energy - 1, 0)

    return "idle", f"{character.name} attend et continue sa journée."


# -------------------------
# DEATH SYSTEM
# -------------------------

def check_death(character):
    """
    HP is the final life stat.
    If a vital need reaches 0, HP decreases.
    If HP reaches 0, the character dies.
    """

    if character.hunger <= 0:
        character.hp = max(character.hp - 1, 0)

    if character.energy <= 0:
        character.hp = max(character.hp - 1, 0)

    if character.hygiene <= 0:
        character.hp = max(character.hp - 1, 0)

    if character.hp <= 0:
        character.is_alive = False

        if character.hunger <= 0:
            character.death_reason = "mort de faim"
        elif character.energy <= 0:
            character.death_reason = "mort d’épuisement"
        elif character.hygiene <= 0:
            character.death_reason = "mort à cause du manque d’hygiène"
        else:
            character.death_reason = "mort inconnue"


# -------------------------
# FEELING SYSTEM
# -------------------------

def generate_feeling(character):
    if not character.is_alive:
        return character.death_reason

    if character.hp <= 3:
        return "Je me sens très faible..."

    if character.hunger <= 25:
        return "J’ai très faim..."
    if character.energy <= 20:
        return "Je suis épuisé..."
    if character.hygiene <= 20:
        return "Je ne me sens vraiment pas propre..."

    if character.food == 0:
        return "Je n’ai plus rien à manger..."
    if character.money <= 10:
        return "Je n’ai presque plus d’argent..."

    if character.hunger <= 45:
        return "Je commence à avoir faim..."
    if character.energy <= 40:
        return "Je commence à être fatigué..."

    return "Je me sens plutôt bien."


# -------------------------
# LOG SYSTEM
# -------------------------

def add_log(character, action, message, reason=None):
    if reason:
        full_message = f"{message} Raison : {reason}."
    else:
        full_message = message

    log = ActionLog(
        character_id=character.id,
        action=action,
        message=full_message
    )

    db.session.add(log)


# -------------------------
# GAME ENGINE
# -------------------------

def run_tick(character):
    """
    Main simulation function.
    This is the Game Engine.
    """

    if not character.is_alive:
        return character

    hours_passed = calculate_time_passed(character)

    decrease_needs(character, hours_passed)

    check_death(character)

    if not character.is_alive:
        character.feeling = generate_feeling(character)
        character.last_action = "death"
        character.last_update = datetime.utcnow()

        add_log(character, "death", character.death_reason)

        db.session.commit()
        return character

    action, reason = choose_action(character)

    final_action, message = apply_action(character, action)

    check_death(character)

    character.last_action = final_action
    character.feeling = generate_feeling(character)
    character.last_update = datetime.utcnow()

    add_log(character, final_action, message, reason)

    db.session.commit()

    return character