# home/views.py - v1.0.3 - Fix SQLite StdDev compatibility
import re
from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, Count, Sum
from django.http import JsonResponse
from django.db import connection
from .models import Municipio, ContaDetalhada, Noticia
import numpy as np
import math
from collections import defaultdict


def _format_brl(value):
    """Formata float para 'R$ 1.234' (sem decimais, separador BR)."""
    if value is None:
        return '—'
    return 'R$ ' + f'{int(round(value)):,}'.replace(',', '.')


def _medias_por_grupo(field, prefix):
    """
    Agrega Avg(rc_atual_pc) por quintil/decil e devolve dict
    {<prefix><n>: 'R$ X.XXX'} indexado pelo número do grupo (q1, q2, ..., d1, d2, ...).
    """
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

    # Médias per capita por grupo, acessando via 'dados_atuais'
    medias_quintis = _medias_por_grupo('dados_atuais__quintil_atual', 'q')
    medias_decis = _medias_por_grupo('dados_atuais__decil_atual', 'd')

    # Composição da receita nacional: transferências x arrecadação própria (gráfico "O dinheiro na contramão").
    agg = ContaDetalhada.objects.aggregate(
        total_transferencias=Sum('transferencias_correntes'),
        total_impostos=Sum('imposto_taxas_contribuicoes'),
        total_contribuicoes=Sum('contribuicoes'),
        total_outras=Sum('outras_receita'),
    )
    total_transferencias = agg['total_transferencias'] or 0
    total_propria = (agg['total_impostos'] or 0) + (agg['total_contribuicoes'] or 0) + (agg['total_outras'] or 0)
    total_receita = total_transferencias + total_propria

    pct_transferencias = round(total_transferencias / total_receita * 100) if total_receita else 0
    pct_propria = 100 - pct_transferencias

    return render(request, 'ifem/index.html', {
        'noticias': noticias,
        'medias_quintis': medias_quintis,
        'medias_decis': medias_decis,
        'pct_transferencias': pct_transferencias,
        'pct_propria': pct_propria,
        'pie_offset': round(502 * pct_transferencias / 100),
    })

# --- FUNÇÕES DE API ---
# Faixas de porte populacional, na ordem em que aparecem no select. None = sem limite.
FAIXAS_DE_PORTE = {
    'Até 5 mil': (None, 5000),
    '5 mil a 10 mil': (5000, 10000),
    '10 mil a 20 mil': (10000, 20000),
    '20 mil a 50 mil': (20000, 50000),
    '50 mil a 100 mil': (50000, 100000),
    '100 mil a 200 mil': (100000, 200000),
    '200 mil a 500 mil': (200000, 500000),
    'Acima de 500 mil': (500000, None),
    'Acima de 80 mil': (80000, None),
    'Abaixo de 80 mil': (None, 80000),
}


def _filtrar_por_porte(queryset, porte):
    """Aplica a faixa populacional ao queryset. Porte desconhecido não filtra nada."""
    if not porte or porte == 'todos' or porte not in FAIXAS_DE_PORTE:
        return queryset

    minimo, maximo = FAIXAS_DE_PORTE[porte]
    # 'Acima de 80 mil' é estritamente maior e 'Abaixo de 80 mil' inclui o limite:
    # é o que faz as duas faixas serem complementares em vez de contarem o município
    # de exatamente 80 mil habitantes duas vezes. As demais faixas usam [mín, máx).
    if minimo is not None:
        lookup = 'gt' if porte == 'Acima de 80 mil' else 'gte'
        queryset = queryset.filter(**{f'dados_atuais__populacao_atual__{lookup}': minimo})
    if maximo is not None:
        lookup = 'lte' if porte == 'Abaixo de 80 mil' else 'lt'
        queryset = queryset.filter(**{f'dados_atuais__populacao_atual__{lookup}': maximo})
    return queryset


