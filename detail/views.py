import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from home.models import Municipio, RegiaoMetropolitana, ContaDetalhada # Assuming you have your models set up
from django.db.models import Sum, Avg

# Helper function to format a single revenue item (no changes needed here)
def _prepare_revenue_item(name, field_base, model_instance, model_instance_percentile, is_collapsible=False):
    if not model_instance:
        return None
    
    value_abs = getattr(model_instance, field_base, 0)
    value_pc = getattr(model_instance, f"{field_base}_pc", 0)
    
    if value_abs == 0 and value_pc == 0:
        return None

    percentiles = {
        'nacional': getattr(model_instance_percentile, f"{field_base}_nacional", 0),
        'estadual': getattr(model_instance_percentile, f"{field_base}_estadual", 0),
        'faixa': getattr(model_instance_percentile, f"{field_base}_regional", 0),
    }

    item = {
        'name': name, 'field_base': field_base, 'value_abs': value_abs,
        'value_pc': value_pc, 'percentiles': percentiles, 'children': [],
    }

    if is_collapsible:
        item['target_id'] = f'detalhe-{field_base.replace("_", "-")}'

    return item

def municipio_detalhe_view(request, municipio_id):
    municipio = get_object_or_404(Municipio.objects.prefetch_related(
        'conta_detalhada', 'conta_especifica', 'conta_mais_especifica',
        'conta_detalhada_percentil', 'conta_especifica_percentil', 'conta_mais_especifica_percentil'
    ), cod_ibge=municipio_id)

    cd = municipio.conta_detalhada
    cs = municipio.conta_especifica
    cme = municipio.conta_mais_especifica

    cdp= municipio.conta_detalhada_percentil
    csp= municipio.conta_especifica_percentil
    cmep= municipio.conta_mais_especifica_percentil
    
    revenue_tree = []

    # 1. Impostos, Taxas e Contribuições (ITC)
    itc_item = _prepare_revenue_item("Impostos, Taxas e Contribuições de Melhoria", "imposto_taxas_contribuicoes", cd, cdp, is_collapsible=True)
    if itc_item:
        imposto_item = _prepare_revenue_item("Impostos", "imposto", cs, csp, is_collapsible=True)
        if imposto_item:
            imposto_item['children'].extend(filter(None, [
                _prepare_revenue_item("Imposto sobre a Propriedade Predial e Territorial Urbana", "iptu", cme, cmep),
                _prepare_revenue_item("Imposto sobre a Transmissão 'Inter Vivos'", "itbi", cme, cmep),
                _prepare_revenue_item("Imposto sobre Serviços", "iss", cme, cmep),
                _prepare_revenue_item("Outros Impostos", "outros_impostos", cme, cmep),
            ]))
            itc_item['children'].append(imposto_item)

        taxas_item = _prepare_revenue_item("Taxas", "taxas", cs, csp, is_collapsible=True)
        if taxas_item:
            taxas_item['children'].extend(filter(None, [
                _prepare_revenue_item("Taxas pelo Exercício do Poder de Polícia", "taxa_policia", cme, cmep),
                _prepare_revenue_item("Taxas pela Prestação de Serviços", "taxa_prestacao_servico", cme, cmep),
                _prepare_revenue_item("Outras Taxas", "outras_taxas", cme, cmep),
            ]))
            itc_item['children'].append(taxas_item)

        cm_item = _prepare_revenue_item("Contribuições de Melhoria", "contribuicoes_melhoria", cs, csp, is_collapsible=True)
        if cm_item:
            cm_item['children'].extend(filter(None, [
                _prepare_revenue_item("Contribuição de Melhoria para Pavimentação e Obras", "contribuicao_melhoria_pavimento_obras", cme, cmep),
                _prepare_revenue_item("Contribuição de Melhoria para Rede de Água e Esgoto", "contribuicao_melhoria_agua_potavel", cme, cmep),
                _prepare_revenue_item("Contribuição de Melhoria para Iluminação Pública", "contribuicao_melhoria_iluminacao_publica", cme, cmep),
                _prepare_revenue_item("Outras Contribuições de Melhoria", "outras_contribuicoes_melhoria", cme, cmep),
            ]))
            itc_item['children'].append(cm_item)

        revenue_tree.append(itc_item)

    # 2. Contribuições
    contribuicoes_item = _prepare_revenue_item("Contribuições", "contribuicoes", cd, cdp, is_collapsible=True)
    if contribuicoes_item:
        contribuicoes_item['children'].extend(filter(None, [
            _prepare_revenue_item("Contribuições Sociais", "contribuicoes_sociais", cs, csp),
            _prepare_revenue_item("Custeio do Serviço de Iluminação Pública", "contribuicoes_iluminacao_publica", cs, csp),
            _prepare_revenue_item("Outras Contribuições", "outras_contribuicoes", cs, csp),
        ]))
        revenue_tree.append(contribuicoes_item)

    # 3. Transferências Correntes
    transferencias_item = _prepare_revenue_item("Transferências Correntes", "transferencias_correntes", cd, cdp, is_collapsible=True)
    if transferencias_item:
        uniao = _prepare_revenue_item("Transferências da União", "tranferencias_uniao", cs, csp, is_collapsible=True)
        if uniao:
            uniao['children'].extend(filter(None, [
                _prepare_revenue_item("Cota-Parte do FPM", "transferencia_uniao_fpm", cme, cmep),
                _prepare_revenue_item("Compensação Financeira (Recursos Naturais)", "transferencia_uniao_exploracao", cme, cmep),
                _prepare_revenue_item("Recursos do SUS", "transferencia_uniao_sus", cme, cmep),
                _prepare_revenue_item("Recursos do FNDE", "transferencia_uniao_fnde", cme, cmep),
                _prepare_revenue_item("Recursos do FNAS", "transferencia_uniao_fnas", cme, cmep),
                _prepare_revenue_item("Outras Transferências da União", "outras_transferencias_uniao", cme, cmep),
            ]))
            transferencias_item['children'].append(uniao)

        estados = _prepare_revenue_item("Transferências dos Estados", "tranferencias_estados", cs, csp, is_collapsible=True)
        if estados:
            estados['children'].extend(filter(None, [
                _prepare_revenue_item("Cota-Parte do ICMS", "transferencia_estado_icms", cme, cmep),
                _prepare_revenue_item("Cota-Parte do IPVA", "transferencia_estado_ipva", cme, cmep),
                _prepare_revenue_item("Compensação Financeira (Recursos Naturais)", "transferencia_estado_exploracao", cme, cmep),
                _prepare_revenue_item("Recursos do SUS", "transferencia_estado_sus", cme, cmep),
                _prepare_revenue_item("Assistência Social", "transferencia_estado_assistencia", cme, cmep),
                _prepare_revenue_item("Outras Transferências dos Estados", "outras_transferencias_estado", cme, cmep),
            ]))
            transferencias_item['children'].append(estados)

        transferencias_item['children'].append(_prepare_revenue_item("Outras Transferências", "outras_tranferencias", cs, csp))
        revenue_tree.append(transferencias_item)
    
    # 4. Outras Receitas Correntes
    outras_receitas_item = _prepare_revenue_item("Outras Receitas Correntes", "outras_receita", cd, cdp, is_collapsible=True)
    if outras_receitas_item:
        outras_receitas_item['children'].extend(filter(None, [
            _prepare_revenue_item("Receita Patrimonial", "receita_patrimonial", cs, csp),
            _prepare_revenue_item("Receita Agropecuária", "receita_agropecuaria", cs, csp),
            _prepare_revenue_item("Receita Industrial", "receita_industrial", cs, csp),
            _prepare_revenue_item("Receita de Serviços", "receita_servicos", cs, csp),
            _prepare_revenue_item("Outras Receitas", "outras_receitas", cs, csp),
        ]))
        revenue_tree.append(outras_receitas_item)

    # Prepare Chart Data
    def get_chart_series(labels, values):
        series = [(label, value) for label, value in zip(labels, values) if value and value > 0]
        # Se não houver dados, retorna listas vazias para evitar erros no frontend
        if not series:
            return {"labels": [], "values": []}
        # Descompacta a lista de tuplas em duas listas separadas
        unzipped_series = list(zip(*series))
        return {"labels": list(unzipped_series[0]), "values": list(unzipped_series[1])}

    # Prepara os dados do gráfico usando a função auxiliar e os valores PER CAPITA (_pc)
    chart_data = {
        "main_categories": get_chart_series(
            ["ITC", "Contribuições", "Transf. Correntes", "Outras"],
            [cd.imposto_taxas_contribuicoes_pc, cd.contribuicoes_pc, cd.transferencias_correntes_pc, cd.outras_receita_pc]
        ),
        "imposto_taxas_contribuicoes": get_chart_series(
            ["Impostos", "Taxas", "Contrib. Melhoria"],
            [cs.imposto_pc, cs.taxas_pc, cs.contribuicoes_melhoria_pc]
        ),
        "imposto": get_chart_series(
            ["IPTU", "ITBI", "ISS", "Outros"],
            [cme.iptu_pc, cme.itbi_pc, cme.iss_pc, cme.outros_impostos_pc]
        ),
        "taxas": get_chart_series(
            ["Poder de Polícia", "Prestação de Serviços", "Outras"],
            [cme.taxa_policia_pc, cme.taxa_prestacao_servico_pc, cme.outras_taxas_pc]
        ),
        "contribuicoes_melhoria": get_chart_series(
            ["Pavimentação", "Água/Esgoto", "Iluminação", "Outras"],
            [cme.contribuicao_melhoria_pavimento_obras_pc, cme.contribuicao_melhoria_agua_potavel_pc, cme.contribuicao_melhoria_iluminacao_publica_pc, cme.outras_contribuicoes_melhoria_pc]
        ),
        "contribuicoes": get_chart_series(
            ["Sociais", "Iluminação Pública", "Outras"],
            [cs.contribuicoes_sociais_pc, cs.contribuicoes_iluminacao_publica_pc, cs.outras_contribuicoes_pc]
        ),
        "transferencias_correntes": get_chart_series(
            ["União", "Estados", "Outras"],
            [cs.tranferencias_uniao_pc, cs.tranferencias_estados_pc, cs.outras_tranferencias_pc]
        ),
        "transferencias_uniao": get_chart_series(
            ["FPM", "Rec. Naturais", "SUS", "FNDE", "FNAS", "Outras"],
            [cme.transferencia_uniao_fpm_pc, cme.transferencia_uniao_exploracao_pc, cme.transferencia_uniao_sus_pc, cme.transferencia_uniao_fnde_pc, cme.transferencia_uniao_fnas_pc, cme.outras_transferencias_uniao_pc]
        ),
        "transferencias_estado": get_chart_series(
            ["ICMS", "IPVA", "Rec. Naturais", "SUS", "Assistência", "Outras"],
            [cme.transferencia_estado_icms_pc, cme.transferencia_estado_ipva_pc, cme.transferencia_estado_exploracao_pc, cme.transferencia_estado_sus_pc, cme.transferencia_estado_assistencia_pc, cme.outras_transferencias_estado_pc]
        ),
        "outras_receitas": get_chart_series(
            ["Patrimonial", "Agropecuária", "Industrial", "Serviços", "Outras"],
            [cs.receita_patrimonial_pc, cs.receita_agropecuaria_pc, cs.receita_industrial_pc, cs.receita_servicos_pc, cs.outras_receitas_pc]
        ),
    }

    

    # Prepare Percentile Data for JS
    percentile_data = {}
    
    # Recursively populate percentiles
    def populate_percentiles(items):
        for item in items:
            if item:
                percentile_data[item['field_base']] = item['percentiles']
                if item.get('children'):
                    populate_percentiles(item['children'])
    populate_percentiles(revenue_tree)

    context = {
        'municipio': municipio,
        'revenue_tree': revenue_tree,
        'chart_data_json': json.dumps(chart_data),
        'percentile_data_json': json.dumps(percentile_data),
    }

    
    return render(request, 'detail/detalhe_municipio.html', context)






