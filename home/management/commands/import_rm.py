import pandas as pd
from django.core.management.base import BaseCommand
from home.models import Municipio, RegiaoMetropolitana

class Command(BaseCommand):
    help = 'Lê o arquivo Excel de RMs e associa aos municípios no banco de dados'

    def handle(self, *args, **options):
        # Caminho para o seu arquivo Excel
        path_arquivo_rm = 'base_datas\Composicao_RM_2023.xls'
        
        self.stdout.write(f'Lendo o arquivo: {path_arquivo_rm}')
        df = pd.read_excel(path_arquivo_rm)

        # Garante que a coluna do código IBGE seja texto
        df['cod_ibge'] = df['cod_ibge'].astype(str)

        # 1. Criar os objetos de RegiaoMetropolitana
        nomes_rm_unicos = df['rm'].unique()
        for nome_rm in nomes_rm_unicos:
            # get_or_create evita a criação de RMs duplicadas
            rm_obj, created = RegiaoMetropolitana.objects.get_or_create(nome=nome_rm)
            if created:
                self.stdout.write(self.style.SUCCESS(f'RM Criada: {rm_obj.nome}'))

        # 2. Associar cada município à sua RM
        total_municipios = len(df)
        self.stdout.write('Associando municípios às RMs...')
        for index, row in df.iterrows():
            cod_ibge = row['cod_ibge']
            nome_rm = row['rm']
            
            try:
                # Encontra o município e a RM no banco de dados
                municipio = Municipio.objects.get(cod_ibge=cod_ibge)
                rm_obj = RegiaoMetropolitana.objects.get(nome=nome_rm)
                
                # Associa a RM ao município e salva
                municipio.rm = rm_obj
                municipio.save()

            except Municipio.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Município com código {cod_ibge} não encontrado no banco.'))
            except RegiaoMetropolitana.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'RM com nome {nome_rm} não encontrada.'))
        
        self.stdout.write(self.style.SUCCESS('Processo de associação concluído!'))
