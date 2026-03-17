import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Sum, Avg, F, ExpressionWrapper, FloatField, Q, Value
from home.models import Municipio, RegiaoMetropolitana, ContaDetalhada, MediaNacionalReceita, MediaUfReceita, MediaPorteReceita, CrescimentoMedioUf, CrescimentoMedioPorte, MedianaNacionalReceita, MedianaUfReceita, MedianaPorteReceita
from django.db.models.functions import Coalesce
from functools import reduce
import operator

def _get_filtered_municipios(request):
    """
    Helper centralizado para aplicar os filtros geográficos e populacionais 
    às consultas de análise agregada.
    """
    queryset = Municipio.objects.all()
    
    uf_filtro = request.GET.get('uf')
    regiao_filtro = request.GET.get('regiao')
    municipio_filtro = request.GET.get('municipio')
    porte_filtro = request.GET.get('porte')
    rm_filtro = request.GET.get('rm')
    classification_filter = request.GET.get('classification', 'quintil')
    subgroup_filter = request.GET.get('subgrupo')

    filtros_ativos = any([
        uf_filtro and uf_filtro != 'todos',
        regiao_filtro and regiao_filtro != 'todos',
        municipio_filtro and municipio_filtro != 'todos',
        porte_filtro and porte_filtro != 'todos',
        rm_filtro and rm_filtro != 'todos',
        subgroup_filter and subgroup_filter != 'todos'
    ])

    if not filtros_ativos:
        return queryset, False

    if regiao_filtro and regiao_filtro != 'todos':
        queryset = queryset.filter(regiao=regiao_filtro)
    if uf_filtro and uf_filtro != 'todos':
        queryset = queryset.filter(uf=uf_filtro)
    if municipio_filtro and municipio_filtro != 'todos':
        queryset = queryset.filter(name_muni_uf=municipio_filtro)
    if rm_filtro and rm_filtro != 'todos':
        queryset = queryset.filter(rm__nome=rm_filtro)

    if porte_filtro and porte_filtro != 'todos':
        if porte_filtro == 'Até 5 mil':
            queryset = queryset.filter(populacao24__lt=5000)
        elif porte_filtro == '5 mil a 10 mil':
            queryset = queryset.filter(populacao24__gte=5000, populacao24__lt=10000)
        elif porte_filtro == '10 mil a 20 mil':
            queryset = queryset.filter(populacao24__gte=10000, populacao24__lt=20000)
        elif porte_filtro == '20 mil a 50 mil':
            queryset = queryset.filter(populacao24__gte=20000, populacao24__lt=50000)
        elif porte_filtro == '50 mil a 100 mil':
            queryset = queryset.filter(populacao24__gte=50000, populacao24__lt=100000)
        elif porte_filtro == '100 mil a 200 mil':
            queryset = queryset.filter(populacao24__gte=100000, populacao24__lt=200000)
        elif porte_filtro == '200 mil a 500 mil':
            queryset = queryset.filter(populacao24__gte=200000, populacao24__lt=500000)
        elif porte_filtro == 'Acima de 500 mil':
            queryset = queryset.filter(populacao24__gte=500000)
        elif porte_filtro == 'Acima de 80 mil':
            queryset = queryset.filter(populacao24__gt=80000)
        elif porte_filtro == 'Abaixo de 80 mil':
            queryset = queryset.filter(populacao24__lte=80000)

    if subgroup_filter and subgroup_filter != "todos":
        if classification_filter == 'quintil':
            queryset = queryset.filter(quintil24=subgroup_filter)
        elif classification_filter == 'decil':
            queryset = queryset.filter(decil24=subgroup_filter)

    return queryset, True

def _prepare_revenue_item_aggregated(
    name: str,
    field_base: str,      
    field_path,           
    aggregated_data: dict,
    total_population: float,
    value_pc_nac: float,
    is_collapsible: bool = False,
):
    """Auxiliar para preparar item de receita na análise agregada."""
    value_abs = aggregated_data.get(f"total_{field_base}", 0) or 0
    
    avg_key = f"avg_{field_base}"
    value_pc = aggregated_data.get(avg_key)
    if value_pc is None:
        if total_population > 0:
            value_pc = value_abs / total_population
        else:
            value_pc = 0.0

    diff = {
        "pc": round(((value_pc - value_pc_nac) / value_pc_nac * 100), 2) if value_pc_nac else 0
    }

    item = {
        "name": name,
        "field_base": field_base,
        "value_abs": value_abs,
        "value_pc": value_pc,
        "diff": diff,
        "media_nacional": value_pc_nac,
        "children": [],
    }

    if is_collapsible:
        item["target_id"] = f"detalhe-{field_base.replace('_', '-')}"
    return item


def nacional_pc_media(fields):
    if isinstance(fields, str):
        expr = F(fields)
    else:
        expr = None
        for f in fields:
            expr = F(f) if expr is None else expr + F(f)

    qs = (
        Municipio.objects
        .filter(populacao24__gt=0)
        .annotate(total=expr)          # cria a soma primeiro
        .filter(total__gt=0)           # remove os zeros
        .annotate(
            pc=ExpressionWrapper(
                F('total') / F('populacao24'),
                output_field=FloatField()
            )
        )
    )

    return qs.aggregate(avg=Avg('pc'))['avg'] or 0

def _group_pc_media(queryset, fields):
    if isinstance(fields, str):
        expr = F(fields)
    else:
        expr = None
        for f in fields:
            expr = F(f) if expr is None else expr + F(f)

    qs = (
        queryset
        .filter(populacao24__gt=0)
        .annotate(total=expr)
        .filter(total__gt=0)
        .annotate(
            pc=ExpressionWrapper(
                F('total') / F('populacao24'),
                output_field=FloatField()
            )
        )
    )

    return qs.aggregate(avg=Avg('pc'))['avg'] or 0

