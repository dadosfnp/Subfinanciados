from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, StdDev
from django.http import JsonResponse
from .models import Municipio, ContaDetalhada, Noticia 
import numpy as np
import math
from collections import defaultdict

# --- VIEW DASHBOARD ---
def home(request):
    """
    Renderiza o template HTML para a visualização dos gráficos (Dashboard).
    """
    return render(request, 'home/home.html')

# --- VIEW LANDING PAGE ---
def index(request):
    """
    Renderiza a Landing Page (IFEM) e carrega as notícias.
    """
    # Busca as notícias cadastradas no Admin
    noticias = Noticia.objects.all().order_by('-data')
    # ATENÇÃO: Verifique se o arquivo está na pasta templates/ifem/index.html
    return render(request, 'ifem/index.html', {'noticias': noticias})

# --- FUNÇÕES DE API (MANTIDAS IGUAIS) ---
def api_get_dependent_filters(request):
    regiao_selecionada = request.GET.get('regiao')
    uf_selecionada = request.GET.get('uf')
    rm_selecionada = request.GET.get('rm')
    queryset = Municipio.objects.all()

    if rm_selecionada and rm_selecionada != 'todos':
        queryset = queryset.filter(rm__nome=rm_selecionada)
    if regiao_selecionada and regiao_selecionada != 'todos':
        queryset = queryset.filter(regiao=regiao_selecionada)
    if uf_selecionada and uf_selecionada != 'todos':
        queryset = queryset.filter(uf=uf_selecionada)

    regioes = queryset.values_list('regiao', flat=True).distinct().order_by('regiao')
    ufs = queryset.values_list('uf', flat=True).distinct().order_by('uf')
    municipios = queryset.values_list('name_muni_uf', flat=True).distinct().order_by('name_muni_uf')
    rms = queryset.exclude(rm=None).values_list('rm__nome', flat=True).distinct().order_by('rm__nome')

    return JsonResponse({
        'regioes': list(regioes),
        'ufs': list(ufs),
        'municipios': list(municipios),
        'rms': list(rms)
    })

