# Exemplo de script para popular ReceitaMunicipal com base no cod_ibge
import pandas as pd
from home.models import Municipio, ContaEspecifica, ContaEspecificaPercentil

ContaEspecifica.objects.all().delete()  # Limpa os dados antigos
ContaEspecificaPercentil.objects.all().delete()  # Limpa os dados antigos

df = pd.read_excel("base_datas/receitas_correntes_detalhamento_n1.xlsx")
# Substitui todos os valores vazios/NaN por 0 nas colunas de receita.

colunas_receita = [
    'itc_imp', 'itc_tax', 'itc_con', 'con_soc', 'con_ipl', 
    'con_our', 'trf_uni', 'trf_est', 'trf_our',
    'our_pat', 'our_ser', 'our_agr', 'our_ind', 
    'our_our'
    ]

df[colunas_receita] = df[colunas_receita].fillna(0)
df['cod_ibge'] = df['cod_ibge'].astype(str)  # Garante que o código IBGE seja tratado como string
for _, row in df.iterrows():
    try:
        muni = Municipio.objects.get(cod_ibge=row['cod_ibge'])
        ContaEspecifica.objects.create(
            municipio=muni,
            imposto=row['itc_imp'],
            taxas=row['itc_tax'],
            contribuicoes_melhoria=row['itc_con'],
            contribuicoes_sociais=row['con_soc'],
            contribuicoes_iluminacao_publica=row['con_ipl'],
            outras_contribuicoes=row['con_our'],
            tranferencias_uniao=row['trf_uni'],
            tranferencias_estados=row['trf_est'],
            outras_tranferencias=row['trf_our'],
            receita_patrimonial=row['our_pat'],
            receita_agropecuaria=row['our_agr'],
            receita_industrial=row['our_ind'],
            receita_servicos=row['our_ser'],
            outras_receitas=row['our_our'],
            )
        print(f"{muni}")
    except Municipio.DoesNotExist:
        print(f"Município com código {row['cod_ibge']} não encontrado 😵")





df = pd.read_excel("base_datas/percentil_detalhamento_1.xlsx")
df['cod_ibge'] = df['cod_ibge'].astype(str)  # Garante que o código IBGE seja tratado como string

# Substitui todos os valores vazios/NaN por 0 nas colunas de receita.
colunas_receita = [
    # Nacional
    'perc_itc_imp_pc_nac', 
    'perc_itc_tax_pc_nac', 
    'perc_itc_con_pc_nac', 
    'perc_con_soc_pc_nac', 
    'perc_con_ipl_pc_nac', 
    'perc_con_our_pc_nac', 
    'perc_trf_uni_pc_nac', 
    'perc_trf_est_pc_nac', 
    'perc_trf_our_pc_nac',
    'perc_our_pat_pc_nac', 
    'perc_our_agr_pc_nac', 
    'perc_our_ind_pc_nac', 
    'perc_our_ser_pc_nac', 
    'perc_our_our_pc_nac',


    # Regional
    'perc_itc_imp_pc_faixa', 
    'perc_itc_tax_pc_faixa', 
    'perc_itc_con_pc_faixa', 
    'perc_con_soc_pc_faixa', 
    'perc_con_ipl_pc_faixa', 
    'perc_con_our_pc_faixa', 
    'perc_trf_uni_pc_faixa', 
    'perc_trf_est_pc_faixa', 
    'perc_trf_our_pc_faixa',
    'perc_our_pat_pc_faixa', 
    'perc_our_agr_pc_faixa', 
    'perc_our_ind_pc_faixa', 
    'perc_our_ser_pc_faixa', 
    'perc_our_our_pc_faixa',

    # Estadual
    'perc_itc_imp_pc_uf', 
    'perc_itc_tax_pc_uf', 
    'perc_itc_con_pc_uf', 
    'perc_con_soc_pc_uf', 
    'perc_con_ipl_pc_uf', 
    'perc_con_our_pc_uf', 
    'perc_trf_uni_pc_uf', 
    'perc_trf_est_pc_uf', 
    'perc_trf_our_pc_uf',
    'perc_our_pat_pc_uf', 
    'perc_our_agr_pc_uf', 
    'perc_our_ind_pc_uf', 
    'perc_our_ser_pc_uf', 
    'perc_our_our_pc_uf'
    ]
