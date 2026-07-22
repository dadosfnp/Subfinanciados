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
3.  **Crie o arquivo `.env` (passo obrigatório):**

    O `.env` **não vem no repositório** (está no `.gitignore`), então todo clone precisa criar o seu.
    Sem a variável `DJANGO_SECRET_KEY` o Django **não sobe** e você verá o erro
    `A variável de ambiente DJANGO_SECRET_KEY não está definida`.

    ```bash
    cp .env.example .env              # Linux / macOS
    # copy .env.example .env          # Windows (PowerShell/CMD)
    ```

    Agora gere uma `DJANGO_SECRET_KEY` e cole no `.env`:
    ```bash
    python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
    ```
    Abra o `.env` e substitua o valor de `DJANGO_SECRET_KEY` pela chave gerada.
    Para rodar local com **SQLite**, mantenha a linha `DATABASE_URL` **comentada** (é o padrão do `.env.example`).
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

Em produção o app roda **como container** no Droplet (DigitalOcean), atrás do **Nginx**, com banco **PostgreSQL Managed** num database dedicado (`ifem`). Segue o padrão Docker da FNP: um `Dockerfile`/serviço por sistema.

*   **Build/atualização no servidor:**
    ```bash
    docker compose up -d --build
    ```
*   **Validação sem expor publicamente** (túnel SSH — acesse em http://localhost:8003):
    ```bash
    ssh -L 8003:localhost:8003 root@<ip-do-droplet>
    ```
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