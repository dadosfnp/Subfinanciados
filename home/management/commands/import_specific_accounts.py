# Exemplo de script para popular ReceitaMunicipal com base no cod_ibge
import pandas as pd
from home.models import Municipio, ContaEspecifica, ContaEspecificaPercentil

df = pd.read_excel("base_datas\conta_especifica_detalhada.xlsx")
# Substitui todos os valores vazios/NaN por 0 nas colunas de receita.
colunas_receita = [
    'imposto', 'taxas', 'contribuicoes', 'contribuicoes_sociais', 'contribuicoes_iluminacao_publica', 
    'outras_contribuicoes', 'tranferencias_uniao', 'tranferencias_estados', 'outras_tranferencias',
    'receita_patrimonial', 'receita_agropecuaria', 'receita_industrial', 'receita_servicos', 
    'outras_receitas'
    ]
df[colunas_receita] = df[colunas_receita].fillna(0)
df['cod_ibge'] = df['cod_ibge'].astype(str)  # Garante que o código IBGE seja tratado como string
for _, row in df.iterrows():
    try:
        muni = Municipio.objects.get(cod_ibge=row['cod_ibge'])
        ContaEspecifica.objects.create(
            municipio=muni,
            imposto=row['imposto'],
            taxas=row['taxas'],
            contribuicoes=row['contribuicoes'],
            contribuicoes_sociais=row['contribuicoes_sociais'],
            contribuicoes_iluminacao_publica=row['contribuicoes_iluminacao_publica'],
            outras_contribuicoes=row['outras_contribuicoes'],
            tranferencias_uniao=row['tranferencias_uniao'],
            tranferencias_estados=row['tranferencias_estados'],
            outras_tranferencias=row['outras_tranferencias'],
            receita_patrimonial=row['receita_patrimonial'],
            receita_agropecuaria=row['receita_agropecuaria'],
            receita_industrial=row['receita_industrial'],
            receita_servicos=row['receita_servicos'],
            outras_receitas=row['outras_receitas'],
            )
        print(f"{muni}")
    except Municipio.DoesNotExist:
        print(f"Município com código {row['cod_ibge']} não encontrado 😵")





df = pd.read_excel("base_datas\percentis_especificos_detalhado.xlsx")
df['cod_ibge'] = df['cod_ibge'].astype(str)  # Garante que o código IBGE seja tratado como string

# Substitui todos os valores vazios/NaN por 0 nas colunas de receita.
colunas_receita = [
    # Nacional
        'percentil_imposto_per_capita_nacional', 
        'percentil_taxas_per_capita_nacional', 
        'percentil_contribuicoes_per_capita_nacional', 
        'percentil_contribuicoes_sociais_per_capita_nacional', 
        'percentil_contribuicoes_iluminacao_publica_per_capita_nacional', 
        'percentil_outras_contribuicoes_per_capita_nacional', 
        'percentil_tranferencias_uniao_per_capita_nacional', 
        'percentil_tranferencias_estados_per_capita_nacional', 
        'percentil_outras_tranferencias_per_capita_nacional',
        'percentil_receita_patrimonial_per_capita_nacional', 
        'percentil_receita_agropecuaria_per_capita_nacional', 
        'percentil_receita_industrial_per_capita_nacional', 
        'percentil_receita_servicos_per_capita_nacional', 
        'percentil_outras_receitas_per_capita_nacional',


    # Regional
    'percentil_imposto_per_capita_regional', 
    'percentil_taxas_per_capita_regional', 
    'percentil_contribuicoes_per_capita_regional', 
    'percentil_contribuicoes_sociais_per_capita_regional', 
    'percentil_contribuicoes_iluminacao_publica_per_capita_regional', 
    'percentil_outras_contribuicoes_per_capita_regional', 
    'percentil_tranferencias_uniao_per_capita_regional', 
    'percentil_tranferencias_estados_per_capita_regional', 
    'percentil_outras_tranferencias_per_capita_regional',
    'percentil_receita_patrimonial_per_capita_regional', 
    'percentil_receita_agropecuaria_per_capita_regional', 
    'percentil_receita_industrial_per_capita_regional', 
    'percentil_receita_servicos_per_capita_regional', 
    'percentil_outras_receitas_per_capita_regional',

    # Estadual
    'percentil_imposto_per_capita_estadual', 
    'percentil_taxas_per_capita_estadual', 
    'percentil_contribuicoes_per_capita_estadual', 
    'percentil_contribuicoes_sociais_per_capita_estadual', 
    'percentil_contribuicoes_iluminacao_publica_per_capita_estadual', 
    'percentil_outras_contribuicoes_per_capita_estadual', 
    'percentil_tranferencias_uniao_per_capita_estadual', 
    'percentil_tranferencias_estados_per_capita_estadual', 
    'percentil_outras_tranferencias_per_capita_estadual',
    'percentil_receita_patrimonial_per_capita_estadual', 
    'percentil_receita_agropecuaria_per_capita_estadual', 
    'percentil_receita_industrial_per_capita_estadual', 
    'percentil_receita_servicos_per_capita_estadual', 
    'percentil_outras_receitas_per_capita_estadual'
    ]
