import pandas as pd
from django.core.management.base import BaseCommand
from home.models import Percentis

class Command(BaseCommand):
    help = 'Importa dados de municípios do arquivo Excel, limpando os nomes das colunas.'

    def handle(self, *args, **kwargs):
        percentis = pd.read_excel('base_datas/percentis_limites.xlsx')
        

        for _, row in percentis.iterrows():
            Percentis.objects.create(
                percentil=row['percentil'],
                valor=row['valores']
            )    

        self.stdout.write(self.style.SUCCESS('Dados importados com sucesso!'))    


