"""Recria o banco do zero e recarrega todos os dados das planilhas de base_datas/.

POR QUE ESTE COMANDO EXISTE
O fluxo de atualização de dados deste projeto regera as migrations do zero (apaga
home/migrations/* e roda makemigrations), o que produz um 0001_initial novo,
incompatível com o histórico já registrado em django_migrations no banco.

Quando isso acontece, `migrate` não tem o que aplicar — ele vê 0001_initial como já
aplicada e não faz nada — enquanto o código passa a esperar um schema diferente
(colunas renomeadas, tabelas novas, primary key trocada). O app sobe e quebra em
runtime com ProgrammingError: column ... does not exist.

Como todos os dados vêm das planilhas em base_datas/ e são integralmente
substituídos a cada carga, a saída correta não é escrever migration de transição:
é derrubar o schema e reconstruir. É o que este comando faz, na ordem certa.

O QUE É PRESERVADO
Apenas Noticia — é o único modelo alimentado pelo admin, não por planilha. É
exportado antes do drop e reimportado no fim. Todo o resto é reconstruído.

USO
    python manage.py recriar_banco                 # mostra o plano e aborta (dry-run)
    python manage.py recriar_banco --confirmar     # executa

    # dentro do container, em produção:
    docker compose exec ifem python manage.py recriar_banco --confirmar

Idempotente: pode rodar quantas vezes precisar, o resultado é sempre o mesmo.
"""
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from home.models import (
    Cadunico,
    ContaDetalhada,
    ContaDetalhadaPercentil,
    ContaEspecifica,
    ContaEspecificaPercentil,
    ContaMaisEspecifica,
    ContaMaisEspecificaPercentil,
    CrescimentoMedioPorte,
    CrescimentoMedioUf,
    Indicadores2000,
    IndicadoresAtuais,
    MediaNacionalReceita,
    MediaPorteReceita,
    MediaUfReceita,
    MedianaNacionalReceita,
    MedianaPorteReceita,
    MedianaUfReceita,
    Municipio,
    Noticia,
    Percentis,
    RegiaoMetropolitana,
    SusDependente,
)

# Ordem obrigatória: 01 cria os Municipio que todos os demais referenciam por FK,
# e 02 depende de 01 para associar as RMs.
COMANDOS_DE_IMPORTACAO = [
    "01_importar_municipios",
    "02_importar_rm",
    "03_importar_contas",
    "04_importar_contas_01",
    "05_importar_contas_02",
    "06_percentil",
    "07_media_nacional_detalhamento",
    "08_mediana_nacional_detalhamento",
    "09_crescimento_medio",
]

# Piso de sanidade por tabela. Não são contagens exatas — a cobertura varia a cada
# ano de dados — mas qualquer valor abaixo disto significa carga parcial, que é o
# modo de falha perigoso: o site sobe e serve dados incompletos sem sinal de erro.
MINIMOS_ESPERADOS = {
    Municipio: 5000,
    RegiaoMetropolitana: 50,
    Percentis: 90,
    Indicadores2000: 5000,
    IndicadoresAtuais: 5000,
    SusDependente: 5000,
    Cadunico: 5000,
    ContaDetalhada: 5000,
    ContaDetalhadaPercentil: 5000,
    ContaEspecifica: 5000,
    ContaEspecificaPercentil: 5000,
    ContaMaisEspecifica: 5000,
    ContaMaisEspecificaPercentil: 5000,
    MediaNacionalReceita: 1,
    MediaUfReceita: 20,
    MediaPorteReceita: 5,
    MedianaNacionalReceita: 1,
    MedianaUfReceita: 20,
    MedianaPorteReceita: 5,
    CrescimentoMedioUf: 20,
    CrescimentoMedioPorte: 5,
}


