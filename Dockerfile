# Imagem do IFEM/Subfinanciados — piloto do padrão Docker da TIC/FNP.
# Base slim para reduzir footprint no droplet de 2GB (banco é Managed, externo).
FROM python:3.12-slim-bookworm

# Boas práticas Python em container: sem .pyc, log sem buffer (aparece no docker logs).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependências do SO mínimas. psycopg2-binary já traz a libpq embutida,
# então não precisamos de build-essential/libpq-dev (mantém a imagem pequena).
# curl entra só para o healthcheck do compose.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Instala as dependências antes de copiar o código para aproveitar o cache de layer
# (só reinstala quando requirements.txt muda).
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Código da aplicação. O .dockerignore exclui .env, db.sqlite3, staticfiles/, etc.
COPY . .

# Usuário sem privilégio — não rodar como root dentro do container.
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/staticfiles /app/media \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Invocado via sh para não depender do bit de execução (Windows não o preserva no checkout).
ENTRYPOINT ["sh", "/app/entrypoint.sh"]
