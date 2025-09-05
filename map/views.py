from django.shortcuts import render
from django.http import JsonResponse
from home.models import Municipio
import numpy as np


def map(request):
    """
    Renderiza o template HTML para a visualização do mapa.
    A lógica de filtro é tratada dinamicamente por chamadas de API.
    """
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
    
    # Extrai os valores de 'rc_23_pc' para o cálculo
    rc_values = np.array([
        muni['rc_23_pc']
        for muni in base_queryset_for_quantile.values('rc_23_pc')
        if muni.get('rc_23_pc') is not None
    ])

    if len(rc_values) > 0:
        quantiles_to_calculate = np.linspace(0, 1, num_quantiles + 1)[1:-1]
        quantile_boundaries = np.quantile(rc_values, quantiles_to_calculate)
    
    # Agora, aplica o filtro de subgrupo APÓS os cálculos de quantil,
    # se o subgrupo for uma classificação (quintil/decil)
    # ou se for um filtro natural sobre o rc_23_pc.
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
                        queryset = queryset.filter(rc_23_pc__gte=min_val_quantile)
                    elif min_val_quantile == -float('inf'): # Primeiro quantil
                        queryset = queryset.filter(rc_23_pc__lt=max_val_quantile)
                    else:
                        queryset = queryset.filter(rc_23_pc__gte=min_val_quantile, rc_23_pc__lt=max_val_quantile)
                
            except ValueError:
                # Trata o caso onde subgroup_filter não é um inteiro para quantil
                pass
        
        # Se o modo de cálculo é 'total' (quantis pré-calculados) OU se o filtro é 'natural'
        elif classification_filter == 'quintil':
            queryset = queryset.filter(quintil23=subgroup_filter)
        elif classification_filter == 'decil':
            queryset = queryset.filter(decil23=subgroup_filter)
        elif classification_filter == 'natural':
            try:
                min_str, max_str = subgroup_filter.split('-')
                min_val = int(min_str)
                if max_str.lower() == '999999': # Representa "acima de X"
                    queryset = queryset.filter(rc_23_pc__gte=min_val)
                else:
                    max_val = int(max_str)
                    queryset = queryset.filter(rc_23_pc__gte=min_val, rc_23_pc__lt=max_val)
            except ValueError:
                pass # Lida graciosamente com filtros de subgrupo "natural" malformados

    # Constrói as feições GeoJSON a partir dos municípios filtrados
    features = []
    for municipio in queryset:
        # Adiciona o quantil calculado dinamicamente ou o pré-calculado
        current_muni_quantile = None
        if municipio.rc_23_pc is not None and len(quantile_boundaries) > 0:
            current_muni_quantile_idx = np.searchsorted(quantile_boundaries, municipio.rc_23_pc)
            current_muni_quantile = int(current_muni_quantile_idx + 1)
        elif quantil_calculation == 'total':
             # Se o cálculo é 'total', usa o campo pré-calculado do modelo
            if classification_filter == 'quintil':
                current_muni_quantile = municipio.quintil23
            elif classification_filter == 'decil':
                current_muni_quantile = municipio.decil23

        feature = {
            "type": "Feature",
            "geometry": {
                # Se 'geometry' for sempre um Point, isso está ok.
                # Se for Polygon, você precisará carregar os dados geográficos.
                "type": "Point",
                "coordinates": [municipio.coordx, municipio.coordy]
            },
            "properties": {
                'cod_ibge': municipio.cod_ibge,
                'name_muni': municipio.name_muni,
                'name_muni_uf': municipio.name_muni_uf,
                'Populacao23': municipio.populacao23,
                'uf': municipio.uf,
                'rc_23_pc': municipio.rc_23_pc,
                'quintil23_pre_calculado': municipio.quintil23, # Manter para referência
                'decil23_pre_calculado': municipio.decil23,   # Manter para referência
                'percentil': municipio.percentil,
                'percentil_n': municipio.percentil_n,
                # NOVO CAMPO: Quantil dinamicamente calculado
                'dynamic_quantile': current_muni_quantile
            }
        }
        features.append(feature)

    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }

    return JsonResponse(geojson_data)