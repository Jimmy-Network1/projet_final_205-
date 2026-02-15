#!/bin/bash
# build.sh
echo "🚀 Démarrage du build..."

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Installation des dépendances
echo "📦 Installation des dépendances..."
pip install -r requirements.txt

# Collecte des fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo "✅ Build terminé avec succès!"
