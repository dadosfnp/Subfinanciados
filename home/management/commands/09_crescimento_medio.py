import pandas as pd
import numpy as np
from django.core.management.base import BaseCommand
from home.models import CrescimentoMedioPorte, CrescimentoMedioUf

class Command(BaseCommand):
    help = 'Importa dados de municípios do arquivo Excel, limpando os nomes das colunas.'

    def handle(self, *args, **kwargs):
        # 1. Carrega os dados do Excel usando pandas
  
        uf_rec = pd.read_excel('base_datas/crescimento_medio_receita_uf.xlsx')
        uf_pop = pd.read_excel('base_datas/crescimento_medio_populacao_uf.xlsx')

        uf = uf_rec.merge(uf_pop, on='uf', how='left')
        
        porte_rec = pd.read_excel('base_datas/crescimento_medio_receita_porte.xlsx')
        porte_pop = pd.read_excel('base_datas/crescimento_medio_populacao_porte.xlsx')

        porte = porte_rec.merge(porte_pop, on='faixas', how='left')

    

        for _, row in uf.iterrows():
            CrescimentoMedioUf.objects.create(
                    ano_referencia= 2024,
                    uf = row['uf'],
    
                    receita = row['rec_med_uf'],
                    populacao = row['pop_med_uf'],
            )


        for _, row in porte.iterrows():
            CrescimentoMedioPorte.objects.create(
                    ano_referencia= 2024,
                    porte = row['faixas'],
    
                    receita = row['rec_med_porte'],
                    populacao = row['pop_med_porte'],
            )


        self.stdout.write(self.style.SUCCESS('Dados importados com sucesso!'))