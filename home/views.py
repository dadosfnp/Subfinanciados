from django.shortcuts import render, get_object_or_404
from django.db.models import  Avg, StdDev
from django.http import JsonResponse
from .models import Municipio, ContaDetalhada 
import numpy as np
import math
from collections import defaultdict


def home(request):
    """
    Renderiza o template HTML para a visualização dos gráficos.
    """
    return render(request, 'home/home.html')

def api_get_dependent_filters(request):
    """
    Retorna listas de UFs, Municípios e Regiões Metropolitanas
    com base na região, UF ou RM selecionada, passadas como parâmetros na URL.
    """
    regiao_selecionada = request.GET.get('regiao')
    uf_selecionada = request.GET.get('uf')
    rm_selecionada = request.GET.get('rm')

    # Inicializa o queryset com todos os municípios
    queryset = Municipio.objects.all()

    # Aplica filtros com base nos parâmetros da requisição
    if rm_selecionada and rm_selecionada != 'todos':
        queryset = queryset.filter(rm__nome=rm_selecionada)

    if regiao_selecionada and regiao_selecionada != 'todos':
        queryset = queryset.filter(regiao=regiao_selecionada)

    if uf_selecionada and uf_selecionada != 'todos':
        queryset = queryset.filter(uf=uf_selecionada)

    # Extrai valores distintos do queryset filtrado
    regioes = queryset.values_list('regiao', flat=True).distinct().order_by('regiao')
    ufs = queryset.values_list('uf', flat=True).distinct().order_by('uf')
    municipios = queryset.values_list('name_muni_uf', flat=True).distinct().order_by('name_muni_uf')
    rms = queryset.exclude(rm=None).values_list('rm__nome', flat=True).distinct().order_by('rm__nome')

    # Retorna os dados como JSON para consumo no frontend
    return JsonResponse({
        'regioes': list(regioes),
        'ufs': list(ufs),
        'municipios': list(municipios),
        'rms': list(rms)
    })

