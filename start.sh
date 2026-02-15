#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Starting AutoMarket..."

echo "🔄 Applying migrations..."
python manage.py migrate --noinput

echo "🖼️ Ensuring default media..."
python manage.py ensure_default_media || true

if [[ "${ENSURE_SUPERUSER:-}" == "true" ]]; then
  echo "👤 Ensuring superuser..."
  python manage.py ensure_superuser \
    --username "${ADMIN_USERNAME:-admin}" \
    --email "${ADMIN_EMAIL:-admin@example.com}" \
    ${ADMIN_PASSWORD:+--password "${ADMIN_PASSWORD}"} \
    --print-password || true
fi

if [[ "${SEED_DEMO_DATA:-}" == "true" ]]; then
  echo "📊 Seeding demo data..."
  python manage.py create_demo_data || true

  echo "🧩 Generating demo images..."
  python manage.py generate_demo_images || true
else
  echo "ℹ️ Skipping demo seed (set SEED_DEMO_DATA=true to enable)."
fi

echo "🌐 Starting gunicorn on :${PORT:-8000} ..."
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --log-file -
