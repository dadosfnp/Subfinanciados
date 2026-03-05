import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from home.models import Municipio, RegiaoMetropolitana, ContaDetalhada
from django.db.models import Sum, Avg, F, ExpressionWrapper, FloatField, Q
from home.models import Municipio, RegiaoMetropolitana, ContaDetalhada, MediaNacionalReceita

def selecionar_municipio_view(request):
    """
    Renderiza a página isolada para o usuário buscar e selecionar
    o município antes de ir para a Análise Detalhada.
    """
    return render(request, 'detail/selecionar_municipio.html')

def _prepare_revenue_item(name, field_base, model_instance, model_instance_percentile, media_nacional_obj=None, is_collapsible=False):
    """
    Estrutura os dados de uma rubrica especifica para renderizacao recursiva.
    Extrai valores absolutos, per capita, percentis e a media nacional correspondente.
    """
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

    # EXTRACAO DINAMICA DA MEDIA NACIONAL VIA ATRIBUTO DO OBJETO
    media_nac_val = getattr(media_nacional_obj, field_base, None) if media_nacional_obj else None

    item = {
        'name': name, 
        'field_base': field_base, 
        'value_abs': value_abs,
        'value_pc': value_pc, 
        'percentiles': percentiles, 
        'media_nacional': media_nac_val,
        'children': [],
    }

    if is_collapsible:
        item['target_id'] = f'detalhe-{field_base.replace("_", "-")}'

    return item

