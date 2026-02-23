# Exemplo de script para popular ReceitaMunicipal com base no cod_ibge
import pandas as pd
from home.models import Municipio, ContaDetalhada, ContaDetalhadaPercentil

ContaDetalhada.objects.all().delete()  # Limpa os dados antigos
ContaDetalhadaPercentil.objects.all().delete()  # Limpa os dados antigos

contas = pd.read_excel(
    "base_datas/receitas_correntes_2024.xlsx",
    usecols=["cod_ibge", "itc", "con", "trf", "our"]
    )


# Substitui todos os valores vazios/NaN por 0 nas colunas de receita.
colunas_receita = [
    'itc', 'con', 'trf','our'
    ]
contas[colunas_receita] = contas[colunas_receita].fillna(0)
contas['cod_ibge'] = contas['cod_ibge'].astype(str)  # Garante que o código IBGE seja tratado como string
for _, row in contas.iterrows():
    try:
        muni = Municipio.objects.get(cod_ibge=row['cod_ibge'])
        ContaDetalhada.objects.create(
            municipio=muni,
            imposto_taxas_contribuicoes = row['itc'],
            contribuicoes = row['con'],
            transferencias_correntes =row['trf'],
            outras_receita = row['our']
            )
        print(f"{muni}")
    except Municipio.DoesNotExist:
        print(f"Município com código {row['cod_ibge']} não encontrado 😵")


df = pd.read_excel("base_datas/percentil_detalhamento_0.xlsx")
df['cod_ibge'] = df['cod_ibge'].astype(str)  # Garante que o código IBGE seja tratado como string
# Substitui todos os valores vazios/NaN por 0 nas colunas de receita.
colunas_receita = [
    # Nacional
    'perc_itc_pc_nac', 
    'perc_con_pc_nac', 
    'perc_trf_pc_nac',
    'perc_our_pc_nac',

    # Regional
    'perc_itc_pc_faixa', 
    'perc_con_pc_faixa', 
    'perc_trf_pc_faixa',
    'perc_our_pc_faixa',

    # Estadual
    'perc_itc_pc_uf', 
    'perc_con_pc_uf', 
    'perc_trf_pc_uf',
    'perc_our_pc_uf'

    ]
df[colunas_receita] = df[colunas_receita].fillna(0)

for _, row in df.iterrows():
    try:
        muni = Municipio.objects.get(cod_ibge=row['cod_ibge'])
        ContaDetalhadaPercentil.objects.create(
            municipio=muni,

            # Nacional
            imposto_taxas_contribuicoes_nacional = row['perc_itc_pc_nac'],
            contribuicoes_nacional = row['perc_con_pc_nac'],
            transferencias_correntes_nacional =row['perc_trf_pc_nac'],
            outras_receita_nacional = row['perc_our_pc_nac'],
            
            # Regional
            imposto_taxas_contribuicoes_regional = row['perc_itc_pc_faixa'],
            contribuicoes_regional = row['perc_con_pc_faixa'],
            transferencias_correntes_regional =row['perc_trf_pc_faixa'],
            outras_receita_regional = row['perc_our_pc_faixa'],


            # Estadual
            imposto_taxas_contribuicoes_estadual = row['perc_itc_pc_uf'],
            contribuicoes_estadual = row['perc_con_pc_uf'],
            transferencias_correntes_estadual =row['perc_trf_pc_uf'],
            outras_receita_estadual = row['perc_our_pc_uf'],
            )
        print(f"{muni}")
    except Municipio.DoesNotExist:
        print(f"Município com código {row['cod_ibge']} não encontrado 😵")