#!/usr/bin/env bash
# exit on error
set -o errexit

# Instala as dependências
pip install -r requirements.txt

# Coleta os arquivos estáticos (Essencial para o Admin do Django funcionar)
python manage.py collectstatic --no-input

# Aplica as migrações
echo "Running migrations..."
python manage.py migrate --no-input