def municipio_details_api(request):
    queryset = Municipio.objects.all()
    # Recupera os parâmetros de filtro da requisição
    uf_filtro = request.GET.get('uf')
    regiao_filtro = request.GET.get('regiao')
    municipio_filtro = request.GET.get('municipio')
    porte_filtro = request.GET.get('porte')
    rm_filtro = request.GET.get('rm')
    
    # Aplica filtros geográficos e administrativos gerais
    if regiao_filtro and regiao_filtro != 'todos':
        queryset = queryset.filter(regiao=regiao_filtro)

    if uf_filtro and uf_filtro != 'todos':
        queryset = queryset.filter(uf=uf_filtro)

    if municipio_filtro and municipio_filtro != 'todos':
        queryset = queryset.filter(name_muni_uf=municipio_filtro)

    if rm_filtro and rm_filtro != 'todos':
        queryset = queryset.filter(rm__nome=rm_filtro)

    # Aplica filtro de porte populacional
    if porte_filtro and porte_filtro != 'todos':
        if porte_filtro == 'Até 5 mil':
            queryset = queryset.filter(populacao23__lt=5000)
        elif porte_filtro == '5 mil a 10 mil':
            queryset = queryset.filter(populacao23__gte=5000, populacao23__lt=10000)
        elif porte_filtro == '10 mil a 20 mil':
            queryset = queryset.filter(populacao23__gte=10000, populacao23__lt=20000)
        elif porte_filtro == '20 mil a 50 mil':
            queryset = queryset.filter(populacao23__gte=20000, populacao23__lt=50000)
        elif porte_filtro == '50 mil a 100 mil':
            queryset = queryset.filter(populacao23__gte=50000, populacao23__lt=100000)
        elif porte_filtro == '100 mil a 200 mil':
            queryset = queryset.filter(populacao23__gte=100000, populacao23__lt=200000)
        elif porte_filtro == '200 mil a 500 mil':
            queryset = queryset.filter(populacao23__gte=200000, populacao23__lt=500000)
        elif porte_filtro == 'Acima de 500 mil':
            queryset = queryset.filter(populacao23__gte=500000)
    
    national_avg_rc = Municipio.objects.aggregate(avg_rc=Avg('rc_23_pc'))['avg_rc'] or 0

    # Aggregate data from the filtered queryset
    aggregated_data = queryset.aggregate(
        total_populacao=Sum('populacao23'),
        total_receita_corrente=Sum('rc_2023'),
        avg_receita_per_capita=Avg('rc_23_pc'),
    )

    # Get the count of municipalities in the filtered queryset
    quantidade_municipios = queryset.count()
    
    # Format the data for the JSON response
    response_data = {
        "kpis": {
            "populacao": aggregated_data['total_populacao'],
            "quantidade": quantidade_municipios,
            "receita_corrente": aggregated_data['total_receita_corrente'],
            "receita_per_capita": aggregated_data['avg_receita_per_capita'],
            "diferenca_media": ((aggregated_data['avg_receita_per_capita'] or 0) - national_avg_rc) / national_avg_rc  if national_avg_rc != 0 else 0,
        }
    }
    
    # Adicione a agregação das receitas fiscais por categoria
    fiscal_aggregation = queryset.aggregate(
        # Nível Detalhado
        total_imposto_taxas_contribuicoes=Sum('conta_detalhada__imposto_taxas_contribuicoes'),
        total_contribuicoes=Sum('conta_detalhada__contribuicoes'),
        total_transferencias_correntes=Sum('conta_detalhada__transferencias_correntes'),
        total_outras_receita=Sum('conta_detalhada__outras_receita'),

        # Nível Específico
        total_imposto=Sum('conta_especifica__imposto'),
        total_taxas=Sum('conta_especifica__taxas'),
        total_contribuicoes_melhoria=Sum('conta_especifica__contribuicoes_melhoria'),
        total_contribuicoes_sociais=Sum('conta_especifica__contribuicoes_sociais'),
        total_contribuicoes_iluminacao_publica=Sum('conta_especifica__contribuicoes_iluminacao_publica'),
        total_outras_contribuicoes=Sum('conta_especifica__outras_contribuicoes'),
        total_tranferencias_uniao=Sum('conta_especifica__tranferencias_uniao'),
        total_tranferencias_estados=Sum('conta_especifica__tranferencias_estados'),
        total_outras_tranferencias=Sum('conta_especifica__outras_tranferencias'),
        total_receita_patrimonial=Sum('conta_especifica__receita_patrimonial'),
        total_receita_agropecuaria=Sum('conta_especifica__receita_agropecuaria'),
        total_receita_industrial=Sum('conta_especifica__receita_industrial'),
        total_receita_servicos=Sum('conta_especifica__receita_servicos'),
        total_outras_receitas=Sum('conta_especifica__outras_receitas'),

        # Nível Mais Específico
        total_iptu=Sum('conta_mais_especifica__iptu'),
        total_itbi=Sum('conta_mais_especifica__itbi'),
        total_iss=Sum('conta_mais_especifica__iss'),
        total_outros_impostos=Sum('conta_mais_especifica__outros_impostos'),
        total_taxa_policia=Sum('conta_mais_especifica__taxa_policia'),
        total_taxa_prestacao_servico=Sum('conta_mais_especifica__taxa_prestacao_servico'),
        total_outras_taxas=Sum('conta_mais_especifica__outras_taxas'),
        total_contribuicao_melhoria_pavimento_obras=Sum('conta_mais_especifica__contribuicao_melhoria_pavimento_obras'),
        total_contribuicao_melhoria_agua_potavel=Sum('conta_mais_especifica__contribuicao_melhoria_agua_potavel'),
        total_contribuicao_melhoria_iluminacao_publica=Sum('conta_mais_especifica__contribuicao_melhoria_iluminacao_publica'),
        total_outras_contribuicoes_melhoria=Sum('conta_mais_especifica__outras_contribuicoes_melhoria'),
        total_transferencia_uniao_fpm=Sum('conta_mais_especifica__transferencia_uniao_fpm'),
        total_transferencia_uniao_exploracao=Sum('conta_mais_especifica__transferencia_uniao_exploracao'),
        total_transferencia_uniao_sus=Sum('conta_mais_especifica__transferencia_uniao_sus'),
        total_transferencia_uniao_fnde=Sum('conta_mais_especifica__transferencia_uniao_fnde'),
        total_transferencia_uniao_fnas=Sum('conta_mais_especifica__transferencia_uniao_fnas'),
        total_outras_transferencias_uniao=Sum('conta_mais_especifica__outras_transferencias_uniao'),
        total_transferencia_estado_icms=Sum('conta_mais_especifica__transferencia_estado_icms'),
        total_transferencia_estado_ipva=Sum('conta_mais_especifica__transferencia_estado_ipva'),
        total_transferencia_estado_exploracao=Sum('conta_mais_especifica__transferencia_estado_exploracao'),
        total_transferencia_estado_sus=Sum('conta_mais_especifica__transferencia_estado_sus'),
        total_transferencia_estado_assistencia=Sum('conta_mais_especifica__transferencia_estado_assistencia'),
        total_outras_transferencias_estado=Sum('conta_mais_especifica__outras_transferencias_estado'),
    )

    # Incluir os dados agregados na resposta final
    response_data['fiscal_aggregation'] = fiscal_aggregation
    
    return JsonResponse(response_data)




