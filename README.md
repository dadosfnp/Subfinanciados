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

1.  **Clone o repositório e entre na pasta:**
    ```bash
    git clone git@github.com:dadosfnp/Subfinanciados.git
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
4.  **Carregue os dados:**
    ```bash
    docker compose exec ifem python manage.py recriar_banco --confirmar
    ```
    As planilhas já vêm dentro da imagem, então não é preciso pedir arquivo a ninguém.
    Demora uns 10 minutos.
5.  **Abra http://localhost:8003** — plataforma completa com os 5.570 municípios.

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

> ⚠️ **`git pull` no servidor não atualiza o site.** O código é copiado para dentro da
> imagem Docker quando ela é construída. Se você só baixar o código novo, o container
> continua rodando a imagem antiga. É preciso reconstruir a imagem e recriar o container —
> é o que o `deploy.sh` faz.

### 🚀 Como publicar uma alteração (passo a passo)

**Você não precisa entrar no servidor.** Todo push na `main` publica sozinho.

O passo 4 é o que costuma pegar as pessoas — leia até o fim antes de começar.

#### Passo 1 — Faça a alteração numa branch

```bash
git checkout main
git pull production main
git checkout -b feat/nome-da-sua-tarefa
```

Se você mexeu nas planilhas, elas ficam em `base_datas/` e vão para o git normalmente.

#### Passo 2 — Commite e envie

```bash
git add .
git commit -m "update: descreva o que mudou"
git push -u production feat/nome-da-sua-tarefa
```

#### Passo 3 — Abra o Pull Request e faça o merge

Abra o PR no GitHub, da sua branch para a `main`, e faça o merge. **O merge é o que dispara a publicação.**

#### Passo 4 — Veja se publicou mesmo

Vá em **Actions → Deploy produção (droplet)** no GitHub e abra o job mais recente.

Uma das duas coisas vai acontecer:

**✅ Ficou verde** → publicou. Abra https://ifem.fnp.org.br e confira. Acabou.

**❌ Ficou vermelho com `SCHEMA INCOMPATÍVEL`** → o banco de dados ainda tem o formato antigo e não aguenta o código novo. **O site continua no ar com a versão anterior** — nada quebrou. Vá para o passo 5.

> Isso é esperado toda vez que você apaga a pasta `home/migrations/` e roda `makemigrations`
> de novo. Não é erro seu nem bug: o deploy está impedindo que o site fique fora do ar.

#### Passo 5 — Só se deu vermelho: atualize o banco

Aqui você entra no servidor. **São 3 comandos:**

```bash
ssh root@142.93.205.222
cd /var/www/ifem
./atualizar-banco.sh
```

O script mostra o que vai fazer e pede para você digitar `sim` antes de mexer em qualquer coisa. Depois ele:

1. **Faz backup** do banco em `/root/backups/` e confere que o arquivo saiu íntegro. Se o backup falhar, ele para sem apagar nada.
2. **Recria o banco** e recarrega as planilhas. **Demora uns 10 minutos** — é normal, não interrompa.
3. **Sobe o site** com o código novo.

No fim ele lista as tabelas com a quantidade de registros de cada uma e escreve `Banco recriado e validado com sucesso`.

Se aparecer `FALHA` em alguma linha, alguma planilha veio com problema. O caminho do backup fica escrito na tela para você voltar atrás.

> ℹ️ Não rode `docker compose exec ifem ... recriar_banco` na mão. Quando o deploy é
> barrado, o container que está de pé ainda é o antigo — esse comando usaria o código
> velho e deixaria o banco no formato errado. O `atualizar-banco.sh` cuida disso.

#### Passo 6 — Confira

O passo 5 já colocou o site no ar com o código novo. Abra https://ifem.fnp.org.br e veja.

O job vermelho no GitHub continua vermelho — ele registra a tentativa que foi barrada. Se quiser deixar tudo verde, use **Actions → o job que falhou → Re-run jobs**; agora ele passa.

---

### Detalhes de produção (para consulta)

<details>
<summary>Deploy manual — use só se o Actions estiver fora do ar</summary>

```bash
ssh root@142.93.205.222
cd /var/www/ifem
./deploy.sh
```

O `deploy.sh` atualiza o código, reconstrói a imagem, **confere se o banco é compatível** e recria o container.

> ⚠️ **Não use `docker compose up -d --build` direto.** Esse comando pula a conferência do
> banco e publica um site quebrado sem avisar. Use sempre o `./deploy.sh`.

Para ver o site sem expor publicamente, abra um túnel e acesse http://localhost:8003:

```bash
ssh -L 8003:localhost:8003 root@142.93.205.222
```

</details>

<details>
<summary>Como o deploy automático funciona por dentro</summary>

O GitHub Actions (`.github/workflows/deploy.yml`) conecta no droplet por SSH e roda o `deploy.sh`. O `deploy.sh` faz, nesta ordem: atualiza o código → reconstrói a imagem → **confere o banco** → troca o container.

A conferência fica entre a reconstrução e a troca de propósito: a imagem nova já existe, mas o container antigo ainda está servindo o site. Se o banco não for compatível, o deploy para ali e ninguém percebe nada.

Para acompanhar pelo terminal:

```bash
gh run list --repo dadosfnp/subfinanciados --limit 3
gh run view <id> --repo dadosfnp/subfinanciados --log | grep "\[deploy\]"
```

**Acesso do CI:** o Actions entra como `root` com uma chave dedicada, travada no `authorized_keys` do droplet em `command="/var/www/ifem/deploy.sh"`. Essa chave só consegue disparar o deploy — não abre terminal nem roda outro comando. Os secrets são `DROPLET_SSH_HOST`, `DROPLET_SSH_USER`, `DROPLET_SSH_KEY` e `DROPLET_SSH_KNOWN_HOSTS`.

> Se esses secrets forem apagados, o job passa a **terminar verde sem publicar nada**.
> Já aconteceu: um push foi dado como publicado e nunca chegou ao ar. Se o site não mudou
> depois de um job verde, leia o log dele antes de procurar o problema em outro lugar.

**Branch de produção:** o droplet acompanha a `main`. Para conferir, em `/var/www/ifem`: `git branch --show-current`.

</details>

*   **Decisões de arquitetura e passo a passo da migração:** ver `tasks/plan-migracao-droplet.md`, `tasks/runbook-migracao-droplet.md` e o ADR-001 na pasta TIC da FNP.

---

## 📈 Processamento de Dados

Todos os dados vêm das planilhas em `base_datas/`, que ficam versionadas no git. Rodar os
comandos duas vezes é seguro: cada um apaga e recarrega as suas próprias tabelas.

### O comando principal: `recriar_banco`

Faz tudo de uma vez — apaga as tabelas, recria a estrutura e recarrega as 9 etapas na ordem certa.

```bash
python manage.py recriar_banco              # mostra o que vai fazer e para
python manage.py recriar_banco --confirmar  # executa
```

Rode primeiro **sem** `--confirmar`. Ele mostra qual banco vai mexer e o que vai preservar, sem alterar nada.

**O que ele preserva:** as notícias e as contas do admin (usuários, grupos e senhas). Isso é o que não vem de planilha e não daria para recuperar. Todo o resto é recarregado.

**O que ele apaga:** todas as tabelas do banco do IFEM. Em produção, isso é o database `ifem` — os outros bancos do mesmo servidor, como o do sistema da FNP, não são tocados.

**Como saber se deu certo:** no fim ele lista as 21 tabelas com a quantidade de registros de cada uma. Se alguma vier vazia ou quase, ele para e escreve `FALHA` — assim você não fica com o site no ar mostrando dados pela metade.

<details>
<summary>Por que apagar o banco em vez de usar migrations?</summary>

A atualização de dados deste projeto costuma apagar a pasta `home/migrations/` e rodar `makemigrations` do zero. Isso gera um `0001_initial` novo — mas o banco já tem esse nome registrado como aplicado.

Resultado: o `migrate` acha que não tem nada a fazer e termina com sucesso, enquanto o código passa a procurar colunas que não existem. O site sobe e dá erro em toda página.

Como os dados vêm todos das planilhas e são substituídos por inteiro a cada carga, refazer o banco é mais simples e mais seguro do que escrever migrations de conversão a cada atualização.

</details>

### Recarregar só uma parte

Se você quiser recarregar apenas uma etapa, dá para rodar os comandos individualmente.
**A ordem importa:** o `01` cria os municípios que todos os outros usam como referência.

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

> ⚠️ **Nunca rode com `manage.py shell < arquivo`.** Assim o Python engole os erros no meio
> do caminho: a carga fica pela metade e mesmo assim parece ter dado certo. Já aconteceu — as
> tabelas de percentil ficaram vazias por semanas sem ninguém notar. Use sempre
> `manage.py <comando>`.

### Em produção

As planilhas entram na imagem Docker junto com o código, então não precisa copiar arquivo para o servidor. O passo a passo completo está em
[Como publicar uma alteração](#-como-publicar-uma-alteração-passo-a-passo).

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
3.  **Depois de um `git pull`, atualize o seu ambiente local:**
    ```bash
    pip install -r requirements.txt          # se o requirements.txt mudou
    python manage.py recriar_banco --confirmar   # se as migrations ou as planilhas mudaram
    ```
    > Use `recriar_banco`, não `migrate`. Quando as migrations são regeradas do zero — o que
    > é comum aqui — o `migrate` termina sem fazer nada e o seu banco local fica com o
    > formato antigo, dando erro de coluna inexistente ao abrir as páginas.
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

6.  **Depois do merge, confira se publicou.** O merge na `main` dispara o deploy automático,
    e ele pode barrar a publicação de propósito se o banco estiver desatualizado. Veja o
    [passo a passo de publicação](#-como-publicar-uma-alteração-passo-a-passo).

> 📌 **Lembre-se:** o `.env`, o `db.sqlite3` e a pasta `staticfiles/` estão no `.gitignore` e **nunca** vão para o git. Ao trocar de máquina ou após clonar, recrie o `.env` (seção [Como Começar](#-como-começar)) — ele não vem no `git pull`.

---

✍️ **Desenvolvido por:** FNP | 📄 **Licença:** Uso Interno / Restrito