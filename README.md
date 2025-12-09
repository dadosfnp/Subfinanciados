# 📊 Subfinanciados

Sistema Django para **análise de dados financeiros municipais**, com visualização detalhada e mapa interativo, voltado para identificar e analisar municípios subfinanciados a partir de dados contábeis e estatísticos.

---

## 🚀 Funcionalidades Principais

- **📥 Importação de dados** a partir de planilhas Excel (`base_datas/`) para o banco de dados SQLite.
- **🏠 Página inicial (`home`)** com visão geral e filtros de busca.
- **📄 Página de detalhes (`detail`)** com informações financeiras de cada município.
- **🗺 Mapa interativo (`map`)** para visualização geográfica dos municípios.
- **📊 Cálculo de percentis e métricas** a partir de dados importados.
- **🛠 Comandos customizados do Django** para processar e carregar dados automaticamente.

---

## 🗂 Estrutura do Projeto

```
Subfinanciados/
 ├── base_datas/                # Planilhas Excel usadas para importação de dados
 ├── base_statics/              # CSS e arquivos estáticos globais
 ├── base_templates/            # Templates HTML globais
 ├── config/                    # Configuração principal do Django
 ├── home/                      # App inicial + importação de dados
 ├── detail/                    # App para exibir detalhes dos municípios
 ├── map/                       # App para exibir o mapa interativo
 ├── db.sqlite3                 # Banco de dados SQLite
 ├── manage.py                  # Comando principal Django
 └── requirements.txt           # Dependências do projeto
```

### 📁 Pastas importantes

- **`base_datas/`** → Contém os arquivos de entrada no formato `.xls` ou `.xlsx`:
  - `Composicao_RM_2023.xls`
  - `conta_especifica_detalhada.xlsx`
  - `conta_gerais_detalhada.xlsx`
  - `conta_mais_especifica_detalhada.xlsx`
  - `percentis_especificos_detalhado.xlsx`
  - `percentis_gerais_detalhado.xlsx`
  - `percentis_mais_especificos_detalhado.xlsx`
  - `rc_23.xlsx`
  - `receitas_contas.xlsx`

- **`home/management/commands/`** → Scripts de importação de dados, executados via:
  ```bash
  python manage.py nome_do_comando
  ```

- **`templates/`** → Contém os templates HTML de cada app.
- **`static/`** → Contém arquivos CSS e JavaScript.

---

## 📥 Importando Dados

Os dados são importados via **comandos customizados**:

```bash
python manage.py import_accounts                   # Contas gerais
python manage.py import_detail_accounts            # Contas detalhadas
python manage.py import_rm                         # Composição regional
python manage.py import_specific_accounts          # Contas específicas
python manage.py import_specific_detailed_accounts # Contas específicas detalhadas
```

> ⚠ **Importante:** Antes de rodar, coloque todos os arquivos de entrada corretos em `base_datas/`.

---

## 💻 Como Rodar o Projeto

1. **Clonar o repositório**
```bash
git clone <url-do-repo>
cd Subfinanciados
```

