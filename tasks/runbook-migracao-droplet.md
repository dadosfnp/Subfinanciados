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

## Fase D1 — Dump de dados — 2026-06-02 — CONCLUÍDA
- `data_ifem_dump.json` (50MB) gerado via imagem Docker com db.sqlite3 montado (stdout → host).
- Contagens batem com SQLite: 5479 municipio; 6×5479 contas/percentis; medias/medianas; 99 percentis; 84 RM; 5 noticias.
- Ignorado pelo git (*.json). Será transferido ao droplet por scp.

## Fase Git — 2026-06-02 — CONCLUÍDA
- ACHADO: .env (com SECRET_KEY+Mapbox) e db.sqlite3 estavam TRACKEADOS (já no histórico do GitHub).
  → PENDÊNCIA: rotacionar SECRET_KEY e token Mapbox do repo. Droplet usa segredos NOVOS (não afetado).
- Branch `infra/dockerizar-ifem` (a partir de feat/media-quintil-decil), 4 commits:
  chore(rm --cached .env/db.sqlite3) / perf(indices+geojson) / fix(segredos via env) / feat(docker).
- Push OK para remote `production` = github.com/dadosfnp/Subfinanciados.

## Fase E — Deploy no droplet — 2026-06-02 — EM ANDAMENTO
- [x] Swap 2G criado e ativo (/swapfile, em /etc/fstab).
- [x] Deploy key SSH gerada no droplet (/root/.ssh/id_ifem_deploy, alias github-ifem). PUB a adicionar no GitHub (read-only).
- [x] Docker 29.5.2 + Compose v5.1.4 instalados e habilitados.
- [x] Deploy key adicionada no repo (read-only) — auth OK ("Hi dadosfnp/Subfinanciados!").
- [x] Clonado em /var/www/ifem (branch infra/dockerizar-ifem, 4 commits). Lixo: arquivo "$null" no repo (limpar depois).
- [x] .env criado (chmod 600): SECRET_KEY nova (64 chars), DATABASE_URL do ifem, MAPBOX, SECURE_SSL_REDIRECT=False.
- [x] data_ifem_dump.json (49M) transferido via scp para /var/www/ifem/.
- [x] docker compose build no droplet (imagem ifem-subfinanciados:latest).
- [x] CONFLITO de migrations (duas 0003) → merge 0004 commitado/pushed. Lição: rebuild da imagem após git pull (código entra via COPY no build).
- [x] migrate aplicou tudo (0003 x2 + 0004_merge) + loaddata = 38.648 objetos instalados.
- [x] Contagens validadas no Postgres ifem: municipio=5479, noticia=5, contadetalhada=5479.
- [x] docker compose up -d → container HEALTHY, HTTP 200 em 127.0.0.1:8003, 2 workers gunicorn.
- APP NO AR no droplet, lendo o database ifem do Managed. Acesso via túnel SSH (localhost:8003). Render/FNP intocados.

## Perf — 2026-06-02
- Medições no droplet (localhost, sem túnel): home 34ms, mapa 8ms, análise 10ms, geojson 0.32s/2.8MB, query DB 8ms.
- Diagnóstico: app rápido; lentidão percebida = túnel SSH + payload geojson sem compressão.
- Ação: GZipMiddleware ativado. Geojson 2.811KB → 411KB (−85%), Content-Encoding: gzip. Deploy OK.

## PENDÊNCIAS APÓS APP NO AR
- [ ] Dicionário de dados: gerador automático dos models (docs/ no repo + índice TIC).
- [ ] playbook-novo-sistema.md (local a definir com Pedro: repo de docs vs TIC/05_desenvolvimento).
- [ ] SEGURANÇA: rotacionar SECRET_KEY e token Mapbox do histórico do repo; senhas (doadmin, ifem_app) no cofre Bitwarden.
- [ ] Limpeza: arquivo lixo "$null" no repo; 44 staticfiles hashed; db.sqlite3 (deixou de ser versionado, ok).
- [ ] Se precisar do /admin: criar superuser (loaddata não traz usuários).
- [ ] Futuro (publicar): Nginx vhost p/ ifem (deploy/nginx-ifem.conf pronto), TLS, Cloudflare, domínio registro.br, desligar Render.

