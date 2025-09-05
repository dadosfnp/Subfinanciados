# Exemplo de script para popular ReceitaMunicipal com base no cod_ibge
import pandas as pd
from home.models import Municipio, ContaMaisEspecifica, ContaMaisEspecificaPercentil

df = pd.read_excel("base_datas\conta_mais_especifica_detalhada.xlsx")
# Substitui todos os valores vazios/NaN por 0 nas colunas de receita.
colunas_receita = [
            'iptu',
            'itbi',
            'iss',
            'outros_impostos',
            'taxa_policia',
            'taxa_prestacao_servico',
            'outras_taxas',
            'contribuicao_melhoria_pavimento_obras',
            'contribuicao_melhoria_agua_potavel',
            'contribuicao_melhoria_iluminacao_publica',
            'outras_contribuicoes_melhoria',
            'transferencia_uniao_fpm',
            'transferencia_uniao_exploracao',
            'transferencia_uniao_sus',
            'transferencia_uniao_fnde',
            'transferencia_uniao_fnas',
            'outras_transferencias_uniao',
            'transferencia_estado_icms',
            'transferencia_estado_ipva',
            'transferencia_estado_exploracao',
            'transferencia_estado_sus',
            'transferencia_estado_assistencia',
            'outras_transferencias_estado'
    ]
df[colunas_receita] = df[colunas_receita].fillna(0)
df['cod_ibge'] = df['cod_ibge'].astype(str)
for _, row in df.iterrows():
    try:
        muni = Municipio.objects.get(cod_ibge=row['cod_ibge'])
        ContaMaisEspecifica.objects.create(
            municipio=muni,
        iptu = row['iptu'],
        itbi = row['itbi'],
        iss = row['iss'],
        outros_impostos = row['outros_impostos'],
        taxa_policia = row['taxa_policia'],
        taxa_prestacao_servico = row['taxa_prestacao_servico'],
        outras_taxas = row['outras_taxas'],
        contribuicao_melhoria_pavimento_obras = row['contribuicao_melhoria_pavimento_obras'],
        contribuicao_melhoria_agua_potavel = row['contribuicao_melhoria_agua_potavel'],
        contribuicao_melhoria_iluminacao_publica = row['contribuicao_melhoria_iluminacao_publica'],
        outras_contribuicoes_melhoria = row['outras_contribuicoes_melhoria'],
        transferencia_uniao_fpm = row['transferencia_uniao_fpm'],
        transferencia_uniao_exploracao = row['transferencia_uniao_exploracao'],
        transferencia_uniao_sus = row['transferencia_uniao_sus'],
        transferencia_uniao_fnde = row['transferencia_uniao_fnde'],
        transferencia_uniao_fnas = row['transferencia_uniao_fnas'],
        outras_transferencias_uniao = row['outras_transferencias_uniao'],
        transferencia_estado_icms = row['transferencia_estado_icms'],
        transferencia_estado_ipva = row['transferencia_estado_ipva'],
        transferencia_estado_exploracao = row['transferencia_estado_exploracao'],
        transferencia_estado_sus = row['transferencia_estado_sus'],
        transferencia_estado_assistencia = row['transferencia_estado_assistencia'],
        outras_transferencias_estado = row['outras_transferencias_estado']
            )
        print(f"{muni}")
    except Municipio.DoesNotExist:
        print(f"Município com código {row['cod_ibge']} não encontrado 😵")





