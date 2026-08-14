#!/usr/bin/env sh
# Apply migrations (and, when SEED_DEMO=1, load demo data) before handing off to
# the container command. Idempotent, so it is safe on every restart.
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

if [ "${SEED_DEMO:-0}" = "1" ]; then
    echo "Seeding demo data..."
    python manage.py seed_demo
fi

exec "$@"