df[colunas_receita] = df[colunas_receita].fillna(0)

for _, row in df.iterrows():
    try:
        muni = Municipio.objects.get(cod_ibge=row['cod_ibge'])
        ContaEspecificaPercentil.objects.create(
            municipio=muni,

            # Nacional
            imposto_nacional=row['perc_itc_imp_pc_nac'],
            taxas_nacional=row['perc_itc_tax_pc_nac'],
            contribuicoes_melhoria_nacional=row['perc_itc_con_pc_nac'],
            contribuicoes_sociais_nacional=row['perc_con_soc_pc_nac'],
            contribuicoes_iluminacao_publica_nacional=row['perc_con_ipl_pc_nac'],
            outras_contribuicoes_nacional=row['perc_con_our_pc_nac'],
            tranferencias_uniao_nacional=row['perc_trf_uni_pc_nac'],
            tranferencias_estados_nacional=row['perc_trf_est_pc_nac'],
            outras_tranferencias_nacional=row['perc_trf_our_pc_nac'],
            receita_patrimonial_nacional=row['perc_our_pat_pc_nac'],
            receita_agropecuaria_nacional=row['perc_our_agr_pc_nac'],
            receita_industrial_nacional=row['perc_our_ind_pc_nac'],
            receita_servicos_nacional=row['perc_our_ser_pc_nac'],
            outras_receitas_nacional=row['perc_our_our_pc_nac'],

            # Regional
            imposto_regional=row['perc_itc_imp_pc_faixa'],
            taxas_regional=row['perc_itc_tax_pc_faixa'],
            contribuicoes_melhoria_regional=row['perc_itc_con_pc_faixa'],
            contribuicoes_sociais_regional=row['perc_con_soc_pc_faixa'],
            contribuicoes_iluminacao_publica_regional=row['perc_con_ipl_pc_faixa'],
            outras_contribuicoes_regional=row['perc_con_our_pc_faixa'],
            tranferencias_uniao_regional=row['perc_trf_uni_pc_faixa'],
            tranferencias_estados_regional=row['perc_trf_est_pc_faixa'],
            outras_tranferencias_regional=row['perc_trf_our_pc_faixa'],
            receita_patrimonial_regional=row['perc_our_pat_pc_faixa'],
            receita_agropecuaria_regional=row['perc_our_agr_pc_faixa'],
            receita_industrial_regional=row['perc_our_ind_pc_faixa'],
            receita_servicos_regional=row['perc_our_ser_pc_faixa'],
            outras_receitas_regional=row['perc_our_our_pc_faixa'],


            # Estadual
            imposto_estadual=row['perc_itc_imp_pc_uf'],
            taxas_estadual=row['perc_itc_tax_pc_uf'],
            contribuicoes_melhoria_estadual=row['perc_itc_con_pc_uf'],
            contribuicoes_sociais_estadual=row['perc_con_soc_pc_uf'],
            contribuicoes_iluminacao_publica_estadual=row['perc_con_ipl_pc_uf'],
            outras_contribuicoes_estadual=row['perc_con_our_pc_uf'],
            tranferencias_uniao_estadual=row['perc_trf_uni_pc_uf'],
            tranferencias_estados_estadual=row['perc_trf_est_pc_uf'],
            outras_tranferencias_estadual=row['perc_trf_our_pc_uf'],
            receita_patrimonial_estadual=row['perc_our_pat_pc_uf'],
            receita_agropecuaria_estadual=row['perc_our_agr_pc_uf'],
            receita_industrial_estadual=row['perc_our_ind_pc_uf'],
            receita_servicos_estadual=row['perc_our_ser_pc_uf'],
            outras_receitas_estadual=row['perc_our_our_pc_uf'],
            )
        print(f"{muni}")
    except Municipio.DoesNotExist:
        print(f"Município com código {row['cod_ibge']} não encontrado 😵")