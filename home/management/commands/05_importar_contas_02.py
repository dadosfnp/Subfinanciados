# Exemplo de script para popular ReceitaMunicipal com base no cod_ibge
import pandas as pd
from home.models import Municipio, ContaMaisEspecifica, ContaMaisEspecificaPercentil

ContaMaisEspecifica.objects.all().delete()  # Limpa os dados antigos
ContaMaisEspecificaPercentil.objects.all().delete()  # Limpa os dados antigos


df = pd.read_excel("base_datas/dados/receitas_correntes_detalhamento_n2.xlsx")
# Substitui todos os valores vazios/NaN por 0 nas colunas de receita.
colunas_receita = [
        'itc_imp_ptu',
        'itc_imp_tbi',
        'itc_imp_ser',
        'itc_imp_rnd',
        'itc_imp_our',
        'itc_tax_pol',
        'itc_tax_ser',
        'itc_tax_our',
        'itc_con_pav',
        'itc_con_ipl',
        'itc_con_age',
        'itc_con_our',
        'trf_uni_fpm',
        'trf_uni_exp',
        'trf_uni_sus',
        'trf_uni_fnd',
        'trf_uni_fun',
        'trf_uni_fna',
        'trf_uni_our',
        'trf_est_icm',
        'trf_est_ipv',
        'trf_est_sus',
        'trf_est_ass',
        'trf_est_exp',
        'trf_est_our'
    ]
df[colunas_receita] = df[colunas_receita].fillna(0)
df['cod_ibge'] = df['cod_ibge'].astype(str)
for _, row in df.iterrows():
    try:
        muni = Municipio.objects.get(cod_ibge=row['cod_ibge'])
        ContaMaisEspecifica.objects.create(
            municipio=muni,
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
            outras_transferencias_estado = row['trf_est_our']
        )
        print(f"{muni}")
    except Municipio.DoesNotExist:
        print(f"Município com código {row['cod_ibge']} não encontrado 😵")





df = pd.read_excel("base_datas/dados/percentil_detalhamento_2.xlsx")
# Substitui todos os valores vazios/NaN por 0 nas colunas de receita.
colunas_receita = [
    # Nacional
    'perc_itc_imp_ptu_pc_nac', 
    'perc_itc_imp_tbi_pc_nac', 
    'perc_itc_imp_ser_pc_nac', 
    'perc_itc_imp_rnd_pc_nac',
    'perc_itc_imp_our_pc_nac', 
    'perc_itc_tax_pol_pc_nac',
    'perc_itc_tax_ser_pc_nac',
    'perc_itc_tax_our_pc_nac',
    'perc_itc_con_pav_pc_nac',
    'perc_itc_con_ipl_pc_nac',
    'perc_itc_con_age_pc_nac',
    'perc_itc_con_our_pc_nac',
    'perc_trf_uni_fpm_pc_nac',
    'perc_trf_uni_exp_pc_nac',
    'perc_trf_uni_sus_pc_nac',
    'perc_trf_uni_fnd_pc_nac',
    'perc_trf_uni_fun_pc_nac',
    'perc_trf_uni_fna_pc_nac',
    'perc_trf_uni_our_pc_nac',
    'perc_trf_est_icm_pc_nac',
    'perc_trf_est_ipv_pc_nac',
    'perc_trf_est_sus_pc_nac',
    'perc_trf_est_ass_pc_nac',
    'perc_trf_est_exp_pc_nac',
    'perc_trf_est_our_pc_nac',


    # Regional
    'perc_itc_imp_ptu_pc_faixa', 
    'perc_itc_imp_tbi_pc_faixa', 
    'perc_itc_imp_ser_pc_faixa', 
    'perc_itc_imp_rnd_pc_faixa',
    'perc_itc_imp_our_pc_faixa', 
    'perc_itc_tax_pol_pc_faixa',
    'perc_itc_tax_ser_pc_faixa',
    'perc_itc_tax_our_pc_faixa',
    'perc_itc_con_pav_pc_faixa',
    'perc_itc_con_ipl_pc_faixa',
    'perc_itc_con_age_pc_faixa',
    'perc_itc_con_our_pc_faixa',
    'perc_trf_uni_fpm_pc_faixa',
    'perc_trf_uni_exp_pc_faixa',
    'perc_trf_uni_sus_pc_faixa',
    'perc_trf_uni_fnd_pc_faixa',
    'perc_trf_uni_fun_pc_faixa',
    'perc_trf_uni_fna_pc_faixa',
    'perc_trf_uni_our_pc_faixa',
    'perc_trf_est_icm_pc_faixa',
    'perc_trf_est_ipv_pc_faixa',
    'perc_trf_est_sus_pc_faixa',
    'perc_trf_est_ass_pc_faixa',
    'perc_trf_est_exp_pc_faixa',
    'perc_trf_est_our_pc_faixa',


    # Estadual
    'perc_itc_imp_ptu_pc_uf', 
    'perc_itc_imp_tbi_pc_uf', 
    'perc_itc_imp_ser_pc_uf', 
    'perc_itc_imp_rnd_pc_uf',
    'perc_itc_imp_our_pc_uf', 
    'perc_itc_tax_pol_pc_uf',
    'perc_itc_tax_ser_pc_uf',
    'perc_itc_tax_our_pc_uf',
    'perc_itc_con_pav_pc_uf',
    'perc_itc_con_ipl_pc_uf',
    'perc_itc_con_age_pc_uf',
    'perc_itc_con_our_pc_uf',
    'perc_trf_uni_fpm_pc_uf',
    'perc_trf_uni_exp_pc_uf',
    'perc_trf_uni_sus_pc_uf',
    'perc_trf_uni_fnd_pc_uf',
    'perc_trf_uni_fun_pc_uf',
    'perc_trf_uni_fna_pc_uf',
    'perc_trf_uni_our_pc_uf',
    'perc_trf_est_icm_pc_uf',
    'perc_trf_est_ipv_pc_uf',
    'perc_trf_est_sus_pc_uf',
    'perc_trf_est_ass_pc_uf',
    'perc_trf_est_exp_pc_uf',
    'perc_trf_est_our_pc_uf',
    ]