def _filtrar_por_subgrupo(queryset, subgroup_filter, classification_filter, quantil_calculation):
    """Restringe o queryset ao quintil/decil/faixa natural selecionado.

    No modo 'por_filtro' os limites do quantil são recalculados sobre o próprio
    queryset recebido — por isso esta função é chamada uma vez por dimensão de
    filtro, e não uma única vez para todas.
    """
    if not subgroup_filter or subgroup_filter == 'todos':
        return queryset

    if quantil_calculation == 'por_filtro' and classification_filter in ('quintil', 'decil'):
        num_quantiles = 5 if classification_filter == 'quintil' else 10
        rc_values = np.array([
            m['dados_atuais__rc_atual_pc']
            for m in queryset.values('dados_atuais__rc_atual_pc')
            if m.get('dados_atuais__rc_atual_pc') is not None
        ])
        if len(rc_values) == 0:
            return queryset
        try:
            target_idx = int(subgroup_filter) - 1
        except ValueError:
            return queryset
        if not (0 <= target_idx < num_quantiles):
            return queryset

        bounds = np.quantile(rc_values, np.linspace(0, 1, num_quantiles + 1)[1:-1])
        min_val = bounds[target_idx - 1] if target_idx > 0 else None
        max_val = bounds[target_idx] if target_idx < num_quantiles - 1 else None
        if min_val is None:
            return queryset.filter(dados_atuais__rc_atual_pc__lt=max_val)
        if max_val is None:
            return queryset.filter(dados_atuais__rc_atual_pc__gte=min_val)
        return queryset.filter(
            dados_atuais__rc_atual_pc__gte=min_val,
            dados_atuais__rc_atual_pc__lt=max_val,
        )

    if classification_filter == 'quintil':
        return queryset.filter(dados_atuais__quintil_atual=f'{subgroup_filter}º quintil')
    if classification_filter == 'decil':
        return queryset.filter(dados_atuais__decil_atual=f'{subgroup_filter}º decil')
    if classification_filter == 'natural':
        try:
            min_str, max_str = subgroup_filter.split('-')
            min_val = int(min_str)
            if max_str.lower() == '999999':
                return queryset.filter(dados_atuais__rc_atual_pc__gte=min_val)
            return queryset.filter(
                dados_atuais__rc_atual_pc__gte=min_val,
                dados_atuais__rc_atual_pc__lt=int(max_str),
            )
        except ValueError:
            return queryset

    return queryset