class Command(BaseCommand):
    help = "Derruba o schema, aplica as migrations e recarrega todos os dados de base_datas/."

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirmar",
            action="store_true",
            help="Executa de fato. Sem esta flag o comando só mostra o plano e sai.",
        )
        parser.add_argument(
            "--sem-preservar-noticias",
            action="store_true",
            help="Não exporta/reimporta as Notícias cadastradas no admin (elas serão perdidas).",
        )

    def handle(self, *args, **options):
        confirmado = options["confirmar"]
        preservar_noticias = not options["sem_preservar_noticias"]

        db = connection.settings_dict
        alvo = f"{db.get('ENGINE', '').split('.')[-1]} · {db.get('NAME')}"
        if db.get("HOST"):
            alvo += f" @ {db['HOST']}"

        if not confirmado:
            self.stdout.write(self.style.WARNING("MODO DE VERIFICAÇÃO — nada será alterado.\n"))
            self.stdout.write(f"Banco alvo         : {alvo}")
            self.stdout.write(f"Tabelas a derrubar : {len(connection.introspection.table_names())}")
            self.stdout.write(f"Notícias a preservar: {Noticia.objects.count() if preservar_noticias else 0}")
            self.stdout.write("Imports que rodarão : " + ", ".join(COMANDOS_DE_IMPORTACAO))
            self.stdout.write(self.style.WARNING("\nPara executar de verdade: --confirmar"))
            return

        self.stdout.write(self.style.WARNING(f"Recriando o banco: {alvo}"))

        backup_noticias = None
        if preservar_noticias:
            backup_noticias = self._exportar_noticias()

        self._derrubar_tabelas()

        self.stdout.write("\n[2/4] Aplicando migrations...")
        call_command("migrate", interactive=False, verbosity=1)

        self.stdout.write("\n[3/4] Carregando dados das planilhas...")
        for i, comando in enumerate(COMANDOS_DE_IMPORTACAO, start=1):
            self.stdout.write(f"  ({i}/{len(COMANDOS_DE_IMPORTACAO)}) {comando}")
            # Sem try/except de propósito: se um import falha, parar aqui é o
            # comportamento correto. Seguir adiante produziria um banco parcial,
            # e os comandos seguintes dependem dos Municipio criados pelo 01.
            call_command(comando, verbosity=0)

        if backup_noticias is not None:
            self._restaurar_noticias(backup_noticias)

        self._validar()

    def _exportar_noticias(self) -> Path | None:
        """Serializa as Notícias para um arquivo temporário antes do drop.

        Retorna None quando não há nada a preservar, para o passo de restauração
        ser pulado sem precisar de flag extra.
        """
        total = Noticia.objects.count()
        if total == 0:
            self.stdout.write("[1/4] Nenhuma notícia cadastrada — nada a preservar.")
            return None

        destino = Path(tempfile.gettempdir()) / "ifem_noticias_backup.json"
        with destino.open("w", encoding="utf-8") as arquivo:
            call_command("dumpdata", "home.Noticia", indent=2, stdout=arquivo)
        self.stdout.write(f"[1/4] {total} notícia(s) exportada(s) para {destino}")
        return destino

    def _restaurar_noticias(self, backup: Path) -> None:
        self.stdout.write("\n[4/4] Restaurando notícias...")
        try:
            call_command("loaddata", str(backup), verbosity=0)
        except Exception as erro:
            # O backup em disco é a rede de segurança: sem apontar onde ele está,
            # a falha aqui significaria perder as notícias silenciosamente.
            raise CommandError(
                f"Falha ao restaurar as notícias a partir de {backup}: {erro}. "
                f"O arquivo foi mantido — recarregue com: manage.py loaddata {backup}"
            ) from erro
        self.stdout.write(self.style.SUCCESS(f"  {Noticia.objects.count()} notícia(s) restaurada(s)."))

    def _derrubar_tabelas(self) -> None:
        """Remove todas as tabelas, inclusive django_migrations.

        Zerar django_migrations é o ponto central: é o que permite ao `migrate`
        seguinte aplicar o 0001_initial novo do zero, em vez de considerá-lo já
        aplicado e não fazer nada.
        """
        tabelas = connection.introspection.table_names()
        if not tabelas:
            self.stdout.write("\n[1/4] Banco já está vazio.")
            return

        self.stdout.write(f"\n[1/4] Derrubando {len(tabelas)} tabela(s)...")
        # Nomes vêm da introspecção do próprio banco, nunca de entrada do usuário.
        with connection.cursor() as cursor:
            if connection.vendor == "postgresql":
                for tabela in tabelas:
                    cursor.execute(f'DROP TABLE IF EXISTS "{tabela}" CASCADE')
            else:
                # SQLite não tem CASCADE em DROP TABLE; desligar a checagem de FK
                # evita depender da ordem de remoção.
                cursor.execute("PRAGMA foreign_keys = OFF")
                for tabela in tabelas:
                    cursor.execute(f'DROP TABLE IF EXISTS "{tabela}"')
                cursor.execute("PRAGMA foreign_keys = ON")

    def _validar(self) -> None:
        """Confere que nenhuma tabela ficou abaixo do piso de sanidade."""
        self.stdout.write("\nConferência final:")
        problemas = []
        for modelo, minimo in MINIMOS_ESPERADOS.items():
            total = modelo.objects.count()
            ok = total >= minimo
            if not ok:
                problemas.append(f"{modelo.__name__}: {total} (esperado ≥ {minimo})")
            marca = "  ok  " if ok else " FALHA"
            self.stdout.write(f"{marca} {modelo.__name__:32} {total}")

        if problemas:
            raise CommandError(
                "Carga incompleta — o banco NÃO está pronto para uso:\n  "
                + "\n  ".join(problemas)
            )

        self.stdout.write(self.style.SUCCESS("\nBanco recriado e validado com sucesso."))
