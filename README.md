# 📊 Subfinanciados

> **Inteligência Fiscal e Populacional para Municípios Brasileiros.**

O **Subfinanciados** é uma plataforma robusta desenvolvida em Django para análise, processamento e visualização de dados fiscais dos municípios brasileiros. O sistema transforma planilhas complexas em dashboards interativos, permitindo identificar disparidades de receita, calcular percentis nacionais e visualizar a saúde financeira municipal por meio de mapas geográficos.

---

## ✨ Destaques do Sistema

*   **⚡ DNA Financeiro:** Árvore de receitas interativa que detalha cada rubrica contábil com comparativos de média e mediana nacional.
*   **🗺️ Análise Geográfica:** Integração com Mapbox para visualização espacial dos dados fiscais e populacionais.
*   **📊 Insights Agregados:** Ferramentas para análise de conjuntos de municípios (por região ou porte), com suporte a valores *Per Capita* e absolutos.
*   **⚙️ Data Engine:** Pipeline automatizado de importação e processamento de dados (`.xlsx`/`.xls`) com validação de integridade.
*   **🎨 Design Premium:** Interface inspirada em sistemas modernos, com Bento Cards, micro-interações e suporte a WhiteNoise.

---

## 🛠️ Stack Tecnológica

![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Mapbox](https://img.shields.io/badge/Mapbox-000000?style=for-the-badge&logo=mapbox&logoColor=white)

---

## 🚀 Como Começar

> 🐳 **Recomendado:** a forma mais rápida e padronizada de rodar o projeto é via **Docker** — pule para a seção [Rodando com Docker](#-rodando-com-docker-recomendado-para-testar). Um único comando sobe o app idêntico ao de produção.
>
> O fluxo abaixo (venv) é uma **alternativa** para desenvolvimento local sem container.

### Alternativa: ambiente local sem Docker (venv)

#### Pré-requisitos
*   Python 3.10+
*   Ambiente virtual (venv)

#### Instalação Rápida
1.  **Clone o projeto e entre na pasta:**
    ```bash
    git clone git@github.com:dadosfnp/subfinanciados.git
    cd Subfinanciados
    ```
2.  **Crie e ative o ambiente virtual e instale as dependências:**
    ```bash
    python -m venv venv
    ./venv/Scripts/activate           # Windows (PowerShell)
    # source venv/bin/activate        # Linux / macOS
    pip install -r requirements.txt
    ```
3.  **Crie o arquivo `.env` (passo obrigatório — não pule):**

    O `.env` **não vem no repositório** (está no `.gitignore`), então todo clone precisa criar o seu.
    Sem a variável `DJANGO_SECRET_KEY` o Django **não sobe** e você verá o erro
    `A variável de ambiente DJANGO_SECRET_KEY não está definida`.

    **3.1 — Copie o template `.env.example` para `.env`:**
    ```bash
    cp .env.example .env              # Linux / macOS
    ```
    ```powershell
    Copy-Item .env.example .env       # Windows (PowerShell)
    ```

    **3.2 — Gere uma chave secreta.** Rode o comando abaixo e copie a linha que ele imprimir:
    ```bash
    python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
    ```

    **3.3 — Abra o `.env` num editor de texto** e cole a chave gerada:
    ```bash
    notepad .env                      # Windows
    # nano .env  (ou code .env)       # Linux / macOS / VS Code
    ```
    Localize a linha `DJANGO_SECRET_KEY=...` e substitua o valor pela chave do passo 3.2. Deve ficar assim:
    ```env
    DJANGO_SECRET_KEY=cole-aqui-a-chave-gerada-no-passo-3.2
    ```

    **3.4 — Ajuste as demais variáveis conforme o seu caso:**
    *   `DATABASE_URL` → **deixe comentada** (com `#` na frente) para rodar em **SQLite local**. Para usar o PostgreSQL de produção, veja a seção [Conectando ao PostgreSQL de produção](#conectando-ao-postgresql-de-produção-opcional) logo abaixo.
    *   `MAPBOX_PUBLIC_TOKEN` → cole o token público do Mapbox (peça ao time) para os mapas carregarem.
    *   As demais (`DJANGO_DEBUG`, `ALLOWED_HOSTS`, etc.) já vêm com valores razoáveis para rodar local.

    Salve e feche o arquivo.
4.  **Prepare o Banco e Estáticos:**
    ```bash
    python manage.py migrate
    python manage.py collectstatic --noinput
    ```
5.  **Inicie o Servidor:**
    ```bash
    python manage.py runserver
    ```
    Acesse **http://localhost:8000**.

> ⚠️ **Erro `DJANGO_SECRET_KEY não está definida`?** É o passo 3 faltando: o `.env` não existe ou a chave está vazia. Refaça o passo 3.

#### Conectando ao PostgreSQL de produção (opcional)

Por padrão o projeto roda em **SQLite local**. Para trabalhar sobre os dados reais, aponte o `.env` para o PostgreSQL Managed:

1.  **Peça a `DATABASE_URL` completa** (com a senha da role `ifem_app`) ao responsável pela infra — **nunca** peça/compartilhe a senha por canal aberto (Slack/e-mail); use o cofre de segredos da FNP.
2.  No `.env`, **descomente e preencha** a linha `DATABASE_URL` (o `.env.example` já tem o template). O `sslmode=require` é **obrigatório**:
    ```env
    DATABASE_URL=postgresql://ifem_app:SENHA_REAL@fnp-database-...ondigitalocean.com:25060/ifem?sslmode=require
    ```
3.  Confirme que está conectado no banco certo antes de qualquer comando:
    ```bash
    python manage.py dbshell   # deve abrir o psql do banco 'ifem'
    ```

> 🚨 **Cuidado — este é o banco de produção.** Comandos como `migrate`, `loaddata` ou os scripts de `import_*` **alteram os dados reais**. Rode-os apenas quando for essa a intenção. Para desenvolvimento e testes, prefira o SQLite local (deixe `DATABASE_URL` comentada) ou uma cópia do banco.

---

## 🐳 Rodando com Docker (recomendado para testar)

O projeto é **containerizado**. Com Docker você sobe o app idêntico ao de produção com um único comando — sem instalar Python nem dependências na máquina.

**Pré-requisitos:** Docker Desktop (ou Docker Engine + Compose).

### Modo local (SQLite + dados de exemplo)

Ideal para **testar/avaliar na sua máquina**, sem acesso ao banco de produção.

1.  **Clone a branch e entre na pasta:**
    ```bash
    git clone -b infra/dockerizar-ifem git@github.com:dadosfnp/Subfinanciados.git
    cd Subfinanciados
    ```
2.  **Crie o `.env` a partir do exemplo:**
    ```bash
    cp .env.example .env
    ```
    No `.env`, defina uma `DJANGO_SECRET_KEY` qualquer (50+ caracteres) e **mantenha a linha `DATABASE_URL` comentada** — assim o app usa SQLite local automaticamente.
3.  **Suba o container:**
    ```bash
    docker compose up -d --build
    ```
    O app fica em **http://localhost:8003** (ainda sem dados).
4.  **Carregue os dados de exemplo** (peça o arquivo `data_ifem_dump.json` ao time e coloque na pasta do projeto):
    ```bash
    docker compose cp data_ifem_dump.json ifem:/app/data_ifem_dump.json
    docker compose exec ifem python manage.py loaddata /app/data_ifem_dump.json
    ```
5.  **Abra http://localhost:8003** — plataforma completa com os 5.479 municípios.

> 💡 Para parar **sem perder** os dados locais: `docker compose stop`. Evite `docker compose down`, que recria o container e zera o SQLite local.

### Variáveis de ambiente

A lista completa está em `.env.example`. As principais:

| Variável | Para quê |
| :--- | :--- |
| `DJANGO_SECRET_KEY` | Chave do Django (obrigatória). |
| `DATABASE_URL` | Conexão PostgreSQL. **Comentada/vazia = SQLite local.** |
| `MAPBOX_PUBLIC_TOKEN` | Token público do Mapbox para os mapas. |
| `DJANGO_DEBUG` | `False` em produção, sempre. |
| `GUNICORN_WORKERS` | Nº de workers do Gunicorn dentro do container. |
| `RUN_MIGRATIONS` | `1` aplica migrações automaticamente no start do container. |

---

## ☁️ Produção (Droplet + PostgreSQL Managed)

O IFEM está publicado em **https://ifem.fnp.org.br**. Em produção o app roda **como container** num Droplet (DigitalOcean), atrás do **Nginx** (que termina o TLS via Let's Encrypt), com banco **PostgreSQL Managed** num database dedicado (`ifem`). O clone de produção fica em `/var/www/ifem` no servidor. Segue o padrão Docker da FNP: um `Dockerfile`/serviço por sistema.

> ⚠️ **Por que não basta `git pull`:** o código entra na **imagem** Docker via `COPY . .` no build, não em runtime. Um `pull` sozinho **não** atualiza o app — o container continua rodando a imagem antiga. É obrigatório **rebuildar a imagem e recriar o container** após atualizar o código.

### Como atualizar o IFEM em produção (deploy manual)

É o fluxo em uso hoje. Qualquer pessoa com **acesso SSH ao droplet** e os dados corretos consegue atualizar:

1.  **Conecte no droplet** (peça o IP e o usuário ao responsável pela infra — não ficam neste repositório):
    ```bash
    ssh <usuario>@<ip-do-droplet>
    ```
2.  **Entre na pasta do app e sincronize o código** com o remoto:
    ```bash
    cd /var/www/ifem
    git fetch --all --prune
    git reset --hard @{u}          # sincroniza com a branch remota (histórico já sofreu force-push)
    ```
3.  **Rebuild da imagem e recriação do container:**
    ```bash
    docker compose up -d --build
    ```
    `migrate` e `collectstatic` rodam sozinhos no `entrypoint.sh` quando o container sobe.
4.  **Confira que subiu:**
    ```bash
    docker compose ps
    ```
    App interno em `http://127.0.0.1:8003`; o Nginx faz o proxy público para `https://ifem.fnp.org.br`.

> 💡 Onde há o `deploy.sh` (branch de infra), os passos 2–4 viram um comando só: `cd /var/www/ifem && ./deploy.sh`.

*   **Validação sem expor publicamente** (túnel SSH — acesse em http://localhost:8003):
    ```bash
    ssh -L 8003:localhost:8003 <usuario>@<ip-do-droplet>
    ```

### Deploy automático (em transição)

Há um **GitHub Actions** (`.github/workflows/deploy.yml`, na branch de infra `chore/deploy-script-e-runbook`, ainda **não mergeada** na `main`) que dispara o deploy sozinho **a cada push na `main`**: o runner conecta no droplet via SSH e roda o `deploy.sh`. Enquanto os secrets `DROPLET_SSH_*` não estiverem configurados no repositório, o job passa sem fazer nada (guard de segurança).

> **Atenção à branch de produção:** hoje o droplet acompanha a branch **`feat/pagina-metodologia`** (deploy manual). Quando o auto-deploy entrar em vigor, a branch de produção passa a ser a **`main`**. Sempre confirme a branch ativa no droplet com `git branch --show-current` antes de deployar.

*   **Decisões de arquitetura e passo a passo da migração:** ver `tasks/plan-migracao-droplet.md`, `tasks/runbook-migracao-droplet.md` e o ADR-001 na pasta TIC da FNP.

---

## 📈 Processamento de Dados

O sistema utiliza comandos customizados para digerir as planilhas localizadas em `base_datas/`.

| Comando | Descrição |
| :--- | :--- |
| `import_accounts` | Importação das contas gerais e estruturais. |
| `import_detail_accounts` | Dados detalhados de receitas por município. |
| `import_rm` | Composição das Regiões Metropolitanas. |
| `calculate_percentiles` | Processamento estatístico de rankings nacionais. |

---

## 🤝 Desenvolvimento e Contribuição

Para manter a integridade e uniformidade do projeto, seguimos padrões rigorosos de desenvolvimento.

*   **Commits:** Seguimos o padrão [Conventional Commits](https://www.conventionalcommits.org/).
*   **Branching:** Nunca trabalhe diretamente na branch principal (`main`). Use `feat/` ou `fix/`.
*   **Fluxo Multi-Agente:** Consulte o arquivo [GEMINI.md](./GEMINI.md) para diretrizes específicas de coordenação entre agentes e regras de branch por tarefa.

### Atualizar o projeto e enviar mudanças (passo a passo)

Este repositório usa o remote **`production`** (`git@github.com:dadosfnp/subfinanciados.git`) — **não** existe um remote `origin`. Confira com `git remote -v`.

1.  **Antes de começar, atualize a `main`:**
    ```bash
    git checkout main
    git pull production main
    ```
2.  **Crie uma branch para a sua tarefa** (nunca trabalhe na `main`):
    ```bash
    git checkout -b feat/nome-curto-da-tarefa
    ```
3.  **Sempre que mexer no código, reaplique migrações e dependências** — um `git pull` pode trazer novas:
    ```bash
    pip install -r requirements.txt   # caso requirements.txt tenha mudado
    python manage.py migrate          # caso haja novas migrações
    ```
4.  **Faça commits pequenos e semânticos:**
    ```bash
    git add .
    git commit -m "feat: descrição curta da mudança"
    ```
5.  **Envie a branch e abra um Pull Request:**
    ```bash
    git push -u production feat/nome-curto-da-tarefa
    ```
    Depois abra o PR no GitHub, da sua branch para a `main`.

> 📌 **Lembre-se:** o `.env`, o `db.sqlite3` e a pasta `staticfiles/` estão no `.gitignore` e **nunca** vão para o git. Ao trocar de máquina ou após clonar, recrie o `.env` (seção [Como Começar](#-como-começar)) — ele não vem no `git pull`.

---

✍️ **Desenvolvido por:** FNP | 📄 **Licença:** Uso Interno / Restrito