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
    git clone <url-do-repo>
    cd Subfinanciados
    ```
2.  **Configure o ambiente:**
    ```bash
    python -m venv venv
    ./venv/Scripts/activate  # Windows
    pip install -r requirements.txt
    ```
3.  **Prepare o Banco e Estáticos:**
    ```bash
    python manage.py migrate
    python manage.py collectstatic
    ```
4.  **Inicie o Servidor:**
    ```bash
    python manage.py runserver
    ```

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
*   **Branching:** Nunca trabalhe diretamente na branch principal. Use `feat/` ou `fix/`.
*   **Fluxo Multi-Agente:** Consulte o arquivo [GEMINI.md](./GEMINI.md) para diretrizes específicas de coordenação entre agentes e regras de branch por tarefa.

---

✍️ **Desenvolvido por:** FNP | 📄 **Licença:** Uso Interno / Restrito