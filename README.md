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

### Deploy automático (ATIVO desde 2026-08-05)

**Todo push na `main` publica em produção sozinho.** O GitHub Actions
(`.github/workflows/deploy.yml`) conecta no droplet via SSH e roda o `deploy.sh`. Não é
preciso fazer nada além do merge — mas **confira o resultado do job**, porque ele pode
barrar o deploy de propósito (veja abaixo).

Acompanhe em **Actions → Deploy produção (droplet)**, ou pelo terminal:

```bash
gh run list --repo dadosfnp/subfinanciados --limit 3
gh run view <id> --repo dadosfnp/subfinanciados --log | grep "\[deploy\]"
```

#### Os dois desfechos possíveis

| Resultado | O que aconteceu | O que fazer |
| :--- | :--- | :--- |
| ✅ verde | Publicado. O log termina em `[deploy] Concluido`. | Nada. |
| ❌ vermelho com `SCHEMA INCOMPATÍVEL` | O banco não suporta o código novo. **O deploy foi abortado e o site anterior continua no ar, intacto.** | Rodar o `recriar_banco` (abaixo) e disparar o deploy de novo. |

O segundo caso é esperado sempre que a atualização mexe no schema — o que acontece toda
vez que as migrations são regeradas. Não é bug: é o deploy se recusando a publicar um site
que serviria erro em toda página.

```bash
ssh root@<ip-do-droplet>
cd /var/www/ifem
docker compose exec ifem python manage.py recriar_banco              # confira o plano
docker compose exec ifem python manage.py recriar_banco --confirmar  # execute
```

Depois é só reexecutar o job em **Actions → Re-run jobs** (ou dar um novo push).

> 🚨 **Tire um backup do banco antes do `recriar_banco`.** No droplet, use a versão do
> `pg_dump` que casa com o servidor (o do host é 16, o Managed é 18):
> ```bash
> docker run --rm -e PGURL="$(tr -d '\r\n' < /root/.ifem_db_url)" -v /root/backups:/backup \
>   postgres:18-alpine sh -c 'pg_dump "$PGURL" -Fc -f /backup/ifem-$(date +%F-%H%M).dump'
> ```

#### Como o acesso do CI está montado

O Actions entra como `root` por uma chave dedicada, restrita no `authorized_keys` do droplet
a `command="/var/www/ifem/deploy.sh"` (mais `no-pty` e os `no-*-forwarding`). Na prática a
chave **só consegue disparar o deploy** — não abre shell, não lê arquivo, não roda outro
comando, mesmo que vaze. Os secrets são `DROPLET_SSH_HOST`, `DROPLET_SSH_USER`,
`DROPLET_SSH_KEY` e `DROPLET_SSH_KNOWN_HOSTS`.

> Se um dia os secrets forem removidos, o job volta a cair num guard e **termina verde sem
> publicar nada** (com um `::notice` explicando). Foi assim durante semanas, e já houve push
> dado como publicado que nunca chegou ao ar — se o site não mudou, confira o log do job
> antes de procurar o problema em outro lugar.

> **Branch de produção:** o droplet acompanha a **`main`** desde 2026-08-05. Antes disso
> seguia a `feat/pagina-metodologia`, e por isso pushes na `main` não apareciam em produção.
> Para conferir: `git branch --show-current` em `/var/www/ifem`.

*   **Decisões de arquitetura e passo a passo da migração:** ver `tasks/plan-migracao-droplet.md`, `tasks/runbook-migracao-droplet.md` e o ADR-001 na pasta TIC da FNP.

---

## 📈 Processamento de Dados

Todos os dados do sistema vêm das planilhas em `base_datas/` (versionadas no git) e são
carregados por comandos customizados. Cada comando **apaga e recarrega** as suas tabelas,
então rodar duas vezes é seguro.

### Atualizar os dados (o caminho normal)

Um comando só faz tudo — derruba o schema, aplica as migrations e recarrega as 9 etapas
na ordem correta:

```bash
python manage.py recriar_banco              # mostra o plano e sai, sem alterar nada
python manage.py recriar_banco --confirmar  # executa
```

Ele preserva o que não vem de planilha e se perderia para sempre: as **Notícias** e as
**contas de acesso ao admin** (usuários, grupos e permissões, com as senhas intactas).
Exporta antes de derrubar e reimporta no fim. No encerramento confere a contagem de todas
as 21 tabelas e **falha** se alguma vier abaixo do piso esperado — carga parcial é o modo
de falha perigoso, porque o site sobe servindo dados incompletos sem sinal de erro.

> **Escopo do drop:** apenas o database ao qual a aplicação está conectada — em produção,
> o `ifem`. Os outros databases do mesmo cluster PostgreSQL (como o `fnp_sistema`, do
> sistema da FNP) são isolados e não são afetados.

> **Por que derrubar o schema em vez de migrar?** O fluxo de atualização de dados deste
> projeto regera as migrations do zero (apaga `home/migrations/*` e roda `makemigrations`).
> Isso produz um `0001_initial` novo que o banco já considera aplicado — `migrate` não faz
> nada, enquanto o código passa a esperar colunas renomeadas, tabelas novas e outra primary
> key. O app sobe e quebra com `ProgrammingError: column ... does not exist`. Como todos os
> dados vêm das planilhas e são substituídos por inteiro a cada carga, reconstruir é mais
> simples e mais seguro do que escrever migrations de transição.

### Os comandos individuais

Rodar um a um só é necessário para recarregar uma parte específica. **A ordem importa:** o
`01` cria os `Municipio` que todos os demais referenciam por chave estrangeira.

| Ordem | Comando | O que carrega |
| :--- | :--- | :--- |
| 1 | `01_importar_municipios` | Municípios, população, receitas e os indicadores (SUS, CadÚnico, rankings). |
| 2 | `02_importar_rm` | Composição das Regiões Metropolitanas. |
| 3 | `03_importar_contas` | Contas detalhadas (nível 0) e seus percentis. |
| 4 | `04_importar_contas_01` | Contas específicas (nível 1) e seus percentis. |
| 5 | `05_importar_contas_02` | Contas mais específicas (nível 2) e seus percentis. |
| 6 | `06_percentil` | Limites dos percentis nacionais. |
| 7 | `07_media_nacional_detalhamento` | Médias nacional, por UF e por porte. |
| 8 | `08_mediana_nacional_detalhamento` | Medianas nacional, por UF e por porte. |
| 9 | `09_crescimento_medio` | Crescimento médio de receita e população. |

> ⚠️ Nunca rode esses comandos com `manage.py shell < arquivo`. Nesse modo o Python
> interrompe blocos indentados em linhas vazias e **engole exceções** — a carga fica pela
> metade e o exit code ainda vem `0`. Use sempre `manage.py <comando>`.

### Atualizando os dados em produção

As planilhas de `base_datas/` entram na imagem Docker, então não é preciso copiar arquivo:

```bash
cd /var/www/ifem && ./deploy.sh                              # sobe o código novo
docker compose exec ifem python manage.py recriar_banco       # confira o plano
docker compose exec ifem python manage.py recriar_banco --confirmar
```

> 🚨 **Tire um backup do banco antes** (snapshot no painel da DigitalOcean ou `pg_dump`).
> O comando derruba todas as tabelas — não há desfazer.

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