# home/views.py - v1.0.4 - Ajustes robustos de Classificação e Mapa
import re
from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, Count
from django.http import JsonResponse
from django.db import connection
from home.models import Municipio, ContaDetalhada, Noticia
import numpy as np
import math
from collections import defaultdict


def _format_brl(value):
    """Formata float para 'R$ 1.234' (sem decimais, separador BR)."""
    if value is None:
        return '—'
    return 'R$ ' + f'{int(round(value)):,}'.replace(',', '.')


def _num_classe(valor):
    """Extrai o número de uma classe textual como '3º quintil' ou '7º decil'."""
    if not valor:
        return None
    m = re.search(r'(\d+)', str(valor))
    return int(m.group(1)) if m else None


def _cresc_pct(novo, velho):
    """Variação percentual de `velho` para `novo`, arredondada a 1 casa."""
    if novo is None or velho is None or velho == 0:
        return None
    return round((novo - velho) / velho * 100, 1)


def _medias_por_grupo(field, prefix):
    qs = (Municipio.objects
          .exclude(**{f'{field}__isnull': True})
          .exclude(dados_atuais__rc_atual_pc__isnull=True)
          .values(field)
          .annotate(media=Avg('dados_atuais__rc_atual_pc')))
    out = {}
    for row in qs:
        match = re.match(r'(\d+)', row[field] or '')
        if match:
            out[f'{prefix}{match.group(1)}'] = _format_brl(row['media'])
    return out

# --- VIEWS DE PÁGINAS ---
def home(request):
    return render(request, 'home/home.html')

def map(request):
    return render(request, 'map/map.html')

def index(request):
    noticias = Noticia.objects.all().order_by('-data')
    medias_quintis = _medias_por_grupo('dados_atuais__quintil_atual', 'q')
    medias_decis = _medias_por_grupo('dados_atuais__decil_atual', 'd')
    return render(request, 'ifem/index.html', {
        'noticias': noticias,
        'medias_quintis': medias_quintis,
        'medias_decis': medias_decis,
    })

RISCO_CAMPO = {
    'media_ponderada': 'dados_adapta_brasil__media_ponderada',
    'bio_int_bio': 'dados_adapta_brasil__bio_int_bio',
    'des_des_ter': 'dados_adapta_brasil__des_des_ter',
    'des_in_enx_ala': 'dados_adapta_brasil__des_in_enx_ala',
    'rec_ris_est_hid': 'dados_adapta_brasil__rec_ris_est_hid',
    'sau_arb': 'dados_adapta_brasil__sau_arb',
    'sau_lei_teg_ame': 'dados_adapta_brasil__sau_lei_teg_ame',
    'sau_lei_vis': 'dados_adapta_brasil__sau_lei_vis',
    'sau_mal': 'dados_adapta_brasil__sau_mal',
    'seg_ali_ace_con_ali': 'dados_adapta_brasil__seg_ali_ace_con_ali',
    'seg_ali_dis': 'dados_adapta_brasil__seg_ali_dis',
    'seg_ene_ace': 'dados_adapta_brasil__seg_ene_ace',
    'seg_ene_dis': 'dados_adapta_brasil__seg_ene_dis',
}

def filtrar_risco_climatico(queryset, request):
    risco_campo = request.GET.get('risco_campo') or request.GET.get('risco_climatico_indicador')
    risco_intensidade = request.GET.get('risco_intensidade') or request.GET.get('risco_climatico') or request.GET.get('riscos_climaticos')

    campo_db = RISCO_CAMPO.get(risco_campo, 'dados_adapta_brasil__media_ponderada')

    if risco_intensidade and risco_intensidade != 'todos':
        if risco_intensidade == 'muito_baixo':
            queryset = queryset.filter(**{f'{campo_db}__gte': 0, f'{campo_db}__lt': 0.2})
        elif risco_intensidade == 'baixo':
            queryset = queryset.filter(**{f'{campo_db}__gte': 0.2, f'{campo_db}__lt': 0.4})
        elif risco_intensidade == 'medio':
            queryset = queryset.filter(**{f'{campo_db}__gte': 0.4, f'{campo_db}__lt': 0.6})
        elif risco_intensidade == 'alto':
            queryset = queryset.filter(**{f'{campo_db}__gte': 0.6, f'{campo_db}__lt': 0.8})
        elif risco_intensidade == 'muito_alto':
            queryset = queryset.filter(**{f'{campo_db}__gte': 0.8})
    elif risco_campo and risco_campo != 'todos' and risco_campo in RISCO_CAMPO:
        queryset = queryset.filter(**{f'{campo_db}__isnull': False})

    return queryset

