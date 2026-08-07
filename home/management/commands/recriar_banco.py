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
Só o que não vem de planilha e se perderia para sempre: as Notícias (cadastradas
no admin) e as contas de acesso ao admin (usuários e grupos). Tudo isso é
exportado antes do drop e reimportado no fim; o resto é reconstruído.

O drop atinge todas as tabelas do database, inclusive auth_user — sem esta
exportação, recriar o banco custaria o acesso ao próprio admin.

ESCOPO DO DROP
Apenas o database ao qual esta aplicação está conectada (em produção, `ifem`).
Outros databases do mesmo cluster PostgreSQL — como o `fnp_sistema` — são
isolados e não são tocados.

USO
    python manage.py recriar_banco                 # mostra o plano e aborta (dry-run)
    python manage.py recriar_banco --confirmar     # executa

    # em produção, NÃO chame direto: use o script, que faz o backup antes e roda a
    # partir da imagem nova (um `docker compose exec` pegaria o container antigo):
    cd /var/www/ifem && ./atualizar-banco.sh

Idempotente: pode rodar quantas vezes precisar, o resultado é sempre o mesmo.
"""
import tempfile
from pathlib import Path

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from home.models import (
    AdaptaBrasil,
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
    Percentis,
    RegiaoMetropolitana,
    SusDependente,
)

# Tudo que não vem das planilhas e não pode ser reconstruído: conteúdo do admin e
# as próprias contas de acesso a ele. Grupos antes de usuários, porque o usuário
# referencia o grupo. As permissões não entram na lista — o migrate as recria, e o
# dump usa natural keys justamente para reencontrá-las mesmo com IDs diferentes.
MODELOS_A_PRESERVAR = ["auth.Group", "auth.User", "home.Noticia"]

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
    "10_adapta_brasil"
]
def descobrir_comandos_de_importacao():
    """Lista os comandos de import na ordem do prefixo numérico (01, 02, ... 10).

    Descoberta automática, e não lista fixa, porque comandos novos aparecem a cada
    atualização de dados. Uma lista fixa aqui significaria que o próximo comando
    criado seria silenciosamente ignorado, e a tabela dele ficaria vazia depois de
    um recriar_banco — o tipo de falha que só se descobre com o site no ar.

    O prefixo com zero à esquerda faz a ordenação alfabética coincidir com a
    numérica, que é obrigatória: o 01 cria os Municipio que os demais referenciam.
    """
    pasta = Path(__file__).parent
    return sorted(
        arquivo.stem
        for arquivo in pasta.glob("[0-9][0-9]_*.py")
        if not arquivo.stem.startswith("_")
    )

# Piso de sanidade por tabela. Não são contagens exatas — a cobertura varia a cada
# ano de dados — mas qualquer valor abaixo disto significa carga parcial, que é o
# modo de falha perigoso: o site sobe e serve dados incompletos sem sinal de erro.
MINIMOS_ESPERADOS = {
    Municipio: 5000,
    AdaptaBrasil: 5000,
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
            "--sem-preservar-conteudo",
            action="store_true",
            help=(
                "Não exporta/reimporta o conteúdo do admin (notícias, usuários e grupos). "
                "Eles serão perdidos."
            ),
        )

    def handle(self, *args, **options):
        confirmado = options["confirmar"]
        preservar = not options["sem_preservar_conteudo"]

        db = connection.settings_dict
        alvo = f"{db.get('ENGINE', '').split('.')[-1]} · {db.get('NAME')}"
        if db.get("HOST"):
            alvo += f" @ {db['HOST']}"

        if not confirmado:
            self.stdout.write(self.style.WARNING("MODO DE VERIFICAÇÃO — nada será alterado.\n"))
            self.stdout.write(f"Banco alvo         : {alvo}")
            self.stdout.write("                     (só este database; outros do mesmo cluster não são tocados)")
            self.stdout.write(f"Tabelas a derrubar : {len(connection.introspection.table_names())}")
            if preservar:
                self.stdout.write("A preservar        : " + ", ".join(f"{r} ({t})" for r, t in self._inventario()))
            else:
                self.stdout.write(self.style.WARNING("A preservar        : NADA (--sem-preservar-conteudo)"))
            self.stdout.write("Imports que rodarão : " + ", ".join(descobrir_comandos_de_importacao()))
            self.stdout.write(self.style.WARNING("\nPara executar de verdade: --confirmar"))
            return

        self.stdout.write(self.style.WARNING(f"Recriando o banco: {alvo}"))

        backup_noticias = None
        if preservar:
            backup_noticias = self._exportar_noticias()

        self._derrubar_tabelas()

        self.stdout.write("\n[2/4] Aplicando migrations...")
        call_command("migrate", interactive=False, verbosity=1)

        self.stdout.write("\n[3/4] Carregando dados das planilhas...")
        comandos = descobrir_comandos_de_importacao()
        for i, comando in enumerate(comandos, start=1):
            self.stdout.write(f"  ({i}/{len(comandos)}) {comando}")
            # Sem try/except de propósito: se um import falha, parar aqui é o
            # comportamento correto. Seguir adiante produziria um banco parcial,
            # e os comandos seguintes dependem dos Municipio criados pelo 01.
            call_command(comando, verbosity=0)

        if backup_noticias is not None:
            self._restaurar_noticias(backup_noticias)

        self._validar()

    def _inventario(self) -> list[tuple[str, int]]:
        """Quantas linhas existem hoje em cada modelo preservado."""
        return [(rotulo, apps.get_model(rotulo).objects.count()) for rotulo in MODELOS_A_PRESERVAR]

    def _exportar_noticias(self) -> Path | None:
        """Serializa o conteúdo do admin para um arquivo temporário antes do drop.

        Retorna None quando não há nada a preservar, para o passo de restauração
        ser pulado sem precisar de flag extra.
        """
        inventario = self._inventario()
        total = sum(quantidade for _, quantidade in inventario)
        if total == 0:
            self.stdout.write("[1/4] Nada a preservar (sem notícias e sem usuários).")
            return None

        destino = Path(tempfile.gettempdir()) / "ifem_conteudo_backup.json"
        with destino.open("w", encoding="utf-8") as arquivo:
            # natural_foreign: grava as permissões por (codename, app_label) em vez de
            # por ID. O migrate recria as permissões com IDs novos, então referenciar
            # por ID devolveria permissões trocadas — ou nenhuma — aos usuários.
            call_command(
                "dumpdata",
                *MODELOS_A_PRESERVAR,
                natural_foreign=True,
                indent=2,
                stdout=arquivo,
            )
        resumo = ", ".join(f"{quantidade} de {rotulo}" for rotulo, quantidade in inventario if quantidade)
        self.stdout.write(f"[1/4] Exportado para {destino}: {resumo}")
        return destino

    def _restaurar_noticias(self, backup: Path) -> None:
        self.stdout.write("\n[4/4] Restaurando conteúdo do admin...")
        try:
            call_command("loaddata", str(backup), verbosity=0)
        except Exception as erro:
            # O backup em disco é a rede de segurança: sem apontar onde ele está,
            # a falha aqui significaria perder notícias e usuários em silêncio.
            raise CommandError(
                f"Falha ao restaurar o conteúdo a partir de {backup}: {erro}. "
                f"O arquivo foi mantido — recarregue com: manage.py loaddata {backup}"
            ) from erro
        restaurado = ", ".join(f"{quantidade} de {rotulo}" for rotulo, quantidade in self._inventario() if quantidade)
        self.stdout.write(self.style.SUCCESS(f"  {restaurado}."))

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