df = pd.read_excel("base_datas\percentis_mais_especificos_detalhado.xlsx")
# Substitui todos os valores vazios/NaN por 0 nas colunas de receita.
colunas_receita = [
    # Nacional
    'percentil_iptu_per_capita_nacional',
    'percentil_itbi_per_capita_nacional',
    'percentil_iss_per_capita_nacional',
    'percentil_outros_impostos_per_capita_nacional',
    'percentil_taxa_policia_per_capita_nacional',
    'percentil_taxa_prestacao_servico_per_capita_nacional',
    'percentil_outras_taxas_per_capita_nacional',
    'percentil_contribuicao_melhoria_pavimento_obras_per_capita_nacional',
    'percentil_contribuicao_melhoria_agua_potavel_per_capita_nacional',
    'percentil_contribuicao_melhoria_iluminacao_publica_per_capita_nacional',
    'percentil_outras_contribuicoes_melhoria_per_capita_nacional',
    'percentil_transferencia_uniao_fpm_per_capita_nacional',
    'percentil_transferencia_uniao_exploracao_per_capita_nacional',
    'percentil_transferencia_uniao_sus_per_capita_nacional',
    'percentil_transferencia_uniao_fnde_per_capita_nacional',
    'percentil_transferencia_uniao_fnas_per_capita_nacional',
    'percentil_outras_transferencias_uniao_per_capita_nacional',
    'percentil_transferencia_estado_icms_per_capita_nacional',
    'percentil_transferencia_estado_ipva_per_capita_nacional',
    'percentil_transferencia_estado_exploracao_per_capita_nacional',
    'percentil_transferencia_estado_sus_per_capita_nacional',
    'percentil_transferencia_estado_assistencia_per_capita_nacional',
    'percentil_outras_transferencias_estado_per_capita_nacional',


    # Regional
    'percentil_iptu_per_capita_regional',
    'percentil_itbi_per_capita_regional',
    'percentil_iss_per_capita_regional',
    'percentil_outros_impostos_per_capita_regional',
    'percentil_taxa_policia_per_capita_regional',
    'percentil_taxa_prestacao_servico_per_capita_regional',
    'percentil_outras_taxas_per_capita_regional',
    'percentil_contribuicao_melhoria_pavimento_obras_per_capita_regional',
    'percentil_contribuicao_melhoria_agua_potavel_per_capita_regional',
    'percentil_contribuicao_melhoria_iluminacao_publica_per_capita_regional',
    'percentil_outras_contribuicoes_melhoria_per_capita_regional',
    'percentil_transferencia_uniao_fpm_per_capita_regional',
    'percentil_transferencia_uniao_exploracao_per_capita_regional',
    'percentil_transferencia_uniao_sus_per_capita_regional',
    'percentil_transferencia_uniao_fnde_per_capita_regional',
    'percentil_transferencia_uniao_fnas_per_capita_regional',
    'percentil_outras_transferencias_uniao_per_capita_regional',
    'percentil_transferencia_estado_icms_per_capita_regional',
    'percentil_transferencia_estado_ipva_per_capita_regional',
    'percentil_transferencia_estado_exploracao_per_capita_regional',
    'percentil_transferencia_estado_sus_per_capita_regional',
    'percentil_transferencia_estado_assistencia_per_capita_regional',
    'percentil_outras_transferencias_estado_per_capita_regional',


    # Estadual
    'percentil_iptu_per_capita_estadual',
    'percentil_itbi_per_capita_estadual',
    'percentil_iss_per_capita_estadual',
    'percentil_outros_impostos_per_capita_estadual',
    'percentil_taxa_policia_per_capita_estadual',
    'percentil_taxa_prestacao_servico_per_capita_estadual',
    'percentil_outras_taxas_per_capita_estadual',
    'percentil_contribuicao_melhoria_pavimento_obras_per_capita_estadual',
    'percentil_contribuicao_melhoria_agua_potavel_per_capita_estadual',
    'percentil_contribuicao_melhoria_iluminacao_publica_per_capita_estadual',
    'percentil_outras_contribuicoes_melhoria_per_capita_estadual',
    'percentil_transferencia_uniao_fpm_per_capita_estadual',
    'percentil_transferencia_uniao_exploracao_per_capita_estadual',
    'percentil_transferencia_uniao_sus_per_capita_estadual',
    'percentil_transferencia_uniao_fnde_per_capita_estadual',
    'percentil_transferencia_uniao_fnas_per_capita_estadual',
    'percentil_outras_transferencias_uniao_per_capita_estadual',
    'percentil_transferencia_estado_icms_per_capita_estadual',
    'percentil_transferencia_estado_ipva_per_capita_estadual',
    'percentil_transferencia_estado_exploracao_per_capita_estadual',
    'percentil_transferencia_estado_sus_per_capita_estadual',
    'percentil_transferencia_estado_assistencia_per_capita_estadual',
    'percentil_outras_transferencias_estado_per_capita_estadual'

    ]