# --- FUNÇÕES DE API ---
def api_get_dependent_filters(request):
    regiao_selecionada = request.GET.get('regiao')
    uf_selecionada = request.GET.get('uf')
    rm_selecionada = request.GET.get('rm')
    porte_filtro = request.GET.get('porte')
    subgroup_filter = request.GET.get('subgrupo')
    capag_filtro = request.GET.get('capag')
    risco_filtro = request.GET.get('risco_climatico')
    classification_filter = request.GET.get('classification', 'quintil')
    quantil_calculation = request.GET.get('calculation_mode', 'total')

    queryset = Municipio.objects.exclude(dados_atuais__rc_atual_pc__isnull=True)

    if rm_selecionada and rm_selecionada != 'todos':
        queryset = queryset.filter(rm__nome=rm_selecionada)
    if regiao_selecionada and regiao_selecionada != 'todos':
        queryset = queryset.filter(regiao=regiao_selecionada)
    if uf_selecionada and uf_selecionada != 'todos':
        queryset = queryset.filter(uf=uf_selecionada)
    if capag_filtro and capag_filtro != 'todos':
        queryset = queryset.filter(dados_atuais__capag=capag_filtro)
    queryset = filtrar_risco_climatico(queryset, request)

    # Porte populacional
    if porte_filtro and porte_filtro != 'todos':
        if porte_filtro == 'Até 5 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__lt=5000)
        elif porte_filtro == '5 mil a 10 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__gte=5000, dados_atuais__populacao_atual__lt=10000)
        elif porte_filtro == '10 mil a 20 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__gte=10000, dados_atuais__populacao_atual__lt=20000)
        elif porte_filtro == '20 mil a 50 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__gte=20000, dados_atuais__populacao_atual__lt=50000)
        elif porte_filtro == '50 mil a 100 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__gte=50000, dados_atuais__populacao_atual__lt=100000)
        elif porte_filtro == '100 mil a 200 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__gte=100000, dados_atuais__populacao_atual__lt=200000)
        elif porte_filtro == '200 mil a 500 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__gte=200000, dados_atuais__populacao_atual__lt=500000)
        elif porte_filtro == 'Acima de 500 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__gte=500000)
        elif porte_filtro == 'Acima de 80 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__gt=80000)
        elif porte_filtro == 'Abaixo de 80 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__lte=80000)

    # Subgrupo
    if subgroup_filter and subgroup_filter != 'todos':
        if quantil_calculation == 'por_filtro' and classification_filter in ('quintil', 'decil'):
            num_quantiles = 5 if classification_filter == 'quintil' else 10
            rc_values = np.array([
                m['dados_atuais__rc_atual_pc']
                for m in queryset.values('dados_atuais__rc_atual_pc')
                if m.get('dados_atuais__rc_atual_pc') is not None
            ])
            if len(rc_values) > 0:
                try:
                    target_idx = int(subgroup_filter) - 1
                    if 0 <= target_idx < num_quantiles:
                        bounds = np.quantile(
                            rc_values,
                            np.linspace(0, 1, num_quantiles + 1)[1:-1]
                        )
                        min_val = bounds[target_idx - 1] if target_idx > 0 else None
                        max_val = bounds[target_idx] if target_idx < num_quantiles - 1 else None
                        if min_val is None:
                            queryset = queryset.filter(dados_atuais__rc_atual_pc__lt=max_val)
                        elif max_val is None:
                            queryset = queryset.filter(dados_atuais__rc_atual_pc__gte=min_val)
                        else:
                            queryset = queryset.filter(dados_atuais__rc_atual_pc__gte=min_val, dados_atuais__rc_atual_pc__lt=max_val)
                except ValueError:
                    pass
        elif classification_filter == 'quintil':
            queryset = queryset.filter(dados_atuais__quintil_atual__icontains=f'{subgroup_filter}')
        elif classification_filter == 'decil':
            queryset = queryset.filter(dados_atuais__decil_atual__icontains=f'{subgroup_filter}')
        elif classification_filter == 'natural':
            try:
                min_str, max_str = subgroup_filter.split('-')
                min_val = int(min_str)
                if max_str.lower() == '999999':
                    queryset = queryset.filter(dados_atuais__rc_atual_pc__gte=min_val)
                else:
                    max_val = int(max_str)
                    queryset = queryset.filter(dados_atuais__rc_atual_pc__gte=min_val, dados_atuais__rc_atual_pc__lt=max_val)
            except ValueError:
                pass

    regioes = queryset.values_list('regiao', flat=True).distinct().order_by('regiao')
    ufs = queryset.values_list('uf', flat=True).distinct().order_by('uf')
    municipios = queryset.values_list('name_muni_uf', flat=True).distinct().order_by('name_muni_uf')
    rms = queryset.exclude(rm=None).values_list('rm__nome', flat=True).distinct().order_by('rm__nome')
    capags = queryset.exclude(dados_atuais__capag__isnull=True).values_list('dados_atuais__capag', flat=True).distinct().order_by('dados_atuais__capag')

    return JsonResponse({
        'regioes': list(regioes),
        'ufs': list(ufs),
        'municipios': list(municipios),
        'rms': list(rms),
        'capags': list(capags)
    })