def _prepare_revenue_item_aggregated(name, field_base, aggregated_data,population,value_pc_nac, is_collapsible=False):
    value_abs = aggregated_data.get(f'total_{field_base}', 0)
    
    if population == 0:
        value_pc = 0
    else:
        value_pc = (value_abs / population)

    if value_abs == 0 and value_pc == 0:
        return None
    
    diff = {
    'pc': round(((value_pc - value_pc_nac) / value_pc_nac * 100), 2) if value_pc_nac != 0 else 0,
    }



    item = {
        'name': name,
        'field_base': field_base,
        'value_abs': value_abs,
        'value_pc': value_pc,
        'diff': diff,
        'children': [],
    }

    if is_collapsible:
        item['target_id'] = f'detalhe-{field_base.replace("_", "-")}'

    return item

def conjunto_detalhe_view(request):
    queryset = Municipio.objects.all()

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
            queryset = queryset.filter(populacao23__lt=5000)
        elif porte_filtro == '5 mil a 10 mil':
            queryset = queryset.filter(populacao23__gte=5000, populacao23__lt=10000)
        elif porte_filtro == '10 mil a 20 mil':
            queryset = queryset.filter(populacao23__gte=10000, populacao23__lt=20000)
        elif porte_filtro == '20 mil a 50 mil':
            queryset = queryset.filter(populacao23__gte=20000, populacao23__lt=50000)
        elif porte_filtro == '50 mil a 100 mil':
            queryset = queryset.filter(populacao23__gte=50000, populacao23__lt=100000)
        elif porte_filtro == '100 mil a 200 mil':
            queryset = queryset.filter(populacao23__gte=100000, populacao23__lt=200000)
        elif porte_filtro == '200 mil a 500 mil':
            queryset = queryset.filter(populacao23__gte=200000, populacao23__lt=500000)
        elif porte_filtro == 'Acima de 500 mil':
            queryset = queryset.filter(populacao23__gte=500000)

    if subgroup_filter and subgroup_filter != "todos":
        if classification_filter == 'quintil':
            queryset = queryset.filter(quintil23=subgroup_filter)
        elif classification_filter == 'decil':
            queryset = queryset.filter(decil23=subgroup_filter)

    # --- agregações ---
    aggregated_data = queryset.aggregate(
        total_receita_corrente=Sum('rc_2023'),

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
        total_outros_impostos=Sum('conta_mais_especifica__outros_impostos'),

        total_taxa_policia=Sum('conta_mais_especifica__taxa_policia'),
        total_taxa_prestacao_servico=Sum('conta_mais_especifica__taxa_prestacao_servico'),
        total_outras_taxas=Sum('conta_mais_especifica__outras_taxas'),

        total_contribuicao_melhoria_pavimento_obras=Sum('conta_mais_especifica__contribuicao_melhoria_pavimento_obras'),
        total_contribuicao_melhoria_agua_potavel=Sum('conta_mais_especifica__contribuicao_melhoria_agua_potavel'),
        total_contribuicao_melhoria_iluminacao_publica=Sum('conta_mais_especifica__contribuicao_melhoria_iluminacao_publica'),
        total_outras_contribuicoes_melhoria=Sum('conta_mais_especifica__outras_contribuicoes_melhoria'),

        total_transferencia_uniao_fpm=Sum('conta_mais_especifica__transferencia_uniao_fpm'),
        total_transferencia_uniao_exploracao=Sum('conta_mais_especifica__transferencia_uniao_exploracao'),
        total_transferencia_uniao_sus=Sum('conta_mais_especifica__transferencia_uniao_sus'),
        total_transferencia_uniao_fnde=Sum('conta_mais_especifica__transferencia_uniao_fnde'),
        total_transferencia_uniao_fnas=Sum('conta_mais_especifica__transferencia_uniao_fnas'),
        total_outras_transferencias_uniao=Sum('conta_mais_especifica__outras_transferencias_uniao'),

        total_transferencia_estado_icms=Sum('conta_mais_especifica__transferencia_estado_icms'),
        total_transferencia_estado_ipva=Sum('conta_mais_especifica__transferencia_estado_ipva'),
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
    population = queryset.aggregate(total_populacao=Sum('populacao23'))['total_populacao'] or 0

    itc_item = _prepare_revenue_item_aggregated(
        "Impostos, Taxas e Contribuições de Melhoria", "imposto_taxas_contribuicoes",
        aggregated_data, population, 1298.32, is_collapsible=True
    )
    if itc_item:
        imposto_item = _prepare_revenue_item_aggregated("Impostos", "imposto", aggregated_data, population, 1210.52, is_collapsible=True)
        if imposto_item:
            imposto_item['children'].extend(filter(None, [
                _prepare_revenue_item_aggregated("Imposto sobre a Propriedade Predial e Territorial Urbana", "iptu", aggregated_data, population, 340.51),
                _prepare_revenue_item_aggregated("Imposto sobre a Transmissão 'Inter Vivos'", "itbi", aggregated_data, population, 100.19),
                _prepare_revenue_item_aggregated("Imposto sobre Serviços", "iss", aggregated_data, population, 572.00),
                _prepare_revenue_item_aggregated("Outros Impostos", "outros_impostos", aggregated_data, population, 197.82),
            ]))
            itc_item['children'].append(imposto_item)

        taxas_item = _prepare_revenue_item_aggregated("Taxas", "taxas", aggregated_data, population, 85.67, is_collapsible=True)
        if taxas_item:
            taxas_item['children'].extend(filter(None, [
                _prepare_revenue_item_aggregated("Taxas pelo Exercício do Poder de Polícia", "taxa_policia", aggregated_data, population, 33.58),
                _prepare_revenue_item_aggregated("Taxas pela Prestação de Serviços", "taxa_prestacao_servico", aggregated_data, population, 52.09),
                _prepare_revenue_item_aggregated("Outras Taxas", "outras_taxas", aggregated_data, population, 0.000001),
            ]))
            itc_item['children'].append(taxas_item)

        cm_item = _prepare_revenue_item_aggregated("Contribuições de Melhoria", "contribuicoes_melhoria", aggregated_data, population, 2.13, is_collapsible=True)
        if cm_item:
            cm_item['children'].extend(filter(None, [
                _prepare_revenue_item_aggregated("Contribuição de Melhoria para Pavimentação e Obras", "contribuicao_melhoria_pavimento_obras", aggregated_data, population, 0.45),
                _prepare_revenue_item_aggregated("Contribuição de Melhoria para Rede de Água e Esgoto", "contribuicao_melhoria_agua_potavel", aggregated_data, population, 0.13),
                _prepare_revenue_item_aggregated("Contribuição de Melhoria para Iluminação Pública", "contribuicao_melhoria_iluminacao_publica", aggregated_data, population, 1.31),
                _prepare_revenue_item_aggregated("Outras Contribuições de Melhoria", "outras_contribuicoes_melhoria", aggregated_data, population, 0.24),
            ]))
            itc_item['children'].append(cm_item)
        revenue_tree.append(itc_item)

    contribuicoes_item = _prepare_revenue_item_aggregated("Contribuições", "contribuicoes", aggregated_data, population, 197.42,  is_collapsible=True)
    if contribuicoes_item:
        contribuicoes_item['children'].extend(filter(None, [
            _prepare_revenue_item_aggregated("Contribuições Sociais", "contribuicoes_sociais", aggregated_data, population, 128.34),
            _prepare_revenue_item_aggregated("Custeio do Serviço de Iluminação Pública", "contribuicoes_iluminacao_publica", aggregated_data, population, 68.48),
            _prepare_revenue_item_aggregated("Outras Contribuições", "outras_contribuicoes", aggregated_data, population, 0.43),
        ]))
        revenue_tree.append(contribuicoes_item)

    transferencias_item = _prepare_revenue_item_aggregated("Transferências Correntes", "transferencias_correntes", aggregated_data, population, 3607.45, is_collapsible=True)
    if transferencias_item:
        uniao = _prepare_revenue_item_aggregated("Transferências da União", "tranferencias_uniao", aggregated_data, population, 1776.02, is_collapsible=True)
        if uniao:
            uniao['children'].extend(filter(None, [
                _prepare_revenue_item_aggregated("Cota-Parte do FPM", "transferencia_uniao_fpm", aggregated_data, population, 876.52),
                _prepare_revenue_item_aggregated("Compensação Financeira (Recursos Naturais)", "transferencia_uniao_exploracao", aggregated_data, population, 149.14),
                _prepare_revenue_item_aggregated("Recursos do SUS", "transferencia_uniao_sus", aggregated_data, population, 422.75),
                _prepare_revenue_item_aggregated("Recursos do FNDE", "transferencia_uniao_fnde", aggregated_data, population, 75.33),
                _prepare_revenue_item_aggregated("Recursos do FNAS", "transferencia_uniao_fnas", aggregated_data, population, 20.25),
                _prepare_revenue_item_aggregated("Outras Transferências da União", "outras_transferencias_uniao", aggregated_data, population, 231.81),
            ]))
            transferencias_item['children'].append(uniao)

        estados = _prepare_revenue_item_aggregated("Transferências dos Estados", "tranferencias_estados", aggregated_data, population, 1167.63, is_collapsible=True)
        if estados:
            estados['children'].extend(filter(None, [
                _prepare_revenue_item_aggregated("Cota-Parte do ICMS", "transferencia_estado_icms", aggregated_data, population, 823.67),
                _prepare_revenue_item_aggregated("Cota-Parte do IPVA", "transferencia_estado_ipva", aggregated_data, population, 192.21),
                _prepare_revenue_item_aggregated("Compensação Financeira (Recursos Naturais)", "transferencia_estado_exploracao", aggregated_data, population,11.68),
                _prepare_revenue_item_aggregated("Recursos do SUS", "transferencia_estado_sus", aggregated_data, population, 61.46),
                _prepare_revenue_item_aggregated("Assistência Social", "transferencia_estado_assistencia", aggregated_data, population, 4.09),
                _prepare_revenue_item_aggregated("Outras Transferências dos Estados", "outras_transferencias_estado", aggregated_data, population, 74.49),
            ]))
            transferencias_item['children'].append(estados)

        transferencias_item['children'].append(
            _prepare_revenue_item_aggregated("Outras Transferências", "outras_tranferencias", aggregated_data, population, 663.77)
        )
        revenue_tree.append(transferencias_item)

    outras_receitas_item = _prepare_revenue_item_aggregated("Outras Receitas Correntes", "outras_receita", aggregated_data, population, 437.74, is_collapsible=True)
    if outras_receitas_item:
        outras_receitas_item['children'].extend(filter(None, [
            _prepare_revenue_item_aggregated("Receita Patrimonial", "receita_patrimonial", aggregated_data, population, 249.68),
            _prepare_revenue_item_aggregated("Receita Agropecuária", "receita_agropecuaria", aggregated_data, population, 0.07),
            _prepare_revenue_item_aggregated("Receita Industrial", "receita_industrial", aggregated_data, population, 0.06),
            _prepare_revenue_item_aggregated("Receita de Serviços", "receita_servicos", aggregated_data, population, 79.29),
            _prepare_revenue_item_aggregated("Outras Receitas", "outras_receitas", aggregated_data, population, 108.52),
        ]))
        revenue_tree.append(outras_receitas_item)

    # ------- CHART DATA EXACTO (valores absolutos) -------
    chart_data = {
        "main_categories": {
            "labels": ["ITC", "Contribuições", "Transf. Correntes", "Outras"],
            "values": [
                v('total_imposto_taxas_contribuicoes'),
                v('total_contribuicoes'),
                v('total_transferencias_correntes'),
                v('total_outras_receita'),
            ],
        },
        "imposto_taxas_contribuicoes": {
            "labels": ["Impostos", "Taxas"],
            "values": [
                v('total_imposto'),
                v('total_taxas'),
            ],
        },
        "imposto": {
            "labels": ["IPTU", "ITBI", "ISS", "Outros"],
            "values": [
                v('total_iptu'),
                v('total_itbi'),
                v('total_iss'),
                v('total_outros_impostos'),
            ],
        },
        "taxas": {
            "labels": ["Poder de Polícia"],
            "values": [v('total_taxa_policia')],
        },
        "contribuicoes_melhoria": {
            "labels": [],
            "values": [],
        },
        "contribuicoes": {
            "labels": ["Sociais"],
            "values": [v('total_contribuicoes')],  # se quiser só sociais, troque para v('total_contribuicoes_sociais')
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
            "labels": ["FPM", "Rec. Naturais", "SUS", "FNDE", "FNAS", "Outras"],
            "values": [
                v('total_transferencia_uniao_fpm'),
                v('total_transferencia_uniao_exploracao'),
                v('total_transferencia_uniao_sus'),
                v('total_transferencia_uniao_fnde'),
                v('total_transferencia_uniao_fnas'),
                v('total_outras_transferencias_uniao'),
            ],
        },
        "transferencias_estado": {
            "labels": ["ICMS", "IPVA", "Outras"],
            "values": [
                v('total_transferencia_estado_icms'),
                v('total_transferencia_estado_ipva'),
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

    context = {
        'revenue_tree': revenue_tree,
        # passe o dict direto; no template use {{ chart_data_json|json_script:"chart-data" }}
        'chart_data_json': chart_data,
    }

    print(revenue_tree)
    return render(request, 'detail/detalhe_conjunto.html', context)




def conjunto_fiscal_api(request):
    queryset = Municipio.objects.all()

    uf_filtro = request.GET.get('uf')
    regiao_filtro = request.GET.get('regiao')
    municipio_filtro = request.GET.get('municipio')
    porte_filtro = request.GET.get('porte')
    rm_filtro = request.GET.get('rm')

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
            queryset = queryset.filter(populacao23__lt=5000)
        elif porte_filtro == '5 mil a 10 mil':
            queryset = queryset.filter(populacao23__gte=5000, populacao23__lt=10000)
        elif porte_filtro == '10 mil a 20 mil':
            queryset = queryset.filter(populacao23__gte=10000, populacao23__lt=20000)
        elif porte_filtro == '20 mil a 50 mil':
            queryset = queryset.filter(populacao23__gte=20000, populacao23__lt=50000)
        elif porte_filtro == '50 mil a 100 mil':
            queryset = queryset.filter(populacao23__gte=50000, populacao23__lt=100000)
        elif porte_filtro == '100 mil a 200 mil':
            queryset = queryset.filter(populacao23__gte=100000, populacao23__lt=200000)
        elif porte_filtro == '200 mil a 500 mil':
            queryset = queryset.filter(populacao23__gte=200000, populacao23__lt=500000)
        elif porte_filtro == 'Acima de 500 mil':
            queryset = queryset.filter(populacao23__gte=500000)

    # Perform the aggregation
    aggregated_data = queryset.aggregate(
        total_receita_corrente=Sum('rc_2023'),
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
        total_tranferencias_uniao=Sum('conta_especifica__tranferencias_uniao'),
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
        total_outros_impostos=Sum('conta_mais_especifica__outros_impostos'),
        total_taxa_policia=Sum('conta_mais_especifica__taxa_policia'),
        total_taxa_prestacao_servico=Sum('conta_mais_especifica__taxa_prestacao_servico'),
        total_outras_taxas=Sum('conta_mais_especifica__outras_taxas'),
        total_contribuicao_melhoria_pavimento_obras=Sum('conta_mais_especifica__contribuicao_melhoria_pavimento_obras'),
        total_contribuicao_melhoria_agua_potavel=Sum('conta_mais_especifica__contribuicao_melhoria_agua_potavel'),
        total_contribuicao_melhoria_iluminacao_publica=Sum('conta_mais_especifica__contribuicao_melhoria_iluminacao_publica'),
        total_outras_contribuicoes_melhoria=Sum('conta_mais_especifica__outras_contribuicoes_melhoria'),
        total_transferencia_uniao_fpm=Sum('conta_mais_especifica__transferencia_uniao_fpm'),
        total_transferencia_uniao_exploracao=Sum('conta_mais_especifica__transferencia_uniao_exploracao'),
        total_transferencia_uniao_sus=Sum('conta_mais_especifica__transferencia_uniao_sus'),
        total_transferencia_uniao_fnde=Sum('conta_mais_especifica__transferencia_uniao_fnde'),
        total_transferencia_uniao_fnas=Sum('conta_mais_especifica__transferencia_uniao_fnas'),
        total_outras_transferencias_uniao=Sum('conta_mais_especifica__outras_transferencias_uniao'),
        total_transferencia_estado_icms=Sum('conta_mais_especifica__transferencia_estado_icms'),
        total_transferencia_estado_ipva=Sum('conta_mais_especifica__transferencia_estado_ipva'),
        total_transferencia_estado_exploracao=Sum('conta_mais_especifica__transferencia_estado_exploracao'),
        total_transferencia_estado_sus=Sum('conta_mais_especifica__transferencia_estado_sus'),
        total_transferencia_estado_assistencia=Sum('conta_mais_especifica__transferencia_estado_assistencia'),
        total_outras_transferencias_estado=Sum('conta_mais_especifica__outras_transferencias_estado'),
    )

    population = queryset.aggregate(total_populacao=Sum('populacao23'))['total_populacao'] or 0


    revenue_tree = []
    # 1. Impostos, Taxas e Contribuições (ITC)
    itc_item = _prepare_revenue_item_aggregated(
        "Impostos, Taxas e Contribuições de Melhoria", "imposto_taxas_contribuicoes",
        aggregated_data, population, 1298.32, is_collapsible=True
    )
    if itc_item:
        imposto_item = _prepare_revenue_item_aggregated("Impostos", "imposto", aggregated_data, population, 1210.52, is_collapsible=True)
        if imposto_item:
            imposto_item['children'].extend(filter(None, [
                _prepare_revenue_item_aggregated("Imposto sobre a Propriedade Predial e Territorial Urbana", "iptu", aggregated_data, population, 340.51),
                _prepare_revenue_item_aggregated("Imposto sobre a Transmissão 'Inter Vivos'", "itbi", aggregated_data, population, 100.19),
                _prepare_revenue_item_aggregated("Imposto sobre Serviços", "iss", aggregated_data, population, 572.00),
                _prepare_revenue_item_aggregated("Outros Impostos", "outros_impostos", aggregated_data, population, 197.82),
            ]))
            itc_item['children'].append(imposto_item)

        taxas_item = _prepare_revenue_item_aggregated("Taxas", "taxas", aggregated_data, population, 85.67, is_collapsible=True)
        if taxas_item:
            taxas_item['children'].extend(filter(None, [
                _prepare_revenue_item_aggregated("Taxas pelo Exercício do Poder de Polícia", "taxa_policia", aggregated_data, population, 33.58),
                _prepare_revenue_item_aggregated("Taxas pela Prestação de Serviços", "taxa_prestacao_servico", aggregated_data, population, 52.09),
                _prepare_revenue_item_aggregated("Outras Taxas", "outras_taxas", aggregated_data, population, 0.000001),
            ]))
            itc_item['children'].append(taxas_item)

        cm_item = _prepare_revenue_item_aggregated("Contribuições de Melhoria", "contribuicoes_melhoria", aggregated_data, population, 2.13, is_collapsible=True)
        if cm_item:
            cm_item['children'].extend(filter(None, [
                _prepare_revenue_item_aggregated("Contribuição de Melhoria para Pavimentação e Obras", "contribuicao_melhoria_pavimento_obras", aggregated_data, population, 0.45),
                _prepare_revenue_item_aggregated("Contribuição de Melhoria para Rede de Água e Esgoto", "contribuicao_melhoria_agua_potavel", aggregated_data, population, 0.13),
                _prepare_revenue_item_aggregated("Contribuição de Melhoria para Iluminação Pública", "contribuicao_melhoria_iluminacao_publica", aggregated_data, population, 1.31),
                _prepare_revenue_item_aggregated("Outras Contribuições de Melhoria", "outras_contribuicoes_melhoria", aggregated_data, population, 0.24),
            ]))
            itc_item['children'].append(cm_item)
        revenue_tree.append(itc_item)

    contribuicoes_item = _prepare_revenue_item_aggregated("Contribuições", "contribuicoes", aggregated_data, population, 197.42,  is_collapsible=True)
    if contribuicoes_item:
        contribuicoes_item['children'].extend(filter(None, [
            _prepare_revenue_item_aggregated("Contribuições Sociais", "contribuicoes_sociais", aggregated_data, population, 128.34),
            _prepare_revenue_item_aggregated("Custeio do Serviço de Iluminação Pública", "contribuicoes_iluminacao_publica", aggregated_data, population, 68.48),
            _prepare_revenue_item_aggregated("Outras Contribuições", "outras_contribuicoes", aggregated_data, population, 0.43),
        ]))
        revenue_tree.append(contribuicoes_item)

    transferencias_item = _prepare_revenue_item_aggregated("Transferências Correntes", "transferencias_correntes", aggregated_data, population, 3607.45, is_collapsible=True)
    if transferencias_item:
        uniao = _prepare_revenue_item_aggregated("Transferências da União", "tranferencias_uniao", aggregated_data, population, 1776.02, is_collapsible=True)
        if uniao:
            uniao['children'].extend(filter(None, [
                _prepare_revenue_item_aggregated("Cota-Parte do FPM", "transferencia_uniao_fpm", aggregated_data, population, 876.52),
                _prepare_revenue_item_aggregated("Compensação Financeira (Recursos Naturais)", "transferencia_uniao_exploracao", aggregated_data, population, 149.14),
                _prepare_revenue_item_aggregated("Recursos do SUS", "transferencia_uniao_sus", aggregated_data, population, 422.75),
                _prepare_revenue_item_aggregated("Recursos do FNDE", "transferencia_uniao_fnde", aggregated_data, population, 75.33),
                _prepare_revenue_item_aggregated("Recursos do FNAS", "transferencia_uniao_fnas", aggregated_data, population, 20.25),
                _prepare_revenue_item_aggregated("Outras Transferências da União", "outras_transferencias_uniao", aggregated_data, population, 231.81),
            ]))
            transferencias_item['children'].append(uniao)

        estados = _prepare_revenue_item_aggregated("Transferências dos Estados", "tranferencias_estados", aggregated_data, population, 1167.63, is_collapsible=True)
        if estados:
            estados['children'].extend(filter(None, [
                _prepare_revenue_item_aggregated("Cota-Parte do ICMS", "transferencia_estado_icms", aggregated_data, population, 823.67),
                _prepare_revenue_item_aggregated("Cota-Parte do IPVA", "transferencia_estado_ipva", aggregated_data, population, 192.21),
                _prepare_revenue_item_aggregated("Compensação Financeira (Recursos Naturais)", "transferencia_estado_exploracao", aggregated_data, population,11.68),
                _prepare_revenue_item_aggregated("Recursos do SUS", "transferencia_estado_sus", aggregated_data, population, 61.46),
                _prepare_revenue_item_aggregated("Assistência Social", "transferencia_estado_assistencia", aggregated_data, population, 4.09),
                _prepare_revenue_item_aggregated("Outras Transferências dos Estados", "outras_transferencias_estado", aggregated_data, population, 74.49),
            ]))
            transferencias_item['children'].append(estados)

        transferencias_item['children'].append(
            _prepare_revenue_item_aggregated("Outras Transferências", "outras_tranferencias", aggregated_data, population, 663.77)
        )
        revenue_tree.append(transferencias_item)

    outras_receitas_item = _prepare_revenue_item_aggregated("Outras Receitas Correntes", "outras_receita", aggregated_data, population, 437.74, is_collapsible=True)
    if outras_receitas_item:
        outras_receitas_item['children'].extend(filter(None, [
            _prepare_revenue_item_aggregated("Receita Patrimonial", "receita_patrimonial", aggregated_data, population, 249.68),
            _prepare_revenue_item_aggregated("Receita Agropecuária", "receita_agropecuaria", aggregated_data, population, 0.07),
            _prepare_revenue_item_aggregated("Receita Industrial", "receita_industrial", aggregated_data, population, 0.06),
            _prepare_revenue_item_aggregated("Receita de Serviços", "receita_servicos", aggregated_data, population, 79.29),
            _prepare_revenue_item_aggregated("Outras Receitas", "outras_receitas", aggregated_data, population, 108.52),
        ]))
        revenue_tree.append(outras_receitas_item)

    # Renderiza o template parcial e retorna como JSON
    rendered_html = render_to_string('detail/partials/_fiscal_details.html', {'revenue_tree': revenue_tree, 'level': 0})
    
    return JsonResponse({'html': rendered_html})


def conjunto_chart_api(request):
    queryset = Municipio.objects.all()

    # --- filtros (copiado da sua view existente) ---
    uf_filtro = request.GET.get('uf')
    regiao_filtro = request.GET.get('regiao')
    municipio_filtro = request.GET.get('municipio')
    porte_filtro = request.GET.get('porte')
    rm_filtro = request.GET.get('rm')

    if regiao_filtro and regiao_filtro != 'todos':
        queryset = queryset.filter(regiao=regiao_filtro)
    if uf_filtro and uf_filtro != 'todos':
        queryset = queryset.filter(uf=uf_filtro)
    if municipio_filtro and municipio_filtro != 'todos':
        queryset = queryset.filter(name_muni_uf=municipio_filtro)
    if rm_filtro and rm_filtro != 'todos':
        queryset = queryset.filter(rm__nome=rm_filtro)

    # --- faixas de porte (copiado da sua view existente) ---
    if porte_filtro and porte_filtro != 'todos':
        if porte_filtro == 'Até 5 mil':
            queryset = queryset.filter(populacao23__lt=5000)
        elif porte_filtro == '5 mil a 10 mil':
            queryset = queryset.filter(populacao23__gte=5000, populacao23__lt=10000)
        elif porte_filtro == '10 mil a 20 mil':
            queryset = queryset.filter(populacao23__gte=10000, populacao23__lt=20000)
        elif porte_filtro == '20 mil a 50 mil':
            queryset = queryset.filter(populacao23__gte=20000, populacao23__lt=50000)
        elif porte_filtro == '50 mil a 100 mil':
            queryset = queryset.filter(populacao23__gte=50000, populacao23__lt=100000)
        elif porte_filtro == '100 mil a 200 mil':
            queryset = queryset.filter(populacao23__gte=100000, populacao23__lt=200000)
        elif porte_filtro == '200 mil a 500 mil':
            queryset = queryset.filter(populacao23__gte=200000, populacao23__lt=500000)
        elif porte_filtro == 'Acima de 500 mil':
            queryset = queryset.filter(populacao23__gte=500000)

    # --- agregações (copiado da sua view existente) ---
    aggregated_data = queryset.aggregate(
        total_imposto_taxas_contribuicoes=Sum('conta_detalhada__imposto_taxas_contribuicoes'),
        total_contribuicoes=Sum('conta_detalhada__contribuicoes'),
        total_transferencias_correntes=Sum('conta_detalhada__transferencias_correntes'),
        total_outras_receita=Sum('conta_detalhada__outras_receita'),
        total_imposto=Sum('conta_especifica__imposto'),
        total_taxas=Sum('conta_especifica__taxas'),
        total_iptu=Sum('conta_mais_especifica__iptu'),
        total_itbi=Sum('conta_mais_especifica__itbi'),
        total_iss=Sum('conta_mais_especifica__iss'),
        total_outros_impostos=Sum('conta_mais_especifica__outros_impostos'),
        total_taxa_policia=Sum('conta_mais_especifica__taxa_policia'),
        total_tranferencias_uniao=Sum('conta_especifica__tranferencias_uniao'),
        total_tranferencias_estados=Sum('conta_especifica__tranferencias_estados'),
        total_outras_tranferencias=Sum('conta_especifica__outras_tranferencias'),
        total_transferencia_uniao_fpm=Sum('conta_mais_especifica__transferencia_uniao_fpm'),
        total_transferencia_uniao_exploracao=Sum('conta_mais_especifica__transferencia_uniao_exploracao'),
        total_transferencia_uniao_sus=Sum('conta_mais_especifica__transferencia_uniao_sus'),
        total_transferencia_uniao_fnde=Sum('conta_mais_especifica__transferencia_uniao_fnde'),
        total_transferencia_uniao_fnas=Sum('conta_mais_especifica__transferencia_uniao_fnas'),
        total_outras_transferencias_uniao=Sum('conta_mais_especifica__outras_transferencias_uniao'),
        total_transferencia_estado_icms=Sum('conta_mais_especifica__transferencia_estado_icms'),
        total_transferencia_estado_ipva=Sum('conta_mais_especifica__transferencia_estado_ipva'),
        total_outras_transferencias_estado=Sum('conta_mais_especifica__outras_transferencias_estado'),
        total_receita_patrimonial=Sum('conta_especifica__receita_patrimonial'),
        total_receita_servicos=Sum('conta_especifica__receita_servicos'),
        total_outras_receitas=Sum('conta_especifica__outras_receitas'),
    )

    def v(key):
        return aggregated_data.get(key) or 0

    chart_data = {
        "main_categories": {
            "labels": ["ITC", "Contribuições", "Transf. Correntes", "Outras"],
            "values": [
                v('total_imposto_taxas_contribuicoes'),
                v('total_contribuicoes'),
                v('total_transferencias_correntes'),
                v('total_outras_receita'),
            ],
        },
        "imposto": {
            "labels": ["IPTU", "ITBI", "ISS", "Outros"],
            "values": [
                v('total_iptu'),
                v('total_itbi'),
                v('total_iss'),
                v('total_outros_impostos'),
            ],
        },
        "taxas": {
            "labels": ["Poder de Polícia"],
            "values": [v('total_taxa_policia')],
        },
        "contribuicoes": {
            "labels": ["Sociais"],
            "values": [v('total_contribuicoes')],
        },
        "transferencias_correntes": {
            "labels": ["União", "Estados", "Outras"],
            "values": [
                v('total_tranferencias_uniao'),
                v('total_tranferencias_estados'),
                v('total_outras_tranferencias'),
            ],
        },
        "transferencias_uniao": {
            "labels": ["FPM", "Rec. Naturais", "SUS", "FNDE", "FNAS", "Outras"],
            "values": [
                v('total_transferencia_uniao_fpm'),
                v('total_transferencia_uniao_exploracao'),
                v('total_transferencia_uniao_sus'),
                v('total_transferencia_uniao_fnde'),
                v('total_transferencia_uniao_fnas'),
                v('total_outras_transferencias_uniao'),
            ],
        },
        "transferencias_estado": {
            "labels": ["ICMS", "IPVA", "Outras"],
            "values": [
                v('total_transferencia_estado_icms'),
                v('total_transferencia_estado_ipva'),
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