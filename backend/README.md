# Backend Tamakoshi

Backend Flask du projet Tamakoshi. Il gere l'API, les modeles SQLAlchemy, le seed des lieux/actions, le moteur de jeu, la decision OpenAI et les logs.

## Fichiers

```text
backend/
|-- app.py              # Routes Flask et configuration
|-- game_engine.py      # Simulation, decision IA, fallback local
|-- models.py           # Tables SQLAlchemy
|-- requirements.txt    # Dependances Python
`-- README.md
```

## Variables d'environnement

Le backend charge automatiquement `.env` depuis la racine du projet.

```env
OPENAI_API_KEY=votre_cle_openai
TAMAKOSHI_DATABASE=sqlite
```

ou avec MariaDB :

```env
OPENAI_API_KEY=votre_cle_openai
DATABASE_URL=mysql+pymysql://tamakoshi_user:password123@localhost/tamakoshi_db
```

Si `OPENAI_API_KEY` est absente, le moteur utilise un fallback local.

## Base de donnees

MariaDB est prevue pour le projet final. SQLite sert au test local.

Creation MariaDB :

```sql
CREATE DATABASE tamakoshi_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'tamakoshi_user'@'localhost' IDENTIFIED BY 'password123';
GRANT ALL PRIVILEGES ON tamakoshi_db.* TO 'tamakoshi_user'@'localhost';
FLUSH PRIVILEGES;
```

## Lancer

Depuis la racine :

```powershell
venv\Scripts\python.exe backend\app.py
```

URL :

```text
http://127.0.0.1:5000
```

## Endpoints

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
