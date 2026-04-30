# Tamakoshi V1

Tamakoshi est une simulation autonome inspiree du Tamagotchi. Le joueur cree un personnage avec un nom et un prompt de depart. Ensuite, le personnage evolue seul selon ses besoins, son lieu actuel, les actions disponibles et, si une cle est configuree, une decision OpenAI.

Le projet contient une interface web, une API Flask, une base SQLAlchemy et un moteur de jeu avec lieux, actions, logs et ticks.

## Fonctionnalites

- Creation de personnages avec un prompt de personnalite.
- Tableau de bord avec vie, faim, energie, hygiene, mental, loisir, argent et nourriture.
- Lieux et actions disponibles selon la position du personnage.
- Decisions autonomes via OpenAI si `OPENAI_API_KEY` est configuree.
- Fallback local si OpenAI n'est pas disponible.
- Actions multi-ticks et deplacements entre lieux.
- Journal des actions en base de donnees.
- Persistance avec MariaDB ou SQLite local.

## Architecture

```text
Navigateur
-> Frontend statique
-> API Flask
-> Moteur de jeu / OpenAI
-> SQLAlchemy
-> MariaDB ou SQLite
```

## Structure

```text
tamakoshi-v1/
|-- backend/
|   |-- app.py              # API Flask, routes, seed des lieux/actions
|   |-- game_engine.py      # Moteur de simulation et decision OpenAI
|   |-- models.py           # Modeles SQLAlchemy
|   |-- requirements.txt    # Dependances backend
|   `-- README.md           # Documentation backend
|-- frontend/
|   |-- index.html          # Interface web
|   |-- app.js              # Appels API et rendu dynamique
|   `-- styles.css          # Style de l'interface
|-- docs/
|-- .env.example            # Exemple de variables d'environnement
|-- .gitignore
`-- README.md
```

## Donnees stockees

Les donnees sont definies dans `backend/models.py`.

### characters

Stocke l'etat actuel du personnage.

```text
id, name, prompt, hp, hunger, energy, hygiene, mental, entertainment,
money, food, is_alive, death_reason, feeling, last_action,
current_location_id, current_action_id, remaining_ticks,
last_update, created_at
```

### locations

Stocke les lieux du monde.

```text
id, nom, description, x_coord, y_coord
```

### actions

Stocke les actions possibles et leurs effets.

```text
id, nom, nb_ticks, mod_energie, mod_argent, mod_hygiene,
mod_mental, mod_divertissement, mod_vie, mod_faim,
mod_stockage, type_effet
```

### location_actions

Associe les actions aux lieux ou elles sont disponibles.

```text
id, location_id, action_id
```

### action_logs

Stocke l'historique des decisions et actions du personnage.

```text
id, character_id, action, message, created_at
```

## Installation

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

## Configuration

Copier `.env.example` vers `.env`, puis remplir les variables utiles.

Exemple SQLite local :

```env
OPENAI_API_KEY=votre_cle_openai
TAMAKOSHI_DATABASE=sqlite
```

Exemple MariaDB :

```env
OPENAI_API_KEY=votre_cle_openai
DATABASE_URL=mysql+pymysql://tamakoshi_user:password123@localhost/tamakoshi_db
```

La vraie cle OpenAI doit rester dans `.env`. Elle ne doit jamais etre mise dans `.env.example` ni poussee sur GitHub.

## MariaDB

```sql
CREATE DATABASE tamakoshi_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'tamakoshi_user'@'localhost' IDENTIFIED BY 'password123';
GRANT ALL PRIVILEGES ON tamakoshi_db.* TO 'tamakoshi_user'@'localhost';
FLUSH PRIVILEGES;
```

## Lancer le projet

Depuis la racine :

```powershell
venv\Scripts\python.exe backend\app.py
```

Puis ouvrir :

```text
http://127.0.0.1:5000
```

## API

```text
GET    /api/health
GET    /api/actions
POST   /api/characters
GET    /api/characters
GET    /api/characters/<id>
DELETE /api/characters/<id>
GET    /api/characters/<id>/logs
GET    /api/characters/<id>/status
POST   /api/characters/<id>/tick
POST   /api/characters/<id>/ticks
```

## Notes de rendu

Le projet final contient le backend, le frontend, la connexion a la base de donnees, l'integration OpenAI, les lieux, les actions, les logs et une documentation de lancement. Si OpenAI n'est pas configure, le jeu reste utilisable grace au fallback local.
