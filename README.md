# Tamakoshi V1

Tamakoshi est une simulation autonome inspirée du Tamagotchi. Le joueur crée un personnage avec un nom et un prompt de départ, puis le personnage évolue seul selon ses besoins : faim, énergie, hygiène, mental, loisir, argent et nourriture.

L'objectif de cette V1 est de poser une base fonctionnelle avec un frontend connecté à une API Flask, une persistance en base de données, un système de logs et une décision autonome basée sur OpenAI quand une clé API est configurée.

## Architecture

```text
Navigateur
-> Frontend statique
-> API Flask
-> Moteur de décision OpenAI ou fallback local
-> SQLAlchemy
-> MariaDB ou SQLite local
```

MariaDB est la base prévue pour le projet. SQLite sert uniquement à tester facilement en local quand MariaDB n'est pas disponible.

## Structure du projet

```text
tamakoshi-v1/
|-- backend/
|   |-- app.py              # API Flask et routes
|   |-- models.py           # Modèles SQLAlchemy
|   |-- game_engine.py      # Moteur de simulation
|   |-- requirements.txt    # Dépendances Python
|   |-- README.md           # Notes backend
|   `-- tamakoshi.db        # Base SQLite locale, ignorée par Git
|-- frontend/
|   |-- index.html          # Interface utilisateur
|   |-- app.js              # Appels API et logique côté navigateur
|   `-- styles.css          # Design
|-- docs/
|-- .env.example
|-- .gitignore
`-- README.md
```

## Stockage des données

Les données sont stockées en base via SQLAlchemy.

Table `characters` :

```text
id
name
prompt
hp
hunger
energy
hygiene
mental
entertainment
money
food
is_alive
death_reason
feeling
last_action
last_update
created_at
```

Table `action_logs` :

```text
id
character_id
action
message
created_at
```

Les personnages, leurs statistiques et l'historique des actions sont donc conservés même après un rechargement de la page.

Table `locations` :

```text
id
nom
description
x_coord
y_coord
```

Table `actions` :

```text
id
nom
nb_ticks
mod_energie
mod_argent
mod_hygiene
mod_mental
mod_divertissement
mod_vie
mod_faim
mod_stockage
type_effet
```

Table `location_actions` :

```text
id
location_id
action_id
```

Ces tables permettent au personnage d'être dans un lieu, de voir les actions disponibles autour de lui, puis de choisir une action ou un déplacement.

## Installation

Créer et activer l'environnement virtuel :

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

Installer les dépendances :

```powershell
pip install -r backend\requirements.txt
```

## Configuration MariaDB

Créer la base et l'utilisateur :

```sql
CREATE DATABASE tamakoshi_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'tamakoshi_user'@'localhost' IDENTIFIED BY 'password123';
GRANT ALL PRIVILEGES ON tamakoshi_db.* TO 'tamakoshi_user'@'localhost';
FLUSH PRIVILEGES;
```

Lancer avec MariaDB :

```powershell
$env:DATABASE_URL="mysql+pymysql://tamakoshi_user:password123@localhost/tamakoshi_db"
venv\Scripts\python.exe backend\app.py
```

Activer la décision OpenAI :

```powershell
$env:OPENAI_API_KEY="votre_cle_openai"
```

Si `OPENAI_API_KEY` n'est pas définie, le jeu continue avec un fallback local basé sur les besoins du personnage.

Lancer en mode SQLite local :

```powershell
$env:TAMAKOSHI_DATABASE="sqlite"
venv\Scripts\python.exe backend\app.py
```

Application :

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


### Notes

Le projet est maintenant lançable depuis la racine avec `backend/app.py`. Le frontend est servi par Flask et communique avec l'API via `/api`. Les données sont stockées soit dans MariaDB, soit dans `backend/tamakoshi.db` en mode SQLite local.