def api_get_dashboard_data(request):
    queryset = Municipio.objects.all()
    regiao_filtro = request.GET.get('regiao')
    uf_filtro = request.GET.get('uf')
    rm_filtro = request.GET.get('rm')
    capag_filtro = request.GET.get('capag')
    riscos_filtro = request.GET.get('riscos_climaticos')
    porte_filtro = request.GET.get('porte')
    classification_filter = request.GET.get('classification', 'quintil')
    display_format = request.GET.get('display_format', 'numero')
    quantil_calculation = request.GET.get('calculation_mode', 'total')
    include_2000_data = (request.GET.get('include_2000_data', 'false').lower() == 'true')
    
    if regiao_filtro and regiao_filtro != 'todos':
        queryset = queryset.filter(regiao=regiao_filtro)
    if uf_filtro and uf_filtro != 'todos':
        queryset = queryset.filter(uf=uf_filtro)
    if rm_filtro and rm_filtro != 'todos':
        queryset = queryset.filter(rm__nome=rm_filtro)
    if capag_filtro and capag_filtro != 'todos':
        queryset = queryset.filter(dados_atuais__capag=capag_filtro)
        
    queryset = filtrar_risco_climatico(queryset, request)

    if porte_filtro and porte_filtro != 'todos':
        if porte_filtro == 'Até 5 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__lt=5000)
        elif porte_filtro == '5 mil a 10 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__gte=5000, dados_atuais__populacao_atual__lt=10000)
        elif porte_filtro == '10 mil a 20 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__gte=10000, dados_atuais__populacao_atual__lt=20000)
        elif porte_filtro == '20 mil a 50 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__gte=20000, dados_atuais__populacao_atual__lt=50000)
        elif porte_filtro == '50 mil a 100 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__gte=50000, dados_atuais__populacao_atual__lt=100000)
        elif porte_filtro == '100 mil a 200 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__gte=100000, dados_atuais__populacao_atual__lt=200000)
        elif porte_filtro == '200 mil a 500 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__gte=200000, dados_atuais__populacao_atual__lt=500000)
        elif porte_filtro == 'Acima de 500 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__gte=500000)
        elif porte_filtro == 'Acima de 80 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__gt=80000)
        elif porte_filtro == 'Abaixo de 80 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__lte=80000)

    num_quantiles = 5 if classification_filter == 'quintil' else 10
    base_classification_labels = [f'{i+1}º {classification_filter}' for i in range(num_quantiles)]
    
    # Dicionário à prova de falhas: Mapeia um número inteiro para o rótulo ideal do eixo
    classification_map = {i + 1: base_classification_labels[i] for i in range(num_quantiles)}

    try:
        # --- Lógica 2024 (dados_atuais) ---
        aggregated_data_list_24 = []
        field_for_aggregation_24 = ''

        if quantil_calculation == 'por_filtro':
            municipios_raw_data_24 = list(queryset.values('cod_ibge', 'dados_atuais__populacao_atual', 'dados_atuais__rc_atual_pc'))
            rc_values_24 = np.array([m['dados_atuais__rc_atual_pc'] for m in municipios_raw_data_24 if m.get('dados_atuais__rc_atual_pc') is not None])
            
            if len(rc_values_24) > 0:
                field_for_aggregation_24 = 'dynamic_quantile_val'
                quantiles_to_calculate = np.linspace(0, 1, num_quantiles + 1)[1:-1]
                quantile_boundaries = np.quantile(rc_values_24, quantiles_to_calculate)
                for muni in municipios_raw_data_24:
                    if muni.get('dados_atuais__rc_atual_pc') is not None:
                        quantile_group_idx = np.searchsorted(quantile_boundaries, muni['dados_atuais__rc_atual_pc'])
                        muni[field_for_aggregation_24] = int(quantile_group_idx + 1)
                    else:
                        muni[field_for_aggregation_24] = None
                    aggregated_data_list_24.append(muni)
            else:
                field_for_aggregation_24 = f'dados_atuais__{classification_filter}_atual'
                aggregated_data_list_24 = list(queryset.values('cod_ibge', 'dados_atuais__populacao_atual', 'dados_atuais__rc_atual_pc', field_for_aggregation_24))
        else:
            field_for_aggregation_24 = f'dados_atuais__{classification_filter}_atual'
            aggregated_data_list_24 = list(queryset.values('cod_ibge', 'dados_atuais__populacao_atual', 'dados_atuais__rc_atual_pc', field_for_aggregation_24))

        # --- Lógica 2000 (dados_2000) ---
        aggregated_data_list_00 = []
        field_for_aggregation_00 = ''

        if include_2000_data:
            if quantil_calculation == 'por_filtro':
                municipios_raw_data_00 = list(queryset.values('cod_ibge', 'dados_2000__populacao_00', 'dados_2000__rc_00_pc'))
                rc_values_00 = np.array([m['dados_2000__rc_00_pc'] for m in municipios_raw_data_00 if m.get('dados_2000__rc_00_pc') is not None])
                if len(rc_values_00) > 0:
                    field_for_aggregation_00 = 'dynamic_quantile_val'
                    quantiles_to_calculate = np.linspace(0, 1, num_quantiles + 1)[1:-1]
                    quantile_boundaries_00 = np.quantile(rc_values_00, quantiles_to_calculate)
                    for muni in municipios_raw_data_00:
                        if muni.get('dados_2000__rc_00_pc') is not None:
                            quantile_group_idx = np.searchsorted(quantile_boundaries_00, muni['dados_2000__rc_00_pc'])
                            muni[field_for_aggregation_00] = int(quantile_group_idx + 1)
                        else:
                            muni[field_for_aggregation_00] = None
                        aggregated_data_list_00.append(muni)
                else:
                    field_for_aggregation_00 = f'dados_2000__{classification_filter}_00'
                    aggregated_data_list_00 = list(queryset.values('cod_ibge', 'dados_2000__populacao_00', 'dados_2000__rc_00_pc', field_for_aggregation_00))
            else:
                field_for_aggregation_00 = f'dados_2000__{classification_filter}_00'
                aggregated_data_list_00 = list(queryset.values('cod_ibge', 'dados_2000__populacao_00', 'dados_2000__rc_00_pc', field_for_aggregation_00))

        # --- Resumo e Gráficos ---
        total_municipios = queryset.count()
        media_receita_per_capita = queryset.aggregate(Avg('dados_atuais__rc_atual_pc'))['dados_atuais__rc_atual_pc__avg'] or 0
        
        rc_values_for_std = list(queryset.values_list('dados_atuais__rc_atual_pc', flat=True))
        rc_values_for_std = [v for v in rc_values_for_std if v is not None]
        std_dev_res = np.std(rc_values_for_std) if rc_values_for_std else 0
        
        coeficiente_de_variacao = 0
        if media_receita_per_capita > 0:
            coeficiente_de_variacao = std_dev_res / media_receita_per_capita
        
        _nacional_stats = Municipio.objects.aggregate(total=Count('cod_ibge'), media_rc=Avg('dados_atuais__rc_atual_pc'))
        nacional_total_municipios_base = _nacional_stats['total'] or 0
        nacional_media_receita_per_capita_base = _nacional_stats['media_rc'] or 1
        gini_index = 0.202 
        perc_municipios_selecao = (total_municipios / nacional_total_municipios_base * 100) if nacional_total_municipios_base > 0 else 0
        diff_media_nacional = ((media_receita_per_capita - nacional_media_receita_per_capita_base) / nacional_media_receita_per_capita_base * 100) if nacional_media_receita_per_capita_base > 0 else 0

        total_pop_for_chart_percentage_24 = sum(item.get('dados_atuais__populacao_atual', 0) for item in aggregated_data_list_24 if item.get('dados_atuais__populacao_atual') is not None)
        chart_y_axis_label = 'População (milhões)'
        chart_value_multiplier_24 = 1_000_000
        if display_format == 'porcentagem':
            chart_y_axis_label = 'População (%)'
            chart_value_multiplier_24 = total_pop_for_chart_percentage_24 / 100 if total_pop_for_chart_percentage_24 > 0 else 1

        pop_by_group_24 = defaultdict(int)
        for item in aggregated_data_list_24:
            val = item.get(field_for_aggregation_24)
            idx = _num_classe(val) # Transforma qualquer variação em um simples INT
            label = classification_map.get(idx)
            if label:
                pop_by_group_24[label] += item.get('dados_atuais__populacao_atual', 0) if item.get('dados_atuais__populacao_atual') is not None else 0
        
        chart_labels = list(classification_map.values())
        chart_data_values_24 = [
            (pop_by_group_24.get(label, 0) / chart_value_multiplier_24) if chart_value_multiplier_24 != 0 else 0
            for label in chart_labels
        ]
        
        chart_data_values_00 = []
        if include_2000_data:
            total_pop_for_chart_percentage_00 = sum(item.get('dados_2000__populacao_00', 0) for item in aggregated_data_list_00 if item.get('dados_2000__populacao_00') is not None)
            chart_value_multiplier_00 = 1_000_000 
            if display_format == 'porcentagem':
                chart_value_multiplier_00 = total_pop_for_chart_percentage_00 / 100 if total_pop_for_chart_percentage_00 > 0 else 1

            pop_by_group_00 = defaultdict(int)
            for item in aggregated_data_list_00:
                val = item.get(field_for_aggregation_00)
                idx = _num_classe(val)
                label_00 = classification_map.get(idx)
                if label_00:
                    pop_by_group_00[label_00] += item.get('dados_2000__populacao_00', 0) if item.get('dados_2000__populacao_00') is not None else 0
            
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
        classification_columns = list(classification_map.values())

        table_data_24 = []
        raw_grand_total_classification_counts_24 = defaultdict(int)

        for range_label, min_pop, max_pop in population_ranges:
            row_data = {'Faixas': range_label}
            range_data_24_filtered = [m for m in aggregated_data_list_24 if m.get('dados_atuais__populacao_atual') is not None and (min_pop <= m['dados_atuais__populacao_atual'] < max_pop if max_pop != float('inf') else m['dados_atuais__populacao_atual'] >= min_pop)]
            
            raw_counts_in_row_24 = defaultdict(int)
            for muni in range_data_24_filtered:
                val = muni.get(field_for_aggregation_24)
                idx = _num_classe(val)
                column_label = classification_map.get(idx)
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
                range_data_00_filtered = [m for m in aggregated_data_list_00 if m.get('dados_2000__populacao_00') is not None and (min_pop <= m['dados_2000__populacao_00'] < max_pop if max_pop != float('inf') else m['dados_2000__populacao_00'] >= min_pop)]
                
                raw_counts_in_row_00 = defaultdict(int)
                for muni in range_data_00_filtered:
                    val = muni.get(field_for_aggregation_00)
                    idx = _num_classe(val)
                    column_label = classification_map.get(idx)
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
    except Exception as e:
        import traceback
        return JsonResponse({"error": str(e), "traceback": traceback.format_exc()}, status=500)