def api_get_dependent_filters(request):
    """Devolve as opções de cada select de filtro já considerando os demais filtros.

    Cada lista é montada aplicando todos os filtros ativos MENOS o da própria
    dimensão. Sem isso, selecionar UF=PE reduzia o queryset a Pernambuco e a lista
    de UFs voltava só com PE — para trocar de estado o usuário tinha que passar por
    "Todas" primeiro. Ignorando a própria dimensão, a lista continua completa, e as
    outras seleções seguem valendo (UF=PE com Região=Nordeste ainda lista só as 9
    UFs do Nordeste, que é a cascata útil).
    """
    regiao_selecionada = request.GET.get('regiao')
    uf_selecionada = request.GET.get('uf')
    rm_selecionada = request.GET.get('rm')
    consorcio_selecionado = request.GET.get('consorcio')
    porte_filtro = request.GET.get('porte')
    subgroup_filter = request.GET.get('subgrupo')
    capag_filtro = request.GET.get('capag')
    risco_filtro = request.GET.get('risco_climatico')
    classification_filter = request.GET.get('classification', 'quintil')
    quantil_calculation = request.GET.get('calculation_mode', 'total')

    RISCO_CAMPO = {
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

    # Dimensão -> (valor selecionado, lookup do ORM). São os filtros que têm lista
    # própria e por isso precisam ser ignorados ao montar a lista deles mesmos.
    dimensoes = {
        'regiao': (regiao_selecionada, 'regiao'),
        'uf': (uf_selecionada, 'uf'),
        'rm': (rm_selecionada, 'rm__nome'),
        'consorcio': (consorcio_selecionado, 'consorcios__nome'),
        'capag': (capag_filtro, 'dados_atuais__capag'),
    }

    def montar_queryset(ignorar=None):
        """Queryset com todos os filtros ativos, exceto o da dimensão `ignorar`."""
        queryset = Municipio.objects.filter(dados_atuais__rc_atual_pc__isnull=False)

        for dimensao, (valor, lookup) in dimensoes.items():
            if dimensao == ignorar:
                continue
            if valor and valor != 'todos':
                queryset = queryset.filter(**{lookup: valor})

        if risco_filtro and risco_filtro != 'todos' and risco_filtro in RISCO_CAMPO:
            queryset = queryset.filter(**{f'{RISCO_CAMPO[risco_filtro]}__gte': 0.6})

        queryset = _filtrar_por_porte(queryset, porte_filtro)
        return _filtrar_por_subgrupo(
            queryset, subgroup_filter, classification_filter, quantil_calculation
        )

    regioes = (montar_queryset(ignorar='regiao')
               .values_list('regiao', flat=True).distinct().order_by('regiao'))
    ufs = (montar_queryset(ignorar='uf')
           .values_list('uf', flat=True).distinct().order_by('uf'))
    rms = (montar_queryset(ignorar='rm').exclude(rm=None)
           .values_list('rm__nome', flat=True).distinct().order_by('rm__nome'))
    consorcios = (montar_queryset(ignorar='consorcio').exclude(consorcios=None)
                  .values_list('consorcios__nome', flat=True).distinct().order_by('consorcios__nome'))
    capags = (montar_queryset(ignorar='capag').exclude(dados_atuais__capag__isnull=True)
              .values_list('dados_atuais__capag', flat=True).distinct().order_by('dados_atuais__capag'))
    # Município é a dimensão mais fina e não filtra o queryset deste endpoint: a lista
    # é sempre a dos municípios que sobrevivem a todos os outros filtros.
    municipios = (montar_queryset()
                  .values_list('name_muni_uf', flat=True).distinct().order_by('name_muni_uf'))

    return JsonResponse({
        'regioes': list(regioes),
        'ufs': list(ufs),
        'municipios': list(municipios),
        'rms': list(rms),
        'consorcios': list(consorcios),
        'capags': list(capags)
    })

def api_get_dashboard_data(request):
    queryset = Municipio.objects.filter(dados_atuais__rc_atual_pc__isnull=False)
    regiao_filtro = request.GET.get('regiao')
    uf_filtro = request.GET.get('uf')
    rm_filtro = request.GET.get('rm')
    consorcio_filtro = request.GET.get('consorcio')
    porte_filtro = request.GET.get('porte')
    classification_filter = request.GET.get('classification', 'quintil')
    display_format = request.GET.get('display_format', 'numero')
    quantil_calculation = request.GET.get('calculation_mode', 'total')
    include_2000_data_str = request.GET.get('include_2000_data', 'false')
    include_2000_data = (include_2000_data_str.lower() == 'true')
    variavel_analisada = request.GET.get('variavel_analisada', 'populacao')
    # Filtros específicos de risco climático
    risco_campo = request.GET.get('risco_campo', 'media_ponderada')  # campo do AdaptaBrasil
    risco_nivel = request.GET.get('risco_nivel', 'todos')           # nível de intensidade

    # Mapeamento de campo simbólico → campo ORM do AdaptaBrasil
    RISCO_CAMPO_ORM = {
        'media_ponderada':    'dados_adapta_brasil__media_ponderada',
        'bio_int_bio':        'dados_adapta_brasil__bio_int_bio',
        'des_des_ter':        'dados_adapta_brasil__des_des_ter',
        'des_in_enx_ala':     'dados_adapta_brasil__des_in_enx_ala',
        'rec_ris_est_hid':    'dados_adapta_brasil__rec_ris_est_hid',
        'sau_arb':            'dados_adapta_brasil__sau_arb',
        'sau_lei_teg_ame':    'dados_adapta_brasil__sau_lei_teg_ame',
        'sau_lei_vis':        'dados_adapta_brasil__sau_lei_vis',
        'sau_mal':            'dados_adapta_brasil__sau_mal',
        'seg_ali_ace_con_ali':'dados_adapta_brasil__seg_ali_ace_con_ali',
        'seg_ali_dis':        'dados_adapta_brasil__seg_ali_dis',
        'seg_ene_ace':        'dados_adapta_brasil__seg_ene_ace',
        'seg_ene_dis':        'dados_adapta_brasil__seg_ene_dis',
    }
    orm_risco_campo = RISCO_CAMPO_ORM.get(risco_campo, 'dados_adapta_brasil__media_ponderada')

    # Filtros específicos de saúde fiscal (notas da CAPAG e indicadores do RGF)
    capag_campo = request.GET.get('capag_campo', 'geral')  # nota geral, indicador da CAPAG ou do RGF
    capag_nota = request.GET.get('capag_nota', 'todos')    # nota/classificação selecionada

    # Mapeamento de campo simbólico → campo ORM da saúde fiscal
    CAPAG_CAMPO_ORM = {
        'geral':         'dados_atuais__capag',
        'indicador_i':   'dados_atuais__capag_indicador_I',
        'indicador_ii':  'dados_atuais__capag_indicador_II',
        'indicador_iii': 'dados_atuais__capag_indicador_III',
        'rgf_pessoal':   'dados_atuais__rgf_comprometimento_pessoal',
        'rgf_divida':    'dados_atuais__rgf_divida_consolidada_liquida',
    }
    orm_capag_campo = CAPAG_CAMPO_ORM.get(capag_campo, 'dados_atuais__capag')

    CAPAG_CAMPO_LABELS = {
        'geral':         'Nota CAPAG',
        'indicador_i':   'Indicador I – Endividamento',
        'indicador_ii':  'Indicador II – Poupança Corrente',
        'indicador_iii': 'Indicador III – Liquidez Relativa',
        'rgf_pessoal':   'RGF – Comprometimento com Pessoal',
        'rgf_divida':    'RGF – Dívida Consolidada Líquida',
    }

    # Nomes legíveis para o campo selecionado (para título do gráfico)
    RISCO_CAMPO_LABELS = {
        'media_ponderada':    'Risco Climático Médio (Média Geral)',
        'bio_int_bio':        'Biodiversidade – Integridade do Bioma',
        'des_des_ter':        'Desastres – Deslizamento de Terra',
        'des_in_enx_ala':     'Desastres – Inundações e Alagamentos',
        'rec_ris_est_hid':    'Recursos Hídricos – Estresse Hídrico',
        'sau_arb':            'Saúde – Arboviroses',
        'sau_lei_teg_ame':    'Saúde – Leishmaniose Tegumentar',
        'sau_lei_vis':        'Saúde – Leishmaniose Visceral',
        'sau_mal':            'Saúde – Malária',
        'seg_ali_ace_con_ali':'Segurança Alimentar – Acesso e Consumo',
        'seg_ali_dis':        'Segurança Alimentar – Disponibilidade',
        'seg_ene_ace':        'Segurança Energética – Acesso',
        'seg_ene_dis':        'Segurança Energética – Disponibilidade',
    }

    if regiao_filtro and regiao_filtro != 'todos':
        queryset = queryset.filter(regiao=regiao_filtro)
    if uf_filtro and uf_filtro != 'todos':
        queryset = queryset.filter(uf=uf_filtro)
    if rm_filtro and rm_filtro != 'todos':
        queryset = queryset.filter(rm__nome=rm_filtro)
    # Consórcio é M2M (um município pode estar em vários): o lookup por nome não
    # duplica linhas porque casa no máximo uma associação por município.
    if consorcio_filtro and consorcio_filtro != 'todos':
        queryset = queryset.filter(consorcios__nome=consorcio_filtro)

    # Filtragem de Porte Populacional
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

    if classification_filter == 'quintil':
        num_quantiles = 5
    elif classification_filter == 'decil':
        num_quantiles = 10
    else:
        classification_filter = 'quintil'
        num_quantiles = 5

    # Campos carregados apenas quando o filtro selecionado exige (media_ponderada e capag já vêm por padrão)
    extra_value_fields = [
        campo for campo in (orm_risco_campo, orm_capag_campo)
        if campo not in ('dados_adapta_brasil__media_ponderada', 'dados_atuais__capag')
    ]

    base_classification_labels = [f'{i+1}º {classification_filter}' for i in range(num_quantiles)]
    try:
        # --- Lógica 2025 (dados_atuais) ---
        aggregated_data_list_24 = []
        field_for_aggregation_24 = ''
        classification_map_24 = {}

        if quantil_calculation == 'por_filtro':
            municipios_raw_data_24 = list(queryset.values(
                'cod_ibge', 'dados_atuais__populacao_atual', 'dados_atuais__rc_atual_pc',
                'dados_atuais__capag', 'dados_adapta_brasil__media_ponderada',
                *extra_value_fields
            ))
            rc_values_24 = np.array([muni['dados_atuais__rc_atual_pc'] for muni in municipios_raw_data_24 if muni.get('dados_atuais__rc_atual_pc') is not None])
            
            if len(rc_values_24) > 0:
                field_for_aggregation_24 = 'dynamic_quantile_val'
                classification_map_24 = {i + 1: base_classification_labels[i] for i in range(num_quantiles)}
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
                classification_map_24 = {label: label for label in base_classification_labels}
                aggregated_data_list_24 = list(queryset.values(
                    'cod_ibge', 'dados_atuais__populacao_atual', 'dados_atuais__rc_atual_pc',
                    field_for_aggregation_24, 'dados_atuais__capag',
                    'dados_adapta_brasil__media_ponderada',
                    *extra_value_fields
                ))
        else:
            field_for_aggregation_24 = f'dados_atuais__{classification_filter}_atual'
            classification_map_24 = {label: label for label in base_classification_labels}
            aggregated_data_list_24 = list(queryset.values(
                'cod_ibge', 'dados_atuais__populacao_atual', 'dados_atuais__rc_atual_pc',
                field_for_aggregation_24, 'dados_atuais__capag',
                'dados_adapta_brasil__media_ponderada',
                *extra_value_fields
            ))

        # --- Lógica 2000 (dados_2000) ---
        aggregated_data_list_00 = []
        field_for_aggregation_00 = ''
        classification_map_00 = {} 

        if quantil_calculation == 'por_filtro':
            municipios_raw_data_00 = list(queryset.values('cod_ibge', 'dados_2000__populacao_00', 'dados_2000__rc_00_pc'))
            rc_values_00 = np.array([muni['dados_2000__rc_00_pc'] for muni in municipios_raw_data_00 if muni.get('dados_2000__rc_00_pc') is not None])
            if len(rc_values_00) > 0:
                field_for_aggregation_00 = 'dynamic_quantile_val'
                classification_map_00 = {i + 1: base_classification_labels[i] for i in range(num_quantiles)}
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
                classification_map_00 = {label: label for label in base_classification_labels}
                aggregated_data_list_00 = list(queryset.values('cod_ibge', 'dados_2000__populacao_00', 'dados_2000__rc_00_pc', field_for_aggregation_00))
        else:
            field_for_aggregation_00 = f'dados_2000__{classification_filter}_00'
            classification_map_00 = {label: label for label in base_classification_labels}
            aggregated_data_list_00 = list(queryset.values('cod_ibge', 'dados_2000__populacao_00', 'dados_2000__rc_00_pc', field_for_aggregation_00))

        # --- Resumo e Gráficos ---
        total_municipios = queryset.count()
        media_receita_per_capita = queryset.aggregate(Avg('dados_atuais__rc_atual_pc'))['dados_atuais__rc_atual_pc__avg'] or 0
        
        # Correção Crítica para o SQLite (Cálculo de Desvio Padrão com NumPy)
        rc_values_for_std = list(queryset.values_list('dados_atuais__rc_atual_pc', flat=True))
        rc_values_for_std = [v for v in rc_values_for_std if v is not None]
        std_dev_res = np.std(rc_values_for_std) if rc_values_for_std else 0
        
        coeficiente_de_variacao = 0
        if media_receita_per_capita > 0:
            coeficiente_de_variacao = std_dev_res / media_receita_per_capita
        
        _nacional_stats = Municipio.objects.filter(dados_atuais__rc_atual_pc__isnull=False).aggregate(total=Count('cod_ibge'), media_rc=Avg('dados_atuais__rc_atual_pc'))
        nacional_total_municipios_base = _nacional_stats['total'] or 0
        nacional_media_receita_per_capita_base = _nacional_stats['media_rc'] or 1
        gini_index = 0.202 
        perc_municipios_selecao = (total_municipios / nacional_total_municipios_base * 100) if nacional_total_municipios_base > 0 else 0
        diff_media_nacional = ((media_receita_per_capita - nacional_media_receita_per_capita_base) / nacional_media_receita_per_capita_base * 100) if nacional_media_receita_per_capita_base > 0 else 0

        chart_labels = list(classification_map_24.values())
        classification_columns = list(classification_map_24.values())
        
        # Helpers para variáveis
        def get_capag_grade(capag_val):
            if not capag_val: return 'Sem Nota'
            val = capag_val.strip().upper()
            if val.startswith('A'): return 'A'
            if val.startswith('B'): return 'B'
            if val.startswith('C'): return 'C'
            if val.startswith('D'): return 'D'
            return 'Sem Nota'

        # Comprometimento com pessoal (% da RCL): o teto da LRF para o Executivo municipal
        # é 54%, com limite prudencial em 95% do teto (51,3%) e alerta em 90% (48,6%).
        def get_lrf_pessoal(val):
            if val is None: return 'Sem dados'
            if val >= 54: return 'Acima do Limite Máximo'
            if val >= 51.3: return 'Acima do Limite Prudencial'
            if val >= 48.6: return 'Acima do Limite de Alerta'
            return 'Regular'

        # Dívida Consolidada Líquida (% da RCL): teto de 120%, alerta dos TCEs em 108%
        # (90% do teto). DCL negativa significa disponibilidade de caixa maior que a dívida.
        def get_lrf_divida(val):
            if val is None: return 'Sem dados'
            if val > 120: return 'Acima do Limite'
            if val >= 108: return 'Em Alerta (TCE)'
            if val >= 0: return 'Regular'
            return 'Caixa Positivo (DCL Negativa)'

        def get_risco_climatico(val):
            if val is None: return 'Sem Dados'
            if val >= 0.8: return 'Muito alto'
            if val >= 0.6: return 'Alto'
            if val >= 0.4: return 'Médio'
            if val >= 0.2: return 'Baixo'
            return 'Muito baixo'

        # 'capag' é o nome antigo deste modo, aceito para não quebrar links já salvos
        if variavel_analisada in ('saude_fiscal', 'capag'):
            # Usa o campo selecionado (nota geral, indicador da CAPAG ou indicador do RGF)
            campo_key = orm_capag_campo
            campo_label = CAPAG_CAMPO_LABELS.get(capag_campo, 'Nota CAPAG')

            if capag_campo == 'rgf_pessoal':
                classificar = get_lrf_pessoal
                faixas = ['Regular', 'Acima do Limite de Alerta',
                          'Acima do Limite Prudencial', 'Acima do Limite Máximo', 'Sem dados']
                table_row_header = 'Classificação LRF – Pessoal'
            elif capag_campo == 'rgf_divida':
                classificar = get_lrf_divida
                faixas = ['Caixa Positivo (DCL Negativa)', 'Regular',
                          'Em Alerta (TCE)', 'Acima do Limite', 'Sem dados']
                table_row_header = 'Classificação LRF – Dívida'
            else:
                # Só a nota geral chega até D; os indicadores vão de A a C
                outros_label = 'D e outros' if capag_campo == 'geral' else 'n.d. ou n.e.'

                def classificar(val, outros=outros_label):
                    grade = get_capag_grade(val)
                    return grade if grade in ('A', 'B', 'C') else outros

                faixas = ['A', 'B', 'C', outros_label]
                table_row_header = 'Notas CAPAG'

            all_row_configs = [
                (faixa, lambda m, ck=campo_key, f=faixa, cl=classificar: cl(m.get(ck)) == f)
                for faixa in faixas
            ]
            # Aplica filtro de nota/classificação se selecionado
            if capag_nota and capag_nota != 'todos':
                row_configs = [rc for rc in all_row_configs if rc[0] == capag_nota]
            else:
                row_configs = all_row_configs
            y_axis_title = 'Quantidade de Municípios'
            chart_title = f'Distribuição de Municípios por {campo_label}'
            is_count = True
        elif variavel_analisada == 'risco_climatico':
            # Usa o campo selecionado (tipo de risco ou média ponderada)
            campo_key = orm_risco_campo
            campo_label = RISCO_CAMPO_LABELS.get(risco_campo, 'Risco Climático')

            all_row_configs = [
                ('Muito baixo', lambda m, ck=campo_key: get_risco_climatico(m.get(ck)) == 'Muito baixo'),
                ('Baixo',       lambda m, ck=campo_key: get_risco_climatico(m.get(ck)) == 'Baixo'),
                ('Médio',       lambda m, ck=campo_key: get_risco_climatico(m.get(ck)) == 'Médio'),
                ('Alto',        lambda m, ck=campo_key: get_risco_climatico(m.get(ck)) == 'Alto'),
                ('Muito alto',  lambda m, ck=campo_key: get_risco_climatico(m.get(ck)) == 'Muito alto'),
            ]
            # Aplica filtro de nível se selecionado
            if risco_nivel and risco_nivel != 'todos':
                row_configs = [rc for rc in all_row_configs if rc[0] == risco_nivel]
            else:
                row_configs = all_row_configs
            y_axis_title = 'Quantidade de Municípios'
            table_row_header = 'Níveis de Risco Climático'
            chart_title = f'Distribuição por {campo_label}'
            is_count = True
        else: # populacao
            row_configs = [
                (label, lambda m, min_p=min_p, max_p=max_p: min_p <= (m.get('dados_atuais__populacao_atual') or 0) < max_p if max_p != float('inf') else (m.get('dados_atuais__populacao_atual') or 0) >= min_p)
                for label, min_p, max_p in [
                    ('Até 5 mil', 0, 5000), ('5 mil a 10 mil', 5000, 10000), ('10 mil a 20 mil', 10000, 20000),
                    ('20 mil a 50 mil', 20000, 50000), ('50 mil a 100 mil', 50000, 100000),
                    ('100 mil a 200 mil', 100000, 200000), ('200 mil a 500 mil', 200000, 500000),
                    ('Acima de 500 mil', 500000, float('inf')),
                ]
            ]
            y_axis_title = 'População (milhões)'
            if display_format == 'porcentagem':
                 y_axis_title = 'População (%)'
            table_row_header = 'Faixas Populacionais'
            chart_title = 'Distribuição da População Municipal'
            is_count = False

        # --- Gráfico ---
        datasets_to_send = []
        column_totals_24 = {col: 0 for col in classification_columns}
        for item in aggregated_data_list_24:
            key = item.get(field_for_aggregation_24)
            label = classification_map_24.get(key)
            if label:
                column_totals_24[label] += 1

        if is_count:
            # Multiples datasets para o ano atual, contando municípios
            for row_label, condition in row_configs:
                group_counts = {label: 0 for label in chart_labels}
                for item in aggregated_data_list_24:
                    if condition(item):
                        key = item.get(field_for_aggregation_24)
                        label = classification_map_24.get(key)
                        if label:
                            group_counts[label] += 1
                
                data_array = []
                for l in chart_labels:
                    val = group_counts.get(l, 0)
                    if display_format == 'porcentagem':
                        total_col = column_totals_24.get(l, 0)
                        data_array.append((val / total_col * 100) if total_col > 0 else 0)
                    else:
                        data_array.append(val)
                
                datasets_to_send.append({
                    "label": f"{row_label} (2025)",
                    "data": data_array
                })
            
            # Reverte a ordem dos datasets para que o primeiro item da tabela (ex: A) fique no topo do gráfico empilhado
            datasets_to_send.reverse()
        else:
            # Um único dataset somando população
            total_pop_for_chart_percentage_24 = sum(item.get('dados_atuais__populacao_atual', 0) for item in aggregated_data_list_24 if item.get('dados_atuais__populacao_atual') is not None)
            chart_value_multiplier_24 = 1_000_000
            if display_format == 'porcentagem':
                chart_value_multiplier_24 = total_pop_for_chart_percentage_24 / 100 if total_pop_for_chart_percentage_24 > 0 else 1

            pop_by_group_24 = {label: 0 for label in chart_labels}
            for item in aggregated_data_list_24:
                key = item.get(field_for_aggregation_24)
                label = classification_map_24.get(key)
                if label:
                    pop_by_group_24[label] += item.get('dados_atuais__populacao_atual', 0) if item.get('dados_atuais__populacao_atual') is not None else 0
            
            datasets_to_send.append({
                "label": f"{y_axis_title} (2025)",
                "data": [(pop_by_group_24.get(l, 0) / chart_value_multiplier_24) for l in chart_labels]
            })

            # Gráfico 2000
            if include_2000_data:
                total_pop_for_chart_percentage_00 = sum(item.get('dados_2000__populacao_00', 0) for item in aggregated_data_list_00 if item.get('dados_2000__populacao_00') is not None)
                chart_value_multiplier_00 = 1_000_000 
                if display_format == 'porcentagem':
                    chart_value_multiplier_00 = total_pop_for_chart_percentage_00 / 100 if total_pop_for_chart_percentage_00 > 0 else 1

                pop_by_group_00 = {label: 0 for label in chart_labels}
                for item in aggregated_data_list_00:
                    key = item.get(field_for_aggregation_00)
                    label_00 = classification_map_00.get(key)
                    if label_00:
                        pop_by_group_00[label_00] += item.get('dados_2000__populacao_00', 0) if item.get('dados_2000__populacao_00') is not None else 0
                
                datasets_to_send.append({
                    "label": f"{y_axis_title} (2000)",
                    "data": [(pop_by_group_00.get(l, 0) / chart_value_multiplier_00) for l in chart_labels]
                })

        # --- Tabela Dinâmica ---
        table_data_24 = []
        raw_grand_total_classification_counts_24 = {col: 0 for col in classification_columns}
        total_municipios_24 = sum(column_totals_24.values())

        for row_label, condition in row_configs:
            row_data = {table_row_header: row_label}
            range_data_24_filtered = [m for m in aggregated_data_list_24 if condition(m)]
            
            raw_counts_in_row_24 = {col: 0 for col in classification_columns}
            for muni in range_data_24_filtered:
                classification_key = muni.get(field_for_aggregation_24)
                column_label = classification_map_24.get(classification_key)
                if column_label:
                    raw_counts_in_row_24[column_label] += 1
            
            current_range_total_raw_24 = len(range_data_24_filtered)
            for col_label in classification_columns:
                val = raw_counts_in_row_24.get(col_label, 0)
                if display_format == 'porcentagem' and is_count:
                    col_total = column_totals_24.get(col_label, 0)
                    row_data[col_label] = f"{(val / col_total * 100):.1f}%" if col_total > 0 else "0.0%"
                elif display_format == 'porcentagem':
                    row_data[col_label] = f"{(val / current_range_total_raw_24 * 100):.1f}%" if current_range_total_raw_24 > 0 else "0.0%"
                else:
                    row_data[col_label] = val
                
                raw_grand_total_classification_counts_24[col_label] += val

            if display_format == 'porcentagem' and is_count:
                row_data['Total'] = f"{(current_range_total_raw_24 / total_municipios_24 * 100):.1f}%" if total_municipios_24 > 0 else "0.0%"
            elif display_format == 'porcentagem':
                row_data['Total'] = "100.0%"
            else:
                row_data['Total'] = current_range_total_raw_24
            
            table_data_24.append(row_data)

        grand_total_row_24 = {table_row_header: 'Total Geral'}
        raw_grand_total_rows_total_24 = sum(raw_grand_total_classification_counts_24.values())
        total_municipios_for_table_24 = len(aggregated_data_list_24)

        for col_label in classification_columns:
            count = raw_grand_total_classification_counts_24.get(col_label, 0)
            if display_format == 'porcentagem' and is_count:
                grand_total_row_24[col_label] = "100.0%"
            elif display_format == 'porcentagem':
                grand_total_row_24[col_label] = f"{(count / total_municipios_for_table_24 * 100):.1f}%" if total_municipios_for_table_24 > 0 else "0.0%"
            else:
                grand_total_row_24[col_label] = count

        if display_format == 'porcentagem' and is_count:
            grand_total_row_24['Total'] = "100.0%"
        elif display_format == 'porcentagem':
            grand_total_row_24['Total'] = "100.0%"
        else:
            grand_total_row_24['Total'] = raw_grand_total_rows_total_24
            
        table_data_24.append(grand_total_row_24)
        table_headers_24 = [table_row_header] + classification_columns + ['Total']

        # --- Tabela 2000 (Apenas se for população e houver include_2000_data) ---
        table_data_00 = []
        table_headers_00 = []
        if include_2000_data and not is_count:
            raw_grand_total_classification_counts_00 = {col: 0 for col in classification_columns}
            for row_label, condition in row_configs:
                row_data = {table_row_header: row_label}
                # Na tabela 2000 as faixas são baseadas na população_00. Precisamos de uma condition_00.
                # Como a lógica `condition` pode acessar `dados_atuais__populacao_atual`, precisamos usar uma variação:
                # Mas para simplificar, usaremos o approach nativo:
                try:
                    min_pop_00 = float(row_label.split('a')[0].replace('Até', '').replace('mil', '').strip()) * 1000 if 'mil' in row_label and 'Acima' not in row_label and 'Até' not in row_label else (0 if 'Até' in row_label else (500000 if 'Acima' in row_label else 0))
                    # Fallback simplificado se der erro:
                except Exception:
                    min_pop_00 = 0
                
                # Solução robusta: em vez de fazer parser da string, iterar pela list original de faixas
                
                # Mas para evitar complicações no 2000, iteramos pelas population_ranges:
                population_ranges_for_2000 = [
                    ('Até 5 mil', 0, 5000), ('5 mil a 10 mil', 5000, 10000), ('10 mil a 20 mil', 10000, 20000),
                    ('20 mil a 50 mil', 20000, 50000), ('50 mil a 100 mil', 50000, 100000),
                    ('100 mil a 200 mil', 100000, 200000), ('200 mil a 500 mil', 200000, 500000),
                    ('Acima de 500 mil', 500000, float('inf')),
                ]
                
                found_range = [pr for pr in population_ranges_for_2000 if pr[0] == row_label]
                if found_range:
                    _, min_pop, max_pop = found_range[0]
                    range_data_00_filtered = [m for m in aggregated_data_list_00 if m.get('dados_2000__populacao_00') is not None and (min_pop <= m['dados_2000__populacao_00'] < max_pop if max_pop != float('inf') else m['dados_2000__populacao_00'] >= min_pop)]
                else:
                    range_data_00_filtered = []

                raw_counts_in_row_00 = {col: 0 for col in classification_columns}
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

            grand_total_row_00 = {table_row_header: 'Total Geral'}
            raw_grand_total_rows_total_00 = sum(raw_grand_total_classification_counts_00.values())
            total_municipios_for_table_00 = len(aggregated_data_list_00)

            for col_label in classification_columns:
                count = raw_grand_total_classification_counts_00.get(col_label, 0)
                grand_total_row_00[col_label] = f"{(count / total_municipios_for_table_00 * 100):.1f}%" if display_format == 'porcentagem' and total_municipios_for_table_00 > 0 else (count if display_format != 'porcentagem' else "0.0%")

            grand_total_row_00['Total'] = "100.0%" if display_format == 'porcentagem' else raw_grand_total_rows_total_00
            table_data_00.append(grand_total_row_00)
            table_headers_00 = [table_row_header] + classification_columns + ['Total']


        response_data = {
            "summaryCards": {
                "totalMunicipios": total_municipios,
                "percTotalMunicipios": round(perc_municipios_selecao, 1),
                "mediaReceitaPerCapita": round(media_receita_per_capita, 2),
                "diffMediaNacional": round(diff_media_nacional, 2),
                "giniIndex": round(coeficiente_de_variacao*100, 2)
            },
            "chartData": {"labels": chart_labels, "datasets": datasets_to_send, "yAxisTitle": y_axis_title, "xAxisTitle": classification_filter.capitalize(), "chartTitle": chart_title},
            "tableData24": table_data_24, "tableHeaders24": table_headers_24, "tableTitle24": f"Distribuição de Municípios por {table_row_header} (2025)",
        }
        if include_2000_data and not is_count:
            response_data["tableData00"] = table_data_00
            response_data["tableHeaders00"] = table_headers_00
            response_data["tableTitle00"] = f"Distribuição de Municípios por {table_row_header} (2000)"
        return JsonResponse(response_data)
    except Exception as e:
        import traceback
        return JsonResponse({"error": str(e), "traceback": traceback.format_exc()}, status=500)

def api_debug_status(request):
    from django.db import connection
    from django.conf import settings
    import os
    
    db_info = settings.DATABASES['default']
    try:
        municipio_count = Municipio.objects.count()
        conn_ok = True
    except Exception as e:
        municipio_count = -1
        conn_ok = False
        
    return JsonResponse({
        "database_engine": db_info['ENGINE'],
        "database_host": db_info.get('HOST', 'N/A')[:10] + "...",
        "municipio_count": municipio_count,
        "connection_alive": conn_ok,
        "env_db_url": bool(os.getenv("DATABASE_URL")),
        "debug_mode": settings.DEBUG
    })