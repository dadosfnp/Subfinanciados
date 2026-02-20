# Exemplo de script para popular ReceitaMunicipal com base no cod_ibge
import pandas as pd
from home.models import Municipio, ContaDetalhada, ContaDetalhadaPercentil

ContaDetalhada.objects.all().delete()  # Limpa os dados antigos
ContaDetalhadaPercentil.objects.all().delete()  # Limpa os dados antigos

df = pd.read_excel("base_datas\conta_gerais_detalhada.xlsx")
# Substitui todos os valores vazios/NaN por 0 nas colunas de receita.
colunas_receita = [
    'imposto_taxas_contribuicoes', 'contribuicoes', 'transferencias_correntes',
    'outras_receita'
    ]
df[colunas_receita] = df[colunas_receita].fillna(0)
df['cod_ibge'] = df['cod_ibge'].astype(str)  # Garante que o código IBGE seja tratado como string
for _, row in df.iterrows():
    try:
        muni = Municipio.objects.get(cod_ibge=row['cod_ibge'])
        ContaDetalhada.objects.create(
            municipio=muni,
            imposto_taxas_contribuicoes = row['imposto_taxas_contribuicoes'],
            contribuicoes = row['contribuicoes'],
            transferencias_correntes =row['transferencias_correntes'],
            outras_receita = row['outras_receita']
            )
        print(f"{muni}")
    except Municipio.DoesNotExist:
        print(f"Município com código {row['cod_ibge']} não encontrado 😵")


df = pd.read_excel("base_datas\percentis_gerais_detalhado.xlsx")
df['cod_ibge'] = df['cod_ibge'].astype(str)  # Garante que o código IBGE seja tratado como string
# Substitui todos os valores vazios/NaN por 0 nas colunas de receita.
colunas_receita = [
    # Nacional
    'percentil_imposto_taxas_contribuicoes_per_capita_nacional', 
    'percentil_contribuicoes_per_capita_nacional', 
    'percentil_transferencias_correntes_per_capita_nacional',
    'percentil_outras_receita_per_capita_nacional',

    # Regional
    'percentil_imposto_taxas_contribuicoes_per_capita_regional', 
    'percentil_contribuicoes_per_capita_regional', 
    'percentil_transferencias_correntes_per_capita_regional',
    'percentil_outras_receita_per_capita_regional',

    # Estadual
    'percentil_imposto_taxas_contribuicoes_per_capita_estadual', 
    'percentil_contribuicoes_per_capita_estadual', 
    'percentil_transferencias_correntes_per_capita_estadual',
    'percentil_outras_receita_per_capita_estadual'

    ]
df[colunas_receita] = df[colunas_receita].fillna(0)

for _, row in df.iterrows():
    try:
        muni = Municipio.objects.get(cod_ibge=row['cod_ibge'])
        ContaDetalhadaPercentil.objects.create(
            municipio=muni,

            # Nacional
            imposto_taxas_contribuicoes_nacional = row['percentil_imposto_taxas_contribuicoes_per_capita_nacional'],
            contribuicoes_nacional = row['percentil_contribuicoes_per_capita_nacional'],
            transferencias_correntes_nacional =row['percentil_transferencias_correntes_per_capita_nacional'],
            outras_receita_nacional = row['percentil_outras_receita_per_capita_nacional'],
            
            # Regional
            imposto_taxas_contribuicoes_regional = row['percentil_imposto_taxas_contribuicoes_per_capita_regional'],
            contribuicoes_regional = row['percentil_contribuicoes_per_capita_regional'],
            transferencias_correntes_regional =row['percentil_transferencias_correntes_per_capita_regional'],
            outras_receita_regional = row['percentil_outras_receita_per_capita_regional'],


            # Estadual
            imposto_taxas_contribuicoes_estadual = row['percentil_imposto_taxas_contribuicoes_per_capita_estadual'],
            contribuicoes_estadual = row['percentil_contribuicoes_per_capita_estadual'],
            transferencias_correntes_estadual =row['percentil_transferencias_correntes_per_capita_estadual'],
            outras_receita_estadual = row['percentil_outras_receita_per_capita_estadual'],
            )
        print(f"{muni}")
    except Municipio.DoesNotExist:
        print(f"Município com código {row['cod_ibge']} não encontrado 😵")