df[colunas_receita] = df[colunas_receita].fillna(0)
df['cod_ibge'] = df['cod_ibge'].astype(str)

for _, row in df.iterrows():
    try:
        muni = Municipio.objects.get(cod_ibge=row['cod_ibge'])
        ContaMaisEspecificaPercentil.objects.create(
            municipio=muni,

            # Nacional
            iptu_nacional = row['perc_itc_imp_ptu_pc_nac'],         
            itbi_nacional = row['perc_itc_imp_tbi_pc_nac'],                                                                                  
            iss_nacional = row['perc_itc_imp_ser_pc_nac'],
            renda_nacional = row['perc_itc_imp_rnd_pc_nac'],
            outros_impostos_nacional = row['perc_itc_imp_our_pc_nac'],
            taxa_policia_nacional = row['perc_itc_tax_pol_pc_nac'],
            taxa_prestacao_servico_nacional = row['perc_itc_tax_ser_pc_nac'],
            outras_taxas_nacional = row['perc_itc_tax_our_pc_nac'],
            contribuicao_melhoria_pavimento_obras_nacional = row['perc_itc_con_pav_pc_nac'],
            contribuicao_melhoria_agua_potavel_nacional = row['perc_itc_con_ipl_pc_nac'],
            contribuicao_melhoria_iluminacao_publica_nacional = row['perc_itc_con_age_pc_nac'],
            outras_contribuicoes_melhoria_nacional = row['perc_itc_con_our_pc_nac'],
            transferencia_uniao_fpm_nacional = row['perc_trf_uni_fpm_pc_nac'],
            transferencia_uniao_exploracao_nacional = row['perc_trf_uni_exp_pc_nac'],
            transferencia_uniao_sus_nacional = row['perc_trf_uni_sus_pc_nac'],
            transferencia_uniao_fnde_nacional = row['perc_trf_uni_fnd_pc_nac'],
            transferencia_uniao_fundeb_nacional = row['perc_trf_uni_fun_pc_nac'],
            transferencia_uniao_fnas_nacional = row['perc_trf_uni_fna_pc_nac'],
            outras_transferencias_uniao_nacional = row['perc_trf_uni_our_pc_nac'],
            transferencia_estado_icms_nacional = row['perc_trf_est_icm_pc_nac'],
            transferencia_estado_ipva_nacional = row['perc_trf_est_ipv_pc_nac'],
            transferencia_estado_sus_nacional = row['perc_trf_est_sus_pc_nac'],
            transferencia_estado_assistencia_nacional = row['perc_trf_est_ass_pc_nac'],
            transferencia_estado_exploracao_nacional = row['perc_trf_est_exp_pc_nac'],
            outras_transferencias_estado_nacional = row['perc_trf_est_our_pc_nac'],

            # Regional
            iptu_regional = row['perc_itc_imp_ptu_pc_faixa'],         
            itbi_regional = row['perc_itc_imp_tbi_pc_faixa'],                                                                                  
            iss_regional = row['perc_itc_imp_ser_pc_faixa'],
            renda_regional = row['perc_itc_imp_rnd_pc_faixa'],
            outros_impostos_regional = row['perc_itc_imp_our_pc_faixa'],
            taxa_policia_regional = row['perc_itc_tax_pol_pc_faixa'],
            taxa_prestacao_servico_regional = row['perc_itc_tax_ser_pc_faixa'],
            outras_taxas_regional = row['perc_itc_tax_our_pc_faixa'],
            contribuicao_melhoria_pavimento_obras_regional = row['perc_itc_con_pav_pc_faixa'],
            contribuicao_melhoria_agua_potavel_regional = row['perc_itc_con_ipl_pc_faixa'],
            contribuicao_melhoria_iluminacao_publica_regional = row['perc_itc_con_age_pc_faixa'],
            outras_contribuicoes_melhoria_regional = row['perc_itc_con_our_pc_faixa'],
            transferencia_uniao_fpm_regional = row['perc_trf_uni_fpm_pc_faixa'],
            transferencia_uniao_exploracao_regional = row['perc_trf_uni_exp_pc_faixa'],
            transferencia_uniao_sus_regional = row['perc_trf_uni_sus_pc_faixa'],
            transferencia_uniao_fnde_regional = row['perc_trf_uni_fnd_pc_faixa'],
            transferencia_uniao_fundeb_regional = row['perc_trf_uni_fun_pc_faixa'],
            transferencia_uniao_fnas_regional = row['perc_trf_uni_fna_pc_faixa'],
            outras_transferencias_uniao_regional = row['perc_trf_uni_our_pc_faixa'],
            transferencia_estado_icms_regional = row['perc_trf_est_icm_pc_faixa'],
            transferencia_estado_ipva_regional = row['perc_trf_est_ipv_pc_faixa'],
            transferencia_estado_sus_regional = row['perc_trf_est_sus_pc_faixa'],
            transferencia_estado_assistencia_regional = row['perc_trf_est_ass_pc_faixa'],
            transferencia_estado_exploracao_regional = row['perc_trf_est_exp_pc_faixa'],
            outras_transferencias_estado_regional = row['perc_trf_est_our_pc_faixa'],



            # Estadual
            iptu_estadual = row['perc_itc_imp_ptu_pc_uf'],         
            itbi_estadual = row['perc_itc_imp_tbi_pc_uf'],                                                                                  
            iss_estadual = row['perc_itc_imp_ser_pc_uf'],
            renda_estadual = row['perc_itc_imp_rnd_pc_uf'],
            outros_impostos_estadual = row['perc_itc_imp_our_pc_uf'],
            taxa_policia_estadual = row['perc_itc_tax_pol_pc_uf'],
            taxa_prestacao_servico_estadual = row['perc_itc_tax_ser_pc_uf'],
            outras_taxas_estadual = row['perc_itc_tax_our_pc_uf'],
            contribuicao_melhoria_pavimento_obras_estadual = row['perc_itc_con_pav_pc_uf'],
            contribuicao_melhoria_agua_potavel_estadual = row['perc_itc_con_ipl_pc_uf'],
            contribuicao_melhoria_iluminacao_publica_estadual = row['perc_itc_con_age_pc_uf'],
            outras_contribuicoes_melhoria_estadual = row['perc_itc_con_our_pc_uf'],
            transferencia_uniao_fpm_estadual = row['perc_trf_uni_fpm_pc_uf'],
            transferencia_uniao_exploracao_estadual = row['perc_trf_uni_exp_pc_uf'],
            transferencia_uniao_sus_estadual = row['perc_trf_uni_sus_pc_uf'],
            transferencia_uniao_fnde_estadual = row['perc_trf_uni_fnd_pc_uf'],
            transferencia_uniao_fundeb_estadual = row['perc_trf_uni_fun_pc_uf'],
            transferencia_uniao_fnas_estadual = row['perc_trf_uni_fna_pc_uf'],
            outras_transferencias_uniao_estadual = row['perc_trf_uni_our_pc_uf'],
            transferencia_estado_icms_estadual = row['perc_trf_est_icm_pc_uf'],
            transferencia_estado_ipva_estadual = row['perc_trf_est_ipv_pc_uf'],
            transferencia_estado_sus_estadual = row['perc_trf_est_sus_pc_uf'],
            transferencia_estado_assistencia_estadual = row['perc_trf_est_ass_pc_uf'],
            transferencia_estado_exploracao_estadual = row['perc_trf_est_exp_pc_uf'],
            outras_transferencias_estado_estadual = row['perc_trf_est_our_pc_uf'],
            )
        print(f"{muni}")
    except Municipio.DoesNotExist:
        print(f"Município com código {row['cod_ibge']} não encontrado 😵")