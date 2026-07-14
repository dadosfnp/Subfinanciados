# Plano: Migrar Subfinanciados/IFEM para Droplet DO + PostgreSQL Managed
Data: 2026-06-02
Branch: feat/media-quintil-decil (criar branch própria de infra a partir de `dev`/`main`)

## Goal
Preparar e validar a aplicação Subfinanciados/IFEM rodando no Droplet DigitalOcean
com banco PostgreSQL Managed (schema dedicado `ifem`), respeitando a arquitetura TIC,
**sem publicar online e sem tocar na produção atual (Render)**.

## Decisões travadas (com o Pedro)
- **Fonte de dados**: SQLite local (`db.sqlite3`) — 5.479 municípios + tabelas de receitas/percentis/notícias.
- **Schema no Managed**: novo dedicado `ifem`, com role de escrita própria (isolado de `app`/`rag`).
- **Execução no droplet**: eu (Claude) via SSH a partir desta máquina, mostrando cada passo antes de aplicar.
- **Escopo desta fase**: NÃO publicar. Render continua no ar como produção (intocado).
  Pedro só precisa **enxergar** a app rodando → via **túnel SSH** (`ssh -L 8003:localhost:8003`), acesso por `localhost:8003`.
- **Domínio/Cloudflare/Nginx público**: fase futura, quando o registro.br liberar.

## Infra alvo (docs TIC)
- Droplet: Ubuntu 24, 2GB RAM, IP provável `142.93.205.222`, SSH porta 22.
- Postgres Managed: `fnp-database-do-user-37776190-0.k.db.ondigitalocean.com:25060`, SSL obrigatório.
- Convenção: 1 sistema = 1 schema. IFEM ocupa a porta interna **8003** (era "Planejado" no inventário).

## DESCOBERTA Fase A (dump de terminal do droplet, 25/05) — diverge do doc TIC
O droplet `fnp-web` (root) NÃO usa Docker. O Sistema FNP roda assim:
- `/var/www/fnp/sistema-fnp/` com venv Python 3.12.
- **systemd** `fnp.service` → **Gunicorn** → **socket unix** `/run/fnp/fnp.sock` (não TCP).
- **Nginx** como proxy reverso (`/etc/nginx/sites-available/fnp`).
- Settings split: `configuracao/base.py` + `configuracao/producao.py`; estáticos via WhiteNoise + ManifestStaticFilesStorage.
- `DATABASE_URL` com `ssl_require=True` (aponta pro Managed); `.env` em `/var/www/fnp/sistema-fnp/.env`.
- Droplet pequeno (2GB, cgroup task limit 2315) já roda Sistema FNP (+ RAG previsto).

**Decisão de arquitetura pendente**: doc TIC diz "Docker + Compose", realidade é "systemd + venv + nginx + socket".
RECOMENDAÇÃO: seguir o padrão REAL (systemd+venv), espelhando o Sistema FNP — mais leve no droplet de 2GB
e consistente com o que já está implantado. Atualizar o doc TIC depois para refletir a realidade.
=> Se aprovado, o Scope abaixo muda: sai Dockerfile/compose; entra `ifem.service` (systemd) + location no Nginx
   + socket `/run/ifem/ifem.sock` (porta lógica 8003 fica só como identificador do sistema no inventário).

## Scope
### Arquivos a criar
- `Dockerfile` — imagem da app (Python 3.12, gunicorn).
- `docker-compose.yml` — serviço web na porta 8003, lê `.env`.
- `.dockerignore`
- `.env.example` — template das variáveis (sem segredos).
- `scripts/dump_sqlite_to_pg.py` (ou uso de `dumpdata`/`loaddata`) — migração de dados.
- `tasks/runbook-migracao-droplet.md` — registro do que foi executado (comandos + resultados).

### Arquivos a modificar
- `config/settings.py` — search_path do schema `ifem`; ALLOWED_HOSTS/CSRF via env; manter compat com Render.
- `home/migrations/0003_...` — já existe (índices); commitar junto com models.py.
- `.gitignore` — garantir `.env`, `db.sqlite3` ignorados (padrão TIC) — **avaliar impacto: hoje db.sqlite3 é versionado**.
- `requirements.txt` — revisar (psycopg2-binary já presente).

### Arquivos a NÃO tocar (produção Render)
- `render.yaml`, `build.sh` — Render permanece no ar exatamente como está.
- Banco Supabase atual.

## Subtasks

### Fase A — Reconhecimento (read-only, zero alteração) — CONCLUÍDA 2026-06-02 (ver runbook)
- [x] A1. SSH OK (root@142.93.205.222). Roda só FNP+nginx; RAG não implantado; sem Docker; 1.3G RAM livre; sem swap.
- [x] A2. Postgres 18.4. Databases: defaultdb, fnp_sistema. `doadmin` cria db/role; `admin_sistema` não.
- [x] A3. IP do droplet na allowlist do banco (psql conectou). Padrão = database-por-sistema, schema `public`.
- [x] A4. Findings gravados em `tasks/runbook-migracao-droplet.md`.

