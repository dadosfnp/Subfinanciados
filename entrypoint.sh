#!/usr/bin/env sh
# Entrypoint do container IFEM.
# Roda migrações (opcional via RUN_MIGRATIONS) e coleta estáticos antes de subir o Gunicorn.
# Ter isso no runtime — e não no build — garante que SECRET_KEY/DATABASE_URL venham do ambiente.
set -e

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
    echo "[entrypoint] Aplicando migrações..."
    python manage.py migrate --noinput
fi

echo "[entrypoint] Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "[entrypoint] Iniciando Gunicorn na 0.0.0.0:8000..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-2}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --access-logfile - \
    --error-logfile -