def conjunto_detalhe_view(request):
    queryset = Municipio.objects.all()

    # Calcular a média nacional de receita per capita para comparação usando uma única query
    
    # 1. Helper para construir a expressão per capita
    # A consulta anterior tinha que filtrar por > 0, mas aqui como vamos calcular a média geral
    # usaremos diretamente as funções Avg() como o Django recomenda para consolidar de uma vez:
    def avg_pc(campo):
        return Avg(ExpressionWrapper(F(campo) / F('populacao24'), output_field=FloatField()), filter=Q(**{f'{campo}__gt': 0, 'populacao24__gt': 0}))

    # 2. Executa UMA ÚNICA query de agregação para pegar todas as médias nacionais
    medias_nac = Municipio.objects.aggregate(
        itc_pc = avg_pc('conta_detalhada__imposto_taxas_contribuicoes'),
        imp_pc = avg_pc('conta_especifica__imposto'),
        iss_pc = avg_pc('conta_mais_especifica__iss'),
        iptu_pc = avg_pc('conta_mais_especifica__iptu'),
        itbi_pc = avg_pc('conta_mais_especifica__itbi'),
        renda_pc = avg_pc('conta_mais_especifica__imposto_renda'),
        # Para outros impostos formados por multiplas colunas, a abordagem correta seria somar as colunas no aggregate, 
        # mas como estamos otimizando as queries e elas dependem do populacao, vamos fazer a expressao completa.
        outros_impostos_pc = Avg(
            ExpressionWrapper(
                (Coalesce(F('conta_mais_especifica__outros_impostos'), 0.0) + 
                 Coalesce(F('conta_mais_especifica__imposto_icms'), 0.0) + 
                 Coalesce(F('conta_mais_especifica__imposto_ipva'), 0.0)) / F('populacao24'),
                output_field=FloatField()
            ),
            filter=Q(populacao24__gt=0)
        ),
        taxas_pc = avg_pc('conta_especifica__taxas'),
        taxa_policia_pc = avg_pc('conta_mais_especifica__taxa_policia'),
        taxa_prestacao_servico_pc = avg_pc('conta_mais_especifica__taxa_prestacao_servico'),
        outras_taxas_pc = avg_pc('conta_mais_especifica__outras_taxas'),
        
        contribuicoes_melhoria_pc = avg_pc('conta_especifica__contribuicoes_melhoria'),
        contribuicao_melhoria_pavimento_obras_pc = avg_pc('conta_mais_especifica__contribuicao_melhoria_pavimento_obras'),
        contribuicao_melhoria_agua_potavel_pc = avg_pc('conta_mais_especifica__contribuicao_melhoria_agua_potavel'),
        contribuicao_melhoria_iluminacao_publica_pc = avg_pc('conta_mais_especifica__contribuicao_melhoria_iluminacao_publica'),
        outras_contribuicoes_melhoria_pc = avg_pc('conta_mais_especifica__outras_contribuicoes_melhoria'),

        contribuicoes_pc = avg_pc('conta_detalhada__contribuicoes'),
        contribuicoes_sociais_pc = avg_pc('conta_especifica__contribuicoes_sociais'),
        contribuicoes_iluminacao_publica_pc = avg_pc('conta_especifica__contribuicoes_iluminacao_publica'),
        outras_contribuicoes_pc = avg_pc('conta_especifica__outras_contribuicoes'),

        trasnsferencias_correntes_pc = avg_pc('conta_detalhada__transferencias_correntes'),
        tranferencias_uniao_pc = avg_pc('conta_especifica__tranferencias_uniao'),
        tranferencias_uniao_fpm_pc = avg_pc('conta_mais_especifica__transferencia_uniao_fpm'),
        tranferencias_uniao_exploracao_pc = avg_pc('conta_mais_especifica__transferencia_uniao_exploracao'),
        tranferencias_uniao_sus_pc = avg_pc('conta_mais_especifica__transferencia_uniao_sus'),
        tranferencias_uniao_fnde_pc = avg_pc('conta_mais_especifica__transferencia_uniao_fnde'),
        tranferencias_uniao_fundeb_pc = avg_pc('conta_mais_especifica__transferencia_uniao_fundeb'),
        tranferencias_uniao_fnas_pc = avg_pc('conta_mais_especifica__transferencia_uniao_fnas'),
        outras_tranferencias_uniao_pc = avg_pc('conta_mais_especifica__outras_transferencias_uniao'),

        tranferencias_estados_pc = avg_pc('conta_especifica__tranferencias_estados'),
        transferencias_estado_icms_pc = avg_pc('conta_mais_especifica__transferencia_estado_icms'),
        transferencias_estado_ipva_pc = avg_pc('conta_mais_especifica__transferencia_estado_ipva'),
        transferencias_estado_exploracao_pc = avg_pc('conta_mais_especifica__transferencia_estado_exploracao'),
        transferencias_estado_sus_pc = avg_pc('conta_mais_especifica__transferencia_estado_sus'),
        transferencias_estado_assistencia_pc = avg_pc('conta_mais_especifica__transferencia_estado_assistencia'),
        outras_transferencias_estado_pc = avg_pc('conta_mais_especifica__outras_transferencias_estado'),

        outras_tranferencias_pc = avg_pc('conta_especifica__outras_tranferencias'),

        outras_receitas_pc = avg_pc('conta_detalhada__outras_receita'),
        receita_patrimonial_pc = avg_pc('conta_especifica__receita_patrimonial'),
        receita_agropecuaria_pc = avg_pc('conta_especifica__receita_agropecuaria'),
        receita_industrial_pc = avg_pc('conta_especifica__receita_industrial'),
        receita_servicos_pc = avg_pc('conta_especifica__receita_servicos'),
        outras_receitas_outras_pc = avg_pc('conta_especifica__outras_receitas'),
    )

    # 3. Desempacotando o dicionario nas variaveis originais (fallback com 0)
    nacional_med_itc_pc = medias_nac['itc_pc'] or 0
    nacional_med_imp_pc = medias_nac['imp_pc'] or 0
    nacional_med_iss = medias_nac['iss_pc'] or 0
    nacional_med_iptu = medias_nac['iptu_pc'] or 0
    nacional_med_itbi = medias_nac['itbi_pc'] or 0
    nacional_med_renda = medias_nac['renda_pc'] or 0
    nacional_med_outros_impostos = medias_nac['outros_impostos_pc'] or 0
    nacional_med_taxas_pc = medias_nac['taxas_pc'] or 0
    nacional_med_taxa_policia_pc = medias_nac['taxa_policia_pc'] or 0
    nacional_med_taxa_prestacao_servico_pc = medias_nac['taxa_prestacao_servico_pc'] or 0
    nacional_med_outras_taxas_pc = medias_nac['outras_taxas_pc'] or 0
    nacional_med_contribuicoes_melhoria_pc = medias_nac['contribuicoes_melhoria_pc'] or 0
    nacional_med_contribuicao_melhoria_pavimento_obras_pc = medias_nac['contribuicao_melhoria_pavimento_obras_pc'] or 0
    nacional_med_contribuicao_melhoria_agua_potavel_pc = medias_nac['contribuicao_melhoria_agua_potavel_pc'] or 0
    nacional_med_contribuicao_melhoria_iluminacao_publica_pc = medias_nac['contribuicao_melhoria_iluminacao_publica_pc'] or 0
    nacional_med_outras_contribuicoes_melhoria_pc = medias_nac['outras_contribuicoes_melhoria_pc'] or 0
    nacional_med_contribuicoes_pc = medias_nac['contribuicoes_pc'] or 0
    nacional_med_contribuicoes_sociais_pc = medias_nac['contribuicoes_sociais_pc'] or 0
    nacional_med_contribuicoes_iluminacao_publica_pc = medias_nac['contribuicoes_iluminacao_publica_pc'] or 0
    nacional_med_outras_contribuicoes_pc = medias_nac['outras_contribuicoes_pc'] or 0
    nacional_med_trasnsferencias_correntes_pc = medias_nac['trasnsferencias_correntes_pc'] or 0
    nacional_med_tranferencias_uniao_pc = medias_nac['tranferencias_uniao_pc'] or 0
    nacional_med_tranferencias_uniao_fpm_pc = medias_nac['tranferencias_uniao_fpm_pc'] or 0
    nacional_med_tranferencias_uniao_exploracao_pc = medias_nac['tranferencias_uniao_exploracao_pc'] or 0
    nacional_med_tranferencias_uniao_sus_pc = medias_nac['tranferencias_uniao_sus_pc'] or 0
    nacional_med_tranferencias_uniao_fnde_pc = medias_nac['tranferencias_uniao_fnde_pc'] or 0
    nacional_med_tranferencias_uniao_fundeb_pc = medias_nac['tranferencias_uniao_fundeb_pc'] or 0
    nacional_med_tranferencias_uniao_fnas_pc = medias_nac['tranferencias_uniao_fnas_pc'] or 0
    nacional_med_outras_tranferencias_uniao_pc = medias_nac['outras_tranferencias_uniao_pc'] or 0
    nacional_med_tranferencias_estados_pc = medias_nac['tranferencias_estados_pc'] or 0
    nacional_med_transferencias_estado_icms_pc = medias_nac['transferencias_estado_icms_pc'] or 0
    nacional_med_transferencias_estado_ipva_pc = medias_nac['transferencias_estado_ipva_pc'] or 0
    nacional_med_transferencias_estado_exploracao_pc = medias_nac['transferencias_estado_exploracao_pc'] or 0
    nacional_med_transferencias_estado_sus_pc = medias_nac['transferencias_estado_sus_pc'] or 0
    nacional_med_transferencias_estado_assistencia_pc = medias_nac['transferencias_estado_assistencia_pc'] or 0
    nacional_med_outras_transferencias_estado_pc = medias_nac['outras_transferencias_estado_pc'] or 0
    nacional_med_outras_tranferencias_pc = medias_nac['outras_tranferencias_pc'] or 0
    nacional_med_outras_receitas_pc = medias_nac['outras_receitas_pc'] or 0
    nacional_med_receita_patrimonial_pc = medias_nac['receita_patrimonial_pc'] or 0
    nacional_med_receita_agropecuaria_pc = medias_nac['receita_agropecuaria_pc'] or 0
    nacional_med_receita_industrial_pc = medias_nac['receita_industrial_pc'] or 0
    nacional_med_receita_servicos_pc = medias_nac['receita_servicos_pc'] or 0
    nacional_med_outras_receitas_outras_pc = medias_nac['outras_receitas_outras_pc'] or 0

    # --- filtros ---
    uf_filtro = request.GET.get('uf')
    regiao_filtro = request.GET.get('regiao')
    municipio_filtro = request.GET.get('municipio')
    porte_filtro = request.GET.get('porte')
    rm_filtro = request.GET.get('rm')
    classification_filter = request.GET.get('classification', 'quintil')
    subgroup_filter = request.GET.get('subgrupo')

    if regiao_filtro and regiao_filtro != 'todos':
        queryset = queryset.filter(regiao=regiao_filtro)
    if uf_filtro and uf_filtro != 'todos':
        queryset = queryset.filter(uf=uf_filtro)
    if municipio_filtro and municipio_filtro != 'todos':
        queryset = queryset.filter(name_muni_uf=municipio_filtro)
    if rm_filtro and rm_filtro != 'todos':
        queryset = queryset.filter(rm__nome=rm_filtro)

    # --- faixas de porte ---
    if porte_filtro and porte_filtro != 'todos':
        if porte_filtro == 'Até 5 mil':
            queryset = queryset.filter(populacao24__lt=5000)
        elif porte_filtro == '5 mil a 10 mil':
            queryset = queryset.filter(populacao24__gte=5000, populacao24__lt=10000)
        elif porte_filtro == '10 mil a 20 mil':
            queryset = queryset.filter(populacao24__gte=10000, populacao24__lt=20000)
        elif porte_filtro == '20 mil a 50 mil':
            queryset = queryset.filter(populacao24__gte=20000, populacao24__lt=50000)
        elif porte_filtro == '50 mil a 100 mil':
            queryset = queryset.filter(populacao24__gte=50000, populacao24__lt=100000)
        elif porte_filtro == '100 mil a 200 mil':
            queryset = queryset.filter(populacao24__gte=100000, populacao24__lt=200000)
        elif porte_filtro == '200 mil a 500 mil':
            queryset = queryset.filter(populacao24__gte=200000, populacao24__lt=500000)
        elif porte_filtro == 'Acima de 500 mil':
            queryset = queryset.filter(populacao24__gte=500000)
        elif porte_filtro == 'Acima de 80 mil':
            queryset = queryset.filter(populacao24__gt=80000)
        elif porte_filtro == 'Abaixo de 80 mil':
            queryset = queryset.filter(populacao24__lte=80000)

    if subgroup_filter and subgroup_filter != "todos":
        if classification_filter == 'quintil':
            queryset = queryset.filter(quintil24=subgroup_filter)
        elif classification_filter == 'decil':
            queryset = queryset.filter(decil24=subgroup_filter)

    # --- agregações ---
    aggregated_data = queryset.aggregate(
        total_receita_corrente=Sum('rc_2024'),
        total_receita_2000=Sum('rc_2000'),
        total_populacao_24=Sum('populacao24'),
        total_populacao_00=Sum('populacao00'),

        total_imposto_taxas_contribuicoes=Sum('conta_detalhada__imposto_taxas_contribuicoes'),
        total_contribuicoes=Sum('conta_detalhada__contribuicoes'),
        total_transferencias_correntes=Sum('conta_detalhada__transferencias_correntes'),
        total_outras_receita=Sum('conta_detalhada__outras_receita'),

        total_imposto=Sum('conta_especifica__imposto'),
        total_taxas=Sum('conta_especifica__taxas'),
        total_contribuicoes_melhoria=Sum('conta_especifica__contribuicoes_melhoria'),

        total_contribuicoes_sociais=Sum('conta_especifica__contribuicoes_sociais'),
        total_contribuicoes_iluminacao_publica=Sum('conta_especifica__contribuicoes_iluminacao_publica'),
        total_outras_contribuicoes=Sum('conta_especifica__outras_contribuicoes'),

        total_tranferencias_uniao=Sum('conta_especifica__tranferencias_uniao'),          # (grafado assim no modelo)
        total_tranferencias_estados=Sum('conta_especifica__tranferencias_estados'),
        total_outras_tranferencias=Sum('conta_especifica__outras_tranferencias'),

        total_receita_patrimonial=Sum('conta_especifica__receita_patrimonial'),
        total_receita_agropecuaria=Sum('conta_especifica__receita_agropecuaria'),
        total_receita_industrial=Sum('conta_especifica__receita_industrial'),
        total_receita_servicos=Sum('conta_especifica__receita_servicos'),
        total_outras_receitas=Sum('conta_especifica__outras_receitas'),

        total_iptu=Sum('conta_mais_especifica__iptu'),
        total_itbi=Sum('conta_mais_especifica__itbi'),
        total_iss=Sum('conta_mais_especifica__iss'),
        total_imposto_renda=Sum('conta_mais_especifica__imposto_renda'),
        total_outros_impostos=Sum('conta_mais_especifica__outros_impostos') + Sum('conta_mais_especifica__imposto_icms') + Sum('conta_mais_especifica__imposto_ipva'),

        total_taxa_policia=Sum('conta_mais_especifica__taxa_policia'),
        total_taxa_prestacao_servico=Sum('conta_mais_especifica__taxa_prestacao_servico'),
        total_outras_taxas=Sum('conta_mais_especifica__outras_taxas'),

        total_contribuicao_melhoria_pavimento_obras=Sum('conta_mais_especifica__contribuicao_melhoria_pavimento_obras'),
        total_contribuicao_melhoria_agua_potavel=Sum('conta_mais_especifica__contribuicao_melhoria_agua_potavel'),
        total_contribuicao_melhoria_iluminacao_publica=Sum('conta_mais_especifica__contribuicao_melhoria_iluminacao_publica'),
        total_outras_contribuicoes_melhoria=Sum('conta_mais_especifica__outras_contribuicoes_melhoria'),

        total_transferencia_uniao_fpm=Sum('conta_mais_especifica__transferencia_uniao_fpm'),
        #total_transferencia_uniao_fpe=Sum('conta_mais_especifica__transferencia_uniao_fpe'),
        total_transferencia_uniao_exploracao=Sum('conta_mais_especifica__transferencia_uniao_exploracao'),
        total_transferencia_uniao_sus=Sum('conta_mais_especifica__transferencia_uniao_sus'),
        total_transferencia_uniao_fnde=Sum('conta_mais_especifica__transferencia_uniao_fnde'),
        total_transferencia_uniao_fundeb=Sum('conta_mais_especifica__transferencia_uniao_fundeb'),
        total_transferencia_uniao_fnas=Sum('conta_mais_especifica__transferencia_uniao_fnas'),
        total_outras_transferencias_uniao=Sum('conta_mais_especifica__outras_transferencias_uniao'),

        total_transferencia_estado_icms=Sum('conta_mais_especifica__transferencia_estado_icms') ,  
        total_transferencia_estado_ipva=Sum('conta_mais_especifica__transferencia_estado_ipva') ,
        total_transferencia_estado_exploracao=Sum('conta_mais_especifica__transferencia_estado_exploracao'),
        total_transferencia_estado_sus=Sum('conta_mais_especifica__transferencia_estado_sus'),
        total_transferencia_estado_assistencia=Sum('conta_mais_especifica__transferencia_estado_assistencia'),
        total_outras_transferencias_estado=Sum('conta_mais_especifica__outras_transferencias_estado'),
    )

    # helper para tratar None -> 0
    def v(key):
        return aggregated_data.get(key) or 0

    # ------- revenue_tree (mantive sua lógica original) -------
    revenue_tree = []
    population = aggregated_data['total_populacao_24'] or 0
    pop00 = aggregated_data['total_populacao_00'] or 0
    rc24 = aggregated_data['total_receita_corrente'] or 0
    rc00 = aggregated_data['total_receita_2000'] or 0

    rc_24_pc_agregado = _group_pc_media(queryset, 'rc_2024')
    rc_00_pc_agregado = _group_pc_media(queryset, 'rc_2000')

    delta_rc_pc_agg = queryset.filter(rc_24_pc__gt=0, rc_00_pc__gt=0).annotate(
        d=(F('rc_24_pc') / F('rc_00_pc') - 1) * 100
    ).aggregate(avg_d=Avg('d'))
    delta_rc_pc = delta_rc_pc_agg['avg_d'] if delta_rc_pc_agg['avg_d'] is not None else 0

    delta_pop_agg = queryset.filter(populacao00__gt=0).annotate(
        dp=(F('populacao24') * 1.0 / F('populacao00') - 1) * 100
    ).aggregate(avg_dp=Avg('dp'))
    delta_pop = delta_pop_agg['avg_dp'] if delta_pop_agg['avg_dp'] is not None else 0

    # ---------------------------
    # ITC (Impostos, Taxas e Contribuições de Melhoria)
    # ---------------------------
    itc_item = _prepare_revenue_item_aggregated(
        "Impostos, Taxas e Contribuições de Melhoria",
        "imposto_taxas_contribuicoes",
        "conta_detalhada__imposto_taxas_contribuicoes",
        aggregated_data,
                            population,
        nacional_med_itc_pc,
        is_collapsible=True,
    )

    if itc_item:
        # ---------------------------
        # ITC_IMP (Impostos)
        # ---------------------------
        imposto_item = _prepare_revenue_item_aggregated(
            "Impostos",
            "imposto",
            "conta_especifica__imposto",
            aggregated_data,
                            population,
            nacional_med_imp_pc,
            is_collapsible=True,
        )

        if imposto_item:
            imposto_item["children"].extend(
                filter(
                    None,
                    [
                        _prepare_revenue_item_aggregated(
                            "Imposto sobre a Propriedade Predial e Territorial Urbana",
                            "iptu",
                            "conta_mais_especifica__iptu",
                            aggregated_data,
                            population,
                            nacional_med_iptu,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Imposto sobre a Transmissão 'Inter Vivos'",
                            "itbi",
                            "conta_mais_especifica__itbi",
                            aggregated_data,
                            population,
                            nacional_med_itbi,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Imposto sobre Serviços",
                            "iss",
                            "conta_mais_especifica__iss",
                            aggregated_data,
                            population,
                            nacional_med_iss,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Imposto de Renda",
                            "imposto_renda",
                            "conta_mais_especifica__imposto_renda",
                            aggregated_data,
                            population,
                            nacional_med_renda,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Outros Impostos",
                            "outros_impostos",
                            ["conta_mais_especifica__outros_impostos", "conta_mais_especifica__imposto_icms", "conta_mais_especifica__imposto_ipva"],
                            aggregated_data,
                            population,
                            nacional_med_outros_impostos,
                        ),
                    ],
                )
            )
            itc_item["children"].append(imposto_item)

        # ---------------------------
        # ITC_TAX (Taxas)
        # ---------------------------
        taxas_item = _prepare_revenue_item_aggregated(
            "Taxas",
            "taxas",
            "conta_especifica__taxas",
            aggregated_data,
                            population,
            nacional_med_taxas_pc,
            is_collapsible=True,
        )

        if taxas_item:
            taxas_item["children"].extend(
                filter(
                    None,
                    [
                        _prepare_revenue_item_aggregated(
                            "Taxas pelo Exercício do Poder de Polícia",
                            "taxa_policia",
                            "conta_mais_especifica__taxa_policia",
                            aggregated_data,
                            population,
                            nacional_med_taxa_policia_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Taxas pela Prestação de Serviços",
                            "taxa_prestacao_servico",
                            "conta_mais_especifica__taxa_prestacao_servico",
                            aggregated_data,
                            population,
                            nacional_med_taxa_prestacao_servico_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Outras Taxas",
                            "outras_taxas",
                            "conta_mais_especifica__outras_taxas",
                            aggregated_data,
                            population,
                            nacional_med_outras_taxas_pc,
                        ),
                    ],
                )
            )
            itc_item["children"].append(taxas_item)

        # ---------------------------
        # ITC_CON (Contribuições de Melhoria)
        # ---------------------------
        cm_item = _prepare_revenue_item_aggregated(
            "Contribuições de Melhoria",
            "contribuicoes_melhoria",
            "conta_especifica__contribuicoes_melhoria",
            aggregated_data,
                            population,
            nacional_med_contribuicoes_melhoria_pc,
            is_collapsible=True,
        )

        if cm_item:
            cm_item["children"].extend(
                filter(
                    None,
                    [
                        _prepare_revenue_item_aggregated(
                            "Contribuição de Melhoria para Pavimentação e Obras",
                            "contribuicao_melhoria_pavimento_obras",
                            "conta_mais_especifica__contribuicao_melhoria_pavimento_obras",
                            aggregated_data,
                            population,
                            nacional_med_contribuicao_melhoria_pavimento_obras_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Contribuição de Melhoria para Rede de Água e Esgoto",
                            "contribuicao_melhoria_agua_potavel",
                            "conta_mais_especifica__contribuicao_melhoria_agua_potavel",
                            aggregated_data,
                            population,
                            nacional_med_contribuicao_melhoria_agua_potavel_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Contribuição de Melhoria para Iluminação Pública",
                            "contribuicao_melhoria_iluminacao_publica",
                            "conta_mais_especifica__contribuicao_melhoria_iluminacao_publica",
                            aggregated_data,
                            population,
                            nacional_med_contribuicao_melhoria_iluminacao_publica_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Outras Contribuições de Melhoria",
                            "outras_contribuicoes_melhoria",
                            "conta_mais_especifica__outras_contribuicoes_melhoria",
                            aggregated_data,
                            population,
                            nacional_med_outras_contribuicoes_melhoria_pc,
                        ),
                    ],
                )
            )
            itc_item["children"].append(cm_item)

        revenue_tree.append(itc_item)

    # ---------------------------
    # CON (Contribuições)
    # ---------------------------
    contribuicoes_item = _prepare_revenue_item_aggregated(
        "Contribuições",
        "contribuicoes",
        "conta_detalhada__contribuicoes",
        aggregated_data,
                            population,
        nacional_med_contribuicoes_pc,
        is_collapsible=True,
    )

    if contribuicoes_item:
        contribuicoes_item["children"].extend(
            filter(
                None,
                [
                    _prepare_revenue_item_aggregated(
                        "Contribuições Sociais",
                        "contribuicoes_sociais",
                        "conta_especifica__contribuicoes_sociais",
                        aggregated_data,
                            population,
                        nacional_med_contribuicoes_sociais_pc,
                    ),
                    _prepare_revenue_item_aggregated(
                        "Custeio do Serviço de Iluminação Pública",
                        "contribuicoes_iluminacao_publica",
                        "conta_especifica__contribuicoes_iluminacao_publica",
                        aggregated_data,
                            population,
                        nacional_med_contribuicoes_iluminacao_publica_pc,
                    ),
                    _prepare_revenue_item_aggregated(
                        "Outras Contribuições",
                        "outras_contribuicoes",
                        "conta_especifica__outras_contribuicoes",
                        aggregated_data,
                            population,
                        nacional_med_outras_contribuicoes_pc,
                    ),
                ],
            )
        )
        revenue_tree.append(contribuicoes_item)

    # ---------------------------
    # TRF (Transferências Correntes)
    # ---------------------------
    transferencias_item = _prepare_revenue_item_aggregated(
        "Transferências Correntes",
        "transferencias_correntes",
        "conta_detalhada__transferencias_correntes",
        aggregated_data,
                            population,
        nacional_med_trasnsferencias_correntes_pc,
        is_collapsible=True,
    )

    if transferencias_item:
        # ---------------------------
        # TRF_UNI (União)
        # ---------------------------
        uniao = _prepare_revenue_item_aggregated(
            "Transferências da União",
            "tranferencias_uniao",
            "conta_especifica__tranferencias_uniao",
            aggregated_data,
                            population,
            nacional_med_tranferencias_uniao_pc,
            is_collapsible=True,
        )

        if uniao:
            uniao["children"].extend(
                filter(
                    None,
                    [
                        _prepare_revenue_item_aggregated(
                            "Cota-Parte do FPM",
                            "transferencia_uniao_fpm",
                            "conta_mais_especifica__transferencia_uniao_fpm",
                            aggregated_data,
                            population,
                            nacional_med_tranferencias_uniao_fpm_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Compensação Financeira (Recursos Naturais)",
                            "transferencia_uniao_exploracao",
                            "conta_mais_especifica__transferencia_uniao_exploracao",
                            aggregated_data,
                            population,
                            nacional_med_tranferencias_uniao_exploracao_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Recursos do SUS",
                            "transferencia_uniao_sus",
                            "conta_mais_especifica__transferencia_uniao_sus",
                            aggregated_data,
                            population,
                            nacional_med_tranferencias_uniao_sus_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Recursos do FNDE",
                            "transferencia_uniao_fnde",
                            "conta_mais_especifica__transferencia_uniao_fnde",
                            aggregated_data,
                            population,
                            nacional_med_tranferencias_uniao_fnde_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Recursos do FUNDEB",
                            "transferencia_uniao_fundeb",
                            "conta_mais_especifica__transferencia_uniao_fundeb",
                            aggregated_data,
                            population,
                            nacional_med_tranferencias_uniao_fundeb_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Recursos do FNAS",
                            "transferencia_uniao_fnas",
                            "conta_mais_especifica__transferencia_uniao_fnas",
                            aggregated_data,
                            population,
                            nacional_med_tranferencias_uniao_fnas_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Outras Transferências da União",
                            "outras_transferencias_uniao",
                            "conta_mais_especifica__outras_transferencias_uniao",
                            aggregated_data,
                            population,
                            nacional_med_outras_tranferencias_uniao_pc,
                        ),
                    ],
                )
            )
            transferencias_item["children"].append(uniao)

        # ---------------------------
        # TRF_EST (Estados)
        # ---------------------------
        estados = _prepare_revenue_item_aggregated(
            "Transferências dos Estados",
            "tranferencias_estados",
            "conta_especifica__tranferencias_estados",
            aggregated_data,
                            population,
            nacional_med_tranferencias_estados_pc,
            is_collapsible=True,
        )

        if estados:
            estados["children"].extend(
                filter(
                    None,
                    [
                        _prepare_revenue_item_aggregated(
                            "Cota-Parte do ICMS",
                            "transferencia_estado_icms",
                            "conta_mais_especifica__transferencia_estado_icms",
                            aggregated_data,
                            population,
                            nacional_med_transferencias_estado_icms_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Cota-Parte do IPVA",
                            "transferencia_estado_ipva",
                            "conta_mais_especifica__transferencia_estado_ipva",
                            aggregated_data,
                            population,
                            nacional_med_transferencias_estado_ipva_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Compensação Financeira (Recursos Naturais)",
                            "transferencia_estado_exploracao",
                            "conta_mais_especifica__transferencia_estado_exploracao",
                            aggregated_data,
                            population,
                            nacional_med_transferencias_estado_exploracao_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Recursos do SUS",
                            "transferencia_estado_sus",
                            "conta_mais_especifica__transferencia_estado_sus",
                            aggregated_data,
                            population,
                            nacional_med_transferencias_estado_sus_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Assistência Social",
                            "transferencia_estado_assistencia",
                            "conta_mais_especifica__transferencia_estado_assistencia",
                            aggregated_data,
                            population,
                            nacional_med_transferencias_estado_assistencia_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Outras Transferências dos Estados",
                            "outras_transferencias_estado",
                            "conta_mais_especifica__outras_transferencias_estado",
                            aggregated_data,
                            population,
                            nacional_med_outras_transferencias_estado_pc,
                        ),
                    ],
                )
            )
            transferencias_item["children"].append(estados)

        outras_trf = _prepare_revenue_item_aggregated(
            "Outras Transferências",
            "outras_tranferencias",
            "conta_especifica__outras_tranferencias",
            aggregated_data,
                            population,
            nacional_med_outras_tranferencias_pc,
        )
        if outras_trf:
            transferencias_item["children"].append(outras_trf)

        revenue_tree.append(transferencias_item)

    # ---------------------------
    # OUR (Outras Receitas Correntes)
    # ---------------------------
    outras_receitas_item = _prepare_revenue_item_aggregated(
        "Outras Receitas Correntes",
        "outras_receita",
        "conta_detalhada__outras_receita",
        aggregated_data,
                            population,
        nacional_med_outras_receitas_pc,
        is_collapsible=True,
    )

    if outras_receitas_item:
        outras_receitas_item["children"].extend(
            filter(
                None,
                [
                    _prepare_revenue_item_aggregated(
                        "Receita Patrimonial",
                        "receita_patrimonial",
                        "conta_especifica__receita_patrimonial",
                        aggregated_data,
                            population,
                        nacional_med_receita_patrimonial_pc,
                    ),
                    _prepare_revenue_item_aggregated(
                        "Receita Agropecuária",
                        "receita_agropecuaria",
                        "conta_especifica__receita_agropecuaria",
                        aggregated_data,
                            population,
                        nacional_med_receita_agropecuaria_pc,
                    ),
                    _prepare_revenue_item_aggregated(
                        "Receita Industrial",
                        "receita_industrial",
                        "conta_especifica__receita_industrial",
                        aggregated_data,
                            population,
                        nacional_med_receita_industrial_pc,
                    ),
                    _prepare_revenue_item_aggregated(
                        "Receita de Serviços",
                        "receita_servicos",
                        "conta_especifica__receita_servicos",
                        aggregated_data,
                            population,
                        nacional_med_receita_servicos_pc,
                    ),
                    _prepare_revenue_item_aggregated(
                        "Outras Receitas",
                        "outras_receitas",
                        "conta_especifica__outras_receitas",
                        aggregated_data,
                            population,
                        nacional_med_outras_receitas_outras_pc,
                    ),
                ],
            )
        )
        revenue_tree.append(outras_receitas_item)


    # ------- CHART DATA EXACTO (valores absolutos) -------
    chart_data = {
        "main_categories": {
            "labels": ["Impostos, Taxas e Contribuições", "Contribuições", "Transf. Correntes", "Outras"],
            "values": [
                v('total_imposto_taxas_contribuicoes'),
                v('total_contribuicoes'),
                v('total_transferencias_correntes'),
                v('total_outras_receita'),
            ],
        },
        "imposto_taxas_contribuicoes": {
            "labels": ["Impostos", "Taxas", "Contribuições de Melhoria"], 
            "values": [
                v('total_imposto'),
                v('total_taxas'),
                v('total_contribuicoes_melhoria'),
            ],
        },
        "imposto": {
            "labels": ["IPTU", "ITBI", "ISS", "Imposto de Renda", "Outros"],
            "values": [
                v('total_iptu'),
                v('total_itbi'),
                v('total_iss'),
                v('total_imposto_renda'),
                v('total_outros_impostos') + v('total_imposto_icms') + v('total_imposto_ipva'),
            ],
        },
        "taxas": {
            "labels": ["Poder de Polícia", "Prestação de Serviços", "Outras"],
            "values": [
                v('total_taxa_policia'),
                v('total_taxa_prestacao_servico'),
                v('total_outras_taxas'),
                ],
        },
        "contribuicoes_melhoria": {
            "labels": [ "Pavimentação", "Água/Esgoto", "Iluminação", "Outras"],
            "values": [ v('total_contribuicao_melhoria_pavimento_obras'),
                        v('total_contribuicao_melhoria_agua_potavel'),
                        v('total_contribuicao_melhoria_iluminacao_publica'),
                        v('total_outras_contribuicoes_melhoria'),
                     ],
        },
        "contribuicoes": {
            "labels": ["Sociais", "Iluminação Pública", "Outras"],
            "values": [v('total_contribuicoes'),
                       v('total_contribuicoes_iluminacao_publica'),
                       v('total_outras_contribuicoes')],  # se quiser só sociais, troque para v('total_contribuicoes_sociais')
        },
        "transferencias_correntes": {
            "labels": ["União", "Estados", "Outras"],
            "values": [
                v('total_tranferencias_uniao'),    # nota: no modelo está "tranferencias"
                v('total_tranferencias_estados'),
                v('total_outras_tranferencias'),
            ],
        },
        "transferencias_uniao": {
            "labels": ["FPM", "Rec. Naturais", "SUS", "FNDE", "FUNDEB", "FNAS", "Outras"],
            "values": [
                v('total_transferencia_uniao_fpm'),
                v('total_transferencia_uniao_exploracao'),
                v('total_transferencia_uniao_sus'),
                v('total_transferencia_uniao_fnde'),
                v('total_transferencia_uniao_fundeb'),
                v('total_transferencia_uniao_fundeb'),
                v('total_transferencia_uniao_fnas'),
                v('total_outras_transferencias_uniao'),
            ],
        },
        "transferencias_estado": {
            "labels": ["ICMS", "IPVA", "Rec. Naturais", "SUS", "Assistência", "Outras"],
            "values": [
                v('total_transferencia_estado_icms'),
                v('total_transferencia_estado_ipva'),
                v('total_transferencia_estado_exploracao'),
                v('total_transferencia_estado_sus'),
                v('total_transferencia_estado_assistencia'),
                v('total_outras_transferencias_estado'),
            ],
        },
        "outras_receitas": {
            "labels": ["Patrimonial", "Serviços", "Outras"],
            "values": [
                v('total_receita_patrimonial'),
                v('total_receita_servicos'),
                v('total_outras_receitas'),
            ],
        },
    }

    qs = (
        Municipio.objects
        .annotate(
            # Categorias Principais
            main_categories=F('rc_24_pc'),

            # Imposto, Taxas e Contribuições de Melhoria
            imposto_taxas_contribuicoes=F('conta_detalhada__imposto_taxas_contribuicoes')/F('populacao24'),
            imposto = F('conta_especifica__imposto')/F('populacao24'),  
            taxas = F('conta_especifica__taxas')/F('populacao24'),
            contribuicoes_melhoria = F('conta_especifica__contribuicoes_melhoria')/F('populacao24'),

            # Contribuições
            contribuicoes=F('conta_detalhada__contribuicoes')/F('populacao24'),

            # Transferências Correntes
            transferencias_correntes=F('conta_detalhada__transferencias_correntes')/F('populacao24'),
            transferencias_uniao = F('conta_especifica__tranferencias_uniao')/F('populacao24'),
            transferencias_estado = F('conta_especifica__tranferencias_estados')/F('populacao24'),

            # Outras Receitas Correntes
            outras_receitas=F('conta_detalhada__outras_receita')/F('populacao24'),
                  )
        .values(                  # já vem “flat” pro template
            "cod_ibge", "main_categories",
            
            "imposto_taxas_contribuicoes",
            "imposto",
            "taxas",
            "contribuicoes_melhoria",
            
            "contribuicoes",

            "transferencias_correntes",
            "transferencias_uniao",
            "transferencias_estado",
            
            "outras_receitas",
            
            
        )
        .order_by("cod_ibge")
    )

    data = list(qs)  # ~5.570 linhas é tranquilo

    qsf = (
        Municipio.objects
        .annotate(
            # Categorias Principais
            main_categories=F('rc_24_pc'),

            # Imposto, Taxas e Contribuições de Melhoria
            imposto_taxas_contribuicoes=F('conta_detalhada__imposto_taxas_contribuicoes')/F('populacao24'),
            imposto = F('conta_especifica__imposto')/F('populacao24'),  
            taxas = F('conta_especifica__taxas')/F('populacao24'),
            contribuicoes_melhoria = F('conta_especifica__contribuicoes_melhoria')/F('populacao24'),

            # Contribuições
            contribuicoes=F('conta_detalhada__contribuicoes')/F('populacao24'),

            # Transferências Correntes
            transferencias_correntes=F('conta_detalhada__transferencias_correntes')/F('populacao24'),
            transferencias_uniao = F('conta_especifica__tranferencias_uniao')/F('populacao24'),
            transferencias_estado = F('conta_especifica__tranferencias_estados')/F('populacao24'),

            # Outras Receitas Correntes
            outras_receitas=F('conta_detalhada__outras_receita')/F('populacao24'),
                  )
        .values(                  # já vem “flat” pro template
            "cod_ibge", "main_categories",
            
            "imposto_taxas_contribuicoes",
            "imposto",
            "taxas",
            "contribuicoes_melhoria",
            
            "contribuicoes",

            "transferencias_correntes",
            "transferencias_uniao",
            "transferencias_estado",
            
            "outras_receitas",
            
            
        )
        .order_by("cod_ibge")
    )

    data_f = list(qsf)  # ~5.570 linhas é tranquilo
    print(data_f)
    print("a")
    context = {
        'revenue_tree': revenue_tree,
        # passe o dict direto; no template use {{ chart_data_json|json_script:"chart-data" }}
        'chart_data_json': chart_data,
        'data_json': data,
        'data_f_json': data_f,
        'hist_data': {
            'pop24': population,
            'pop00': pop00,
            'rc24': rc24,
            'rc00': rc00,
            'rc24_pc': rc_24_pc_agregado,
            'rc00_pc': rc_00_pc_agregado,
            'delta_rc_pc': delta_rc_pc,
            'delta_pop': delta_pop,
        },
        'evolucao_historica': {
            'delta_populacao': round(delta_pop, 2),
            'delta_rc_pc': round(delta_rc_pc, 2),
            'has_2000_data': bool(pop00 > 0 or rc00 > 0)
        },
        'media_nacional_rc_pc': 316.74,
        'media_nacional_pop': 16.04,
    }

    print(revenue_tree)
    return render(request, 'detail_agg/detalhe_conjunto.html', context)




