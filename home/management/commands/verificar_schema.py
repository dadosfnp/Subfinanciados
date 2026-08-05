"""Verifica se o schema do banco corresponde ao que os models esperam.

POR QUE ESTE COMANDO EXISTE
`migrate` não detecta o problema mais perigoso deste projeto. Quando as migrations
são regeradas do zero, o 0001_initial novo já consta como aplicado no banco: o
`migrate` diz "No migrations to apply" e sai com sucesso, enquanto o código passa a
esperar colunas que não existem. O deploy parece ter dado certo e o site serve 500.

Este comando compara os models com o schema real, coluna a coluna, e falha quando
divergem. Roda no deploy.sh depois do build e antes de trocar o container, de modo
que um deploy incompatível é barrado com o site atual ainda no ar.

USO
    python manage.py verificar_schema     # exit 0 se compatível, 1 se divergente

Quando acusa divergência, o caminho é `manage.py recriar_banco --confirmar`.
"""
from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Compara o schema do banco com os models. Exit 1 se houver divergência."

    def add_arguments(self, parser):
        parser.add_argument(
            "--silencioso",
            action="store_true",
            help="Não imprime as tabelas compatíveis, só as divergências.",
        )

    def handle(self, *args, **options):
        silencioso = options["silencioso"]

        tabelas_no_banco = set(connection.introspection.table_names())
        tabelas_faltando = []
        colunas_faltando = []
        colunas_extras = []
        compativeis = 0

        with connection.cursor() as cursor:
            for modelo in apps.get_models():
                if not modelo._meta.managed or modelo._meta.proxy:
                    continue

                tabela = modelo._meta.db_table
                rotulo = f"{modelo._meta.app_label}.{modelo.__name__}"

                if tabela not in tabelas_no_banco:
                    tabelas_faltando.append(f"{rotulo} (tabela '{tabela}')")
                    continue

                esperadas = {campo.column for campo in modelo._meta.local_fields}
                reais = {
                    coluna.name
                    for coluna in connection.introspection.get_table_description(cursor, tabela)
                }

                faltando = esperadas - reais
                # Colunas a mais não quebram nada em runtime — o Django simplesmente as
                # ignora — mas denunciam que o schema ficou para trás do código.
                extras = reais - esperadas

                if faltando:
                    colunas_faltando.append(f"{rotulo}: {', '.join(sorted(faltando))}")
                if extras:
                    colunas_extras.append(f"{rotulo}: {', '.join(sorted(extras))}")
                if not faltando and not extras:
                    compativeis += 1
                    if not silencioso:
                        self.stdout.write(f"  ok   {rotulo}")

        return self._relatar(compativeis, tabelas_faltando, colunas_faltando, colunas_extras)

    def _relatar(self, compativeis, tabelas_faltando, colunas_faltando, colunas_extras):
        """Imprime o resultado. Levanta SystemExit(1) se o banco estiver incompatível."""
        if tabelas_faltando:
            self.stdout.write(self.style.ERROR("\nTABELAS QUE NÃO EXISTEM NO BANCO:"))
            for item in tabelas_faltando:
                self.stdout.write(self.style.ERROR(f"  - {item}"))

        if colunas_faltando:
            self.stdout.write(self.style.ERROR("\nCOLUNAS QUE O CÓDIGO ESPERA E O BANCO NÃO TEM:"))
            for item in colunas_faltando:
                self.stdout.write(self.style.ERROR(f"  - {item}"))

        if colunas_extras:
            self.stdout.write(self.style.WARNING("\nCOLUNAS NO BANCO QUE O CÓDIGO NÃO USA MAIS:"))
            for item in colunas_extras:
                self.stdout.write(self.style.WARNING(f"  - {item}"))

        incompativel = bool(tabelas_faltando or colunas_faltando)

        if incompativel:
            self.stdout.write(
                self.style.ERROR(
                    "\nSCHEMA INCOMPATÍVEL — subir este código quebraria o site com\n"
                    "ProgrammingError em toda página que tocar nessas tabelas.\n\n"
                    "Para resolver (derruba e recarrega os dados das planilhas):\n"
                    "    docker compose exec ifem python manage.py recriar_banco\n"
                    "    docker compose exec ifem python manage.py recriar_banco --confirmar\n\n"
                    "Tire um backup do banco antes."
                )
            )
            # SystemExit em vez de CommandError: o deploy.sh testa o exit code, e o
            # CommandError imprimiria um traceback que só atrapalha a leitura do log.
            raise SystemExit(1)

        if colunas_extras:
            self.stdout.write(
                self.style.WARNING(
                    f"\n{compativeis} tabela(s) compatível(is). Há colunas sobrando, mas o código "
                    "não depende delas — o deploy pode seguir."
                )
            )
            return

        self.stdout.write(self.style.SUCCESS(f"\nSchema compatível ({compativeis} tabelas conferidas)."))
