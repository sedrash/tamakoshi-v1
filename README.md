# Tamakoshi V1

## Description du projet

Tamakoshi est un jeu de simulation autonome inspiré du Tamagotchi.

Le joueur crée un personnage avec un prompt initial qui définit sa personnalité et sa situation de départ.

Ensuite, le joueur n’intervient plus directement.

Le personnage vit seul et prend ses propres décisions selon ses besoins.

Le frontend sert uniquement à observer l’état du personnage.

Le backend gère :

* les statistiques du personnage
* la logique métier de base
* les actions automatiques
* la sauvegarde en base de données
* l’historique des actions

L’objectif du jeu est simple :

**survivre le plus longtemps possible**

Il n’y a pas de victoire, seulement la survie.

---

## Architecture du projet

```text
Frontend
↓
API Flask
↓
MariaDB (Base de données)
↓
Logique métier / Actions automatiques
```

Le projet contient :

* un backend Flask
* une base de données MariaDB
* une logique métier pour les actions du personnage
* un système de logs pour suivre les décisions
* une structure prête pour accueillir le frontend

---

## Structure du projet

```text
tamakoshi-v1/
│
├── backend/
│   ├── app.py
│   ├── models.py
│   ├── game_engine.py
│   ├── requirements.txt
│   └── README.md
│
├── frontend/
│   └── (à compléter)
│
├── docs/
│   └── (diagrammes / documentation)
│
├── .gitignore
│
└── venv/ (non push)
```

---

## Base de données

### Table : characters

Cette table stocke l’état actuel du personnage.

### Champs principaux :

* id
* name
* prompt
* hp
* hunger
* energy
* hygiene
* money
* food
* is_alive
* death_reason
* feeling
* last_action
* last_update
* created_at

Exemples :

* faim
* énergie
* argent
* nourriture
* hygiène

Le champ `last_update` permet de gérer l’évolution du personnage dans le temps.

---

### Table : action_logs

Cette table stocke l’historique des actions du personnage.

### Champs principaux :

* id
* character_id
* action
* message
* created_at

Exemples :

* Lina a mangé
* Lina a travaillé
* Lina a dormi

Cela permet de suivre toutes les décisions automatiques.

---

## API Endpoints

| Method | Endpoint               | Description                    |
| ------ | ---------------------- | ------------------------------ |
| GET    | /                      | Test serveur                   |
| POST   | /characters            | Créer un personnage            |
| GET    | /characters            | Voir tous les personnages      |
| GET    | /characters/:id        | Voir un personnage             |
| GET    | /characters/:id/logs   | Voir les 10 derniers logs      |
| GET    | /characters/:id/status | Voir le statut rapide          |
| POST   | /characters/:id/tick   | Forcer une simulation manuelle |

---

## Technologies utilisées

* Python
* Flask
* Flask-SQLAlchemy
* MariaDB
* PyMySQL
* Thunder Client
* DBeaver
* VS Code

---

## Installation

### 1. Cloner le projet

```bash
git clone https://github.com/sedrash/tamakoshi-v1.git
cd tamakoshi-v1
```

---

### 2. Créer l’environnement virtuel

```bash
python -m venv venv
```

---

### 3. Activer l’environnement virtuel

### Windows PowerShell

```bash
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

### Windows CMD

```bash
venv\Scripts\activate.bat
```

---

### 4. Installer les dépendances

```bash
cd backend
pip install -r requirements.txt
```

---

### 5. Configurer MariaDB

Créer la base :

```sql
CREATE DATABASE tamakoshi_db;
```

Créer l’utilisateur :

```sql
CREATE USER 'tamakoshi_user'@'localhost' IDENTIFIED BY 'password123';
GRANT ALL PRIVILEGES ON tamakoshi_db.* TO 'tamakoshi_user'@'localhost';
FLUSH PRIVILEGES;
```

---

### 6. Lancer le backend

```bash
python app.py
```

Le serveur sera disponible sur :

```text
http://127.0.0.1:5000
```

---

## Tests API

Les tests peuvent être réalisés avec :

* Thunder Client
* Postman
* navigateur pour les GET simples

Exemple :

### Création d’un personnage

```http
POST /characters
```

Body JSON :

```json
{
  "name": "Lina",
  "prompt": "Lina est prudente et veut survivre longtemps."
}
```

---

## Mon rôle dans le projet

Je me suis occupé principalement de la partie backend.

Mon travail :

* création de l’API Flask
* connexion avec MariaDB
* structure de la base de données
* endpoints REST
* persistance des personnages
* système de logs
* préparation de la logique métier

Le moteur de simulation complet sera amélioré avec le reste de l’équipe dans les prochaines versions.

---

## Objectif de la V1

Cette première version permet de valider :

* l’architecture backend
* la communication API ↔ BDD
* la persistance des données
* la structure des actions automatiques

Cette base servira pour la suite du développement du projet.
