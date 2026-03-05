import pandas as pd
import numpy as np
from django.core.management.base import BaseCommand
from home.models import Municipio, Percentis

class Command(BaseCommand):
    help = 'Importa dados de municípios do arquivo Excel, limpando os nomes das colunas.'

    def handle(self, *args, **kwargs):
        # 1. Carrega os dados do Excel usando pandas
        pop = pd.read_excel('base_datas/populacao.xlsx')
        rec24 = pd.read_excel('base_datas/receitas_correntes_2024.xlsx')
        rec00 = pd.read_excel('base_datas/receitas_correntes_2000.xlsx')
        percentis = pd.read_excel('base_datas/percentis_limites.xlsx')
        
        # 2. Converte todos os nomes de colunas para minúsculo
        pop.columns = pop.columns.str.lower()
        rec24.columns = rec24.columns.str.lower()
        rec00.columns = rec00.columns.str.lower()

        rec24 = rec24.merge(pop, on='cod_ibge', how='left')
        rec24 = rec24.merge(rec00, on='cod_ibge', how='left')

        print("Nomes de colunas após limpeza:")
        print(list(rec24.columns))
        # -------------------------

        # Coluna base para o ranking
        coluna_ranking = 'receita_pc'

        # 1. Ranking Nacional
        # ascending=False -> O maior valor de rc_23_pc recebe o rank 1
        rec24['rank_nacional'] = rec24[coluna_ranking].rank(method='min', ascending=False).astype(int)
        rec24['total_nacional'] = len(rec24) # O total é simplesmente o número de municípios

        # 2. Ranking Estadual
        # O groupby('uf') faz o ranking ser calculado separadamente para cada estado
        rec24['rank_estadual'] = rec24.groupby('uf')[coluna_ranking].rank(method='min', ascending=False).astype(int)
        # O transform('count') conta quantos municípios existem em cada grupo (estado)
        rec24['total_estadual'] = rec24.groupby('uf')['uf'].transform('count')

        # 3. Ranking por Faixa Populacional (ASSUMINDO QUE A COLUNA 'faixa_pop' EXISTE)
        rec24['rank_faixa'] = rec24.groupby('faixas')[coluna_ranking].rank(method='min', ascending=False).astype(int)
        rec24['total_faixa'] = rec24.groupby('faixas')['faixas'].transform('count')


        # 4. Coletar número dos percentis
        print(rec24['percentil'].str.extract(r'(\d+)º percentil', expand=False))
        rec24['percentil24_n'] = rec24['percentil'].str.extract(r'(\d+)º percentil', expand=False).astype(int)
        rec24["percentil00_n"] = (rec24["percentil00"]
                                        .astype("string")
                                        .str.extract(r"(\d+)\s*º\s*percentil", expand=False)
                                        .astype(object)
                                        .where(lambda s: s.notna(), None)
                                )

        # 5. Criar coluna de nome_muni_uf
        rec24['name_muni_uf'] = rec24['nome_muni'] + ' - ' + rec24['uf']

        Municipio.objects.all().delete()
        self.stdout.write("Nomes de colunas limpos. Importando dados...")
        print("Pandas está trabalhando com estes nomes de colunas agora:", list(rec24.columns))

        rec24 = rec24.where(rec24.notna(), None)

        for _, row in rec24.iterrows():
            Municipio.objects.create(
                cod_ibge=row['cod_ibge'],
                name_muni=row['nome_muni'],
                cadunico = row['pop_cadunico_24'],
                sus_dependente = row['dependencia_sus'],
                uf=row['uf'],
                coordx=row['coordx'],
                coordy=row['coordy'],
                populacao24=row['populacao_24'],
                populacao00=row['populacao_00'],
                rc_2024=row['receita'],
                rc_2000=row['receita_00'],
                quintil24=row['quintil'],
                decil24=row['decil'],
                percentil24=row['percentil'],
                percentil24_n=row['percentil24_n'],
                quintil00=row['quintil00'],
                decil00=row['decil00'],
                percentil00=row['percentil00'],
                percentil00_n=row['percentil00_n'],
                regiao=row['regiao'],
                name_muni_uf = row['name_muni_uf'],
                rc_24_pc = row['receita_pc'],
                rc_00_pc = row['receita_00_pc'],
                rank_nacional = row['rank_nacional'],
                total_nacional = row['total_nacional'],
                rank_estadual = row['rank_estadual'] ,
                total_estadual = row['total_estadual'],
                rank_faixa = row['rank_faixa'],
                total_faixa = row['total_faixa'],
                cadunico_rank_nacional = row['rank_cadunico_nac'],
                cadunico_total_nacional = row['total_nac_cad'],
                cadunico_rank_estadual = row['rank_cadunico_uf'],
                cadunico_total_estadual = row['total_uf_cad'],
                cadunico_rank_faixa = row['rank_cadunico_faixas'],
                cadunico_total_faixa = row['total_fax_cad'],
                populacao24_rank_nacional = row['rank_pop_nac'],
                populacao24_total_nacional = row['total_nac_pop'],  
                populacao24_rank_estadual = row['rank_pop_uf'],
                populacao24_total_estadual = row['total_uf_pop'],
                populacao24_rank_faixa = row['rank_pop_faixas'],
                populacao24_total_faixa = row['total_fax_pop']

            )

        self.stdout.write(self.style.SUCCESS('Dados importados com sucesso!'))