2. **Criar e ativar o ambiente virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate   # Windows
```

3. **Instalar dependências**
```bash
pip install -r requirements.txt
```

4. **Aplicar migrações**
```bash
python manage.py migrate
```

5. **Rodar o servidor**
```bash
python manage.py runserver
```

6. **Acessar o sistema**
```
http://127.0.0.1:8000/
```

---

## 🗺 Uso do Mapa

O módulo `map/` permite visualizar no mapa:
- Localização geográfica dos municípios
- Status de financiamento
- Dados resumidos ao clicar em um ponto

O mapa é alimentado pelos dados importados e pode ser customizado para exibir filtros.

---

## 🔍 Uso da Página de Detalhes

O módulo `detail/` exibe:
- Receita por conta
- Percentis por município
- Evolução histórica
- Comparações com outros municípios

A URL segue o formato:
```
/detail/<id_municipio>/
```

---

## 📌 Tecnologias Utilizadas

- **Django** → Backend e gerenciamento do projeto
- **SQLite** → Banco de dados local
- **Bootstrap** → Layout responsivo
- **JavaScript** → Interatividade no mapa e gráficos
- **Pandas** → Leitura e manipulação de planilhas Excel
- **Leaflet.js** (ou similar) → Mapa interativo

---

## 👨‍💻 Comandos Úteis para Desenvolvimento

- Criar superusuário:
```bash
python manage.py createsuperuser
```
- Listar comandos disponíveis:
```bash
python manage.py help
```
- Executar servidor:
```bash
python manage.py runserver
```

## 👨‍💻 Comandos GIT para Desenvolvimento
- Verificar status da branch e logs:
```bash
git status                # Mostra mudanças não commitadas e estado atual
git log                   # Histórico completo de commits 
```
- Trabalhando com alterações:
```bash
git add arquivo.ext       # Adiciona arquivo específico à área de staging
git add .                 # Adiciona todas as mudanças
git commit -m "Mensagem"  # Faz commit com mensagem
git commit --amend        # Edita o último commit (ex: corrigir mensagem)
```
- Branches (ramificações):
```bash
git branch                # Lista branches locais
git branch nome-branch    # Cria nova branch
git checkout nome-branch  # Vai para uma branch existente
git checkout -b nova      # Cria e troca para nova branch
```
- Sincronização com remoto:
```bash
git fetch                    # Busca mudanças do remoto (sem aplicar)
git pull                     # Atualiza branch local com remoto
git push                     # Envia commits para o remoto
git push -u origin main      # Primeira vez para setar upstream
git push origin nome-branch  # Envia branch específica
```
---

## 🔁 Fluxo de Trabalho (Fork + Branch + Pull Request)

Este projeto utiliza um **fluxo profissional baseado em Fork**, garantindo que o ambiente de **produção permaneça sempre estável**, enquanto as melhorias são desenvolvidas de forma isolada.

### 🏗 Estrutura de Repositórios

- **Produção oficial:**  
  `dadosfnp/Subfinanciados` → branch `main`

- **Ambiente de Desenvolvimento (Fork):**  
  `pedrofnp/IFEM` → branch `main`

Toda **nova funcionalidade ou melhoria é desenvolvida no fork**, nunca diretamente na `main` de produção.

---

# ============================================================
# ✅ CICLO COMPLETO DE DESENVOLVIMENTO (FORK + BRANCH + PR)
# ============================================================

# 1) Sincronizar a main do fork com a produção (ANTES de iniciar qualquer feature)
git checkout main
git pull upstream main
git push origin main

# ------------------------------------------------------------

# 2) Criar uma nova branch para a feature
git checkout -b feature/nome-da-melhoria

# Exemplos de nomes:
# feature/mapa-zoom
# feature/popup-auto
# feature/print-mapa
# feature/novos-indicadores

# ------------------------------------------------------------

# 3) Trabalhar normalmente na feature
git add .
git commit -m "feat(map): adiciona zoom automático por município"
git push -u origin feature/nome-da-melhoria

# (Esse push envia a branch para: pedrofnp/IFEM:feature/nome-da-melhoria)

# ------------------------------------------------------------

# 4) Criar Pull Request no GitHub
# Base:     dadosfnp/Subfinanciados:main
# Compare: pedrofnp/IFEM:feature/nome-da-melhoria

# ------------------------------------------------------------

# 5) Após o merge do Pull Request, sincronizar novamente o fork
git checkout main
git pull upstream main
git push origin main

# ============================================================
# ✅ REGRAS IMPORTANTES
# ============================================================
# - NUNCA desenvolver diretamente na main
# - Toda mudança nasce em feature/*
# - Toda entrega passa por Pull Request
# - O fork (pedrofnp/IFEM) é o ambiente de desenvolvimento
# - A main representa sempre a versão de produção
# ============================================================



## 📝 Convenção de Commits

Utilizamos uma convenção baseada no **Conventional Commits**, adaptada para o projeto.  
O formato geral é:

### 🔑 Tipos aceitos

- **feat** → nova funcionalidade  
  - `feat(map): adiciona lupa ao filtro de municípios`
- **fix** → correção de bug  
  - `fix(detail): corrige alinhamento do botão de busca`
- **docs** → alterações apenas em documentação  
  - `docs(readme): adiciona seção de boas práticas`
- **style** → ajustes visuais (CSS, HTML, formatação, sem alterar lógica)  
  - `style(home): ajusta espaçamento dos cards`
- **refactor** → refatoração de código sem mudar comportamento  
  - `refactor(map): simplifica função de atualização dos filtros`
- **test** → adição ou ajuste em testes  
  - `test(detail): adiciona teste para cálculo de percentis`
- **chore** → tarefas gerais (build, dependências, configs)  
  - `chore: atualiza requirements.txt`


### ✅ Boas práticas

- **Descrição curta** (máx. 72 caracteres) → explique o que foi feito.  
- **Escopo** (opcional) → indique onde foi feita a mudança (`home`, `map`, `detail`, `readme`, etc.).  
- Use o **imperativo**: “adiciona”, “corrige”, “refatora”, em vez de “adicionado”, “corrigido”.  



✍ **Autor:** FNP  
📅 **Ano:** 2025  
📄 **Licença:** Uso interno / restrito
