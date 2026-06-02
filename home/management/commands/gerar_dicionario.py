"""Gera o dicionário de dados do projeto a partir dos models do Django.

Lê os models de todos os apps locais (sob BASE_DIR) por introspection e produz
um Markdown padronizado — uma tabela por model com coluna do banco, atributo,
tipo, nulo, índice, único e descrição. Como é gerado, nunca diverge do schema real.

Uso:
    python manage.py gerar_dicionario              # imprime no stdout
    python manage.py gerar_dicionario -o docs/dicionario-dados.md

Padrão da FNP: rode novamente sempre que mexer nos models, e versione o resultado.
"""
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand


def _bool(valor):
    """Renderiza booleanos como ✓/—, para uma tabela mais legível."""
    return "✓" if valor else "—"


class Command(BaseCommand):
    help = "Gera o dicionário de dados (Markdown) a partir dos models locais."

    def add_arguments(self, parser):
        parser.add_argument(
            "-o", "--output",
            help="Arquivo de saída. Se omitido, imprime no stdout.",
        )

    def handle(self, *args, **options):
        base_dir = str(settings.BASE_DIR)
        linhas = [
            "# Dicionário de Dados — IFEM/Subfinanciados",
            "",
            "> **Gerado automaticamente** por `python manage.py gerar_dicionario`. "
            "Não edite à mão — rode o comando novamente após alterar os models.",
            "",
            "Legenda: **PK** = chave primária · **Índice** inclui PK/único/`db_index` · "
            "**FK →** tabela referenciada.",
            "",
        ]

        # Considera apenas apps locais (dentro do projeto), ignorando Django e libs.
        app_configs = [
            ac for ac in apps.get_app_configs()
            if str(ac.path).startswith(base_dir) and "site-packages" not in str(ac.path)
        ]

        for app_config in sorted(app_configs, key=lambda a: a.label):
            models = list(app_config.get_models())
            if not models:
                continue
            linhas.append(f"\n## App: `{app_config.label}`\n")

            for model in sorted(models, key=lambda m: m._meta.db_table):
                meta = model._meta
                # Docstring padrão do Django (auto-gerada) começa com o nome da classe;
                # só usamos o docstring quando é uma descrição real escrita por humano.
                doc = (model.__doc__ or "").strip()
                if doc.startswith(model.__name__ + "("):
                    doc = ""

                linhas.append(f"### `{meta.db_table}` — {model.__name__}")
                if doc:
                    linhas.append(f"\n{doc}\n")
                linhas.append("")
                linhas.append("| Coluna | Atributo | Tipo | Nulo | Índice | Único | FK → | Descrição |")
                linhas.append("|---|---|---|---|---|---|---|---|")

                for field in meta.concrete_fields:
                    fk = ""
                    if field.is_relation and field.many_to_one and field.related_model:
                        fk = f"`{field.related_model._meta.db_table}`"
                    tipo = field.get_internal_type()
                    max_length = getattr(field, "max_length", None)
                    if max_length:
                        tipo += f"({max_length})"
                    indexado = field.db_index or field.primary_key or field.unique
                    descricao = (str(field.help_text) or str(field.verbose_name)).replace("\n", " ").strip()
                    nome_attr = field.name + (" 🔑" if field.primary_key else "")
                    linhas.append(
                        f"| `{field.column}` | {nome_attr} | {tipo} | {_bool(field.null)} "
                        f"| {_bool(indexado)} | {_bool(field.unique)} | {fk} | {descricao} |"
                    )

                # Campos ManyToMany (tabelas de junção) entram como nota.
                for field in meta.many_to_many:
                    alvo = field.related_model._meta.db_table
                    linhas.append(
                        f"| _(M2M)_ `{field.name}` | {field.name} | ManyToMany | — | — | — "
                        f"| `{alvo}` | {str(field.help_text).strip()} |"
                    )
                linhas.append("")

        conteudo = "\n".join(linhas) + "\n"

        output = options.get("output")
        if output:
            caminho = Path(output)
            caminho.parent.mkdir(parents=True, exist_ok=True)
            caminho.write_text(conteudo, encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"Dicionário gravado em {caminho}"))
        else:
            self.stdout.write(conteudo)
