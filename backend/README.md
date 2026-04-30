# Backend Tamakoshi

API Flask + SQLAlchemy pour le jeu Tamakoshi.

## Base de donnees

Par defaut, le backend utilise MariaDB avec PyMySQL :

```text
mysql+pymysql://tamakoshi_user:password123@localhost/tamakoshi_db
```

Tu peux remplacer cette configuration avec la variable d'environnement `DATABASE_URL`.

Exemple PowerShell :

```powershell
$env:DATABASE_URL="mysql+pymysql://tamakoshi_user:password123@localhost/tamakoshi_db"
python backend/app.py
```

Pour tester sans MariaDB :

```powershell
$env:TAMAKOSHI_DATABASE="sqlite"
python backend/app.py
```

## Creation MariaDB

```sql
CREATE DATABASE tamakoshi_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'tamakoshi_user'@'localhost' IDENTIFIED BY 'password123';
GRANT ALL PRIVILEGES ON tamakoshi_db.* TO 'tamakoshi_user'@'localhost';
FLUSH PRIVILEGES;
```

## Lancer

Depuis la racine du projet :

```powershell
venv\Scripts\python.exe backend\app.py
```

Le frontend est servi par Flask sur :

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