def api_get_dashboard_data(request):
    queryset = Municipio.objects.all()
    regiao_filtro = request.GET.get('regiao')
    uf_filtro = request.GET.get('uf')
    rm_filtro = request.GET.get('rm')
    porte_filtro = request.GET.get('porte')
    classification_filter = request.GET.get('classification', 'quintil')
    display_format = request.GET.get('display_format', 'numero')
    quantil_calculation = request.GET.get('calculation_mode', 'total')
    include_2000_data_str = request.GET.get('include_2000_data', 'false')
    include_2000_data = (include_2000_data_str.lower() == 'true')
    
    if regiao_filtro and regiao_filtro != 'todos':
        queryset = queryset.filter(regiao=regiao_filtro)
    if uf_filtro and uf_filtro != 'todos':
        queryset = queryset.filter(uf=uf_filtro)
    if rm_filtro and rm_filtro != 'todos':
        queryset = queryset.filter(rm__nome=rm_filtro)

    # --- NOVO: Filtragem de Porte Populacional ---
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

    if classification_filter == 'quintil':
        num_quantiles = 5
    elif classification_filter == 'decil':
        num_quantiles = 10
    else:
        classification_filter = 'quintil'
        num_quantiles = 5

    base_classification_labels = [f'{i+1}º {classification_filter}' for i in range(num_quantiles)]

    # --- Lógica 2024 ---
    aggregated_data_list_24 = []
    field_for_aggregation_24 = ''
    classification_map_24 = {}

    if quantil_calculation == 'por_filtro':
        municipios_raw_data_24 = list(queryset.values('id', 'populacao24', 'rc_24_pc'))
        rc_values_24 = np.array([muni['rc_24_pc'] for muni in municipios_raw_data_24 if muni.get('rc_24_pc') is not None])
        
        if len(rc_values_24) > 0:
            field_for_aggregation_24 = 'dynamic_quantile_val'
            classification_map_24 = {i + 1: base_classification_labels[i] for i in range(num_quantiles)}
            quantiles_to_calculate = np.linspace(0, 1, num_quantiles + 1)[1:-1]
            quantile_boundaries = np.quantile(rc_values_24, quantiles_to_calculate)
            for muni in municipios_raw_data_24:
                if muni.get('rc_24_pc') is not None:
                    quantile_group_idx = np.searchsorted(quantile_boundaries, muni['rc_24_pc'])
                    muni[field_for_aggregation_24] = int(quantile_group_idx + 1)
                else:
                    muni[field_for_aggregation_24] = None
                aggregated_data_list_24.append(muni)
        else:
            field_for_aggregation_24 = f'{classification_filter}24'
            classification_map_24 = {label: label for label in base_classification_labels}
            aggregated_data_list_24 = list(queryset.values('id', 'populacao24', 'rc_24_pc', field_for_aggregation_24))
    else:
        field_for_aggregation_24 = f'{classification_filter}24'
        classification_map_24 = {label: label for label in base_classification_labels}
        aggregated_data_list_24 = list(queryset.values('id', 'populacao24', 'rc_24_pc', field_for_aggregation_24))

    # --- Lógica 2000 ---
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
            field_for_aggregation_00 = f'{classification_filter}00'
            classification_map_00 = {label: label for label in base_classification_labels}
            aggregated_data_list_00 = list(queryset.values('id', 'populacao00', 'rc_00_pc', field_for_aggregation_00))
    else:
        field_for_aggregation_00 = f'{classification_filter}00'
        classification_map_00 = {label: label for label in base_classification_labels}
        aggregated_data_list_00 = list(queryset.values('id', 'populacao00', 'rc_00_pc', field_for_aggregation_00))

    # --- Resumo e Gráficos (Mantido igual) ---
    total_municipios = queryset.count()
    media_receita_per_capita = queryset.aggregate(Avg('rc_24_pc'))['rc_24_pc__avg'] or 0
    coeficiente_de_variacao= queryset.aggregate(std_dev_rc_24_pc=StdDev('rc_24_pc'))['std_dev_rc_24_pc']/media_receita_per_capita or 0
    
    nacional_total_municipios_base = Municipio.objects.all().count()
    nacional_media_receita_per_capita_base = Municipio.objects.all().aggregate(Avg('rc_24_pc'))['rc_24_pc__avg']
    gini_index = 0.202 
    perc_municipios_selecao = (total_municipios / nacional_total_municipios_base * 100) if nacional_total_municipios_base > 0 else 0
    diff_media_nacional = ((media_receita_per_capita - nacional_media_receita_per_capita_base) / nacional_media_receita_per_capita_base * 100) if nacional_media_receita_per_capita_base > 0 else 0

    total_pop_for_chart_percentage_24 = sum(item.get('populacao24', 0) for item in aggregated_data_list_24)
    chart_y_axis_label = 'População (milhões)'
    chart_value_multiplier_24 = 1_000_000
    if display_format == 'porcentagem':
        chart_y_axis_label = 'População (%)'
        chart_value_multiplier_24 = total_pop_for_chart_percentage_24 / 100 if total_pop_for_chart_percentage_24 > 0 else 1

    pop_by_group_24 = defaultdict(int)
    for item in aggregated_data_list_24:
        key = item.get(field_for_aggregation_24)
        label = classification_map_24.get(key)
        if label:
            pop_by_group_24[label] += item.get('populacao24', 0)
    
    chart_labels = list(classification_map_24.values())
    chart_data_values_24 = [
        (pop_by_group_24.get(label, 0) / chart_value_multiplier_24) if chart_value_multiplier_24 != 0 else 0
        for label in chart_labels
    ]
    
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

    # --- Tabela Dinâmica ---
    population_ranges = [
        ('Até 5 mil', 0, 5000), ('5 mil a 10 mil', 5000, 10000), ('10 mil a 20 mil', 10000, 20000),
        ('20 mil a 50 mil', 20000, 50000), ('50 mil a 100 mil', 50000, 100000),
        ('100 mil a 200 mil', 100000, 200000), ('200 mil a 500 mil', 200000, 500000),
        ('Acima de 500 mil', 500000, float('inf')),
    ]
    classification_columns = list(classification_map_24.values())

    table_data_24 = []
    raw_grand_total_classification_counts_24 = defaultdict(int)

    for range_label, min_pop, max_pop in population_ranges:
        row_data = {'Faixas': range_label}
        range_data_24_filtered = [m for m in aggregated_data_list_24 if m.get('populacao24') is not None and (min_pop <= m['populacao24'] < max_pop if max_pop != float('inf') else m['populacao24'] >= min_pop)]
        
        raw_counts_in_row_24 = defaultdict(int)
        for muni in range_data_24_filtered:
            classification_key = muni.get(field_for_aggregation_24)
            column_label = classification_map_24.get(classification_key)
            if column_label:
                raw_counts_in_row_24[column_label] += 1
        
        current_range_total_raw_24 = len(range_data_24_filtered)
        for col_label in classification_columns:
            val = raw_counts_in_row_24.get(col_label, 0)
            row_data[col_label] = f"{(val / current_range_total_raw_24 * 100):.1f}%" if display_format == 'porcentagem' and current_range_total_raw_24 > 0 else (val if display_format != 'porcentagem' else "0.0%")
            raw_grand_total_classification_counts_24[col_label] += val

        row_data['Total'] = f"100.0%" if display_format == 'porcentagem' else current_range_total_raw_24
        table_data_24.append(row_data)

    grand_total_row_24 = {'Faixas': 'Total Geral'}
    raw_grand_total_rows_total_24 = sum(raw_grand_total_classification_counts_24.values())
    total_municipios_for_table_24 = len(aggregated_data_list_24)

    for col_label in classification_columns:
        count = raw_grand_total_classification_counts_24.get(col_label, 0)
        grand_total_row_24[col_label] = f"{(count / total_municipios_for_table_24 * 100):.1f}%" if display_format == 'porcentagem' and total_municipios_for_table_24 > 0 else (count if display_format != 'porcentagem' else "0.0%")

    grand_total_row_24['Total'] = "100.0%" if display_format == 'porcentagem' else raw_grand_total_rows_total_24
    table_data_24.append(grand_total_row_24)
    table_headers_24 = ['Faixas'] + classification_columns + ['Total']

    # --- Tabela 2000 ---
    table_data_00 = []
    table_headers_00 = []
    if include_2000_data:
        raw_grand_total_classification_counts_00 = defaultdict(int)
        for range_label, min_pop, max_pop in population_ranges:
            row_data = {'Faixas': range_label}
            range_data_00_filtered = [m for m in aggregated_data_list_00 if m.get('populacao00') is not None and (min_pop <= m['populacao00'] < max_pop if max_pop != float('inf') else m['populacao00'] >= min_pop)]
            
            raw_counts_in_row_00 = defaultdict(int)
            for muni in range_data_00_filtered:
                classification_key = muni.get(field_for_aggregation_00)
                column_label = classification_map_00.get(classification_key)
                if column_label:
                    raw_counts_in_row_00[column_label] += 1
            
            current_range_total_raw_00 = len(range_data_00_filtered)
            for col_label in classification_columns:
                val = raw_counts_in_row_00.get(col_label, 0)
                row_data[col_label] = f"{(val / current_range_total_raw_00 * 100):.1f}%" if display_format == 'porcentagem' and current_range_total_raw_00 > 0 else (val if display_format != 'porcentagem' else "0.0%")
                raw_grand_total_classification_counts_00[col_label] += val

            row_data['Total'] = f"100.0%" if display_format == 'porcentagem' else current_range_total_raw_00
            table_data_00.append(row_data)

        grand_total_row_00 = {'Faixas': 'Total Geral'}
        raw_grand_total_rows_total_00 = sum(raw_grand_total_classification_counts_00.values())
        total_municipios_for_table_00 = len(aggregated_data_list_00)

        for col_label in classification_columns:
            count = raw_grand_total_classification_counts_00.get(col_label, 0)
            grand_total_row_00[col_label] = f"{(count / total_municipios_for_table_00 * 100):.1f}%" if display_format == 'porcentagem' and total_municipios_for_table_00 > 0 else (count if display_format != 'porcentagem' else "0.0%")

        grand_total_row_00['Total'] = "100.0%" if display_format == 'porcentagem' else raw_grand_total_rows_total_00
        table_data_00.append(grand_total_row_00)
        table_headers_00 = ['Faixas'] + classification_columns + ['Total']

    datasets_to_send = [{"label": chart_y_axis_label + ' (2024)', "data": chart_data_values_24}]
    if include_2000_data:
        datasets_to_send.append({"label": chart_y_axis_label + ' (2000)', "data": chart_data_values_00})

    response_data = {
        "summaryCards": {
            "totalMunicipios": total_municipios,
            "percTotalMunicipios": round(perc_municipios_selecao, 1),
            "mediaReceitaPerCapita": round(media_receita_per_capita, 2),
            "diffMediaNacional": round(diff_media_nacional, 2),
            "giniIndex": round(coeficiente_de_variacao*100, 2)
        },
        "chartData": {"labels": chart_labels, "datasets": datasets_to_send, "yAxisTitle": chart_y_axis_label, "xAxisTitle": classification_filter.capitalize()},
        "tableData24": table_data_24, "tableHeaders24": table_headers_24,
    }
    if include_2000_data:
        response_data["tableData00"] = table_data_00
        response_data["tableHeaders00"] = table_headers_00

    return JsonResponse(response_data)