def conjunto_fiscal_api(request):
    queryset = Municipio.objects.all()


    # Calcular a média nacional de receita per capita para comparação
    # ITC
    nacional_med_itc_pc = nacional_pc_media('conta_detalhada__imposto_taxas_contribuicoes')

    # ITC_IMP
    nacional_med_imp_pc = nacional_pc_media('conta_especifica__imposto')

    # impostos (mais específico)
    nacional_med_iss = nacional_pc_media('conta_mais_especifica__iss')
    nacional_med_iptu = nacional_pc_media('conta_mais_especifica__iptu')
    nacional_med_itbi = nacional_pc_media('conta_mais_especifica__itbi')
    nacional_med_renda = nacional_pc_media('conta_mais_especifica__imposto_renda')

    nacional_med_outros_impostos = nacional_pc_media(['conta_mais_especifica__outros_impostos', 'conta_mais_especifica__imposto_icms', 'conta_mais_especifica__imposto_ipva'])

    # ITC_TAX
    nacional_med_taxas_pc = nacional_pc_media('conta_especifica__taxas')
    nacional_med_taxa_policia_pc = nacional_pc_media('conta_mais_especifica__taxa_policia')
    nacional_med_taxa_prestacao_servico_pc = nacional_pc_media('conta_mais_especifica__taxa_prestacao_servico')
    nacional_med_outras_taxas_pc = nacional_pc_media('conta_mais_especifica__outras_taxas')

    # ITC_CON
    nacional_med_contribuicoes_melhoria_pc = nacional_pc_media('conta_especifica__contribuicoes_melhoria')
    nacional_med_contribuicao_melhoria_pavimento_obras_pc = nacional_pc_media('conta_mais_especifica__contribuicao_melhoria_pavimento_obras')
    nacional_med_contribuicao_melhoria_agua_potavel_pc = nacional_pc_media('conta_mais_especifica__contribuicao_melhoria_agua_potavel')
    nacional_med_contribuicao_melhoria_iluminacao_publica_pc = nacional_pc_media('conta_mais_especifica__contribuicao_melhoria_iluminacao_publica')
    nacional_med_outras_contribuicoes_melhoria_pc = nacional_pc_media('conta_mais_especifica__outras_contribuicoes_melhoria')

    # CON
    nacional_med_contribuicoes_pc = nacional_pc_media('conta_detalhada__contribuicoes')
    nacional_med_contribuicoes_sociais_pc = nacional_pc_media('conta_especifica__contribuicoes_sociais')
    nacional_med_contribuicoes_iluminacao_publica_pc = nacional_pc_media('conta_especifica__contribuicoes_iluminacao_publica')
    nacional_med_outras_contribuicoes_pc = nacional_pc_media('conta_especifica__outras_contribuicoes')

    # TRF
    nacional_med_trasnsferencias_correntes_pc = nacional_pc_media('conta_detalhada__transferencias_correntes')

    # TRF_UNI
    nacional_med_tranferencias_uniao_pc = nacional_pc_media('conta_especifica__tranferencias_uniao')
    nacional_med_tranferencias_uniao_fpm_pc = nacional_pc_media('conta_mais_especifica__transferencia_uniao_fpm')
    nacional_med_tranferencias_uniao_exploracao_pc = nacional_pc_media('conta_mais_especifica__transferencia_uniao_exploracao')
    nacional_med_tranferencias_uniao_sus_pc = nacional_pc_media('conta_mais_especifica__transferencia_uniao_sus')
    nacional_med_tranferencias_uniao_fnde_pc = nacional_pc_media('conta_mais_especifica__transferencia_uniao_fnde')
    nacional_med_tranferencias_uniao_fundeb_pc = nacional_pc_media('conta_mais_especifica__transferencia_uniao_fundeb')
    nacional_med_tranferencias_uniao_fnas_pc = nacional_pc_media('conta_mais_especifica__transferencia_uniao_fnas')
    nacional_med_outras_tranferencias_uniao_pc = nacional_pc_media('conta_mais_especifica__outras_transferencias_uniao')

    # TRF_EST
    nacional_med_tranferencias_estados_pc = nacional_pc_media('conta_especifica__tranferencias_estados')
    nacional_med_transferencias_estado_icms_pc = nacional_pc_media('conta_mais_especifica__transferencia_estado_icms')
    nacional_med_transferencias_estado_ipva_pc = nacional_pc_media('conta_mais_especifica__transferencia_estado_ipva')
    nacional_med_transferencias_estado_exploracao_pc = nacional_pc_media('conta_mais_especifica__transferencia_estado_exploracao')
    nacional_med_transferencias_estado_sus_pc = nacional_pc_media('conta_mais_especifica__transferencia_estado_sus')
    nacional_med_transferencias_estado_assistencia_pc = nacional_pc_media('conta_mais_especifica__transferencia_estado_assistencia')
    nacional_med_outras_transferencias_estado_pc = nacional_pc_media('conta_mais_especifica__outras_transferencias_estado')

    # TRF_OUR
    nacional_med_outras_tranferencias_pc = nacional_pc_media('conta_especifica__outras_tranferencias')

    # OUR
    nacional_med_outras_receitas_pc = nacional_pc_media('conta_detalhada__outras_receita')
    nacional_med_receita_patrimonial_pc = nacional_pc_media('conta_especifica__receita_patrimonial')
    nacional_med_receita_agropecuaria_pc = nacional_pc_media('conta_especifica__receita_agropecuaria')
    nacional_med_receita_industrial_pc = nacional_pc_media('conta_especifica__receita_industrial')
    nacional_med_receita_servicos_pc = nacional_pc_media('conta_especifica__receita_servicos')
    nacional_med_outras_receitas_outras_pc = nacional_pc_media('conta_especifica__outras_receitas')

    queryset, filtros_ativos = _get_filtered_municipios(request)

    # Perform the aggregation
    aggregated_data = queryset.aggregate(
        total_receita_corrente=Coalesce(Sum('rc_2024'), Value(0.0)),
        total_receita_2000=Coalesce(Sum('rc_2000'), Value(0.0)),
        total_populacao_24=Coalesce(Sum('populacao24'), Value(1)), # Avoid div by zero
        total_populacao_00=Coalesce(Sum('populacao00'), Value(0)),
        total_imposto_taxas_contribuicoes=Coalesce(Sum('conta_detalhada__imposto_taxas_contribuicoes'), Value(0.0)),
        total_contribuicoes=Coalesce(Sum('conta_detalhada__contribuicoes'), Value(0.0)),
        total_transferencias_correntes=Coalesce(Sum('conta_detalhada__transferencias_correntes'), Value(0.0)),
        total_outras_receita=Coalesce(Sum('conta_detalhada__outras_receita'), Value(0.0)),
        total_imposto=Coalesce(Sum('conta_especifica__imposto'), Value(0.0)),
        total_taxas=Coalesce(Sum('conta_especifica__taxas'), Value(0.0)),
        total_contribuicoes_melhoria=Coalesce(Sum('conta_especifica__contribuicoes_melhoria'), Value(0.0)),
        total_contribuicoes_sociais=Coalesce(Sum('conta_especifica__contribuicoes_sociais'), Value(0.0)),
        total_contribuicoes_iluminacao_publica=Coalesce(Sum('conta_especifica__contribuicoes_iluminacao_publica'), Value(0.0)),
        total_outras_contribuicoes=Coalesce(Sum('conta_especifica__outras_contribuicoes'), Value(0.0)),
        total_tranferencias_uniao=Coalesce(Sum('conta_especifica__tranferencias_uniao'), Value(0.0)),
        total_tranferencias_estados=Coalesce(Sum('conta_especifica__tranferencias_estados'), Value(0.0)),
        total_outras_tranferencias=Coalesce(Sum('conta_especifica__outras_tranferencias'), Value(0.0)),
        total_receita_patrimonial=Coalesce(Sum('conta_especifica__receita_patrimonial'), Value(0.0)),
        total_receita_agropecuaria=Coalesce(Sum('conta_especifica__receita_agropecuaria'), Value(0.0)),
        total_receita_industrial=Coalesce(Sum('conta_especifica__receita_industrial'), Value(0.0)),
        total_receita_servicos=Coalesce(Sum('conta_especifica__receita_servicos'), Value(0.0)),
        total_outras_receitas=Coalesce(Sum('conta_especifica__outras_receitas'), Value(0.0)),
        total_iptu=Coalesce(Sum('conta_mais_especifica__iptu'), Value(0.0)),
        total_itbi=Coalesce(Sum('conta_mais_especifica__itbi'), Value(0.0)),
        total_iss=Coalesce(Sum('conta_mais_especifica__iss'), Value(0.0)),
        total_imposto_renda=Coalesce(Sum('conta_mais_especifica__imposto_renda'), Value(0.0)),
        total_outros_impostos=Coalesce(Sum('conta_mais_especifica__outros_impostos') + Sum('conta_mais_especifica__imposto_icms') + Sum('conta_mais_especifica__imposto_ipva'), Value(0.0)),
        total_taxa_policia=Coalesce(Sum('conta_mais_especifica__taxa_policia'), Value(0.0)),
        total_taxa_prestacao_servico=Coalesce(Sum('conta_mais_especifica__taxa_prestacao_servico'), Value(0.0)),
        total_outras_taxas=Coalesce(Sum('conta_mais_especifica__outras_taxas'), Value(0.0)),
        total_contribuicao_melhoria_pavimento_obras=Coalesce(Sum('conta_mais_especifica__contribuicao_melhoria_pavimento_obras'), Value(0.0)),
        total_contribuicao_melhoria_agua_potavel=Coalesce(Sum('conta_mais_especifica__contribuicao_melhoria_agua_potavel'), Value(0.0)),
        total_contribuicao_melhoria_iluminacao_publica=Coalesce(Sum('conta_mais_especifica__contribuicao_melhoria_iluminacao_publica'), Value(0.0)),
        total_outras_contribuicoes_melhoria=Coalesce(Sum('conta_mais_especifica__outras_contribuicoes_melhoria'), Value(0.0)),
        total_transferencia_uniao_fpm=Coalesce(Sum('conta_mais_especifica__transferencia_uniao_fpm'), Value(0.0)),
        total_transferencia_uniao_exploracao=Coalesce(Sum('conta_mais_especifica__transferencia_uniao_exploracao'), Value(0.0)),
        total_transferencia_uniao_sus=Coalesce(Sum('conta_mais_especifica__transferencia_uniao_sus'), Value(0.0)),
        total_transferencia_uniao_fnde=Sum('conta_mais_especifica__transferencia_uniao_fnde'),
        total_transferencia_uniao_fundeb=Sum('conta_mais_especifica__transferencia_uniao_fundeb'),
        total_transferencia_uniao_fnas=Sum('conta_mais_especifica__transferencia_uniao_fnas'),
        total_outras_transferencias_uniao=Sum('conta_mais_especifica__outras_transferencias_uniao'),
        total_transferencia_estado_icms=Sum('conta_mais_especifica__transferencia_estado_icms'),
        total_transferencia_estado_ipva=Sum('conta_mais_especifica__transferencia_estado_ipva'),
        total_transferencia_estado_exploracao=Sum('conta_mais_especifica__transferencia_estado_exploracao'),
        total_transferencia_estado_sus=Sum('conta_mais_especifica__transferencia_estado_sus'),
        total_transferencia_estado_assistencia=Sum('conta_mais_especifica__transferencia_estado_assistencia'),
        total_outras_transferencias_estado=Sum('conta_mais_especifica__outras_transferencias_estado'),
    )

    population = aggregated_data['total_populacao_24'] or 0
    pop00 = aggregated_data['total_populacao_00'] or 0
    rc24 = aggregated_data['total_receita_corrente'] or 0
    rc00 = aggregated_data['total_receita_2000'] or 0

    aggregated_data['avg_rc_24'] = _group_pc_media(queryset, 'rc_2024')
    aggregated_data['avg_rc_00'] = _group_pc_media(queryset, 'rc_2000')

    rc_24_pc_agregado = aggregated_data['avg_rc_24']
    rc_00_pc_agregado = aggregated_data['avg_rc_00']
    
    delta_rc_pc_agg = queryset.filter(rc_24_pc__gt=0, rc_00_pc__gt=0).annotate(
        d=(F('rc_24_pc') / F('rc_00_pc') - 1) * 100
    ).aggregate(avg_d=Avg('d'))
    delta_rc_pc = round(delta_rc_pc_agg['avg_d'], 2) if delta_rc_pc_agg['avg_d'] is not None else 0

    delta_pop_agg = queryset.filter(populacao00__gt=0).annotate(
        dp=(F('populacao24') * 1.0 / F('populacao00') - 1) * 100
    ).aggregate(avg_dp=Avg('dp'))
    delta_pop = round(delta_pop_agg['avg_dp'], 2) if delta_pop_agg['avg_dp'] is not None else 0

    total_mun_24 = Municipio.objects.filter(rc_24_pc__gt=0).count()
    mun_menor_24 = Municipio.objects.filter(rc_24_pc__lt=rc_24_pc_agregado, rc_24_pc__gt=0).count()
    percentil24_dyn = int((mun_menor_24 / total_mun_24 * 100)) if total_mun_24 > 0 else 0
    
    total_mun_00 = Municipio.objects.filter(rc_00_pc__gt=0).count()
    mun_menor_00 = Municipio.objects.filter(rc_00_pc__lt=rc_00_pc_agregado, rc_00_pc__gt=0).count()
    percentil00_dyn = int((mun_menor_00 / total_mun_00 * 100)) if total_mun_00 > 0 else 0

    aggregated_data['avg_imposto_taxas_contribuicoes'] = _group_pc_media(queryset, 'conta_detalhada__imposto_taxas_contribuicoes')
    aggregated_data['avg_imposto'] = _group_pc_media(queryset, 'conta_especifica__imposto')
    aggregated_data['avg_iss'] = _group_pc_media(queryset, 'conta_mais_especifica__iss')
    aggregated_data['avg_iptu'] = _group_pc_media(queryset, 'conta_mais_especifica__iptu')
    aggregated_data['avg_itbi'] = _group_pc_media(queryset, 'conta_mais_especifica__itbi')
    aggregated_data['avg_imposto_renda'] = _group_pc_media(queryset, 'conta_mais_especifica__imposto_renda')
    aggregated_data['avg_outros_impostos'] = _group_pc_media(queryset, ['conta_mais_especifica__outros_impostos', 'conta_mais_especifica__imposto_icms', 'conta_mais_especifica__imposto_ipva'])
    aggregated_data['avg_taxas'] = _group_pc_media(queryset, 'conta_especifica__taxas')
    aggregated_data['avg_taxa_policia'] = _group_pc_media(queryset, 'conta_mais_especifica__taxa_policia')
    aggregated_data['avg_taxa_prestacao_servico'] = _group_pc_media(queryset, 'conta_mais_especifica__taxa_prestacao_servico')
    aggregated_data['avg_outras_taxas'] = _group_pc_media(queryset, 'conta_mais_especifica__outras_taxas')
    aggregated_data['avg_contribuicoes_melhoria'] = _group_pc_media(queryset, 'conta_especifica__contribuicoes_melhoria')
    aggregated_data['avg_contribuicao_melhoria_pavimento_obras'] = _group_pc_media(queryset, 'conta_mais_especifica__contribuicao_melhoria_pavimento_obras')
    aggregated_data['avg_contribuicao_melhoria_agua_potavel'] = _group_pc_media(queryset, 'conta_mais_especifica__contribuicao_melhoria_agua_potavel')
    aggregated_data['avg_contribuicao_melhoria_iluminacao_publica'] = _group_pc_media(queryset, 'conta_mais_especifica__contribuicao_melhoria_iluminacao_publica')
    aggregated_data['avg_outras_contribuicoes_melhoria'] = _group_pc_media(queryset, 'conta_mais_especifica__outras_contribuicoes_melhoria')
    aggregated_data['avg_contribuicoes'] = _group_pc_media(queryset, 'conta_detalhada__contribuicoes')
    aggregated_data['avg_contribuicoes_sociais'] = _group_pc_media(queryset, 'conta_especifica__contribuicoes_sociais')
    aggregated_data['avg_contribuicoes_iluminacao_publica'] = _group_pc_media(queryset, 'conta_especifica__contribuicoes_iluminacao_publica')
    aggregated_data['avg_outras_contribuicoes'] = _group_pc_media(queryset, 'conta_especifica__outras_contribuicoes')
    aggregated_data['avg_transferencias_correntes'] = _group_pc_media(queryset, 'conta_detalhada__transferencias_correntes')
    aggregated_data['avg_tranferencias_uniao'] = _group_pc_media(queryset, 'conta_especifica__tranferencias_uniao')
    aggregated_data['avg_transferencia_uniao_fpm'] = _group_pc_media(queryset, 'conta_mais_especifica__transferencia_uniao_fpm')
    aggregated_data['avg_transferencia_uniao_exploracao'] = _group_pc_media(queryset, 'conta_mais_especifica__transferencia_uniao_exploracao')
    aggregated_data['avg_transferencia_uniao_sus'] = _group_pc_media(queryset, 'conta_mais_especifica__transferencia_uniao_sus')
    aggregated_data['avg_transferencia_uniao_fnde'] = _group_pc_media(queryset, 'conta_mais_especifica__transferencia_uniao_fnde')
    aggregated_data['avg_transferencia_uniao_fundeb'] = _group_pc_media(queryset, 'conta_mais_especifica__transferencia_uniao_fundeb')
    aggregated_data['avg_transferencia_uniao_fnas'] = _group_pc_media(queryset, 'conta_mais_especifica__transferencia_uniao_fnas')
    aggregated_data['avg_outras_transferencias_uniao'] = _group_pc_media(queryset, 'conta_mais_especifica__outras_transferencias_uniao')
    aggregated_data['avg_tranferencias_estados'] = _group_pc_media(queryset, 'conta_especifica__tranferencias_estados')
    aggregated_data['avg_transferencia_estado_icms'] = _group_pc_media(queryset, 'conta_mais_especifica__transferencia_estado_icms')
    aggregated_data['avg_transferencia_estado_ipva'] = _group_pc_media(queryset, 'conta_mais_especifica__transferencia_estado_ipva')
    aggregated_data['avg_transferencia_estado_exploracao'] = _group_pc_media(queryset, 'conta_mais_especifica__transferencia_estado_exploracao')
    aggregated_data['avg_transferencia_estado_sus'] = _group_pc_media(queryset, 'conta_mais_especifica__transferencia_estado_sus')
    aggregated_data['avg_transferencia_estado_assistencia'] = _group_pc_media(queryset, 'conta_mais_especifica__transferencia_estado_assistencia')
    aggregated_data['avg_outras_transferencias_estado'] = _group_pc_media(queryset, 'conta_mais_especifica__outras_transferencias_estado')
    aggregated_data['avg_outras_tranferencias'] = _group_pc_media(queryset, 'conta_especifica__outras_tranferencias')
    aggregated_data['avg_outras_receita'] = _group_pc_media(queryset, 'conta_detalhada__outras_receita')
    aggregated_data['avg_receita_patrimonial'] = _group_pc_media(queryset, 'conta_especifica__receita_patrimonial')
    aggregated_data['avg_receita_agropecuaria'] = _group_pc_media(queryset, 'conta_especifica__receita_agropecuaria')
    aggregated_data['avg_receita_industrial'] = _group_pc_media(queryset, 'conta_especifica__receita_industrial')
    aggregated_data['avg_receita_servicos'] = _group_pc_media(queryset, 'conta_especifica__receita_servicos')
    aggregated_data['avg_outras_receitas'] = _group_pc_media(queryset, 'conta_especifica__outras_receitas')


    revenue_tree = []
    # 1. Impostos, Taxas e Contribuições (ITC)
    # ---------------------------
    # ITC (Impostos, Taxas e Contribuições de Melhoria)
    # ---------------------------
    itc_item = _prepare_revenue_item_aggregated(
        "Impostos, Taxas e Contribuições de Melhoria",
        "imposto_taxas_contribuicoes",
        "conta_detalhada__imposto_taxas_contribuicoes",
        aggregated_data,
                            population,
        nacional_med_itc_pc,
        is_collapsible=True,
    )

    if itc_item:
        # ---------------------------
        # ITC_IMP (Impostos)
        # ---------------------------
        imposto_item = _prepare_revenue_item_aggregated(
            "Impostos",
            "imposto",
            "conta_especifica__imposto",
            aggregated_data,
                            population,
            nacional_med_imp_pc,
            is_collapsible=True,
        )

        if imposto_item:
            imposto_item["children"].extend(
                filter(
                    None,
                    [
                        _prepare_revenue_item_aggregated(
                            "Imposto sobre a Propriedade Predial e Territorial Urbana",
                            "iptu",
                            "conta_mais_especifica__iptu",
                            aggregated_data,
                            population,
                            nacional_med_iptu,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Imposto sobre a Transmissão 'Inter Vivos'",
                            "itbi",
                            "conta_mais_especifica__itbi",
                            aggregated_data,
                            population,
                            nacional_med_itbi,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Imposto sobre Serviços",
                            "iss",
                            "conta_mais_especifica__iss",
                            aggregated_data,
                            population,
                            nacional_med_iss,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Imposto de Renda",
                            "imposto_renda",
                            "conta_mais_especifica__imposto_renda",
                            aggregated_data,
                            population,
                            nacional_med_renda,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Outros Impostos",
                            "outros_impostos",
                            ["conta_mais_especifica__outros_impostos", "conta_mais_especifica__imposto_icms", "conta_mais_especifica__imposto_ipva"],
                            aggregated_data,
                            population,
                            nacional_med_outros_impostos,
                        ),
                    ],
                )
            )
            itc_item["children"].append(imposto_item)

        # ---------------------------
        # ITC_TAX (Taxas)
        # ---------------------------
        taxas_item = _prepare_revenue_item_aggregated(
            "Taxas",
            "taxas",
            "conta_especifica__taxas",
            aggregated_data,
                            population,
            nacional_med_taxas_pc,
            is_collapsible=True,
        )

        if taxas_item:
            taxas_item["children"].extend(
                filter(
                    None,
                    [
                        _prepare_revenue_item_aggregated(
                            "Taxas pelo Exercício do Poder de Polícia",
                            "taxa_policia",
                            "conta_mais_especifica__taxa_policia",
                            aggregated_data,
                            population,
                            nacional_med_taxa_policia_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Taxas pela Prestação de Serviços",
                            "taxa_prestacao_servico",
                            "conta_mais_especifica__taxa_prestacao_servico",
                            aggregated_data,
                            population,
                            nacional_med_taxa_prestacao_servico_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Outras Taxas",
                            "outras_taxas",
                            "conta_mais_especifica__outras_taxas",
                            aggregated_data,
                            population,
                            nacional_med_outras_taxas_pc,
                        ),
                    ],
                )
            )
            itc_item["children"].append(taxas_item)

        # ---------------------------
        # ITC_CON (Contribuições de Melhoria)
        # ---------------------------
        cm_item = _prepare_revenue_item_aggregated(
            "Contribuições de Melhoria",
            "contribuicoes_melhoria",
            "conta_especifica__contribuicoes_melhoria",
            aggregated_data,
                            population,
            nacional_med_contribuicoes_melhoria_pc,
            is_collapsible=True,
        )

        if cm_item:
            cm_item["children"].extend(
                filter(
                    None,
                    [
                        _prepare_revenue_item_aggregated(
                            "Contribuição de Melhoria para Pavimentação e Obras",
                            "contribuicao_melhoria_pavimento_obras",
                            "conta_mais_especifica__contribuicao_melhoria_pavimento_obras",
                            aggregated_data,
                            population,
                            nacional_med_contribuicao_melhoria_pavimento_obras_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Contribuição de Melhoria para Rede de Água e Esgoto",
                            "contribuicao_melhoria_agua_potavel",
                            "conta_mais_especifica__contribuicao_melhoria_agua_potavel",
                            aggregated_data,
                            population,
                            nacional_med_contribuicao_melhoria_agua_potavel_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Contribuição de Melhoria para Iluminação Pública",
                            "contribuicao_melhoria_iluminacao_publica",
                            "conta_mais_especifica__contribuicao_melhoria_iluminacao_publica",
                            aggregated_data,
                            population,
                            nacional_med_contribuicao_melhoria_iluminacao_publica_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Outras Contribuições de Melhoria",
                            "outras_contribuicoes_melhoria",
                            "conta_mais_especifica__outras_contribuicoes_melhoria",
                            aggregated_data,
                            population,
                            nacional_med_outras_contribuicoes_melhoria_pc,
                        ),
                    ],
                )
            )
            itc_item["children"].append(cm_item)

        revenue_tree.append(itc_item)

    # ---------------------------
    # CON (Contribuições)
    # ---------------------------
    contribuicoes_item = _prepare_revenue_item_aggregated(
        "Contribuições",
        "contribuicoes",
        "conta_detalhada__contribuicoes",
        aggregated_data,
                            population,
        nacional_med_contribuicoes_pc,
        is_collapsible=True,
    )

    if contribuicoes_item:
        contribuicoes_item["children"].extend(
            filter(
                None,
                [
                    _prepare_revenue_item_aggregated(
                        "Contribuições Sociais",
                        "contribuicoes_sociais",
                        "conta_especifica__contribuicoes_sociais",
                        aggregated_data,
                            population,
                        nacional_med_contribuicoes_sociais_pc,
                    ),
                    _prepare_revenue_item_aggregated(
                        "Custeio do Serviço de Iluminação Pública",
                        "contribuicoes_iluminacao_publica",
                        "conta_especifica__contribuicoes_iluminacao_publica",
                        aggregated_data,
                            population,
                        nacional_med_contribuicoes_iluminacao_publica_pc,
                    ),
                    _prepare_revenue_item_aggregated(
                        "Outras Contribuições",
                        "outras_contribuicoes",
                        "conta_especifica__outras_contribuicoes",
                        aggregated_data,
                            population,
                        nacional_med_outras_contribuicoes_pc,
                    ),
                ],
            )
        )
        revenue_tree.append(contribuicoes_item)

    # ---------------------------
    # TRF (Transferências Correntes)
    # ---------------------------
    transferencias_item = _prepare_revenue_item_aggregated(
        "Transferências Correntes",
        "transferencias_correntes",
        "conta_detalhada__transferencias_correntes",
        aggregated_data,
                            population,
        nacional_med_trasnsferencias_correntes_pc,
        is_collapsible=True,
    )

    if transferencias_item:
        # ---------------------------
        # TRF_UNI (União)
        # ---------------------------
        uniao = _prepare_revenue_item_aggregated(
            "Transferências da União",
            "tranferencias_uniao",
            "conta_especifica__tranferencias_uniao",
            aggregated_data,
                            population,
            nacional_med_tranferencias_uniao_pc,
            is_collapsible=True,
        )

        if uniao:
            uniao["children"].extend(
                filter(
                    None,
                    [
                        _prepare_revenue_item_aggregated(
                            "Cota-Parte do FPM",
                            "transferencia_uniao_fpm",
                            "conta_mais_especifica__transferencia_uniao_fpm",
                            aggregated_data,
                            population,
                            nacional_med_tranferencias_uniao_fpm_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Compensação Financeira (Recursos Naturais)",
                            "transferencia_uniao_exploracao",
                            "conta_mais_especifica__transferencia_uniao_exploracao",
                            aggregated_data,
                            population,
                            nacional_med_tranferencias_uniao_exploracao_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Recursos do SUS",
                            "transferencia_uniao_sus",
                            "conta_mais_especifica__transferencia_uniao_sus",
                            aggregated_data,
                            population,
                            nacional_med_tranferencias_uniao_sus_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Recursos do FNDE",
                            "transferencia_uniao_fnde",
                            "conta_mais_especifica__transferencia_uniao_fnde",
                            aggregated_data,
                            population,
                            nacional_med_tranferencias_uniao_fnde_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Recursos do FUNDEB",
                            "transferencia_uniao_fundeb",
                            "conta_mais_especifica__transferencia_uniao_fundeb",
                            aggregated_data,
                            population,
                            nacional_med_tranferencias_uniao_fundeb_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Recursos do FNAS",
                            "transferencia_uniao_fnas",
                            "conta_mais_especifica__transferencia_uniao_fnas",
                            aggregated_data,
                            population,
                            nacional_med_tranferencias_uniao_fnas_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Outras Transferências da União",
                            "outras_transferencias_uniao",
                            "conta_mais_especifica__outras_transferencias_uniao",
                            aggregated_data,
                            population,
                            nacional_med_outras_tranferencias_uniao_pc,
                        ),
                    ],
                )
            )
            transferencias_item["children"].append(uniao)

        # ---------------------------
        # TRF_EST (Estados)
        # ---------------------------
        estados = _prepare_revenue_item_aggregated(
            "Transferências dos Estados",
            "tranferencias_estados",
            "conta_especifica__tranferencias_estados",
            aggregated_data,
                            population,
            nacional_med_tranferencias_estados_pc,
            is_collapsible=True,
        )

        if estados:
            estados["children"].extend(
                filter(
                    None,
                    [
                        _prepare_revenue_item_aggregated(
                            "Cota-Parte do ICMS",
                            "transferencia_estado_icms",
                            "conta_mais_especifica__transferencia_estado_icms",
                            aggregated_data,
                            population,
                            nacional_med_transferencias_estado_icms_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Cota-Parte do IPVA",
                            "transferencia_estado_ipva",
                            "conta_mais_especifica__transferencia_estado_ipva",
                            aggregated_data,
                            population,
                            nacional_med_transferencias_estado_ipva_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Compensação Financeira (Recursos Naturais)",
                            "transferencia_estado_exploracao",
                            "conta_mais_especifica__transferencia_estado_exploracao",
                            aggregated_data,
                            population,
                            nacional_med_transferencias_estado_exploracao_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Recursos do SUS",
                            "transferencia_estado_sus",
                            "conta_mais_especifica__transferencia_estado_sus",
                            aggregated_data,
                            population,
                            nacional_med_transferencias_estado_sus_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Assistência Social",
                            "transferencia_estado_assistencia",
                            "conta_mais_especifica__transferencia_estado_assistencia",
                            aggregated_data,
                            population,
                            nacional_med_transferencias_estado_assistencia_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Outras Transferências dos Estados",
                            "outras_transferencias_estado",
                            "conta_mais_especifica__outras_transferencias_estado",
                            aggregated_data,
                            population,
                            nacional_med_outras_transferencias_estado_pc,
                        ),
                    ],
                )
            )
            transferencias_item["children"].append(estados)

        outras_trf = _prepare_revenue_item_aggregated(
            "Outras Transferências",
            "outras_tranferencias",
            "conta_especifica__outras_tranferencias",
            aggregated_data,
                            population,
            nacional_med_outras_tranferencias_pc,
        )
        if outras_trf:
            transferencias_item["children"].append(outras_trf)

        revenue_tree.append(transferencias_item)

    # ---------------------------
    # OUR (Outras Receitas Correntes)
    # ---------------------------
    outras_receitas_item = _prepare_revenue_item_aggregated(
        "Outras Receitas Correntes",
        "outras_receita",
        "conta_detalhada__outras_receita",
        aggregated_data,
                            population,
        nacional_med_outras_receitas_pc,
        is_collapsible=True,
    )

    if outras_receitas_item:
        outras_receitas_item["children"].extend(
            filter(
                None,
                [
                    _prepare_revenue_item_aggregated(
                        "Receita Patrimonial",
                        "receita_patrimonial",
                        "conta_especifica__receita_patrimonial",
                        aggregated_data,
                            population,
                        nacional_med_receita_patrimonial_pc,
                    ),
                    _prepare_revenue_item_aggregated(
                        "Receita Agropecuária",
                        "receita_agropecuaria",
                        "conta_especifica__receita_agropecuaria",
                        aggregated_data,
                            population,
                        nacional_med_receita_agropecuaria_pc,
                    ),
                    _prepare_revenue_item_aggregated(
                        "Receita Industrial",
                        "receita_industrial",
                        "conta_especifica__receita_industrial",
                        aggregated_data,
                            population,
                        nacional_med_receita_industrial_pc,
                    ),
                    _prepare_revenue_item_aggregated(
                        "Receita de Serviços",
                        "receita_servicos",
                        "conta_especifica__receita_servicos",
                        aggregated_data,
                            population,
                        nacional_med_receita_servicos_pc,
                    ),
                    _prepare_revenue_item_aggregated(
                        "Outras Receitas",
                        "outras_receitas",
                        "conta_especifica__outras_receitas",
                        aggregated_data,
                            population,
                        nacional_med_outras_receitas_outras_pc,
                    ),
                ],
            )
        )
        revenue_tree.append(outras_receitas_item)

    # Renderiza o template parcial e retorna como JSON
    rendered_html = render_to_string('detail_agg/partials/_fiscal_details.html', {'revenue_tree': revenue_tree, 'level': 0})
    
    return JsonResponse({
        'html': rendered_html,
        'hist_data': {
            'pop24': population,
            'pop00': pop00,
            'rc24': rc24,
            'rc00': rc00,
            'rc24_pc': rc_24_pc_agregado,
            'rc00_pc': rc_00_pc_agregado,
            'delta_rc_pc': delta_rc_pc,
            'delta_pop': delta_pop,
            'percentil24': percentil24_dyn,
            'percentil00': percentil00_dyn,
            'media_nacional_rc_pc': 316.74,
            'media_nacional_pop': 16.04,
        }
    })


