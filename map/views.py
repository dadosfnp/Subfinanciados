from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from home.models import Municipio
import numpy as np
import re


def _num_classe(valor):
    """Extrai o número de uma classe textual como '3º quintil' ou '7º decil'.

    Retorna None quando o valor é nulo/sem dígito, para que a variação seja
    tratada como "sem dado" em vez de quebrar com erro.
    """
    if not valor:
        return None
    m = re.search(r'(\d+)', str(valor))
    return int(m.group(1)) if m else None


def _cresc_pct(novo, velho):
    """Variação percentual de `velho` para `novo`, arredondada a 1 casa.

    Retorna None se faltar base ou se a base for zero (evita divisão por zero),
    para o frontend pintar como "sem dado".
    """
    if novo is None or velho is None or velho == 0:
        return None
    return round((novo - velho) / velho * 100, 1)


def map(request):
    """
    Renderiza o template HTML para a visualização do mapa.
    A lógica de filtro é tratada dinamicamente por chamadas de API.
    """
    context = {
        'MAPBOX_PUBLIC_TOKEN': getattr(settings, 'MAPBOX_PUBLIC_TOKEN', ''),
    }

    return render(request, 'map/map.html')



def municipios_geojson_api(request):
    """
    Retorna dados GeoJSON para municípios, aplicando diversos filtros
    incluindo região, UF, nome do município, porte populacional,
    região metropolitana e subgrupos de classificação (quintil, decil, natural).
    """
    queryset = Municipio.objects.all()

    # Recupera os parâmetros de filtro da requisição
    uf_filtro = request.GET.get('uf')
    regiao_filtro = request.GET.get('regiao')
    municipio_filtro = request.GET.get('municipio')
    porte_filtro = request.GET.get('porte')
    classification_filter = request.GET.get('classification', 'quintil')
    subgroup_filter = request.GET.get('subgrupo')
    rm_filtro = request.GET.get('rm')

    classification_filter = request.GET.get('classification', 'quintil') # 'quintil' ou 'decil'
    quantil_calculation = request.GET.get('calculation_mode', 'total') # 'total' ou 'por_filtro'

    subgroup_filter = request.GET.get('subgrupo') # Este filtro agora se aplicará APÓS o cálculo dinâmico, se 'por_filtro'

    

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
        # Novas regras adicionadas:
        elif porte_filtro == 'Acima de 80 mil':
            queryset = queryset.filter(populacao24__gt=80000)
        elif porte_filtro == 'Abaixo de 80 mil':
            queryset = queryset.filter(populacao24__lte=80000)

    # Lógica de cálculo de quantil dinâmico
    num_quantiles = 5 if classification_filter == 'quintil' else 10
    quantile_boundaries = []
    
    # Determina o queryset base para o cálculo do quantil
    if quantil_calculation == 'total':
        # Calcula o quantil sobre TODOS os municípios do Brasil
        base_queryset_for_quantile = Municipio.objects.all()
    else: # quantil_calculation == 'por_filtro'
        # Calcula o quantil sobre o queryset já filtrado
        base_queryset_for_quantile = queryset
    
    # Extrai os valores de 'rc_24_pc' para o cálculo
    rc_values = np.array([
        muni['rc_24_pc']
        for muni in base_queryset_for_quantile.values('rc_24_pc')
        if muni.get('rc_24_pc') is not None
    ])

    if len(rc_values) > 0:
        quantiles_to_calculate = np.linspace(0, 1, num_quantiles + 1)[1:-1]
        quantile_boundaries = np.quantile(rc_values, quantiles_to_calculate)
    
    # Agora, aplica o filtro de subgrupo APÓS os cálculos de quantil,
    # se o subgrupo for uma classificação (quintil/decil)
    # ou se for um filtro natural sobre o rc_24_pc.
    if subgroup_filter and subgroup_filter != "todos":
        # Se o modo de cálculo é 'por_filtro', o campo dinâmico será usado
        # para aplicar o filtro de subgrupo.
        if quantil_calculation == 'por_filtro' and len(rc_values) > 0:
            # Filtra o queryset com base nos quantis dinamicamente calculados
            try:
                # O subgroup_filter virá como '1', '2', etc. para quintil/decil
                target_quantile_idx = int(subgroup_filter) - 1
                if 0 <= target_quantile_idx < num_quantiles:
                    min_val_quantile = quantile_boundaries[target_quantile_idx -1] if target_quantile_idx > 0 else -float('inf')
                    max_val_quantile = quantile_boundaries[target_quantile_idx] if target_quantile_idx < num_quantiles -1 else float('inf')
                    
                    if max_val_quantile == float('inf'): # Último quantil
                        queryset = queryset.filter(rc_24_pc__gte=min_val_quantile)
                    elif min_val_quantile == -float('inf'): # Primeiro quantil
                        queryset = queryset.filter(rc_24_pc__lt=max_val_quantile)
                    else:
                        queryset = queryset.filter(rc_24_pc__gte=min_val_quantile, rc_24_pc__lt=max_val_quantile)
                
            except ValueError:
                # Trata o caso onde subgroup_filter não é um inteiro para quantil
                pass
        
        # Se o modo de cálculo é 'total' (quantis pré-calculados) OU se o filtro é 'natural'
        elif classification_filter == 'quintil':
            quintil_filter = f"{subgroup_filter}º quintil"
            queryset = queryset.filter(quintil24=quintil_filter)
        elif classification_filter == 'decil':
            decil_filter = f"{subgroup_filter}º decil"
            queryset = queryset.filter(decil24=decil_filter)
        elif classification_filter == 'natural':
            try:
                min_str, max_str = subgroup_filter.split('-')
                min_val = int(min_str)
                if max_str.lower() == '999999': # Representa "acima de X"
                    queryset = queryset.filter(rc_24_pc__gte=min_val)
                else:
                    max_val = int(max_str)
                    queryset = queryset.filter(rc_24_pc__gte=min_val, rc_24_pc__lt=max_val)
            except ValueError:
                pass # Lida graciosamente com filtros de subgrupo "natural" malformados

    # Modo de análise: 'receita' (padrão, comportamento original) ou 'crescimento' (2000 vs 2024).
    # No modo crescimento puxamos também os campos históricos e devolvemos métricas calculadas.
    analise = request.GET.get('analise', 'receita')

    # Constrói as feições GeoJSON a partir dos municípios filtrados
    # Usa .values() para evitar instanciar objetos ORM completos (mais rápido)
    _fields = (
        'cod_ibge', 'name_muni', 'name_muni_uf', 'populacao24', 'uf',
        'rc_24_pc', 'cadunico', 'sus_dependente', 'quintil24', 'decil24',
        'percentil24', 'percentil24_n', 'coordx', 'coordy',
    )
    if analise == 'crescimento':
        # Campos extras só neste modo — mantém o payload do modo 'receita' enxuto.
        _fields = _fields + (
            'populacao00', 'rc_00_pc', 'quintil00', 'decil00', 'percentil00_n',
            'rank_nacional', 'rank_nacional_00', 'total_nacional',
        )
    features = []
    for municipio in queryset.values(*_fields):
        rc = municipio['rc_24_pc']
        current_muni_quantile = None
        if rc is not None and len(quantile_boundaries) > 0:
            current_muni_quantile = int(np.searchsorted(quantile_boundaries, rc) + 1)
        elif quantil_calculation == 'total':
            if classification_filter == 'quintil':
                current_muni_quantile = municipio['quintil24']
            elif classification_filter == 'decil':
                current_muni_quantile = municipio['decil24']

        pop = municipio['populacao24'] or 0
        cadunico = municipio['cadunico'] or 0
        perc_cadunico = min((cadunico / pop * 100) if pop > 0 else 0, 100)

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
                'Populacao24': municipio['populacao24'],
                'uf': municipio['uf'],
                'rc_24_pc': rc,
                'perc_pop_cadunico': perc_cadunico,
                'sus_dependente': municipio['sus_dependente'],
                'quintil24_pre_calculado': municipio['quintil24'],
                'decil24_pre_calculado': municipio['decil24'],
                'percentil24': municipio['percentil24'],
                'percentil24_n': municipio['percentil24_n'],
                'dynamic_quantile': current_muni_quantile
            }
        }

        # Métricas de crescimento 2000→2024 (somente quando solicitado).
        if analise == 'crescimento':
            pop00 = municipio['populacao00']
            rc00pc = municipio['rc_00_pc']
            q24, q00 = _num_classe(municipio['quintil24']), _num_classe(municipio['quintil00'])
            d24, d00 = _num_classe(municipio['decil24']), _num_classe(municipio['decil00'])
            p24n, p00n = municipio['percentil24_n'], municipio['percentil00_n']
            rk24, rk00 = municipio['rank_nacional'], municipio['rank_nacional_00']
            feature['properties'].update({
                # Valores-base de 2000 (para o popup comparativo)
                'populacao00': pop00,
                'rc_00_pc': rc00pc,
                'quintil00': municipio['quintil00'],
                'decil00': municipio['decil00'],
                'percentil00_n': p00n,
                'rank_nacional': rk24,
                'rank_nacional_00': rk00,
                'total_nacional': municipio['total_nacional'],
                # Métricas de variação (None = sem dado → frontend pinta cinza)
                'cresc_pop_pct': _cresc_pct(municipio['populacao24'], pop00),
                'cresc_rcpc_pct': _cresc_pct(rc, rc00pc),
                # Variação de classe: positivo = melhorou (subiu de quintil/decil/percentil)
                'var_quintil': (q24 - q00) if (q24 is not None and q00 is not None) else None,
                'var_decil': (d24 - d00) if (d24 is not None and d00 is not None) else None,
                'var_percentil': (p24n - p00n) if (p24n is not None and p00n is not None) else None,
                # Ranking: número menor é melhor, então melhora = rank_2000 - rank_2024 (positivo sobe)
                'var_rank': (rk00 - rk24) if (rk24 is not None and rk00 is not None) else None,
            })

        features.append(feature)

    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }

    return JsonResponse(geojson_data)