### DECISÕES TRAVADAS (2026-06-02)
- [x] Docker+Compose como padrão; IFEM de piloto (FNP/RAG migram depois). Atualizar doc TIC ao final.
- [x] Banco: **database `ifem` dedicado** + role `ifem_app` (espelha fnp_sistema).
- [x] Swapfile 2G no droplet; avaliar upgrade 4GB quando RAG entrar.
- [ ] PENDENTE: obter connection string do `doadmin` (painel DO) — necessária só na Fase B.

### Fase B — Banco: database e role dedicados — CONCLUÍDA 2026-06-02
- [x] B1. `doadmin` validado. CREATE ROLE `ifem_app` (senha forte gerada no droplet) + CREATE DATABASE `ifem` OWNER ifem_app.
- [x] B2. REVOKE PUBLIC no database; GRANT ALL ao ifem_app; GRANT ALL + ALTER OWNER no schema public.
- [x] B3. DATABASE_URL `postgresql://ifem_app:***@.../ifem?sslmode=require` gravada em `/root/.ifem_db_url` (600).
- [x] B4. Conexão testada como ifem_app → `ifem_app|ifem|PG 18.4`. fnp_sistema intocado.
- [ ] PENDENTE: guardar senha do ifem_app no cofre (está só em /root/.ifem_db_url).

### Fase C — App: containerização e settings
- [x] C1. settings.py NÃO alterado: já suporta Docker via env (DATABASE_URL/ALLOWED_HOSTS/SECRET_KEY). Menos risco. Database `ifem` (não schema) dispensa search_path.
- [x] C2. Criados: Dockerfile, entrypoint.sh, docker-compose.yml (bind 127.0.0.1:8003), .dockerignore, .gitattributes; .env.example atualizado com DATABASE_URL/Gunicorn.
- [x] C3. Build local OK (imagem 1.4GB) + smoke test `manage.py check` = 0 issues. (Melhoria futura: enxugar imagem.)
- [ ] C4. Commit em branch de infra (semântico), sem mexer no que é da produção Render.

### Fase D — Migração de dados (SQLite -> Postgres `ifem`)
- [x] D1. Dump gerado via imagem Docker (db.sqlite3 montado) → `data_ifem_dump.json` (50MB, ignorado pelo git via *.json).
      Contagens conferidas: 5479 municipio + 6×5479 contas/percentis + medias/medianas + 99 percentis + 84 RM + 5 noticias.
- [x] D2. migrate aplicado no database ifem (resolvido conflito 0003 via merge 0004).
- [x] D3. loaddata = 38.648 objetos. Contagens validadas: municipio=5479, noticia=5, contadetalhada=5479.
- [x] D4. App responde HTTP 200 lendo o banco; integridade OK.

### Fase E — Deploy no droplet (sem expor) — CONCLUÍDA 2026-06-02
- [x] E1. Swap 2G + Docker/Compose instalados; repo clonado em /var/www/ifem (deploy key); .env criado (fora do git).
- [x] E2. docker compose up -d → container HEALTHY, bind 127.0.0.1:8003 (sem porta pública).
- [x] E3. entrypoint roda migrate+collectstatic+gunicorn; healthcheck OK; HTTP 200.
- [x] E4. Pronto para Pedro validar via túnel SSH (localhost:8003).

### Fase F — Documentação e handoff
- [ ] F1. Atualizar `inventario_servicos.md` da TIC (IFEM, porta 8003, schema `ifem`, status "Homologação").
- [ ] F2. Preencher `runbook-migracao-droplet.md` com comandos e resultados.
- [ ] F3. Guardar credenciais novas no cofre (Bitwarden/1Password) — não no repo.
- [ ] F4. Deixar pendências mapeadas para a fase pública (Nginx vhost, Cloudflare, domínio registro.br, desligar Render).

## Risks & Open Questions
- **Segredos**: senha do Supabase ficou no histórico do git (`check_db.py`) — rotacionar. Não introduzir novos segredos no repo.
- **db.sqlite3 versionado**: hoje está no git. Mudar o `.gitignore` para ignorá-lo pode confundir; decidir com Pedro se paramos de versionar (recomendado) e como.
- **Credencial admin do Postgres Managed**: necessária para criar schema/role — Pedro precisa fornecer ou criar via painel DO.
- **Allowlist do banco**: só aceita IP do droplet. Testes locais de conexão podem falhar — fazer testes a partir do droplet.
- **search_path multi-schema**: garantir que migrations do Django criem tabelas no schema `ifem` e não no `public`.
- **Recursos do droplet (2GB)**: já roda Sistema FNP + RAG. Validar headroom de RAM antes de subir um 3º container.
- **Não tocar produção**: nenhuma alteração em Render/Supabase nesta fase.

## Definition of Done (desta fase)
- [ ] Schema `ifem` + role criados no Managed, isolados.
- [ ] Dados migrados e validados (contagens batem com SQLite).
- [ ] App rodando em container no droplet na porta interna 8003, sem exposição pública.
- [ ] Pedro consegue enxergar via túnel SSH.
- [ ] Render/Supabase intocados e ainda no ar.
- [ ] Runbook + inventário TIC atualizados; credenciais no cofre.