def conjunto_chart_api(request):
    queryset, filtros_ativos = _get_filtered_municipios(request)

    # --- agregações (copiado da sua view existente) ---
    aggregated_data = queryset.aggregate(
        # Nível Detalhado
        total_imposto_taxas_contribuicoes=Coalesce(Sum('conta_detalhada__imposto_taxas_contribuicoes'), Value(0.0)),
        total_contribuicoes=Coalesce(Sum('conta_detalhada__contribuicoes'), Value(0.0)),
        total_transferencias_correntes=Coalesce(Sum('conta_detalhada__transferencias_correntes'), Value(0.0)),
        total_outras_receita=Coalesce(Sum('conta_detalhada__outras_receita'), Value(0.0)),

        # Nível Específico
        total_imposto=Coalesce(Sum('conta_especifica__imposto'), Value(0.0)),
        total_taxas=Coalesce(Sum('conta_especifica__taxas'), Value(0.0)),
        total_contribuicoes_melhoria=Coalesce(Sum('conta_especifica__contribuicoes_melhoria'), Value(0.0)),
        total_contribuicoes_sociais=Coalesce(Sum('conta_especifica__contribuicoes_sociais'), Value(0.0)),
        total_contribuicoes_iluminacao_publica=Coalesce(Sum('conta_especifica__contribuicoes_iluminacao_publica'), Value(0.0)),
        total_outras_contribuicoes=Coalesce(Sum('conta_especifica__outras_contribuicoes'), Value(0.0)),
        total_tranferencias_uniao=Coalesce(Sum('conta_especifica__tranferencias_uniao'), Value(0.0)),
        total_tranferencias_estados=Coalesce(Sum('conta_especifica__tranferencias_estados'), Value(0.0)),
        total_outras_tranferencias=Coalesce(Sum('conta_especifica__outras_tranferencias'), Value(0.0)),
        total_receita_patrimonial=Coalesce(Sum('conta_especifica__receita_patrimonial'), Value(0.0)),
        total_receita_agropecuaria=Coalesce(Sum('conta_especifica__receita_agropecuaria'), Value(0.0)),
        total_receita_industrial=Coalesce(Sum('conta_especifica__receita_industrial'), Value(0.0)),
        total_receita_servicos=Coalesce(Sum('conta_especifica__receita_servicos'), Value(0.0)),
        total_outras_receitas=Coalesce(Sum('conta_especifica__outras_receitas'), Value(0.0)),

        # Nível Mais Específico
        total_iptu=Coalesce(Sum('conta_mais_especifica__iptu'), Value(0.0)),
        total_itbi=Coalesce(Sum('conta_mais_especifica__itbi'), Value(0.0)),
        total_iss=Coalesce(Sum('conta_mais_especifica__iss'), Value(0.0)),
        total_imposto_renda=Coalesce(Sum('conta_mais_especifica__imposto_renda'), Value(0.0)),
        total_outros_impostos=Coalesce(Sum('conta_mais_especifica__outros_impostos'), Value(0.0)),
        total_imposto_icms=Coalesce(Sum('conta_mais_especifica__imposto_icms'), Value(0.0)),
        total_imposto_ipva=Coalesce(Sum('conta_mais_especifica__imposto_ipva'), Value(0.0)),
        
        total_taxa_policia=Coalesce(Sum('conta_mais_especifica__taxa_policia'), Value(0.0)),
        total_taxa_prestacao_servico=Coalesce(Sum('conta_mais_especifica__taxa_prestacao_servico'), Value(0.0)),
        total_outras_taxas=Coalesce(Sum('conta_mais_especifica__outras_taxas'), Value(0.0)),
        total_contribuicao_melhoria_pavimento_obras=Coalesce(Sum('conta_mais_especifica__contribuicao_melhoria_pavimento_obras'), Value(0.0)),
        total_contribuicao_melhoria_agua_potavel=Coalesce(Sum('conta_mais_especifica__contribuicao_melhoria_agua_potavel'), Value(0.0)),
        total_contribuicao_melhoria_iluminacao_publica=Coalesce(Sum('conta_mais_especifica__contribuicao_melhoria_iluminacao_publica'), Value(0.0)),
        total_outras_contribuicoes_melhoria=Coalesce(Sum('conta_mais_especifica__outras_contribuicoes_melhoria'), Value(0.0)),
        total_transferencia_uniao_fpm=Coalesce(Sum('conta_mais_especifica__transferencia_uniao_fpm'), Value(0.0)),
        total_transferencia_uniao_exploracao=Coalesce(Sum('conta_mais_especifica__transferencia_uniao_exploracao'), Value(0.0)),
        total_transferencia_uniao_sus=Coalesce(Sum('conta_mais_especifica__transferencia_uniao_sus'), Value(0.0)),
        total_transferencia_uniao_fnde=Coalesce(Sum('conta_mais_especifica__transferencia_uniao_fnde'), Value(0.0)),
        total_transferencia_uniao_fundeb=Coalesce(Sum('conta_mais_especifica__transferencia_uniao_fundeb'), Value(0.0)),
        total_transferencia_uniao_fnas=Coalesce(Sum('conta_mais_especifica__transferencia_uniao_fnas'), Value(0.0)),
        total_outras_transferencias_uniao=Coalesce(Sum('conta_mais_especifica__outras_transferencias_uniao'), Value(0.0)),
        total_transferencia_estado_icms=Coalesce(Sum('conta_mais_especifica__transferencia_estado_icms'), Value(0.0)),
        total_transferencia_estado_ipva=Coalesce(Sum('conta_mais_especifica__transferencia_estado_ipva'), Value(0.0)),
        total_transferencia_estado_exploracao=Coalesce(Sum('conta_mais_especifica__transferencia_estado_exploracao'), Value(0.0)),
        total_transferencia_estado_sus=Coalesce(Sum('conta_mais_especifica__transferencia_estado_sus'), Value(0.0)),
        total_transferencia_estado_assistencia=Coalesce(Sum('conta_mais_especifica__transferencia_estado_assistencia'), Value(0.0)),
        total_outras_transferencias_estado=Coalesce(Sum('conta_mais_especifica__outras_transferencias_estado'), Value(0.0)),
    )

    def v(key):
        return aggregated_data.get(key) or 0

    chart_data = {
        "main_categories": {
            "labels": ["Impostos, Taxas e Contribuições", "Contribuições", "Transf. Correntes", "Outras"],
            "values": [
                v('total_imposto_taxas_contribuicoes'),
                v('total_contribuicoes'),
                v('total_transferencias_correntes'),
                v('total_outras_receita'),
            ],
        },
        "imposto_taxas_contribuicoes": {
            "labels": ["Impostos", "Taxas", "Contribuições de Melhoria"], 
            "values": [
                v('total_imposto'),
                v('total_taxas'),
                v('total_contribuicoes_melhoria'),
            ],
        },
        "imposto": {
            "labels": ["IPTU", "ITBI", "ISS", "Imposto de Renda", "Outros"],
            "values": [
                v('total_iptu'),
                v('total_itbi'),
                v('total_iss'),
                v('total_imposto_renda'),
                v('total_outros_impostos') + v('total_imposto_icms') + v('total_imposto_ipva'),
            ],
        },
        "taxas": {
            "labels": ["Poder de Polícia", "Prestação de Serviços", "Outras"],
            "values": [
                v('total_taxa_policia'),
                v('total_taxa_prestacao_servico'),
                v('total_outras_taxas'),
                ],
        },
        "contribuicoes_melhoria": {
            "labels": [ "Pavimentação", "Água/Esgoto", "Iluminação", "Outras"],
            "values": [ v('total_contribuicao_melhoria_pavimento_obras'),
                        v('total_contribuicao_melhoria_agua_potavel'),
                        v('total_contribuicao_melhoria_iluminacao_publica'),
                        v('total_outras_contribuicoes_melhoria'),
                     ],
        },
        "contribuicoes": {
            "labels": ["Sociais", "Iluminação Pública", "Outras"],
            "values": [v('total_contribuicoes'),
                       v('total_contribuicoes_iluminacao_publica'),
                       v('total_outras_contribuicoes')],  # se quiser só sociais, troque para v('total_contribuicoes_sociais')
        },
        "transferencias_correntes": {
            "labels": ["União", "Estados", "Outras"],
            "values": [
                v('total_tranferencias_uniao'),    # nota: no modelo está "tranferencias"
                v('total_tranferencias_estados'),
                v('total_outras_tranferencias'),
            ],
        },
        "transferencias_uniao": {
            "labels": ["FPM", "Rec. Naturais", "SUS", "FNDE", "FUNDEB", "FNAS", "Outras"],
            "values": [
                v('total_transferencia_uniao_fpm'),
                v('total_transferencia_uniao_exploracao'),
                v('total_transferencia_uniao_sus'),
                v('total_transferencia_uniao_fnde'),
                v('total_transferencia_uniao_fundeb'),
                v('total_transferencia_uniao_fnas'),
                v('total_outras_transferencias_uniao'),
            ],
        },
        "transferencias_estado": {
            "labels": ["ICMS", "IPVA", "Rec. Naturais", "SUS", "Assistência", "Outras"],
            "values": [
                v('total_transferencia_estado_icms'),
                v('total_transferencia_estado_ipva'),
                v('total_transferencia_estado_exploracao'),
                v('total_transferencia_estado_sus'),
                v('total_transferencia_estado_assistencia'),
                v('total_outras_transferencias_estado'),
            ],
        },
        "outras_receitas": {
            "labels": ["Patrimonial", "Serviços", "Outras"],
            "values": [
                v('total_receita_patrimonial'),
                v('total_receita_servicos'),
                v('total_outras_receitas'),
            ],
        },
    }

    return JsonResponse(chart_data)


