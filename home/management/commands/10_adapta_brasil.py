import pandas as pd
import numpy as np
from django.core.management.base import BaseCommand
# ATENÇÃO: Verifique se o caminho do import das models (home.models) está correto para o seu app
from home.models import Municipio, AdaptaBrasil 

class Command(BaseCommand):
    help = 'Importa dados da planilha AdaptaBrasil e vincula aos Municípios existentes.'

    def handle(self, *args, **kwargs):
        # 1. Carrega os dados do Excel
        try:
            df = pd.read_excel('base_datas/indicadores_adapta_brasil.xlsx')
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR("Arquivo 'indicadores_adapta_brasil.xlsx' não encontrado."))
            return

        # 2. Converte os nomes das colunas para minúsculo por precaução
        df.columns = df.columns.str.lower()
        
        # --- CORREÇÃO CRÍTICA 1: Garantir que o IBGE seja texto ---
        # Isso garante que o match com o cod_ibge da model Municipio funcione perfeitamente
        df['geocod_ibge'] = df['geocod_ibge'].astype(str)

        # --- CORREÇÃO CRÍTICA 2: Substituir NaN do Pandas por None do Python ---
        # Como os seus campos da model estão com null=True, o Django precisa receber None e não NaN
        df = df.replace({np.nan: None})

        # (Opcional) Limpa os registros antigos do AdaptaBrasil para evitar duplicidade 
        # já que a relação com Município é OneToOneField
        AdaptaBrasil.objects.all().delete()
        self.stdout.write("Registros antigos do AdaptaBrasil removidos. Iniciando importação...")

        registros_criados = 0
        municipios_falhos = 0

        # 3. Itera pelas linhas do dataframe
        for _, row in df.iterrows():
            # Busca a instância do Município baseando-se no cod_ibge
            # Usamos filter().first() para evitar erros caso um município da planilha não exista no banco
            muni = Municipio.objects.filter(cod_ibge=row['geocod_ibge']).first()

            if muni:
                # Cria o registro do AdaptaBrasil vinculado ao Município
                AdaptaBrasil.objects.create(
                    municipio=muni,
                    bio_int_bio=row['bio_int_bio'],
                    des_des_ter=row['des_des_ter'],
                    des_in_enx_ala=row['des_in_enx_ala'],
                    rec_ris_est_hid=row['rec_ris_est_hid'],
                    sau_arb=row['sau_arb'],
                    sau_lei_teg_ame=row['sau_lei_teg_ame'],
                    sau_lei_vis=row['sau_lei_vis'],
                    sau_mal=row['sau_mal'],
                    seg_ali_ace_con_ali=row['seg_ali_ace_con_ali'],
                    seg_ali_dis=row['seg_ali_dis'],
                    seg_ene_ace=row['seg_ene_ace'],
                    seg_ene_dis=row['seg_ene_dis']
                )
                registros_criados += 1
            else:
                municipios_falhos += 1

        # 4. Finalização
        self.stdout.write(self.style.SUCCESS(f'Importação concluída! {registros_criados} registros AdaptaBrasil criados.'))
        
        if municipios_falhos > 0:
            self.stdout.write(self.style.WARNING(f'Atenção: {municipios_falhos} códigos IBGE da planilha não foram encontrados na model Municipio.'))