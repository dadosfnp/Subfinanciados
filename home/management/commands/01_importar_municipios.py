import pandas as pd
import numpy as np
from django.core.management.base import BaseCommand
from home.models import Municipio, IndicadoresAtuais, Indicadores2000, SusDependente, Cadunico

class Command(BaseCommand):
    help = 'Importa dados de municípios do arquivo Excel, limpando os nomes das colunas.'

    def handle(self, *args, **kwargs):
        # 1. Carrega os dados do Excel usando pandas
        pop = pd.read_excel('base_datas/populacao.xlsx')
        rec24 = pd.read_excel('base_datas/receitas_correntes_2025.xlsx')
        rec00 = pd.read_excel('base_datas/receitas_correntes_2000.xlsx')
        capag = pd.read_excel('base_datas/capag_05_08_26.xlsx')
        
        # --- CORREÇÃO CRÍTICA 1: Garantir que o IBGE seja texto (Isso conserta o Merge!) ---
        pop['cod_ibge'] = pop['cod_ibge'].astype(str)
        rec24['cod_ibge'] = rec24['cod_ibge'].astype(str)
        rec00['cod_ibge'] = rec00['cod_ibge'].astype(str)
        capag['cod_ibge'] = capag['cod_ibge'].astype(str)
        # 2. Converte todos os nomes de colunas para minúsculo
        pop.columns = pop.columns.str.lower()
        rec24.columns = rec24.columns.str.lower()
        rec00.columns = rec00.columns.str.lower()
        capag.columns = capag.columns.str.lower()
        
        # Ranking Nacional 2000
        rec00['rank_nacional00'] = rec00['receita_00_pc'].rank(method='min', ascending=False).astype(int)
        rec00['total_nacional00'] = len(rec00)

        rec24 = rec24.merge(pop[['cod_ibge', 'uf', 'faixas']], on='cod_ibge', how='left')

        coluna_ranking = 'receita_pc'

        # Rankings 2024
        rec24['rank_nacional'] = rec24[coluna_ranking].rank(method='min', ascending=False).astype(int)
        rec24['total_nacional'] = len(rec24)

        rec24['rank_estadual'] = rec24.groupby('uf')[coluna_ranking].rank(method='min', ascending=False).astype(int)
        rec24['total_estadual'] = rec24.groupby('uf')['uf'].transform('count')

        rec24['rank_faixa'] = rec24.groupby('faixas')[coluna_ranking].rank(method='min', ascending=False).astype(int)
        rec24['total_faixa'] = rec24.groupby('faixas')['faixas'].transform('count')

        # --- CORREÇÃO DE ERRO: Extração de número segura (evita falha com NaN) ---
        rec24['percentil25_n'] = rec24['percentil'].str.extract(r'(\d+)', expand=False).astype(float)
        rec00['percentil00_n'] = rec00['percentil00'].astype(str).str.extract(r'(\d+)', expand=False).astype(float)

        rec00['rank_nacional00'] = rec00['rank_nacional00'].fillna(0).astype(int)
        rec00['total_nacional00'] = rec00['total_nacional00'].fillna(0).astype(int)

        Municipio.objects.all().delete()
        self.stdout.write("Nomes de colunas limpos. Importando dados...")

        pop = pop.merge(rec24.drop(columns=['uf', 'faixas'], errors='ignore'), on='cod_ibge', how='left')
        pop = pop.merge(rec00, on='cod_ibge', how='left')
        pop = pop.merge(capag[['cod_ibge', 'capag']], on='cod_ibge', how='left')

        pop['name_muni_uf'] = pop['nome_muni'] + ' - ' + pop['uf']

        # --- CORREÇÃO CRÍTICA 2: Substituir NaN do Pandas por None do Python ---
        pop = pop.replace({np.nan: None})

        for _, row in pop.iterrows():
            # 1. Cria o Município base
            muni = Municipio.objects.create(
                cod_ibge=row['cod_ibge'],
                name_muni=row['nome_muni'],
                name_muni_uf=row['name_muni_uf'],
                uf=row['uf'],
                coordx=row['coordx'],
                coordy=row['coordy'],
                regiao=row['regiao']
            )

            # --- CORREÇÃO CRÍTICA 3: Criar IndicadoresAtuais APENAS se tiver a Receita ---
            if row['receita'] is not None:
                IndicadoresAtuais.objects.create(
                    municipio=muni,
                    populacao_atual=row['populacao_25'],
                    populacao_atual_rank_nacional=row['rank_pop_nac'],
                    populacao_atual_total_nacional=row['total_nac_pop'],
                    populacao_atual_rank_estadual=row['rank_pop_uf'],
                    populacao_atual_total_estadual=row['total_uf_pop'],
                    populacao_atual_rank_faixa=row['rank_pop_faixas'],
                    populacao_atual_total_faixa=row['total_fax_pop'],
                    capag=row['capag'],
                    rc_atual=row['receita'],
                    rc_atual_pc=row['receita_pc'],
                    quintil_atual=row['quintil'],
                    decil_atual=row['decil'],
                    percentil_atual=row['percentil'],
                    percentil_atual_n=row['percentil25_n'],
                    rank_nacional=row['rank_nacional'],
                    total_nacional=row['total_nacional'],
                    rank_estadual=row['rank_estadual'],
                    total_estadual=row['total_estadual'],
                    rank_faixa=row['rank_faixa'],
                    total_faixa=row['total_faixa']
                )

            # 3. Cria Indicadores de 2000 APENAS se tiver Receita
            if row['receita_00'] is not None:
                Indicadores2000.objects.create(
                    municipio=muni,
                    populacao_00=row['populacao_00'],
                    rc_00=row['receita_00'],
                    rc_00_pc=row['receita_00_pc'],
                    quintil_00=row['quintil00'],
                    decil_00=row['decil00'],
                    percentil_00=row['percentil00'],
                    percentil_00_n=row['percentil00_n'],
                    rank_nacional_00=row['rank_nacional00'],
                    total_nacional_00=row['total_nacional00']
                )

            if row['dependencia_sus'] is not None:
                SusDependente.objects.create(
                    municipio=muni,
                    sus_dependente=row['dependencia_sus']
                )

            if row['pop_cadunico_25'] is not None:
                Cadunico.objects.create(
                    municipio=muni,
                    cadunico=row['pop_cadunico_25'],
                    cadunico_rank_nacional=row['rank_cadunico_nac'],
                    cadunico_total_nacional=row['total_nac_cad'],
                    cadunico_rank_estadual=row['rank_cadunico_uf'],
                    cadunico_total_estadual=row['total_uf_cad'],
                    cadunico_rank_faixa=row['rank_cadunico_faixas'],
                    cadunico_total_faixa=row['total_fax_cad']
                )

        self.stdout.write(self.style.SUCCESS('Dados importados com sucesso!'))