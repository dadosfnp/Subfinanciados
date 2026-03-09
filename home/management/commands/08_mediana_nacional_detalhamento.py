import pandas as pd
import numpy as np
from django.core.management.base import BaseCommand
from home.models import MedianaNacionalReceita, MedianaUfReceita, MedianaPorteReceita

class Command(BaseCommand):
    help = 'Importa dados de municípios do arquivo Excel, limpando os nomes das colunas.'

    def handle(self, *args, **kwargs):
        # 1. Carrega os dados do Excel usando pandas
        nac = pd.read_excel('base_datas/mediana_nacional_detalhamento.xlsx')
        uf = pd.read_excel('base_datas/mediana_uf_detalhamento.xlsx')
        porte = pd.read_excel('base_datas/mediana_porte_detalhamento.xlsx')
    

        for _, row in nac.iterrows():
            MedianaNacionalReceita.objects.create(
                    ano_referencia= 2024,
    
                    # Metricas de Nivel 1 - Conta Detalhada
                    imposto_taxas_contribuicoes = row['itc'],
                    contribuicoes = row['con'],
                    transferencias_correntes = row['trf'],
                    outras_receita = row['our'],

                    # Metricas de Nivel 2 - Conta Especifica
                    imposto = row['itc_imp'],
                    taxas = row['itc_tax'],
                    contribuicoes_melhoria = row['itc_con'],
                    contribuicoes_sociais = row['con_soc'],
                    contribuicoes_iluminacao_publica = row['con_ipl'],
                    outras_contribuicoes = row['con_our'],
                    tranferencias_uniao = row['trf_uni'],
                    tranferencias_estados = row['trf_est'],
                    outras_tranferencias = row['trf_our'],
                    receita_patrimonial = row['our_pat'],
                    receita_agropecuaria = row['our_agr'],
                    receita_industrial = row['our_ind'],
                    receita_servicos = row['our_ser'],
                    outras_receitas = row['our_our'],
                    
                    # Metricas de Nivel 3 - Conta Mais Especifica
                    iptu = row['itc_imp_ptu'],
                    itbi = row['itc_imp_tbi'],
                    iss = row['itc_imp_ser'],
                    imposto_renda = row['itc_imp_rnd'],
                    outros_impostos = row['itc_imp_our'],
                    taxa_policia = row['itc_tax_pol'],
                    taxa_prestacao_servico = row['itc_tax_ser'],
                    outras_taxas = row['itc_tax_our'],
                    contribuicao_melhoria_pavimento_obras = row['itc_con_pav'],
                    contribuicao_melhoria_agua_potavel = row['itc_con_age'],
                    contribuicao_melhoria_iluminacao_publica = row['itc_con_ipl'],
                    outras_contribuicoes_melhoria = row['itc_con_our'],
                    transferencia_uniao_fpm = row['trf_uni_fpm'],
                    transferencia_uniao_exploracao = row['trf_uni_exp'],
                    transferencia_uniao_sus = row['trf_uni_sus'],
                    transferencia_uniao_fnde = row['trf_uni_fnd'],
                    transferencia_uniao_fundeb = row['trf_uni_fun'],
                    transferencia_uniao_fnas = row['trf_uni_fna'],
                    outras_transferencias_uniao = row['trf_uni_our'],
                    transferencia_estado_icms = row['trf_est_icm'],
                    transferencia_estado_ipva = row['trf_est_ipv'],
                    transferencia_estado_exploracao = row['trf_est_exp'],
                    transferencia_estado_sus = row['trf_est_sus'],
                    transferencia_estado_assistencia = row['trf_est_ass'],
                    outras_transferencias_estado = row['trf_est_our'],
            )

        for _, row in uf.iterrows():
            MedianaUfReceita.objects.create(
                    ano_referencia= 2024,
                    uf = row['uf'],
    
                    # Metricas de Nivel 1 - Conta Detalhada
                    imposto_taxas_contribuicoes = row['itc'],
                    contribuicoes = row['con'],
                    transferencias_correntes = row['trf'],
                    outras_receita = row['our'],

                    # Metricas de Nivel 2 - Conta Especifica
                    imposto = row['itc_imp'],
                    taxas = row['itc_tax'],
                    contribuicoes_melhoria = row['itc_con'],
                    contribuicoes_sociais = row['con_soc'],
                    contribuicoes_iluminacao_publica = row['con_ipl'],
                    outras_contribuicoes = row['con_our'],
                    tranferencias_uniao = row['trf_uni'],
                    tranferencias_estados = row['trf_est'],
                    outras_tranferencias = row['trf_our'],
                    receita_patrimonial = row['our_pat'],
                    receita_agropecuaria = row['our_agr'],
                    receita_industrial = row['our_ind'],
                    receita_servicos = row['our_ser'],
                    outras_receitas = row['our_our'],
                    
                    # Metricas de Nivel 3 - Conta Mais Especifica
                    iptu = row['itc_imp_ptu'],
                    itbi = row['itc_imp_tbi'],
                    iss = row['itc_imp_ser'],
                    imposto_renda = row['itc_imp_rnd'],
                    outros_impostos = row['itc_imp_our'],
                    taxa_policia = row['itc_tax_pol'],
                    taxa_prestacao_servico = row['itc_tax_ser'],
                    outras_taxas = row['itc_tax_our'],
                    contribuicao_melhoria_pavimento_obras = row['itc_con_pav'],
                    contribuicao_melhoria_agua_potavel = row['itc_con_age'],
                    contribuicao_melhoria_iluminacao_publica = row['itc_con_ipl'],
                    outras_contribuicoes_melhoria = row['itc_con_our'],
                    transferencia_uniao_fpm = row['trf_uni_fpm'],
                    transferencia_uniao_exploracao = row['trf_uni_exp'],
                    transferencia_uniao_sus = row['trf_uni_sus'],
                    transferencia_uniao_fnde = row['trf_uni_fnd'],
                    transferencia_uniao_fundeb = row['trf_uni_fun'],
                    transferencia_uniao_fnas = row['trf_uni_fna'],
                    outras_transferencias_uniao = row['trf_uni_our'],
                    transferencia_estado_icms = row['trf_est_icm'],
                    transferencia_estado_ipva = row['trf_est_ipv'],
                    transferencia_estado_exploracao = row['trf_est_exp'],
                    transferencia_estado_sus = row['trf_est_sus'],
                    transferencia_estado_assistencia = row['trf_est_ass'],
                    outras_transferencias_estado = row['trf_est_our'],
            )

        for _, row in porte.iterrows():
            MedianaPorteReceita.objects.create(
                    ano_referencia= 2024,
                    porte = row['faixas'],
    
                    # Metricas de Nivel 1 - Conta Detalhada
                    imposto_taxas_contribuicoes = row['itc'],
                    contribuicoes = row['con'],
                    transferencias_correntes = row['trf'],
                    outras_receita = row['our'],

                    # Metricas de Nivel 2 - Conta Especifica
                    imposto = row['itc_imp'],
                    taxas = row['itc_tax'],
                    contribuicoes_melhoria = row['itc_con'],
                    contribuicoes_sociais = row['con_soc'],
                    contribuicoes_iluminacao_publica = row['con_ipl'],
                    outras_contribuicoes = row['con_our'],
                    tranferencias_uniao = row['trf_uni'],
                    tranferencias_estados = row['trf_est'],
                    outras_tranferencias = row['trf_our'],
                    receita_patrimonial = row['our_pat'],
                    receita_agropecuaria = row['our_agr'],
                    receita_industrial = row['our_ind'],
                    receita_servicos = row['our_ser'],
                    outras_receitas = row['our_our'],
                    
                    # Metricas de Nivel 3 - Conta Mais Especifica
                    iptu = row['itc_imp_ptu'],
                    itbi = row['itc_imp_tbi'],
                    iss = row['itc_imp_ser'],
                    imposto_renda = row['itc_imp_rnd'],
                    outros_impostos = row['itc_imp_our'],
                    taxa_policia = row['itc_tax_pol'],
                    taxa_prestacao_servico = row['itc_tax_ser'],
                    outras_taxas = row['itc_tax_our'],
                    contribuicao_melhoria_pavimento_obras = row['itc_con_pav'],
                    contribuicao_melhoria_agua_potavel = row['itc_con_age'],
                    contribuicao_melhoria_iluminacao_publica = row['itc_con_ipl'],
                    outras_contribuicoes_melhoria = row['itc_con_our'],
                    transferencia_uniao_fpm = row['trf_uni_fpm'],
                    transferencia_uniao_exploracao = row['trf_uni_exp'],
                    transferencia_uniao_sus = row['trf_uni_sus'],
                    transferencia_uniao_fnde = row['trf_uni_fnd'],
                    transferencia_uniao_fundeb = row['trf_uni_fun'],
                    transferencia_uniao_fnas = row['trf_uni_fna'],
                    outras_transferencias_uniao = row['trf_uni_our'],
                    transferencia_estado_icms = row['trf_est_icm'],
                    transferencia_estado_ipva = row['trf_est_ipv'],
                    transferencia_estado_exploracao = row['trf_est_exp'],
                    transferencia_estado_sus = row['trf_est_sus'],
                    transferencia_estado_assistencia = row['trf_est_ass'],
                    outras_transferencias_estado = row['trf_est_our'],
            )            

        self.stdout.write(self.style.SUCCESS('Dados importados com sucesso!'))