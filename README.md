# 📊 Subfinanciados

Sistema Django para análise de dados financeiros municipais, com visualização detalhada e mapa interativo.

## 🚀 Funcionalidades
- **Importação de dados** a partir de planilhas Excel (`base_datas/`) para o banco de dados.
- **Página inicial** com visão geral (`home`).
- **Página de detalhes** (`detail`) com informações financeiras de cada município.
- **Mapa interativo** (`map`) para visualização geográfica dos municípios.

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

## 📥 Importando Dados
Os dados são importados via comandos customizados do Django:

```bash
python manage.py import_accounts
python manage.py import_detail_accounts
python manage.py import_rm
python manage.py import_specific_accounts
python manage.py import_specific_detailed_accounts
```

> Cada comando lê arquivos de `base_datas/` e insere no banco SQLite.

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
venv\Scripts\activate     # Windows
```

3. **Instalar dependências**
```bash
pip install -r requirements.txt
```

4. **Rodar o servidor**
```bash
python manage.py runserver
```

5. **Acessar**
```
http://127.0.0.1:8000/
```

## 📌 Tecnologias Utilizadas
- **Django** (backend)
- **SQLite** (banco de dados)
- **Bootstrap / CSS customizado** (frontend)
- **JavaScript** (interatividade)
- **Pandas** (provavelmente para tratamento de planilhas)

---

✍ **Autor:** [Seu Nome]  
📅 **Ano:** 2025