df[colunas_receita] = df[colunas_receita].fillna(0)

for _, row in df.iterrows():
    try:
        muni = Municipio.objects.get(cod_ibge=row['cod_ibge'])
        ContaEspecificaPercentil.objects.create(
            municipio=muni,

            # Nacional
            imposto_nacional=row['percentil_imposto_per_capita_nacional'],
            taxas_nacional=row['percentil_taxas_per_capita_nacional'],
            contribuicoes_nacional=row['percentil_contribuicoes_per_capita_nacional'],
            contribuicoes_sociais_nacional=row['percentil_contribuicoes_sociais_per_capita_nacional'],
            contribuicoes_iluminacao_publica_nacional=row['percentil_contribuicoes_iluminacao_publica_per_capita_nacional'],
            outras_contribuicoes_nacional=row['percentil_outras_contribuicoes_per_capita_nacional'],
            tranferencias_uniao_nacional=row['percentil_tranferencias_uniao_per_capita_nacional'],
            tranferencias_estados_nacional=row['percentil_tranferencias_estados_per_capita_nacional'],
            outras_tranferencias_nacional=row['percentil_outras_tranferencias_per_capita_nacional'],
            receita_patrimonial_nacional=row['percentil_receita_patrimonial_per_capita_nacional'],
            receita_agropecuaria_nacional=row['percentil_receita_agropecuaria_per_capita_nacional'],
            receita_industrial_nacional=row['percentil_receita_industrial_per_capita_nacional'],
            receita_servicos_nacional=row['percentil_receita_servicos_per_capita_nacional'],
            outras_receitas_nacional=row['percentil_outras_receitas_per_capita_nacional'],

            # Regional
            imposto_regional=row['percentil_imposto_per_capita_regional'],
            taxas_regional=row['percentil_taxas_per_capita_regional'],
            contribuicoes_regional=row['percentil_contribuicoes_per_capita_regional'],
            contribuicoes_sociais_regional=row['percentil_contribuicoes_sociais_per_capita_regional'],
            contribuicoes_iluminacao_publica_regional=row['percentil_contribuicoes_iluminacao_publica_per_capita_regional'],
            outras_contribuicoes_regional=row['percentil_outras_contribuicoes_per_capita_regional'],
            tranferencias_uniao_regional=row['percentil_tranferencias_uniao_per_capita_regional'],
            tranferencias_estados_regional=row['percentil_tranferencias_estados_per_capita_regional'],
            outras_tranferencias_regional=row['percentil_outras_tranferencias_per_capita_regional'],
            receita_patrimonial_regional=row['percentil_receita_patrimonial_per_capita_regional'],
            receita_agropecuaria_regional=row['percentil_receita_agropecuaria_per_capita_regional'],
            receita_industrial_regional=row['percentil_receita_industrial_per_capita_regional'],
            receita_servicos_regional=row['percentil_receita_servicos_per_capita_regional'],
            outras_receitas_regional=row['percentil_outras_receitas_per_capita_regional'],


            # Estadual
            imposto_estadual=row['percentil_imposto_per_capita_estadual'],
            taxas_estadual=row['percentil_taxas_per_capita_estadual'],
            contribuicoes_estadual=row['percentil_contribuicoes_per_capita_estadual'],
            contribuicoes_sociais_estadual=row['percentil_contribuicoes_sociais_per_capita_estadual'],
            contribuicoes_iluminacao_publica_estadual=row['percentil_contribuicoes_iluminacao_publica_per_capita_estadual'],
            outras_contribuicoes_estadual=row['percentil_outras_contribuicoes_per_capita_estadual'],
            tranferencias_uniao_estadual=row['percentil_tranferencias_uniao_per_capita_estadual'],
            tranferencias_estados_estadual=row['percentil_tranferencias_estados_per_capita_estadual'],
            outras_tranferencias_estadual=row['percentil_outras_tranferencias_per_capita_estadual'],
            receita_patrimonial_estadual=row['percentil_receita_patrimonial_per_capita_estadual'],
            receita_agropecuaria_estadual=row['percentil_receita_agropecuaria_per_capita_estadual'],
            receita_industrial_estadual=row['percentil_receita_industrial_per_capita_estadual'],
            receita_servicos_estadual=row['percentil_receita_servicos_per_capita_estadual'],
            outras_receitas_estadual=row['percentil_outras_receitas_per_capita_estadual'],
            )
        print(f"{muni}")
    except Municipio.DoesNotExist:
        print(f"Município com código {row['cod_ibge']} não encontrado 😵")