def municipio_detalhe_view(request, municipio_id):
    municipio = get_object_or_404(Municipio.objects.prefetch_related(
        'conta_detalhada', 'conta_especifica', 'conta_mais_especifica',
        'conta_detalhada_percentil', 'conta_especifica_percentil', 'conta_mais_especifica_percentil'
    ), cod_ibge=municipio_id)

    pop = municipio.populacao24 or 0
    if pop < 5000: filtro_faixa = {'populacao24__lt': 5000}
    elif pop < 10000: filtro_faixa = {'populacao24__gte': 5000, 'populacao24__lt': 10000}
    elif pop < 20000: filtro_faixa = {'populacao24__gte': 10000, 'populacao24__lt': 20000}
    elif pop < 50000: filtro_faixa = {'populacao24__gte': 20000, 'populacao24__lt': 50000}
    elif pop < 100000: filtro_faixa = {'populacao24__gte': 50000, 'populacao24__lt': 100000}
    elif pop < 200000: filtro_faixa = {'populacao24__gte': 100000, 'populacao24__lt': 200000}
    elif pop < 500000: filtro_faixa = {'populacao24__gte': 200000, 'populacao24__lt': 500000}
    else: filtro_faixa = {'populacao24__gte': 500000}

    # 2. FUNÇÃO PARA CALCULAR A MÉDIA PER CAPITA NO BANCO
    def avg_pc(campo):
        return Avg(ExpressionWrapper(F(campo) / F('populacao24'), output_field=FloatField()))

    # 3. FAZENDO A CONSULTA (Apenas municípios com população válida para não dar erro de divisão por zero)
    base_query = Municipio.objects.exclude(populacao24__isnull=True).exclude(populacao24=0)
    
    # Agregações para o 1º Nível (Conta Detalhada)
    agregacoes = {
        'transf_correntes': avg_pc('conta_detalhada__transferencias_correntes'),
        'impostos_taxas': avg_pc('conta_detalhada__imposto_taxas_contribuicoes'),
        'outras_rec': avg_pc('conta_detalhada__outras_receita'),
        'contrib': avg_pc('conta_detalhada__contribuicoes'),
    }

    medias_estadual = base_query.filter(uf=municipio.uf).aggregate(**agregacoes)
    medias_faixa = base_query.filter(**filtro_faixa).aggregate(**agregacoes)

    # RECUPERACAO DA INSTANCIA DE MEDIAS NACIONAIS (TABELA NOVA)
    media_nac = MediaNacionalReceita.objects.filter(ano_referencia=2024).first()

    cd = municipio.conta_detalhada
    cs = municipio.conta_especifica
    cme = municipio.conta_mais_especifica

    cdp = municipio.conta_detalhada_percentil
    csp = municipio.conta_especifica_percentil
    cmep = municipio.conta_mais_especifica_percentil
    
    revenue_tree = []

    # 1. Impostos, Taxas e Contribuições (ITC)
    itc_item = _prepare_revenue_item("Impostos, Taxas e Contribuições de Melhoria", "imposto_taxas_contribuicoes", cd, cdp, media_nac, is_collapsible=True)
    if itc_item:
        imposto_item = _prepare_revenue_item("Impostos", "imposto", cs, csp, media_nac, is_collapsible=True)
        if imposto_item:
            imposto_item['children'].extend(filter(None, [
                _prepare_revenue_item("Imposto sobre a Propriedade Predial e Territorial Urbana", "iptu", cme, cmep, media_nac),
                _prepare_revenue_item("Imposto sobre a Transmissão 'Inter Vivos'", "itbi", cme, cmep, media_nac),
                _prepare_revenue_item("Imposto sobre Serviços", "iss", cme, cmep, media_nac),
                _prepare_revenue_item("Imposto de Renda", "imposto_renda", cme, cmep, media_nac),
                _prepare_revenue_item("Outros Impostos", "outros_impostos", cme, cmep, media_nac),
            ]))
            itc_item['children'].append(imposto_item)

        taxas_item = _prepare_revenue_item("Taxas", "taxas", cs, csp, media_nac, is_collapsible=True)
        if taxas_item:
            taxas_item['children'].extend(filter(None, [
                _prepare_revenue_item("Taxas pelo Exercício do Poder de Polícia", "taxa_policia", cme, cmep, media_nac),
                _prepare_revenue_item("Taxas pela Prestação de Serviços", "taxa_prestacao_servico", cme, cmep, media_nac),
                _prepare_revenue_item("Outras Taxas", "outras_taxas", cme, cmep, media_nac),
            ]))
            itc_item['children'].append(taxas_item)

        cm_item = _prepare_revenue_item("Contribuições de Melhoria", "contribuicoes_melhoria", cs, csp, media_nac, is_collapsible=True)
        if cm_item:
            cm_item['children'].extend(filter(None, [
                _prepare_revenue_item("Contribuição de Melhoria para Pavimentação e Obras", "contribuicao_melhoria_pavimento_obras", cme, cmep, media_nac),
                _prepare_revenue_item("Contribuição de Melhoria para Rede de Água e Esgoto", "contribuicao_melhoria_agua_potavel", cme, cmep, media_nac),
                _prepare_revenue_item("Contribuição de Melhoria para Iluminação Pública", "contribuicao_melhoria_iluminacao_publica", cme, cmep, media_nac),
                _prepare_revenue_item("Outras Contribuições de Melhoria", "outras_contribuicoes_melhoria", cme, cmep, media_nac),
            ]))
            itc_item['children'].append(cm_item)

        revenue_tree.append(itc_item)

    # 2. Contribuições
    contribuicoes_item = _prepare_revenue_item("Contribuições", "contribuicoes", cd, cdp, media_nac, is_collapsible=True)
    if contribuicoes_item:
        contribuicoes_item['children'].extend(filter(None, [
            _prepare_revenue_item("Contribuições Sociais", "contribuicoes_sociais", cs, csp, media_nac),
            _prepare_revenue_item("Custeio do Serviço de Iluminação Pública", "contribuicoes_iluminacao_publica", cs, csp, media_nac),
            _prepare_revenue_item("Outras Contribuições", "outras_contribuicoes", cs, csp, media_nac),
        ]))
        revenue_tree.append(contribuicoes_item)

    # 3. Transferências Correntes
    transferencias_item = _prepare_revenue_item("Transferências Correntes", "transferencias_correntes", cd, cdp, media_nac, is_collapsible=True)
    if transferencias_item:
        uniao = _prepare_revenue_item("Transferências da União", "tranferencias_uniao", cs, csp, media_nac, is_collapsible=True)
        if uniao:
            uniao['children'].extend(filter(None, [
                _prepare_revenue_item("Cota-Parte do FPM", "transferencia_uniao_fpm", cme, cmep, media_nac),
                _prepare_revenue_item("Compensação Financeira (Recursos Naturais)", "transferencia_uniao_exploracao", cme, cmep, media_nac),
                _prepare_revenue_item("Recursos do SUS", "transferencia_uniao_sus", cme, cmep, media_nac),
                _prepare_revenue_item("Recursos do FNDE", "transferencia_uniao_fnde", cme, cmep, media_nac),
                _prepare_revenue_item("Recursos do FUNDEB", "transferencia_uniao_fundeb", cme, cmep, media_nac),
                _prepare_revenue_item("Recursos do FNAS", "transferencia_uniao_fnas", cme, cmep, media_nac),
                _prepare_revenue_item("Outras Transferências da União", "outras_transferencias_uniao", cme, cmep, media_nac),
            ]))
            transferencias_item['children'].append(uniao)

        estados = _prepare_revenue_item("Transferências dos Estados", "tranferencias_estados", cs, csp, media_nac, is_collapsible=True)
        if estados:
            estados['children'].extend(filter(None, [
                _prepare_revenue_item("Cota-Parte do ICMS", "transferencia_estado_icms", cme, cmep, media_nac),
                _prepare_revenue_item("Cota-Parte do IPVA", "transferencia_estado_ipva", cme, cmep, media_nac),
                _prepare_revenue_item("Compensação Financeira (Recursos Naturais)", "transferencia_estado_exploracao", cme, cmep, media_nac),
                _prepare_revenue_item("Recursos do SUS", "transferencia_estado_sus", cme, cmep, media_nac),
                _prepare_revenue_item("Assistência Social", "transferencia_estado_assistencia", cme, cmep, media_nac),
                _prepare_revenue_item("Outras Transferências dos Estados", "outras_transferencias_estado", cme, cmep, media_nac),
            ]))
            transferencias_item['children'].append(estados)

        transferencias_item['children'].append(_prepare_revenue_item("Outras Transferências", "outras_tranferencias", cs, csp, media_nac))
        revenue_tree.append(transferencias_item)
    
    # 4. Outras Receitas Correntes
    outras_receitas_item = _prepare_revenue_item("Outras Receitas Correntes", "outras_receita", cd, cdp, media_nac, is_collapsible=True)
    if outras_receitas_item:
        outras_receitas_item['children'].extend(filter(None, [
            _prepare_revenue_item("Receita Patrimonial", "receita_patrimonial", cs, csp, media_nac),
            _prepare_revenue_item("Receita Agropecuária", "receita_agropecuaria", cs, csp, media_nac),
            _prepare_revenue_item("Receita Industrial", "receita_industrial", cs, csp, media_nac),
            _prepare_revenue_item("Receita de Serviços", "receita_servicos", cs, csp, media_nac),
            _prepare_revenue_item("Outras Receitas", "outras_receitas", cs, csp, media_nac),
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
            ["Impostos, Taxas e Contribuições de Melhoria", "Contribuições", "Transf. Correntes", "Outras"],
            [cd.imposto_taxas_contribuicoes_pc, cd.contribuicoes_pc, cd.transferencias_correntes_pc, cd.outras_receita_pc]
        ),
        "imposto_taxas_contribuicoes": get_chart_series(
            ["Impostos", "Taxas", "Contrib. Melhoria"],
            [cs.imposto_pc, cs.taxas_pc, cs.contribuicoes_melhoria_pc]
        ),
        "imposto": get_chart_series(
            ["IPTU", "ITBI", "ISS", "Imposto de Renda", "Outros"],
            [cme.iptu_pc, cme.itbi_pc, cme.iss_pc, cme.imposto_renda_pc, cme.outros_impostos_pc]
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
            ["FPM", "Rec. Naturais", "SUS", "FNDE", "FUNDEB", "FNAS", "Outras"],
            [cme.transferencia_uniao_fpm_pc, cme.transferencia_uniao_exploracao_pc, cme.transferencia_uniao_sus_pc, cme.transferencia_uniao_fnde_pc, cme.transferencia_uniao_fundeb_pc, cme.transferencia_uniao_fnas_pc, cme.outras_transferencias_uniao_pc]
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

    qs = (
        Municipio.objects
        .annotate(
            # Categorias Principais
            main_categories=F('rc_24_pc'),

            # Imposto, Taxas e Contribuições de Melhoria
            imposto_taxas_contribuicoes=F('conta_detalhada__imposto_taxas_contribuicoes')/F('populacao24'),
            imposto = F('conta_especifica__imposto')/F('populacao24'),  
            iptu = F('conta_mais_especifica__iptu')/F('populacao24'),
            itbi = F('conta_mais_especifica__itbi')/F('populacao24'),
            iss = F('conta_mais_especifica__iss')/F('populacao24'),
            imposto_renda = F('conta_mais_especifica__imposto_renda')/F('populacao24'),
            outros_impostos = F('conta_mais_especifica__outros_impostos')/F('populacao24'),
            taxas = F('conta_especifica__taxas')/F('populacao24'),
            taxa_policia = F('conta_mais_especifica__taxa_policia')/F('populacao24'),
            taxa_prestacao_servico = F('conta_mais_especifica__taxa_prestacao_servico')/F('populacao24'),
            outras_taxas = F('conta_mais_especifica__outras_taxas')/F('populacao24'),

            contribuicoes_melhoria = F('conta_especifica__contribuicoes_melhoria')/F('populacao24'),
            contribuicao_melhoria_pavimento_obras = F('conta_mais_especifica__contribuicao_melhoria_pavimento_obras')/F('populacao24'),
            contribuicao_melhoria_agua_potavel = F('conta_mais_especifica__contribuicao_melhoria_agua_potavel')/F('populacao24'),
            contribuicao_melhoria_iluminacao_publica = F('conta_mais_especifica__contribuicao_melhoria_iluminacao_publica')/F('populacao24'),
            outras_contribuicoes_melhoria = F('conta_mais_especifica__outras_contribuicoes_melhoria')/F('populacao24'),

            # Contribuições
            contribuicoes=F('conta_detalhada__contribuicoes')/F('populacao24'),
            contribuicoes_sociais = F('conta_especifica__contribuicoes_sociais')/F('populacao24'),
            contribuicoes_iluminacao_publica = F('conta_especifica__contribuicoes_iluminacao_publica')/F('populacao24'),
            outras_contribuicoes = F('conta_especifica__outras_contribuicoes')/F('populacao24'),

            # Transferências Correntes
            transferencias_correntes=F('conta_detalhada__transferencias_correntes')/F('populacao24'),
            transferencias_uniao = F('conta_especifica__tranferencias_uniao')/F('populacao24'),
            transferencias_uniao_fpm = F('conta_mais_especifica__transferencia_uniao_fpm')/F('populacao24'),
            transferencias_uniao_exploracao = F('conta_mais_especifica__transferencia_uniao_exploracao')/F('populacao24'),
            transferencias_uniao_sus = F('conta_mais_especifica__transferencia_uniao_sus')/F('populacao24'),
            transferencias_uniao_fnde = F('conta_mais_especifica__transferencia_uniao_fnde')/F('populacao24'),
            transferencia_uniao_fundeb = F('conta_mais_especifica__transferencia_uniao_fundeb')/F('populacao24'),
            transferencias_uniao_fnas = F('conta_mais_especifica__transferencia_uniao_fnas')/F('populacao24'),
            outras_transferencias_uniao = F('conta_mais_especifica__outras_transferencias_uniao')/F('populacao24'),
            transferencias_estado = F('conta_especifica__tranferencias_estados')/F('populacao24'),
            transferencias_estado_icms = F('conta_mais_especifica__transferencia_estado_icms')/F('populacao24'),
            transferencias_estado_ipva = F('conta_mais_especifica__transferencia_estado_ipva')/F('populacao24'),
            transferencias_estado_exploracao = F('conta_mais_especifica__transferencia_estado_exploracao')/F('populacao24'),
            transferencias_estado_sus = F('conta_mais_especifica__transferencia_estado_sus')/F('populacao24'),
            transferencias_estado_assistencia = F('conta_mais_especifica__transferencia_estado_assistencia')/F('populacao24'),
            outras_transferencias_estado = F('conta_mais_especifica__outras_transferencias_estado')/F('populacao24'),

            # Outras Receitas Correntes
            outras_receitas=F('conta_detalhada__outras_receita')/F('populacao24'),
            receita_patrimonial = F('conta_especifica__receita_patrimonial')/F('populacao24'),
            receita_agropecuaria = F('conta_especifica__receita_agropecuaria')/F('populacao24'),
            receita_industrial = F('conta_especifica__receita_industrial')/F('populacao24'),
            receita_servicos = F('conta_especifica__receita_servicos')/F('populacao24'),
            outras_receitas_outras = F('conta_especifica__outras_receitas')/F('populacao24')
                  )
        .values(                  # já vem “flat” pro template
            "cod_ibge", "main_categories",
            
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
            "transferencias_uniao_fpm",
            "transferencias_uniao_exploracao",
            "transferencias_uniao_sus",
            "transferencias_uniao_fnde",
            "transferencia_uniao_fundeb",
            "transferencias_uniao_fnas",
            "outras_transferencias_uniao",
            "transferencias_estado",
            "transferencias_estado_icms",
            "transferencias_estado_ipva",
            "transferencias_estado_exploracao",
            "transferencias_estado_sus",
            "transferencias_estado_assistencia",
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

    # Calcula a variacao percentual da populacao e da receita corrente per capita
    delta_populacao = 0.0
    if municipio.populacao00 and municipio.populacao24 and municipio.populacao00 > 0:
        delta_populacao = ((municipio.populacao24 - municipio.populacao00) / municipio.populacao00) * 100

    delta_rc_pc = 0.0
    if municipio.rc_00_pc and municipio.rc_24_pc and municipio.rc_00_pc > 0:
        delta_rc_pc = ((municipio.rc_24_pc - municipio.rc_00_pc) / municipio.rc_00_pc) * 100

    evolucao_historica = {
        'delta_populacao': round(delta_populacao, 2),
        'delta_rc_pc': round(delta_rc_pc, 2),
        'has_2000_data': bool(municipio.populacao00 or municipio.rc_00_pc)
    }

    context = {
        'municipio': municipio,
        'revenue_tree': revenue_tree,
        'chart_data_json': json.dumps(chart_data),
        'percentile_data_json': json.dumps(percentile_data),
        'data': data,
        'evolucao_historica': evolucao_historica, 
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
    
    national_avg_rc = Municipio.objects.aggregate(avg_rc=Avg('rc_24_pc'))['avg_rc'] or 0

    # Aggregate data from the filtered queryset
    aggregated_data = queryset.aggregate(
        total_populacao=Sum('populacao24'),
        total_receita_corrente=Sum('rc_2024'),
        avg_receita_per_capita=Avg('rc_24_pc'),
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
        total_imposto_renda=Sum('conta_mais_especifica__imposto_renda'),
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

    # Incluir os dados agregados na resposta final
    response_data['fiscal_aggregation'] = fiscal_aggregation
    
    return JsonResponse(response_data)




def _prepare_revenue_item_aggregated(
    name: str,
    field_base: str,      # ex: "imposto_taxas_contribuicoes" (pra casar com total_* no aggregated_data)
    field_path: str,      # ex: "conta_detalhada__imposto_taxas_contribuicoes" (pra usar no queryset/F())
    aggregated_data: dict,
    queryset,
    value_pc_nac: float,
    is_collapsible: bool = False,
):
    value_abs = aggregated_data.get(f"total_{field_base}", 0) or 0

    qs_pc = (
        queryset
        .filter(populacao24__gt=0)
        .filter(Q(**{f"{field_path}__gt": 0}))
        .annotate(
            pc=ExpressionWrapper(
                F(field_path) / F("populacao24"),
                output_field=FloatField(),
            )
        )
    )

    value_pc = qs_pc.aggregate(avg=Avg("pc"))["avg"] or 0

    if value_abs == 0 and value_pc == 0:
        return None

    diff = {
        "pc": round(((value_pc - value_pc_nac) / value_pc_nac * 100), 2) if value_pc_nac else 0
    }

    item = {
        "name": name,
        "field_base": field_base,
        "value_abs": value_abs,
        "value_pc": value_pc,
        "diff": diff,
        "children": [],
    }

    if is_collapsible:
        item["target_id"] = f"detalhe-{field_base.replace('_', '-')}"
    return item

def nacional_pc_media(field_path):
    qs = (
        Municipio.objects
        .filter(
            Q(populacao24__gt=0),
            Q(**{f"{field_path}__gt": 0})
        )
        .annotate(
            pc=ExpressionWrapper(
                F(field_path) / F('populacao24'),
                output_field=FloatField()
            )
        )
    )
    return qs.aggregate(avg=Avg('pc'))['avg'] or 0

def conjunto_detalhe_view(request):
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

    nacional_med_outros_impostos = nacional_pc_media('conta_mais_especifica__outros_impostos')

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

    # helper para tratar None -> 0
    def v(key):
        return aggregated_data.get(key) or 0

    # ------- revenue_tree (mantive sua lógica original) -------
    revenue_tree = []
    population = queryset.aggregate(total_populacao=Sum('populacao24'))['total_populacao'] or 0

    # ---------------------------
    # ITC (Impostos, Taxas e Contribuições de Melhoria)
    # ---------------------------
    itc_item = _prepare_revenue_item_aggregated(
        "Impostos, Taxas e Contribuições de Melhoria",
        "imposto_taxas_contribuicoes",
        "conta_detalhada__imposto_taxas_contribuicoes",
        aggregated_data,
        queryset,
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
            queryset,
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
                            queryset,
                            nacional_med_iptu,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Imposto sobre a Transmissão 'Inter Vivos'",
                            "itbi",
                            "conta_mais_especifica__itbi",
                            aggregated_data,
                            queryset,
                            nacional_med_itbi,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Imposto sobre Serviços",
                            "iss",
                            "conta_mais_especifica__iss",
                            aggregated_data,
                            queryset,
                            nacional_med_iss,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Imposto de Renda",
                            "imposto_renda",
                            "conta_mais_especifica__imposto_renda",
                            aggregated_data,
                            queryset,
                            nacional_med_renda,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Outros Impostos",
                            "outros_impostos",
                            "conta_mais_especifica__outros_impostos",
                            aggregated_data,
                            queryset,
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
            queryset,
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
                            queryset,
                            nacional_med_taxa_policia_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Taxas pela Prestação de Serviços",
                            "taxa_prestacao_servico",
                            "conta_mais_especifica__taxa_prestacao_servico",
                            aggregated_data,
                            queryset,
                            nacional_med_taxa_prestacao_servico_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Outras Taxas",
                            "outras_taxas",
                            "conta_mais_especifica__outras_taxas",
                            aggregated_data,
                            queryset,
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
            queryset,
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
                            queryset,
                            nacional_med_contribuicao_melhoria_pavimento_obras_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Contribuição de Melhoria para Rede de Água e Esgoto",
                            "contribuicao_melhoria_agua_potavel",
                            "conta_mais_especifica__contribuicao_melhoria_agua_potavel",
                            aggregated_data,
                            queryset,
                            nacional_med_contribuicao_melhoria_agua_potavel_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Contribuição de Melhoria para Iluminação Pública",
                            "contribuicao_melhoria_iluminacao_publica",
                            "conta_mais_especifica__contribuicao_melhoria_iluminacao_publica",
                            aggregated_data,
                            queryset,
                            nacional_med_contribuicao_melhoria_iluminacao_publica_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Outras Contribuições de Melhoria",
                            "outras_contribuicoes_melhoria",
                            "conta_mais_especifica__outras_contribuicoes_melhoria",
                            aggregated_data,
                            queryset,
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
        queryset,
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
                        queryset,
                        nacional_med_contribuicoes_sociais_pc,
                    ),
                    _prepare_revenue_item_aggregated(
                        "Custeio do Serviço de Iluminação Pública",
                        "contribuicoes_iluminacao_publica",
                        "conta_especifica__contribuicoes_iluminacao_publica",
                        aggregated_data,
                        queryset,
                        nacional_med_contribuicoes_iluminacao_publica_pc,
                    ),
                    _prepare_revenue_item_aggregated(
                        "Outras Contribuições",
                        "outras_contribuicoes",
                        "conta_especifica__outras_contribuicoes",
                        aggregated_data,
                        queryset,
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
        queryset,
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
            queryset,
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
                            queryset,
                            nacional_med_tranferencias_uniao_fpm_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Compensação Financeira (Recursos Naturais)",
                            "transferencia_uniao_exploracao",
                            "conta_mais_especifica__transferencia_uniao_exploracao",
                            aggregated_data,
                            queryset,
                            nacional_med_tranferencias_uniao_exploracao_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Recursos do SUS",
                            "transferencia_uniao_sus",
                            "conta_mais_especifica__transferencia_uniao_sus",
                            aggregated_data,
                            queryset,
                            nacional_med_tranferencias_uniao_sus_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Recursos do FNDE",
                            "transferencia_uniao_fnde",
                            "conta_mais_especifica__transferencia_uniao_fnde",
                            aggregated_data,
                            queryset,
                            nacional_med_tranferencias_uniao_fnde_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Recursos do FUNDEB",
                            "transferencia_uniao_fundeb",
                            "conta_mais_especifica__transferencia_uniao_fundeb",
                            aggregated_data,
                            queryset,
                            nacional_med_tranferencias_uniao_fundeb_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Recursos do FNAS",
                            "transferencia_uniao_fnas",
                            "conta_mais_especifica__transferencia_uniao_fnas",
                            aggregated_data,
                            queryset,
                            nacional_med_tranferencias_uniao_fnas_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Outras Transferências da União",
                            "outras_transferencias_uniao",
                            "conta_mais_especifica__outras_transferencias_uniao",
                            aggregated_data,
                            queryset,
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
            queryset,
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
                            queryset,
                            nacional_med_transferencias_estado_icms_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Cota-Parte do IPVA",
                            "transferencia_estado_ipva",
                            "conta_mais_especifica__transferencia_estado_ipva",
                            aggregated_data,
                            queryset,
                            nacional_med_transferencias_estado_ipva_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Compensação Financeira (Recursos Naturais)",
                            "transferencia_estado_exploracao",
                            "conta_mais_especifica__transferencia_estado_exploracao",
                            aggregated_data,
                            queryset,
                            nacional_med_transferencias_estado_exploracao_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Recursos do SUS",
                            "transferencia_estado_sus",
                            "conta_mais_especifica__transferencia_estado_sus",
                            aggregated_data,
                            queryset,
                            nacional_med_transferencias_estado_sus_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Assistência Social",
                            "transferencia_estado_assistencia",
                            "conta_mais_especifica__transferencia_estado_assistencia",
                            aggregated_data,
                            queryset,
                            nacional_med_transferencias_estado_assistencia_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Outras Transferências dos Estados",
                            "outras_transferencias_estado",
                            "conta_mais_especifica__outras_transferencias_estado",
                            aggregated_data,
                            queryset,
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
            queryset,
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
        queryset,
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
                        queryset,
                        nacional_med_receita_patrimonial_pc,
                    ),
                    _prepare_revenue_item_aggregated(
                        "Receita Agropecuária",
                        "receita_agropecuaria",
                        "conta_especifica__receita_agropecuaria",
                        aggregated_data,
                        queryset,
                        nacional_med_receita_agropecuaria_pc,
                    ),
                    _prepare_revenue_item_aggregated(
                        "Receita Industrial",
                        "receita_industrial",
                        "conta_especifica__receita_industrial",
                        aggregated_data,
                        queryset,
                        nacional_med_receita_industrial_pc,
                    ),
                    _prepare_revenue_item_aggregated(
                        "Receita de Serviços",
                        "receita_servicos",
                        "conta_especifica__receita_servicos",
                        aggregated_data,
                        queryset,
                        nacional_med_receita_servicos_pc,
                    ),
                    _prepare_revenue_item_aggregated(
                        "Outras Receitas",
                        "outras_receitas",
                        "conta_especifica__outras_receitas",
                        aggregated_data,
                        queryset,
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
                v('total_outros_impostos'),
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
    }

    print(revenue_tree)
    return render(request, 'detail/detalhe_conjunto.html', context)




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

    nacional_med_outros_impostos = nacional_pc_media('conta_mais_especifica__outros_impostos')

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
        # Novas regras adicionadas:
        elif porte_filtro == 'Acima de 80 mil':
            queryset = queryset.filter(populacao24__gt=80000)
        elif porte_filtro == 'Abaixo de 80 mil':
            queryset = queryset.filter(populacao24__lte=80000)

    # Perform the aggregation
    aggregated_data = queryset.aggregate(
        total_receita_corrente=Sum('rc_2024'),
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
        total_imposto_renda=Sum('conta_mais_especifica__imposto_renda'),
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

    population = queryset.aggregate(total_populacao=Sum('populacao24'))['total_populacao'] or 0


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
        queryset,
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
            queryset,
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
                            queryset,
                            nacional_med_iptu,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Imposto sobre a Transmissão 'Inter Vivos'",
                            "itbi",
                            "conta_mais_especifica__itbi",
                            aggregated_data,
                            queryset,
                            nacional_med_itbi,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Imposto sobre Serviços",
                            "iss",
                            "conta_mais_especifica__iss",
                            aggregated_data,
                            queryset,
                            nacional_med_iss,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Imposto de Renda",
                            "imposto_renda",
                            "conta_mais_especifica__imposto_renda",
                            aggregated_data,
                            queryset,
                            nacional_med_renda,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Outros Impostos",
                            "outros_impostos",
                            "conta_mais_especifica__outros_impostos",
                            aggregated_data,
                            queryset,
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
            queryset,
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
                            queryset,
                            nacional_med_taxa_policia_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Taxas pela Prestação de Serviços",
                            "taxa_prestacao_servico",
                            "conta_mais_especifica__taxa_prestacao_servico",
                            aggregated_data,
                            queryset,
                            nacional_med_taxa_prestacao_servico_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Outras Taxas",
                            "outras_taxas",
                            "conta_mais_especifica__outras_taxas",
                            aggregated_data,
                            queryset,
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
            queryset,
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
                            queryset,
                            nacional_med_contribuicao_melhoria_pavimento_obras_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Contribuição de Melhoria para Rede de Água e Esgoto",
                            "contribuicao_melhoria_agua_potavel",
                            "conta_mais_especifica__contribuicao_melhoria_agua_potavel",
                            aggregated_data,
                            queryset,
                            nacional_med_contribuicao_melhoria_agua_potavel_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Contribuição de Melhoria para Iluminação Pública",
                            "contribuicao_melhoria_iluminacao_publica",
                            "conta_mais_especifica__contribuicao_melhoria_iluminacao_publica",
                            aggregated_data,
                            queryset,
                            nacional_med_contribuicao_melhoria_iluminacao_publica_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Outras Contribuições de Melhoria",
                            "outras_contribuicoes_melhoria",
                            "conta_mais_especifica__outras_contribuicoes_melhoria",
                            aggregated_data,
                            queryset,
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
        queryset,
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
                        queryset,
                        nacional_med_contribuicoes_sociais_pc,
                    ),
                    _prepare_revenue_item_aggregated(
                        "Custeio do Serviço de Iluminação Pública",
                        "contribuicoes_iluminacao_publica",
                        "conta_especifica__contribuicoes_iluminacao_publica",
                        aggregated_data,
                        queryset,
                        nacional_med_contribuicoes_iluminacao_publica_pc,
                    ),
                    _prepare_revenue_item_aggregated(
                        "Outras Contribuições",
                        "outras_contribuicoes",
                        "conta_especifica__outras_contribuicoes",
                        aggregated_data,
                        queryset,
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
        queryset,
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
            queryset,
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
                            queryset,
                            nacional_med_tranferencias_uniao_fpm_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Compensação Financeira (Recursos Naturais)",
                            "transferencia_uniao_exploracao",
                            "conta_mais_especifica__transferencia_uniao_exploracao",
                            aggregated_data,
                            queryset,
                            nacional_med_tranferencias_uniao_exploracao_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Recursos do SUS",
                            "transferencia_uniao_sus",
                            "conta_mais_especifica__transferencia_uniao_sus",
                            aggregated_data,
                            queryset,
                            nacional_med_tranferencias_uniao_sus_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Recursos do FNDE",
                            "transferencia_uniao_fnde",
                            "conta_mais_especifica__transferencia_uniao_fnde",
                            aggregated_data,
                            queryset,
                            nacional_med_tranferencias_uniao_fnde_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Recursos do FUNDEB",
                            "transferencia_uniao_fundeb",
                            "conta_mais_especifica__transferencia_uniao_fundeb",
                            aggregated_data,
                            queryset,
                            nacional_med_tranferencias_uniao_fundeb_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Recursos do FNAS",
                            "transferencia_uniao_fnas",
                            "conta_mais_especifica__transferencia_uniao_fnas",
                            aggregated_data,
                            queryset,
                            nacional_med_tranferencias_uniao_fnas_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Outras Transferências da União",
                            "outras_transferencias_uniao",
                            "conta_mais_especifica__outras_transferencias_uniao",
                            aggregated_data,
                            queryset,
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
            queryset,
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
                            queryset,
                            nacional_med_transferencias_estado_icms_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Cota-Parte do IPVA",
                            "transferencia_estado_ipva",
                            "conta_mais_especifica__transferencia_estado_ipva",
                            aggregated_data,
                            queryset,
                            nacional_med_transferencias_estado_ipva_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Compensação Financeira (Recursos Naturais)",
                            "transferencia_estado_exploracao",
                            "conta_mais_especifica__transferencia_estado_exploracao",
                            aggregated_data,
                            queryset,
                            nacional_med_transferencias_estado_exploracao_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Recursos do SUS",
                            "transferencia_estado_sus",
                            "conta_mais_especifica__transferencia_estado_sus",
                            aggregated_data,
                            queryset,
                            nacional_med_transferencias_estado_sus_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Assistência Social",
                            "transferencia_estado_assistencia",
                            "conta_mais_especifica__transferencia_estado_assistencia",
                            aggregated_data,
                            queryset,
                            nacional_med_transferencias_estado_assistencia_pc,
                        ),
                        _prepare_revenue_item_aggregated(
                            "Outras Transferências dos Estados",
                            "outras_transferencias_estado",
                            "conta_mais_especifica__outras_transferencias_estado",
                            aggregated_data,
                            queryset,
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
            queryset,
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
        queryset,
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
                        queryset,
                        nacional_med_receita_patrimonial_pc,
                    ),
                    _prepare_revenue_item_aggregated(
                        "Receita Agropecuária",
                        "receita_agropecuaria",
                        "conta_especifica__receita_agropecuaria",
                        aggregated_data,
                        queryset,
                        nacional_med_receita_agropecuaria_pc,
                    ),
                    _prepare_revenue_item_aggregated(
                        "Receita Industrial",
                        "receita_industrial",
                        "conta_especifica__receita_industrial",
                        aggregated_data,
                        queryset,
                        nacional_med_receita_industrial_pc,
                    ),
                    _prepare_revenue_item_aggregated(
                        "Receita de Serviços",
                        "receita_servicos",
                        "conta_especifica__receita_servicos",
                        aggregated_data,
                        queryset,
                        nacional_med_receita_servicos_pc,
                    ),
                    _prepare_revenue_item_aggregated(
                        "Outras Receitas",
                        "outras_receitas",
                        "conta_especifica__outras_receitas",
                        aggregated_data,
                        queryset,
                        nacional_med_outras_receitas_outras_pc,
                    ),
                ],
            )
        )
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
        # Novas regras adicionadas:
        elif porte_filtro == 'Acima de 80 mil':
            queryset = queryset.filter(populacao24__gt=80000)
        elif porte_filtro == 'Abaixo de 80 mil':
            queryset = queryset.filter(populacao24__lte=80000)

    # --- agregações (copiado da sua view existente) ---
    aggregated_data = queryset.aggregate(
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
        total_imposto_renda=Sum('conta_mais_especifica__imposto_renda'),
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
                v('total_outros_impostos'),
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
    # --- Lógica de filtragem (copiada de outra view) ---
    queryset = Municipio.objects.all()
    uf_filtro = request.GET.get('uf')
    regiao_filtro = request.GET.get('regiao')
    porte_filtro = request.GET.get('porte')
    rm_filtro = request.GET.get('rm')
    classification_filter = request.GET.get('classification', 'quintil')
    subgroup_filter = request.GET.get('subgrupo')

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
        # Novas regras adicionadas:
        elif porte_filtro == 'Acima de 80 mil':
            queryset = queryset.filter(populacao24__gt=80000)
        elif porte_filtro == 'Abaixo de 80 mil':
            queryset = queryset.filter(populacao24__lte=80000)


    if subgroup_filter and subgroup_filter != "todos":
        if classification_filter == 'quintil':
            queryset = queryset.filter(quintil24=subgroup_filter)
        elif classification_filter == 'decil':
            queryset = queryset.filter(decil24=subgroup_filter)

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
            outros_impostos = F('conta_mais_especifica__outros_impostos')/F('populacao24'),
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