def municipios_geojson_api(request):
    """
    Retorna dados GeoJSON para o Mapa.
    Exclui municípios sem dados de receita atual per capita (rc_atual_pc nulo).
    """
    queryset = Municipio.objects.exclude(dados_atuais__rc_atual_pc__isnull=True)

    uf_filtro = request.GET.get('uf')
    regiao_filtro = request.GET.get('regiao')
    municipio_filtro = request.GET.get('municipio')
    porte_filtro = request.GET.get('porte')
    rm_filtro = request.GET.get('rm')
    capag_filtro = request.GET.get('capag')
    risco_filtro = request.GET.get('risco_climatico')
    classification_filter = request.GET.get('classification', 'quintil')
    quantil_calculation = request.GET.get('calculation_mode', 'total')
    subgroup_filter = request.GET.get('subgrupo')

    if regiao_filtro and regiao_filtro != 'todos':
        queryset = queryset.filter(regiao=regiao_filtro)
    if uf_filtro and uf_filtro != 'todos':
        queryset = queryset.filter(uf=uf_filtro)
    if municipio_filtro and municipio_filtro != 'todos':
        queryset = queryset.filter(name_muni_uf=municipio_filtro)
    if rm_filtro and rm_filtro != 'todos':
        queryset = queryset.filter(rm__nome=rm_filtro)
    if capag_filtro and capag_filtro != 'todos':
        queryset = queryset.filter(dados_atuais__capag=capag_filtro)

    queryset = filtrar_risco_climatico(queryset, request)

    if porte_filtro and porte_filtro != 'todos':
        if porte_filtro == 'Até 5 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__lt=5000)
        elif porte_filtro == '5 mil a 10 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__gte=5000, dados_atuais__populacao_atual__lt=10000)
        elif porte_filtro == '10 mil a 20 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__gte=10000, dados_atuais__populacao_atual__lt=20000)
        elif porte_filtro == '20 mil a 50 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__gte=20000, dados_atuais__populacao_atual__lt=50000)
        elif porte_filtro == '50 mil a 100 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__gte=50000, dados_atuais__populacao_atual__lt=100000)
        elif porte_filtro == '100 mil a 200 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__gte=100000, dados_atuais__populacao_atual__lt=200000)
        elif porte_filtro == '200 mil a 500 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__gte=200000, dados_atuais__populacao_atual__lt=500000)
        elif porte_filtro == 'Acima de 500 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__gte=500000)
        elif porte_filtro == 'Acima de 80 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__gt=80000)
        elif porte_filtro == 'Abaixo de 80 mil':
            queryset = queryset.filter(dados_atuais__populacao_atual__lte=80000)

    num_quantiles = 5 if classification_filter == 'quintil' else 10
    quantile_boundaries = []
    
    if quantil_calculation == 'total':
        base_queryset_for_quantile = Municipio.objects.all()
    else: 
        base_queryset_for_quantile = queryset
    
    rc_values = np.array([
        muni['dados_atuais__rc_atual_pc']
        for muni in base_queryset_for_quantile.values('dados_atuais__rc_atual_pc')
        if muni.get('dados_atuais__rc_atual_pc') is not None
    ])

    if len(rc_values) > 0:
        quantiles_to_calculate = np.linspace(0, 1, num_quantiles + 1)[1:-1]
        quantile_boundaries = np.quantile(rc_values, quantiles_to_calculate)
    
    if subgroup_filter and subgroup_filter != "todos":
        if quantil_calculation == 'por_filtro' and len(rc_values) > 0:
            try:
                target_quantile_idx = int(subgroup_filter) - 1
                if 0 <= target_quantile_idx < num_quantiles:
                    min_val_quantile = quantile_boundaries[target_quantile_idx -1] if target_quantile_idx > 0 else -float('inf')
                    max_val_quantile = quantile_boundaries[target_quantile_idx] if target_quantile_idx < num_quantiles -1 else float('inf')
                    
                    if max_val_quantile == float('inf'):
                        queryset = queryset.filter(dados_atuais__rc_atual_pc__gte=min_val_quantile)
                    elif min_val_quantile == -float('inf'):
                        queryset = queryset.filter(dados_atuais__rc_atual_pc__lt=max_val_quantile)
                    else:
                        queryset = queryset.filter(dados_atuais__rc_atual_pc__gte=min_val_quantile, dados_atuais__rc_atual_pc__lt=max_val_quantile)
            except ValueError:
                pass
        
        elif classification_filter == 'quintil':
            queryset = queryset.filter(dados_atuais__quintil_atual__icontains=f'{subgroup_filter}')
        elif classification_filter == 'decil':
            queryset = queryset.filter(dados_atuais__decil_atual__icontains=f'{subgroup_filter}')
        elif classification_filter == 'natural':
            try:
                min_str, max_str = subgroup_filter.split('-')
                min_val = int(min_str)
                if max_str.lower() == '999999': 
                    queryset = queryset.filter(dados_atuais__rc_atual_pc__gte=min_val)
                else:
                    max_val = int(max_str)
                    queryset = queryset.filter(dados_atuais__rc_atual_pc__gte=min_val, dados_atuais__rc_atual_pc__lt=max_val)
            except ValueError:
                pass

    analise = request.GET.get('analise', 'receita')

    _fields = (
        'cod_ibge', 'name_muni', 'name_muni_uf', 'uf', 'coordx', 'coordy',
        'dados_atuais__populacao_atual', 'dados_atuais__rc_atual_pc', 
        'cadunico__cadunico', 'sus_dependente__sus_dependente', 
        'dados_atuais__capag',
        'dados_atuais__quintil_atual', 'dados_atuais__decil_atual',
        'dados_atuais__percentil_atual', 'dados_atuais__percentil_atual_n', 
        'dados_adapta_brasil__media_ponderada',
        'dados_adapta_brasil__bio_int_bio',
        'dados_adapta_brasil__des_des_ter',
        'dados_adapta_brasil__des_in_enx_ala',
        'dados_adapta_brasil__rec_ris_est_hid',
        'dados_adapta_brasil__sau_arb',
        'dados_adapta_brasil__sau_lei_teg_ame',
        'dados_adapta_brasil__sau_lei_vis',
        'dados_adapta_brasil__sau_mal',
        'dados_adapta_brasil__seg_ali_ace_con_ali',
        'dados_adapta_brasil__seg_ali_dis',
        'dados_adapta_brasil__seg_ene_ace',
        'dados_adapta_brasil__seg_ene_dis',
    )
    if analise == 'crescimento':
        _fields = _fields + (
            'dados_2000__populacao_00', 'dados_2000__rc_00_pc', 
            'dados_2000__quintil_00', 'dados_2000__decil_00', 'dados_2000__percentil_00_n',
            'dados_atuais__rank_nacional', 'dados_2000__rank_nacional_00', 'dados_atuais__total_nacional',
        )

    features = []
    for municipio in queryset.values(*_fields):
        rc = municipio['dados_atuais__rc_atual_pc']
        current_muni_quantile = None
        
        if rc is not None and len(quantile_boundaries) > 0:
            current_muni_quantile = int(np.searchsorted(quantile_boundaries, rc) + 1)
        elif quantil_calculation == 'total':
            if classification_filter == 'quintil':
                current_muni_quantile = _num_classe(municipio['dados_atuais__quintil_atual'])
            elif classification_filter == 'decil':
                current_muni_quantile = _num_classe(municipio['dados_atuais__decil_atual'])

        pop = municipio['dados_atuais__populacao_atual'] or 0
        cadunico = municipio['cadunico__cadunico'] or 0
        perc_cadunico = min((cadunico / pop * 100) if pop > 0 else 0, 100)
        
        riscos_altos = municipio.get('dados_adapta_brasil__media_ponderada') 

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [municipio['coordx'], municipio['coordy']]
            },
            "properties": {
                'cod_ibge': municipio['cod_ibge'],
                'name_muni': municipio['name_muni'],
                'name_muni_uf': municipio['name_muni_uf'],
                'Populacao24': pop,
                'uf': municipio['uf'],
                'rc_24_pc': rc,
                'perc_pop_cadunico': perc_cadunico,
                'sus_dependente': municipio['sus_dependente__sus_dependente'],
                'capag': municipio['dados_atuais__capag'],
                'quintil24_pre_calculado': municipio['dados_atuais__quintil_atual'],
                'decil24_pre_calculado': municipio['dados_atuais__decil_atual'],
                'percentil24': municipio['dados_atuais__percentil_atual'],
                'percentil24_n': municipio['dados_atuais__percentil_atual_n'],
                'dynamic_quantile': current_muni_quantile,
                'riscos_climaticos': riscos_altos,
                'bio_int_bio': municipio.get('dados_adapta_brasil__bio_int_bio'),
                'des_des_ter': municipio.get('dados_adapta_brasil__des_des_ter'),
                'des_in_enx_ala': municipio.get('dados_adapta_brasil__des_in_enx_ala'),
                'rec_ris_est_hid': municipio.get('dados_adapta_brasil__rec_ris_est_hid'),
                'sau_arb': municipio.get('dados_adapta_brasil__sau_arb'),
                'sau_lei_teg_ame': municipio.get('dados_adapta_brasil__sau_lei_teg_ame'),
                'sau_lei_vis': municipio.get('dados_adapta_brasil__sau_lei_vis'),
                'sau_mal': municipio.get('dados_adapta_brasil__sau_mal'),
                'seg_ali_ace_con_ali': municipio.get('dados_adapta_brasil__seg_ali_ace_con_ali'),
                'seg_ali_dis': municipio.get('dados_adapta_brasil__seg_ali_dis'),
                'seg_ene_ace': municipio.get('dados_adapta_brasil__seg_ene_ace'),
                'seg_ene_dis': municipio.get('dados_adapta_brasil__seg_ene_dis'),
            }
        }

        if analise == 'crescimento':
            pop00 = municipio['dados_2000__populacao_00']
            rc00pc = municipio['dados_2000__rc_00_pc']
            q24, q00 = _num_classe(municipio['dados_atuais__quintil_atual']), _num_classe(municipio['dados_2000__quintil_00'])
            d24, d00 = _num_classe(municipio['dados_atuais__decil_atual']), _num_classe(municipio['dados_2000__decil_00'])
            p24n, p00n = municipio['dados_atuais__percentil_atual_n'], municipio['dados_2000__percentil_00_n']
            rk24, rk00 = municipio['dados_atuais__rank_nacional'], municipio['dados_2000__rank_nacional_00']
            
            feature['properties'].update({
                'populacao00': pop00,
                'rc_00_pc': rc00pc,
                'quintil00': municipio['dados_2000__quintil_00'],
                'decil00': municipio['dados_2000__decil_00'],
                'percentil00_n': p00n,
                'rank_nacional': rk24,
                'rank_nacional_00': rk00,
                'total_nacional': municipio['dados_atuais__total_nacional'],
                'cresc_pop_pct': _cresc_pct(pop, pop00),
                'cresc_rcpc_pct': _cresc_pct(rc, rc00pc),
                'var_quintil': (q24 - q00) if (q24 is not None and q00 is not None) else None,
                'var_decil': (d24 - d00) if (d24 is not None and d00 is not None) else None,
                'var_percentil': (p24n - p00n) if (p24n is not None and p00n is not None) else None,
                'var_rank': (rk00 - rk24) if (rk24 is not None and rk00 is not None) else None,
            })

        features.append(feature)

    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }

    return JsonResponse(geojson_data)