def conjunto_data_api(request):
    queryset, filtros_ativos = _get_filtered_municipios(request)

    # --- Anotação e seleção de valores (a mesma da view `conjunto_detalhe_view`) ---
    qs = (
        queryset.annotate(
            main_categories=F('rc_24_pc'),
            imposto_taxas_contribuicoes=F('conta_detalhada__imposto_taxas_contribuicoes')/F('populacao24'),
            imposto = F('conta_especifica__imposto')/F('populacao24'),
            iptu = F('conta_mais_especifica__iptu')/F('populacao24'),
            itbi = F('conta_mais_especifica__itbi')/F('populacao24'),
            iss = F('conta_mais_especifica__iss')/F('populacao24'),
            imposto_renda = F('conta_mais_especifica__imposto_renda')/F('populacao24'),
            outros_impostos = (F('conta_mais_especifica__outros_impostos') +  F('conta_mais_especifica__imposto_icms') + F('conta_mais_especifica__imposto_ipva'))/F('populacao24'),
            taxas = F('conta_especifica__taxas')/F('populacao24'),
            taxa_policia = F('conta_mais_especifica__taxa_policia')/F('populacao24'),
            taxa_prestacao_servico = F('conta_mais_especifica__taxa_prestacao_servico')/F('populacao24'),
            outras_taxas = F('conta_mais_especifica__outras_taxas')/F('populacao24'),
            contribuicoes_melhoria = F('conta_especifica__contribuicoes_melhoria')/F('populacao24'),   
            contribuicao_melhoria_pavimento_obras = F('conta_mais_especifica__contribuicao_melhoria_pavimento_obras')/F('populacao24'),
            contribuicao_melhoria_agua_potavel = F('conta_mais_especifica__contribuicao_melhoria_agua_potavel')/F('populacao24'),
            contribuicao_melhoria_iluminacao_publica = F('conta_mais_especifica__contribuicao_melhoria_iluminacao_publica')/F('populacao24'),
            outras_contribuicoes_melhoria = F('conta_mais_especifica__outras_contribuicoes_melhoria')/F('populacao24'),
            contribuicoes=F('conta_detalhada__contribuicoes')/F('populacao24'),
            contribuicoes_sociais = F('conta_especifica__contribuicoes_sociais')/F('populacao24'),
            contribuicoes_iluminacao_publica = F('conta_especifica__contribuicoes_iluminacao_publica')/F('populacao24'),
            outras_contribuicoes = F('conta_especifica__outras_contribuicoes')/F('populacao24'),
            transferencias_correntes=F('conta_detalhada__transferencias_correntes')/F('populacao24'),
            transferencias_uniao = F('conta_especifica__tranferencias_uniao')/F('populacao24'),
            fpm = F('conta_mais_especifica__transferencia_uniao_fpm')/F('populacao24'),
            transferencia_uniao_exploracao = F('conta_mais_especifica__transferencia_uniao_exploracao')/F('populacao24'),
            transferencia_uniao_sus = F('conta_mais_especifica__transferencia_uniao_sus')/F('populacao24'),
            transferencia_uniao_fnde = F('conta_mais_especifica__transferencia_uniao_fnde')/F('populacao24'),
            transferencia_uniao_fundeb = F('conta_mais_especifica__transferencia_uniao_fundeb')/F('populacao24'),
            transferencia_uniao_fnas = F('conta_mais_especifica__transferencia_uniao_fnas')/F('populacao24'),
            outras_transferencias_uniao = F('conta_mais_especifica__outras_transferencias_uniao')/F('populacao24'),
            transferencias_estado = F('conta_especifica__tranferencias_estados')/F('populacao24'),
            transferencia_estado_icms = F('conta_mais_especifica__transferencia_estado_icms')/F('populacao24'),
            transferencia_estado_ipva = F('conta_mais_especifica__transferencia_estado_ipva')/F('populacao24'),
            transferencia_estado_exploracao = F('conta_mais_especifica__transferencia_estado_exploracao')/F('populacao24'),
            transferencia_estado_sus = F('conta_mais_especifica__transferencia_estado_sus')/F('populacao24'),
            transferencia_estado_assistencia = F('conta_mais_especifica__transferencia_estado_assistencia')/F('populacao24'),
            outras_transferencias_estado = F('conta_mais_especifica__outras_transferencias_estado')/F('populacao24'),
            outras_receitas=F('conta_detalhada__outras_receita')/F('populacao24'),
            receita_patrimonial = F('conta_especifica__receita_patrimonial')/F('populacao24'),
            receita_agropecuaria = F('conta_especifica__receita_agropecuaria')/F('populacao24'),
            receita_industrial = F('conta_especifica__receita_industrial')/F('populacao24'),
            receita_servicos = F('conta_especifica__receita_servicos')/F('populacao24'),
            outras_receitas_outras = F('conta_especifica__outras_receitas')/F('populacao24'),
        )
        .values(
            "cod_ibge",
            "main_categories",
            "imposto_taxas_contribuicoes",
            "imposto",
            "iptu",
            "itbi",
            "iss",
            "imposto_renda",
            "outros_impostos",
            "taxas",
            "taxa_policia",
            "taxa_prestacao_servico",
            "outras_taxas",
            "contribuicoes_melhoria",
            "contribuicao_melhoria_pavimento_obras",
            "contribuicao_melhoria_agua_potavel",
            "contribuicao_melhoria_iluminacao_publica",
            "outras_contribuicoes_melhoria",
            "contribuicoes",
            "contribuicoes_sociais",
            "contribuicoes_iluminacao_publica",
            "outras_contribuicoes",
            "transferencias_correntes",
            "transferencias_uniao",
            "fpm",
            "transferencia_uniao_exploracao",
            "transferencia_uniao_sus",
            "transferencia_uniao_fnde",
            "transferencia_uniao_fundeb",
            "transferencia_uniao_fnas",
            "outras_transferencias_uniao",
            "transferencias_estado",
            "transferencia_estado_icms",
            "transferencia_estado_ipva",
            "transferencia_estado_exploracao",
            "transferencia_estado_sus",
            "transferencia_estado_assistencia",
            "outras_transferencias_estado",
            "outras_receitas",
            "receita_patrimonial",
            "receita_agropecuaria",
            "receita_industrial",
            "receita_servicos",
            "outras_receitas_outras",
        )
        .order_by("cod_ibge")
    )

    data = list(qs)
    return JsonResponse(data, safe=False)
