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
