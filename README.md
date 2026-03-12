# 📊 Subfinanciados

> **Inteligência Fiscal e Populacional para Municípios Brasileiros.**

O **Subfinanciados** é uma plataforma robusta desenvolvida em Django para análise, processamento e visualização de dados fiscais dos municípios brasileiros. O sistema transforma planilhas complexas em dashboards interativos, permitindo identificar disparidades de receita, calcular percentis nacionais e visualizar a saúde financeira municipal por meio de mapas geográficos.

---

## ✨ Destaques do Sistema

*   **⚡ DNA Financeiro:** Árvore de receitas interativa que detalha cada rubrica contábil com comparativos de média e mediana nacional.
*   **🗺️ Análise Geográfica:** Integração com Mapbox para visualização espacial dos dados fiscais e populacionais.
*   **📊 Insights Agregados:** Ferramentas para análise de conjuntos de municípios (por região ou porte), com suporte a valores *Per Capita* e absolutos.
*   **⚙️ Data Engine:** Pipeline automatizado de importação e processamento de dados (`.xlsx`/`.xls`) com validação de integridade.
*   **🎨 Design Premium:** Interface inspirada em sistemas modernos (iOS/MacOS), com Bento Cards, micro-interações e suporte a WhiteNoise.

---

## 🛠️ Stack Tecnológica

![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Mapbox](https://img.shields.io/badge/Mapbox-000000?style=for-the-badge&logo=mapbox&logoColor=white)

---

## 🚀 Como Começar

### Pré-requisitos
*   Python 3.10+
*   Ambiente virtual (venv)

### Instalação Rápida
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