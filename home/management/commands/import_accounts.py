import pandas as pd
import numpy as np
from django.core.management.base import BaseCommand
from home.models import Municipio

class Command(BaseCommand):
    help = 'Importa dados de municípios do arquivo Excel, limpando os nomes das colunas.'

    def handle(self, *args, **kwargs):
        caminho_excel = 'base_datas/rc_23.xlsx'
        df = pd.read_excel(caminho_excel)
        
        # 2. Converte todos os nomes de colunas para minúsculo
        df.columns = df.columns.str.lower()
        # -------------------------

        # Coluna base para o ranking
        coluna_ranking = 'rc_23_pc'

        # 1. Ranking Nacional
        # ascending=False -> O maior valor de rc_23_pc recebe o rank 1
        df['rank_nacional'] = df[coluna_ranking].rank(method='min', ascending=False).astype(int)
        df['total_nacional'] = len(df) # O total é simplesmente o número de municípios

        # 2. Ranking Estadual
        # O groupby('uf') faz o ranking ser calculado separadamente para cada estado
        df['rank_estadual'] = df.groupby('uf')[coluna_ranking].rank(method='min', ascending=False).astype(int)
        # O transform('count') conta quantos municípios existem em cada grupo (estado)
        df['total_estadual'] = df.groupby('uf')['uf'].transform('count')

        # 3. Ranking por Faixa Populacional (ASSUMINDO QUE A COLUNA 'faixa_pop' EXISTE)
        df['rank_faixa'] = df.groupby('faixas')[coluna_ranking].rank(method='min', ascending=False).astype(int)
        df['total_faixa'] = df.groupby('faixas')['faixas'].transform('count')
        # Coluna base para o ranking
        coluna_ranking = 'rc_23_pc'

        # 4. Coletar número dos percentis
        print(df['percentil'].str.extract(r'(\d+)º percentil', expand=False))
        df['percentil_n'] = df['percentil'].str.extract(r'(\d+)º percentil', expand=False).astype(int)

        # 5. Criar coluna de nome_muni_uf
        df['name_muni_uf'] = df['name_muni'] + ' - ' + df['uf']

        # 6. Ajustando NA para NONE
        df['populacao00'] = df['populacao00'].fillna(0).astype(int)

        Municipio.objects.all().delete()
        self.stdout.write("Nomes de colunas limpos. Importando dados...")
        print("Pandas está trabalhando com estes nomes de colunas agora:", list(df.columns))


        for _, row in df.iterrows():
            Municipio.objects.create(
                cod_ibge=row['cod_ibge'],
                name_muni=row['name_muni'],
                uf=row['uf'],
                coordx=row['coordx'],
                coordy=row['coordy'],
                populacao23=row['populacao23'],
                populacao00=row['populacao00'],
                rc_2023=row['rc_2023'],
                quintil23=row['quintil23'],
                quintil00=row['quintil00'],
                decil00=row['decil00'],
                decil23=row['decil23'],
                percentil=row['percentil'],
                percentil_n=row['percentil_n'],
                regiao=row['regiao'],
                name_muni_uf = row['name_muni_uf'],
                rc_23_pc = row['rc_2023']/row['populacao23'],
                rc_00_pc = row['rc_2000']/row['populacao00'] if row['populacao00'] > 0 else 0,
                rank_nacional = row['rank_nacional'],
                total_nacional = row['total_nacional'],
                rank_estadual = row['rank_estadual'] ,
                total_estadual = row['total_estadual'],
                rank_faixa = row['rank_faixa'],
                total_faixa = row['total_faixa']

            )
        
        self.stdout.write(self.style.SUCCESS('Dados importados com sucesso!'))