## Segurança/Limpeza do repo — 2026-06-02
- GZipMiddleware ativado (geojson 2.8MB → 411KB).
- staticfiles/ e ~$*.xlsx fora do versionamento; arquivo-lixo "$null" removido.
- REESCRITA DE HISTÓRICO (git-filter-repo): expurgado .env e db.sqlite3 de TODO o histórico (438 commits).
  Backup: ../subfinanciados-backup-pre-filter.bundle. Force-push em todas as branches do remote.
  → AÇÃO EQUIPE: re-clonar (git fetch + reset --hard) — histórico mudou.
  Working local e droplet re-sincronizados; container seguiu healthy / HTTP 200.
- Limpeza não-IFEM: removidos gitlink órfão "Subfinanciados" (submódulo acidental) e package-lock.json (sem package.json).
  Mantidos (decisão do Pedro): check_db.py, debug/test_*.py, exports do folheto.
- PENDÊNCIA SEGURANÇA (Pedro): senhas (doadmin, ifem_app) no Bitwarden; opcional restringir token Mapbox por URL.

## Consolidação main + processo de deploy — 2026-07-14
- CONSOLIDAÇÃO: `main` reintegrada com a branch de produção `feat/pagina-metodologia` via PR #75.
  Trazidos: app próprio `metodologia/` (extraído do `ifem`), scripts de export do folheto e fix HTTPS/Nginx.
  Conflito resolvido em `config/urls.py` (rota `/metodologia/` aponta para o app novo). Árvore da `main`
  ficou idêntica à `feat`. Validado: `check` (0 issues), `makemigrations --check` (sem pendências),
  `GET /metodologia/` → 200.
- COMO O DEPLOY REALMENTE FUNCIONA (importante — não é auto-deploy):
  - O app roda em **container Docker** no droplet (`docker compose`, imagem `ifem-subfinanciados:latest`).
  - O código entra na imagem via `COPY . .` no **build** do Dockerfile — **não** em runtime.
  - Portanto **`git pull` sozinho não atualiza o app**: é obrigatório rebuildar a imagem e recriar o
    container. `migrate` e `collectstatic` rodam sozinhos no `entrypoint.sh` a cada subida do container.
  - **Não há auto-deploy hoje**: nenhum webhook/GitHub Action/cron. O "push→deploy automático" era do
    **Render** (`render.yaml`, a desligar); na migração para o droplet o equivalente não foi configurado.
- FERRAMENTA: adicionado `deploy.sh` na raiz — encapsula `fetch + reset --hard` (resiste à reescrita de
  histórico) → `docker compose build` → `up -d`. Deploy manual vira um comando: `cd /var/www/ifem && ./deploy.sh`.
- AUTO-DEPLOY (decisão: GitHub Actions + SSH, gatilho `main`): workflow `.github/workflows/deploy.yml`.
  A cada push na `main`, o runner conecta via SSH no droplet e roda `deploy.sh`. Enquanto os secrets não
  existirem, o job passa (verde) sem fazer nada — não quebra o primeiro merge.
  - **Setup manual no DROPLET (1x):**
    1. Apontar o clone pra `main` (produção passa a seguir a main): `cd /var/www/ifem && git fetch --all && git checkout main && git reset --hard origin/main` (ajustar nome do remote — no droplet é `github-ifem`).
    2. Garantir `deploy.sh` executável: `chmod +x deploy.sh` (só se o clone não tiver preservado o bit 100755).
    3. Criar chave SSH dedicada ao CI (SEM passphrase): `ssh-keygen -t ed25519 -f ~/.ssh/id_ci_deploy -N ''` e autorizar: `cat ~/.ssh/id_ci_deploy.pub >> ~/.ssh/authorized_keys`.
    4. Pegar o host key pro known_hosts do CI: `ssh-keyscan -H <IP_DO_DROPLET>` (guardar a saída).
  - **Secrets no GitHub (repo → Settings → Secrets and variables → Actions):**
    - `DROPLET_SSH_HOST` = IP/host do droplet · `DROPLET_SSH_USER` = usuário SSH (ex.: root)
    - `DROPLET_SSH_KEY` = conteúdo de `~/.ssh/id_ci_deploy` (chave PRIVADA) · `DROPLET_SSH_KNOWN_HOSTS` = saída do `ssh-keyscan`
    - `DROPLET_APP_DIR` = `/var/www/ifem` (opcional; é o default)
  - Melhoria de segurança futura: usar um usuário `deploy` no grupo `docker` em vez de `root` no SSH.