df[colunas_receita] = df[colunas_receita].fillna(0)
df['cod_ibge'] = df['cod_ibge'].astype(str)

for _, row in df.iterrows():
    try:
        muni = Municipio.objects.get(cod_ibge=row['cod_ibge'])
        ContaMaisEspecificaPercentil.objects.create(
            municipio=muni,

            # Nacional
            iptu_nacional = row['percentil_iptu_per_capita_nacional'],
            itbi_nacional = row['percentil_itbi_per_capita_nacional'],
            iss_nacional = row['percentil_iss_per_capita_nacional'],
            outros_impostos_nacional = row['percentil_outros_impostos_per_capita_nacional'],
            taxa_policia_nacional = row['percentil_taxa_policia_per_capita_nacional'],
            taxa_prestacao_servico_nacional = row['percentil_taxa_prestacao_servico_per_capita_nacional'],
            outras_taxas_nacional = row['percentil_outras_taxas_per_capita_nacional'],
            contribuicao_melhoria_pavimento_obras_nacional = row['percentil_contribuicao_melhoria_pavimento_obras_per_capita_nacional'],
            contribuicao_melhoria_agua_potavel_nacional = row['percentil_contribuicao_melhoria_agua_potavel_per_capita_nacional'],
            contribuicao_melhoria_iluminacao_publica_nacional = row['percentil_contribuicao_melhoria_iluminacao_publica_per_capita_nacional'],
            outras_contribuicoes_melhoria_nacional = row['percentil_outras_contribuicoes_melhoria_per_capita_nacional'],
            transferencia_uniao_fpm_nacional = row['percentil_transferencia_uniao_fpm_per_capita_nacional'],
            transferencia_uniao_exploracao_nacional = row['percentil_transferencia_uniao_exploracao_per_capita_nacional'],
            transferencia_uniao_sus_nacional = row['percentil_transferencia_uniao_sus_per_capita_nacional'],
            transferencia_uniao_fnde_nacional = row['percentil_transferencia_uniao_fnde_per_capita_nacional'],
            transferencia_uniao_fnas_nacional = row['percentil_transferencia_uniao_fnas_per_capita_nacional'],
            outras_transferencias_uniao_nacional = row['percentil_outras_transferencias_uniao_per_capita_nacional'],
            transferencia_estado_icms_nacional = row['percentil_transferencia_estado_icms_per_capita_nacional'],
            transferencia_estado_ipva_nacional = row['percentil_transferencia_estado_ipva_per_capita_nacional'],
            transferencia_estado_exploracao_nacional = row['percentil_transferencia_estado_exploracao_per_capita_nacional'],
            transferencia_estado_sus_nacional = row['percentil_transferencia_estado_sus_per_capita_nacional'],
            transferencia_estado_assistencia_nacional = row['percentil_transferencia_estado_assistencia_per_capita_nacional'],
            outras_transferencias_estado_nacional = row['percentil_outras_transferencias_estado_per_capita_nacional'],

            # Regional
            iptu_regional = row['percentil_iptu_per_capita_regional'],
            itbi_regional = row['percentil_itbi_per_capita_regional'],
            iss_regional = row['percentil_iss_per_capita_regional'],
            outros_impostos_regional = row['percentil_outros_impostos_per_capita_regional'],
            taxa_policia_regional = row['percentil_taxa_policia_per_capita_regional'],
            taxa_prestacao_servico_regional = row['percentil_taxa_prestacao_servico_per_capita_regional'],
            outras_taxas_regional = row['percentil_outras_taxas_per_capita_regional'],
            contribuicao_melhoria_pavimento_obras_regional = row['percentil_contribuicao_melhoria_pavimento_obras_per_capita_regional'],
            contribuicao_melhoria_agua_potavel_regional = row['percentil_contribuicao_melhoria_agua_potavel_per_capita_regional'],
            contribuicao_melhoria_iluminacao_publica_regional = row['percentil_contribuicao_melhoria_iluminacao_publica_per_capita_regional'],
            outras_contribuicoes_melhoria_regional = row['percentil_outras_contribuicoes_melhoria_per_capita_regional'],
            transferencia_uniao_fpm_regional = row['percentil_transferencia_uniao_fpm_per_capita_regional'],
            transferencia_uniao_exploracao_regional = row['percentil_transferencia_uniao_exploracao_per_capita_regional'],
            transferencia_uniao_sus_regional = row['percentil_transferencia_uniao_sus_per_capita_regional'],
            transferencia_uniao_fnde_regional = row['percentil_transferencia_uniao_fnde_per_capita_regional'],
            transferencia_uniao_fnas_regional = row['percentil_transferencia_uniao_fnas_per_capita_regional'],
            outras_transferencias_uniao_regional = row['percentil_outras_transferencias_uniao_per_capita_regional'],
            transferencia_estado_icms_regional = row['percentil_transferencia_estado_icms_per_capita_regional'],
            transferencia_estado_ipva_regional = row['percentil_transferencia_estado_ipva_per_capita_regional'],
            transferencia_estado_exploracao_regional = row['percentil_transferencia_estado_exploracao_per_capita_regional'],
            transferencia_estado_sus_regional = row['percentil_transferencia_estado_sus_per_capita_regional'],
            transferencia_estado_assistencia_regional = row['percentil_transferencia_estado_assistencia_per_capita_regional'],
            outras_transferencias_estado_regional = row['percentil_outras_transferencias_estado_per_capita_regional'],


            # Estadual
            iptu_estadual = row['percentil_iptu_per_capita_estadual'],
            itbi_estadual = row['percentil_itbi_per_capita_estadual'],
            iss_estadual = row['percentil_iss_per_capita_estadual'],
            outros_impostos_estadual = row['percentil_outros_impostos_per_capita_estadual'],
            taxa_policia_estadual = row['percentil_taxa_policia_per_capita_estadual'],
            taxa_prestacao_servico_estadual = row['percentil_taxa_prestacao_servico_per_capita_estadual'],
            outras_taxas_estadual = row['percentil_outras_taxas_per_capita_estadual'],
            contribuicao_melhoria_pavimento_obras_estadual = row['percentil_contribuicao_melhoria_pavimento_obras_per_capita_estadual'],
            contribuicao_melhoria_agua_potavel_estadual = row['percentil_contribuicao_melhoria_agua_potavel_per_capita_estadual'],
            contribuicao_melhoria_iluminacao_publica_estadual = row['percentil_contribuicao_melhoria_iluminacao_publica_per_capita_estadual'],
            outras_contribuicoes_melhoria_estadual = row['percentil_outras_contribuicoes_melhoria_per_capita_estadual'],
            transferencia_uniao_fpm_estadual = row['percentil_transferencia_uniao_fpm_per_capita_estadual'],
            transferencia_uniao_exploracao_estadual = row['percentil_transferencia_uniao_exploracao_per_capita_estadual'],
            transferencia_uniao_sus_estadual = row['percentil_transferencia_uniao_sus_per_capita_estadual'],
            transferencia_uniao_fnde_estadual = row['percentil_transferencia_uniao_fnde_per_capita_estadual'],
            transferencia_uniao_fnas_estadual = row['percentil_transferencia_uniao_fnas_per_capita_estadual'],
            outras_transferencias_uniao_estadual = row['percentil_outras_transferencias_uniao_per_capita_estadual'],
            transferencia_estado_icms_estadual = row['percentil_transferencia_estado_icms_per_capita_estadual'],
            transferencia_estado_ipva_estadual = row['percentil_transferencia_estado_ipva_per_capita_estadual'],
            transferencia_estado_exploracao_estadual = row['percentil_transferencia_estado_exploracao_per_capita_estadual'], 
            transferencia_estado_sus_estadual = row['percentil_transferencia_estado_sus_per_capita_estadual'],
            transferencia_estado_assistencia_estadual = row['percentil_transferencia_estado_assistencia_per_capita_estadual'],
            outras_transferencias_estado_estadual = row['percentil_outras_transferencias_estado_per_capita_estadual'],
            )
        print(f"{muni}")
    except Municipio.DoesNotExist:
        print(f"Município com código {row['cod_ibge']} não encontrado 😵")