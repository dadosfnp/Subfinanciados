#!/usr/bin/env sh
# deploy.sh — Deploy do IFEM/Subfinanciados no droplet (Docker Compose).
# Idempotente: seguro rodar quantas vezes precisar.
#
# POR QUE ESTE SCRIPT EXISTE
# O codigo entra na IMAGEM Docker via `COPY . .` no build do Dockerfile — nao em runtime.
# Logo, um `git pull` sozinho NAO atualiza o app: o container continua rodando a imagem
# antiga. E obrigatorio rebuildar a imagem e recriar o container. Este script encapsula
# esse ciclo (atualizar codigo -> build -> up) num comando so, para evitar deploy pela metade.
#
# USO (no droplet):
#   cd /var/www/ifem && ./deploy.sh
#
# NAO estao aqui de proposito:
#   - migrate e collectstatic -> rodam automaticamente no entrypoint.sh quando o container sobe.
set -eu

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
echo "[deploy] Branch atual: ${BRANCH}"

echo "[deploy] Atualizando codigo (fetch + reset --hard no upstream)..."
# reset --hard em vez de pull: a branch de producao ja sofreu reescrita de historico
# (force-push); um `pull`/`merge` normal quebraria com divergencia. O reset sincroniza
# o clone do droplet exatamente com o remoto, seja qual for o nome do remote.
git fetch --all --prune
git reset --hard "@{u}"
echo "[deploy] Agora em: $(git rev-parse --short HEAD) - $(git log -1 --pretty=%s)"

echo "[deploy] Rebuild da imagem (codigo novo entra via COPY no build)..."
docker compose build

echo "[deploy] Recriando o container..."
docker compose up -d

echo "[deploy] Estado dos containers:"
docker compose ps

echo "[deploy] Concluido. App interno em http://127.0.0.1:8003 (Nginx faz o proxy publico)."