def api_get_dashboard_data(request):
    """
    Retorna dados agregados para o dashboard, incluindo cartões de resumo,
    dados para gráficos e uma tabela dinâmica. Os dados da tabela podem ser exibidos
    como contagens brutas ou porcentagens, e são categorizados por faixas de população
    e classificação (quintil/decil).
    """
    queryset = Municipio.objects.all() # Queryset inicial antes dos filtros

    # 1. RECUPERAÇÃO E APLICAÇÃO DE FILTROS
    # ======================================================================
    regiao_filtro = request.GET.get('regiao')
    uf_filtro = request.GET.get('uf')
    rm_filtro = request.GET.get('rm')
    classification_filter = request.GET.get('classification', 'quintil')
    display_format = request.GET.get('display_format', 'numero')
    quantil_calculation = request.GET.get('calculation_mode', 'total') # 'total' ou 'por_filtro'
    include_2000_data_str = request.GET.get('include_2000_data', 'false')
    include_2000_data = (include_2000_data_str.lower() == 'true')
    
    # Aplica filtros geográficos e administrativos
    if regiao_filtro and regiao_filtro != 'todos':
        queryset = queryset.filter(regiao=regiao_filtro)
    if uf_filtro and uf_filtro != 'todos':
        queryset = queryset.filter(uf=uf_filtro)
    if rm_filtro and rm_filtro != 'todos':
        queryset = queryset.filter(rm__nome=rm_filtro)

    # 2. LÓGICA DE CÁLCULO E PREPARAÇÃO DOS DADOS POR ANO (2023 e 2000)
    # ======================================================================
    if classification_filter == 'quintil':
        num_quantiles = 5
    elif classification_filter == 'decil':
        num_quantiles = 10
    else: # Padrão
        classification_filter = 'quintil'
        num_quantiles = 5

    # Define base classification labels for both years
    base_classification_labels = [f'{i+1}º {classification_filter}' for i in range(num_quantiles)]

    # --- Lógica para o ano 2023 ---
    aggregated_data_list_23 = []
    field_for_aggregation_23 = ''
    classification_map_23 = {}

    if quantil_calculation == 'por_filtro':
        municipios_raw_data_23 = list(queryset.values('id', 'populacao23', 'rc_23_pc'))
        rc_values_23 = np.array([muni['rc_23_pc'] for muni in municipios_raw_data_23 if muni.get('rc_23_pc') is not None])
        
        if len(rc_values_23) > 0:
            field_for_aggregation_23 = 'dynamic_quantile_val'
            classification_map_23 = {i + 1: base_classification_labels[i] for i in range(num_quantiles)}
            
            quantiles_to_calculate = np.linspace(0, 1, num_quantiles + 1)[1:-1]
            quantile_boundaries = np.quantile(rc_values_23, quantiles_to_calculate)
            
            for muni in municipios_raw_data_23:
                if muni.get('rc_23_pc') is not None:
                    quantile_group_idx = np.searchsorted(quantile_boundaries, muni['rc_23_pc'])
                    muni[field_for_aggregation_23] = int(quantile_group_idx + 1)
                else:
                    muni[field_for_aggregation_23] = None
                aggregated_data_list_23.append(muni)
        else:
            # Fallback para o modo 'total' se não houver dados para recalcular
            field_for_aggregation_23 = f'{classification_filter}23'
            classification_map_23 = {label: label for label in base_classification_labels}
            aggregated_data_list_23 = list(queryset.values('id', 'populacao23', 'rc_23_pc', field_for_aggregation_23))
            
    else: # quantil_calculation == 'total'
        field_for_aggregation_23 = f'{classification_filter}23'
        classification_map_23 = {label: label for label in base_classification_labels}
        aggregated_data_list_23 = list(queryset.values('id', 'populacao23', 'rc_23_pc', field_for_aggregation_23))


    # --- Lógica para o ano 2000 ---
    aggregated_data_list_00 = []
    field_for_aggregation_00 = ''
    classification_map_00 = {} 

    if quantil_calculation == 'por_filtro':
        municipios_raw_data_00 = list(queryset.values('id', 'populacao00', 'rc_00_pc'))
        rc_values_00 = np.array([muni['rc_00_pc'] for muni in municipios_raw_data_00 if muni.get('rc_00_pc') is not None])
        
        if len(rc_values_00) > 0:
            field_for_aggregation_00 = 'dynamic_quantile_val'
            classification_map_00 = {i + 1: base_classification_labels[i] for i in range(num_quantiles)}
            
            quantiles_to_calculate = np.linspace(0, 1, num_quantiles + 1)[1:-1]
            quantile_boundaries_00 = np.quantile(rc_values_00, quantiles_to_calculate)
            
            for muni in municipios_raw_data_00:
                if muni.get('rc_00_pc') is not None:
                    quantile_group_idx = np.searchsorted(quantile_boundaries_00, muni['rc_00_pc'])
                    muni[field_for_aggregation_00] = int(quantile_group_idx + 1)
                else:
                    muni[field_for_aggregation_00] = None
                aggregated_data_list_00.append(muni)
        else:
            # Fallback para o modo 'total' se não houver dados para recalcular
            field_for_aggregation_00 = f'{classification_filter}00'
            classification_map_00 = {label: label for label in base_classification_labels}
            aggregated_data_list_00 = list(queryset.values('id', 'populacao00', 'rc_00_pc', field_for_aggregation_00))
            
    else: # quantil_calculation == 'total'
        field_for_aggregation_00 = f'{classification_filter}00'
        classification_map_00 = {label: label for label in base_classification_labels}
        aggregated_data_list_00 = list(queryset.values('id', 'populacao00', 'rc_00_pc', field_for_aggregation_00))


    # 3. CÁLCULO DOS CARDS DE RESUMO
    # ======================================================================
    total_municipios = queryset.count()
    media_receita_per_capita = queryset.aggregate(Avg('rc_23_pc'))['rc_23_pc__avg'] or 0
    coeficiente_de_variacao= queryset.aggregate(std_dev_rc_23_pc=StdDev('rc_23_pc'))['std_dev_rc_23_pc']/media_receita_per_capita or 0
    
    # Use queries para garantir que as bases nacionais sejam dinâmicas e corretas
    nacional_total_municipios_base = Municipio.objects.all().count()
    nacional_media_receita_per_capita_base = Municipio.objects.all().aggregate(Avg('rc_23_pc'))['rc_23_pc__avg']
    
    gini_index = 0.202 # Valor de exemplo (Substitua por um cálculo real se tiver)
    perc_municipios_selecao = (total_municipios / nacional_total_municipios_base * 100) if nacional_total_municipios_base > 0 else 0
    diff_media_nacional = ((media_receita_per_capita - nacional_media_receita_per_capita_base) / nacional_media_receita_per_capita_base * 100) if nacional_media_receita_per_capita_base > 0 else 0

    # 4. PREPARAÇÃO DOS DADOS DO GRÁFICO
    # ======================================================================
    # Lógica para 2023
    total_pop_for_chart_percentage_23 = sum(item.get('populacao23', 0) for item in aggregated_data_list_23)
    chart_y_axis_label = 'População (milhões)'
    chart_value_multiplier_23 = 1_000_000
    if display_format == 'porcentagem':
        chart_y_axis_label = 'População (%)'
        chart_value_multiplier_23 = total_pop_for_chart_percentage_23 / 100 if total_pop_for_chart_percentage_23 > 0 else 1

    pop_by_group_23 = defaultdict(int)
    for item in aggregated_data_list_23:
        key = item.get(field_for_aggregation_23)
        label = classification_map_23.get(key)
        if label:
            pop_by_group_23[label] += item.get('populacao23', 0)
    
    chart_labels = list(classification_map_23.values())
    chart_data_values_23 = [
        (pop_by_group_23.get(label, 0) / chart_value_multiplier_23) if chart_value_multiplier_23 != 0 else 0
        for label in chart_labels
    ]
    
    # Lógica para 2000
    chart_data_values_00 = []
    if include_2000_data:
        total_pop_for_chart_percentage_00 = sum(item.get('populacao00', 0) for item in aggregated_data_list_00)
        chart_value_multiplier_00 = 1_000_000 
        if display_format == 'porcentagem':
            chart_value_multiplier_00 = total_pop_for_chart_percentage_00 / 100 if total_pop_for_chart_percentage_00 > 0 else 1

        pop_by_group_00 = defaultdict(int)
        for item in aggregated_data_list_00:
            key = item.get(field_for_aggregation_00)
            label_00 = classification_map_00.get(key)
            if label_00:
                pop_by_group_00[label_00] += item.get('populacao00', 0)
        
        chart_data_values_00 = [
            (pop_by_group_00.get(label, 0) / chart_value_multiplier_00) if chart_value_multiplier_00 != 0 else 0
            for label in chart_labels
        ]

    # 5. PREPARAÇÃO DOS DADOS DA TABELA DINÂMICA
    # ======================================================================
    population_ranges = [
        ('Até 5 mil', 0, 5000), ('5 mil a 10 mil', 5000, 10000), ('10 mil a 20 mil', 10000, 20000),
        ('20 mil a 50 mil', 20000, 50000), ('50 mil a 100 mil', 50000, 100000),
        ('100 mil a 200 mil', 100000, 200000), ('200 mil a 500 mil', 200000, 500000),
        ('Acima de 500 mil', 500000, float('inf')),
    ]
    
    classification_columns = list(classification_map_23.values())

    # --- Tabela para 2023 ---
    table_data_23 = []
    raw_grand_total_classification_counts_23 = defaultdict(int)

    for range_label, min_pop, max_pop in population_ranges:
        row_data = {'Faixas': range_label}
        
        range_data_23_filtered = [
            m for m in aggregated_data_list_23
            if m.get('populacao23') is not None and min_pop <= m['populacao23'] < max_pop
        ]
        if max_pop == float('inf'):
             range_data_23_filtered = [
                m for m in aggregated_data_list_23
                if m.get('populacao23') is not None and m['populacao23'] >= min_pop
            ]

        raw_counts_in_row_23 = defaultdict(int)
        for muni in range_data_23_filtered:
            classification_key = muni.get(field_for_aggregation_23)
            column_label = classification_map_23.get(classification_key)
            if column_label:
                raw_counts_in_row_23[column_label] += 1
        
        current_range_total_raw_23 = len(range_data_23_filtered)

        for col_label in classification_columns:
            val = raw_counts_in_row_23.get(col_label, 0)
            if display_format == 'porcentagem':
                row_data[col_label] = f"{(val / current_range_total_raw_23 * 100):.1f}%" if current_range_total_raw_23 > 0 else "0.0%"
            else:
                row_data[col_label] = val
            raw_grand_total_classification_counts_23[col_label] += val

        row_data['Total'] = f"100.0%" if display_format == 'porcentagem' else current_range_total_raw_23
        table_data_23.append(row_data)

    grand_total_row_23 = {'Faixas': 'Total Geral'}
    raw_grand_total_rows_total_23 = sum(raw_grand_total_classification_counts_23.values())
    total_municipios_for_table_23 = len(aggregated_data_list_23)

    for col_label in classification_columns:
        count = raw_grand_total_classification_counts_23.get(col_label, 0)
        if display_format == 'porcentagem':
            grand_total_row_23[col_label] = f"{(count / total_municipios_for_table_23 * 100):.1f}%" if total_municipios_for_table_23 > 0 else "0.0%"
        else:
            grand_total_row_23[col_label] = count

    grand_total_row_23['Total'] = "100.0%" if display_format == 'porcentagem' else raw_grand_total_rows_total_23
    table_data_23.append(grand_total_row_23)
    
    table_headers_23 = ['Faixas'] + classification_columns + ['Total']


    # --- Tabela para 2000 (Calculada apenas se include_2000_data é True) ---
    table_data_00 = []
    table_headers_00 = []

    if include_2000_data:
        raw_grand_total_classification_counts_00 = defaultdict(int)

        for range_label, min_pop, max_pop in population_ranges:
            row_data = {'Faixas': range_label}
            
            range_data_00_filtered = [
                m for m in aggregated_data_list_00
                if m.get('populacao00') is not None and min_pop <= m['populacao00'] < max_pop
            ]
            if max_pop == float('inf'):
                range_data_00_filtered = [
                    m for m in aggregated_data_list_00
                    if m.get('populacao00') is not None and m['populacao00'] >= min_pop
                ]

            raw_counts_in_row_00 = defaultdict(int)
            for muni in range_data_00_filtered:
                classification_key = muni.get(field_for_aggregation_00)
                column_label = classification_map_00.get(classification_key)
                if column_label:
                    raw_counts_in_row_00[column_label] += 1
            
            current_range_total_raw_00 = len(range_data_00_filtered)

            for col_label in classification_columns: # Use as mesmas colunas de classificação
                val = raw_counts_in_row_00.get(col_label, 0)
                if display_format == 'porcentagem':
                    row_data[col_label] = f"{(val / current_range_total_raw_00 * 100):.1f}%" if current_range_total_raw_00 > 0 else "0.0%"
                else:
                    row_data[col_label] = val
                raw_grand_total_classification_counts_00[col_label] += val

            row_data['Total'] = f"100.0%" if display_format == 'porcentagem' else current_range_total_raw_00
            table_data_00.append(row_data)

        grand_total_row_00 = {'Faixas': 'Total Geral'}
        raw_grand_total_rows_total_00 = sum(raw_grand_total_classification_counts_00.values())
        total_municipios_for_table_00 = len(aggregated_data_list_00)

        for col_label in classification_columns:
            count = raw_grand_total_classification_counts_00.get(col_label, 0)
            if display_format == 'porcentagem':
                grand_total_row_00[col_label] = f"{(count / total_municipios_for_table_00 * 100):.1f}%" if total_municipios_for_table_00 > 0 else "0.0%"
            else:
                grand_total_row_00[col_label] = count

        grand_total_row_00['Total'] = "100.0%" if display_format == 'porcentagem' else raw_grand_total_rows_total_00
        table_data_00.append(grand_total_row_00)
        
        table_headers_00 = ['Faixas'] + classification_columns + ['Total']


    # 6. MONTAGEM DA RESPOSTA JSON FINAL
    # ======================================================================
    datasets_to_send = [
        {
            "label": chart_y_axis_label + ' (2023)',
            "data": chart_data_values_23,
        }
    ]

    if include_2000_data:
        datasets_to_send.append({
            "label": chart_y_axis_label + ' (2000)',
            "data": chart_data_values_00,
        })

    response_data = {
        "summaryCards": {
            "totalMunicipios": total_municipios,
            "percTotalMunicipios": round(perc_municipios_selecao, 1),
            "mediaReceitaPerCapita": round(media_receita_per_capita, 2),
            "diffMediaNacional": round(diff_media_nacional, 2),
            "giniIndex": round(coeficiente_de_variacao*100, 2)
        },
        "chartData": {
            "labels": chart_labels,
            "datasets": datasets_to_send,
            "yAxisTitle": chart_y_axis_label,
            "xAxisTitle": classification_filter.capitalize()
        },
        "tableData23": table_data_23, 
        "tableHeaders23": table_headers_23, 
    }

    if include_2000_data:
        response_data["tableData00"] = table_data_00
        response_data["tableHeaders00"] = table_headers_00

    return JsonResponse(response_data)

