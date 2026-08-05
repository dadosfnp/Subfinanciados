#!/usr/bin/env sh
# atualizar-banco.sh — Backup + recriacao do banco do IFEM no droplet.
#
# QUANDO USAR
# Quando o deploy falhar com "SCHEMA INCOMPATIVEL". Isso acontece toda vez que as
# migrations sao regeradas do zero: o banco fica no formato antigo e o codigo novo
# espera outro. Este script poe o banco no formato novo e recarrega as planilhas.
#
# USO (no droplet):
#   cd /var/www/ifem && ./atualizar-banco.sh
#
# POR QUE NAO BASTA `docker compose exec ifem ... recriar_banco`
# Quando o deploy aborta, o container em execucao ainda e o ANTIGO. Um `exec` rodaria
# o codigo antigo e recriaria o banco no formato ERRADO — o oposto do que se quer.
# Este script usa `docker compose run`, que sobe um container novo a partir da imagem
# recem-construida, garantindo que o codigo executado e o que se quer publicar.
set -eu

cd "$(dirname "$0")"

ARQUIVO_URL_BANCO="/root/.ifem_db_url"
PASTA_BACKUPS="/root/backups"

echo "=============================================="
echo " Atualizacao do banco do IFEM"
echo "=============================================="
echo ""
echo "Este script vai:"
echo "  1. Fazer backup do banco atual"
echo "  2. APAGAR todas as tabelas do banco do IFEM"
echo "  3. Recriar a estrutura e recarregar as planilhas (uns 10 minutos)"
echo ""
echo "As noticias e os usuarios do admin sao preservados."
echo "Outros bancos do servidor (como o do sistema FNP) NAO sao tocados."
echo ""
printf "Digite 'sim' para continuar: "
read -r RESPOSTA
if [ "$RESPOSTA" != "sim" ]; then
    echo "Cancelado. Nada foi alterado."
    exit 1
fi

# --- 1. Backup -------------------------------------------------------------------
# pg_dump precisa casar com a versao do servidor (Managed roda 18; o pg_dump do host
# e 16 e recusa a conexao). Rodar via container evita instalar pacote no droplet.
echo ""
echo "[1/3] Fazendo backup..."
if [ ! -f "$ARQUIVO_URL_BANCO" ]; then
    echo "ERRO: $ARQUIVO_URL_BANCO nao encontrado — sem ele nao da para fazer o backup."
    echo "Sem backup, nao seguimos: a recriacao apaga os dados e nao tem desfazer."
    exit 1
fi

mkdir -p "$PASTA_BACKUPS"
ARQUIVO_BACKUP="ifem-$(date +%Y%m%d-%H%M).dump"
docker run --rm \
    -e PGURL="$(tr -d '\r\n' < "$ARQUIVO_URL_BANCO")" \
    -v "$PASTA_BACKUPS:/backup" \
    postgres:18-alpine \
    sh -c "pg_dump \"\$PGURL\" -Fc -f /backup/$ARQUIVO_BACKUP"

# Um pg_dump que falha na metade deixa arquivo truncado; conferir tamanho pega isso.
TAMANHO=$(stat -c %s "$PASTA_BACKUPS/$ARQUIVO_BACKUP")
if [ "$TAMANHO" -lt 100000 ]; then
    echo "ERRO: o backup saiu com apenas $TAMANHO bytes — pequeno demais, algo deu errado."
    echo "Nada foi apagado. Verifique a conexao com o banco e tente de novo."
    exit 1
fi
echo "      Backup salvo: $PASTA_BACKUPS/$ARQUIVO_BACKUP ($(( TAMANHO / 1024 )) KB)"

# --- 2. Recriacao ----------------------------------------------------------------
# `run` em vez de `exec`: sobe um container da imagem nova. Ver comentario do cabecalho.
# RUN_MIGRATIONS=0 porque o proprio recriar_banco aplica as migrations na ordem certa.
echo ""
echo "[2/3] Recriando o banco (uns 10 minutos, nao interrompa)..."
docker compose run --rm --no-deps \
    -e RUN_MIGRATIONS=0 \
    -e PYTHONIOENCODING=utf-8 \
    --entrypoint python \
    ifem manage.py recriar_banco --confirmar

# --- 3. Container ----------------------------------------------------------------
echo ""
echo "[3/3] Subindo o site com o codigo novo..."
docker compose up -d
docker compose ps

echo ""
echo "=============================================="
echo " Pronto. Confira em https://ifem.fnp.org.br"
echo ""
echo " Se algo deu errado, o backup esta em:"
echo "   $PASTA_BACKUPS/$ARQUIVO_BACKUP"
echo "=============================================="
