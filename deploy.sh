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
#   ou simplesmente /var/www/ifem/deploy.sh — o script se posiciona sozinho (ver cd abaixo).
#
# NAO estao aqui de proposito:
#   - migrate e collectstatic -> rodam automaticamente no entrypoint.sh quando o container sobe.
#   - recriar_banco -> e destrutivo (derruba as tabelas). Nunca deve disparar sozinho num
#     push. O que este script faz e DETECTAR que ele e necessario e abortar antes de trocar
#     o container, deixando o site atual no ar.
set -eu

# O GitHub Actions entra por uma chave restrita a `command="/var/www/ifem/deploy.sh"`, e
# nesse modo o SSH ignora o comando do cliente — inclusive o `cd`. Sem isto o script
# rodaria a partir de /root e todo comando git falharia.
cd "$(dirname "$0")"

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

# Checagem entre o build e o up, de proposito: a imagem nova ja existe (entao testamos o
# codigo que de fato vai subir), mas o container antigo ainda serve o site. Se o banco for
# incompativel, abortamos aqui e nada muda para quem esta acessando.
#
# `migrate` NAO cobre este caso: quando as migrations sao regeradas do zero, o 0001_initial
# novo ja consta como aplicado e o migrate sai com sucesso sem fazer nada, enquanto o codigo
# espera colunas que nao existem. Sem esta checagem, o deploy publicaria um site em 500.
echo "[deploy] Verificando se o banco e compativel com o codigo novo..."
if ! docker compose run --rm --no-deps -e RUN_MIGRATIONS=0 --entrypoint python ifem \
        manage.py verificar_schema --silencioso; then
    echo ""
    echo "[deploy] ABORTADO — o banco nao suporta este codigo. O site ANTERIOR continua no ar."
    echo "[deploy] Resolva com o recriar_banco (instrucoes acima) e rode o deploy de novo."
    exit 1
fi

echo "[deploy] Recriando o container..."
docker compose up -d

echo "[deploy] Estado dos containers:"
docker compose ps

echo "[deploy] Concluido. App interno em http://127.0.0.1:8003 (Nginx faz o proxy publico)."
