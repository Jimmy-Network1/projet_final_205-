# Projet Final 205 — AutoMarket (Django)

Plateforme web de vente/achat de voitures (annonces, favoris, réservations, notifications, etc.) développée avec Django.

## Code source
- Repo GitHub : `https://github.com/Jimmy-Network1/projet_final_205-.git`

## Démo en ligne (si déployé)
- Exemple : `https://vente-voitures.onrender.com`
- Note (Render plan gratuit) : après quelques minutes d’inactivité, le service peut “sleep”. Le premier chargement peut alors prendre 10–30s.

## Prérequis
- Python 3.10+ (recommandé : 3.10.x comme sur Render)
- (Optionnel) Docker + Docker Compose (pour PostgreSQL)

## Installation locale (simple, SQLite)
```bash
git clone https://github.com/Jimmy-Network1/projet_final_205-.git
cd projet_final_205-

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```
Ouvre `http://127.0.0.1:8000/`.

## Installation locale (PostgreSQL via Docker)
Le projet supporte SQLite par défaut, mais peut imposer PostgreSQL via `REQUIRE_POSTGRES=true`.

```bash
docker compose -f ops/compose.yml up -d db
cp .env.example .env
```

Dans `.env`, configure par exemple :
```bash
DATABASE_URL=postgres://vente_voitures_user:vente_voitures_password@localhost:5432/vente_voitures
REQUIRE_POSTGRES=true
DEBUG=true
```

Puis :
```bash
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

### Accès web à la base (pgAdmin)
Le `docker compose` inclut pgAdmin :

- Lancer : `docker compose -f ops/compose.yml up -d pgadmin`
- Ouvrir : http://localhost:5050
- Connexion : email `admin@local.test`, mot de passe `admin123`
- Ajouter un serveur : hôte `db`, port `5432`, utilisateur `vente_voitures_user`, mot de passe `vente_voitures_password`, base `vente_voitures`.

## Données de démo / comptes
Pour générer des comptes et des données de démo :
```bash
python manage.py create_demo_data
python manage.py generate_demo_images
```

Comptes de démo (uniquement pour développement, non créés automatiquement) :
- `admin / Admin123!`
- `vendeur / Vendeur123!`
- `acheteur / Acheteur123!`

## Admin Django
Créer (ou mettre à jour) un superuser :
```bash
python manage.py ensure_superuser --username admin --email admin@local.test --password Admin123!
```
Puis ouvre `http://127.0.0.1:8000/admin/`.

## Variables d’environnement (résumé)
- `SECRET_KEY` : obligatoire en production
- `DEBUG` : `true/false`
- `DATABASE_URL` : Postgres (`postgres://...`) ou SQLite (par défaut si absent)
- `REQUIRE_POSTGRES` : si `true`, Django refuse SQLite
- `RESERVATION_TTL_HOURS` : délai d’expiration des demandes d’achat en attente
- `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` : domaines autorisés (Render utilise aussi `RENDER_EXTERNAL_HOSTNAME`)

## Déploiement Render
Le dépôt inclut `render.yaml` et les scripts dans `ops/` :
- `ops/build.sh` installe les dépendances et fait `collectstatic`
- `ops/start.sh` applique les migrations, prépare les médias et lance Gunicorn sur `$PORT`

Sur Render, crée un “Web Service” à partir du repo, et un PostgreSQL (ou laisse `render.yaml` le décrire si tu utilises l’Infra-as-Code).

Le `render.yaml` inclut aussi un job cron qui exécute `python manage.py expire_purchase_requests` chaque heure pour libérer les réservations expirées.
