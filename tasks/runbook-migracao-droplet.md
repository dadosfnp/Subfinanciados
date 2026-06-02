# Runbook — Migração IFEM/Subfinanciados → Droplet + Postgres Managed
Registro do que foi executado. Append-only, com data.

## Fase A — Reconhecimento (read-only) — 2026-06-02 — CONCLUÍDA

### Droplet (`fnp-web`, root@142.93.205.222)
- SO: Ubuntu 24.04.4 LTS, kernel 6.8.0-117.
- RAM: total 1.9Gi · usado ~607Mi · disponível ~1.3Gi · **SEM SWAP**.
- Disco: 48G total, 2.9G usado (45G livres) — folga para imagens Docker.
- Serviços rodando: `fnp.service` (Gunicorn) + `nginx.service`. **RAG ainda NÃO implantado.**
- Portas LISTEN: 22 (SSH), 80 (nginx). **Sem 443 (TLS ainda não configurado).** FNP via socket unix, não TCP.
- Docker: **NÃO instalado**.
- App FNP: `/var/www/fnp/sistema-fnp/` (venv 3.12), systemd → gunicorn → `/run/fnp/fnp.sock`.
- Settings split: `configuracao/base.py` + `configuracao/producao.py`; estáticos WhiteNoise/Manifest.

### Nginx (`/etc/nginx/sites-available/fnp`)
```
server {
    listen 80;
    server_name 142.93.205.222 sistema.fnp.org.br;   # domínio fnp.org.br JÁ existe e em uso
    location /static/ { alias /var/www/fnp/sistema-fnp/staticfiles/; }
    location /media/  { alias /var/www/fnp/sistema-fnp/media/; }
    location /        { include proxy_params; proxy_pass http://unix:/run/fnp/fnp.sock; }
}
```

### Postgres Managed (PostgreSQL 18.4)
- Conexão FNP (.env): `postgresql://admin_sistema:****@fnp-database-do-user-37776190-0.k.db.ondigitalocean.com:25060/fnp_sistema?sslmode=require`
- Databases: `defaultdb`, `fnp_sistema`, `_dodb` (interno DO).
- Roles: `doadmin` (createdb=t, createrole=t) = admin do cluster; `admin_sistema` (createdb=f, createrole=f) = user do FNP, sem poder criar db/role; `postgres` (superuser, normalmente inacessível em Managed).
- Schemas em `fnp_sistema`: apenas `public`. **Padrão real = 1 database por sistema, tudo em `public`.**
- IP do droplet está na allowlist (psql conectou do droplet sem erro).

### Conclusões que mudam o plano
1. **Deploy**: realidade é systemd+venv+nginx+socket, não Docker. Decisão: padronizar em Docker (piloto IFEM) — ver plano.
2. **Banco**: padrão real é database-por-sistema, não schema-por-sistema. Recomendar **database `ifem`** (não schema), espelhando `fnp_sistema`.
3. **Credencial**: criar database/role exige `doadmin` (NÃO está no .env do FNP). Precisa pegar do painel DO. → bloqueia Fase B.
4. **RAM/Swap**: hoje cabe IFEM (1.3G livre, RAG ainda fora). Sem swap = risco de OOM com pandas/numpy. Recomendar swapfile 2G já; 4GB quando RAG entrar.
5. **TLS**: sem 443 hoje — coerente com "não publicar ainda".

## Fase C — Containerização (local) — 2026-06-02 — CONCLUÍDA
- Criados: Dockerfile (python:3.12-slim, appuser não-root), entrypoint.sh (migrate+collectstatic+gunicorn, LF),
  docker-compose.yml (bind 127.0.0.1:8003, healthcheck, volume ifem_media), .dockerignore, .gitattributes.
- .env.example atualizado com DATABASE_URL (database `ifem`, role ifem_app) e tuning Gunicorn.
- settings.py NÃO alterado (já suporta Docker via env). Render intocado.
- `docker build` OK → imagem `ifem-subfinanciados:latest` (1.4GB).
- Smoke test: `docker run ... manage.py check` → "0 issues". Django carrega na imagem.
- Melhoria futura: imagem grande (mkdocs/openai/duckdb em runtime?) — avaliar multi-stage/slim.

## Fase B — Database e role no Managed — 2026-06-02 — CONCLUÍDA
- `doadmin` validado (createdb/createrole=t). Usado pontualmente; IFEM nunca mais usa doadmin.
- CREATE ROLE `ifem_app` LOGIN (senha forte `openssl rand -hex 24`, gerada NO droplet, não trafegou no chat).
- CREATE DATABASE `ifem` OWNER ifem_app. REVOKE ALL ON DATABASE FROM PUBLIC; GRANT ALL TO ifem_app.
- No db ifem: GRANT ALL ON SCHEMA public TO ifem_app + ALTER SCHEMA public OWNER TO ifem_app (migrate ok).
- DATABASE_URL do IFEM gravada em `/root/.ifem_db_url` (chmod 600, root-only).
- Teste: `psql "$IFEM_URL" SELECT current_user,current_database()` → ifem_app | ifem. OK.
- PENDÊNCIAS DE SEGURANÇA: levar senha do ifem_app (e doadmin) para o cofre Bitwarden; /root/.ifem_db_url é temporário.
