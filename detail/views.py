from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets
from home.models import Municipio
from home.models import ContaDetalhada
from .serializers import MunicipioPercentilSerializer




def municipio_detalhe_view(request, cod_ibge):
    """
    Renderiza a visualização de detalhes para um município específico, incluindo
    seus dados de conta financeira associados para gráficos.
    """
    # Recupera o município ou retorna um erro 404
    municipio = get_object_or_404(Municipio, cod_ibge=cod_ibge)

    # Tenta recuperar a conta financeira relacionada
    try:
        conta = municipio.conta_detalhada
    except ContaDetalhada.DoesNotExist:
        conta = None

    # Prepara os dados do gráfico se uma conta financeira existir
    chart_data = None
    if conta:
        chart_data = {
            'labels': [
                'Impostos e Taxas',
                'Contribuições',
                'Transf. Correntes',
                'Outras'
            ],
            'values': [
                conta.imposto_taxas_contribuicoes,
                conta.contribuicoes,
                conta.transferencias_correntes,
                conta.outras_receita
            ]
        }

    # Constrói o contexto para o template
    contexto = {
        'municipio': municipio,
        'conta': conta,
        'chart_data': chart_data
    }

    return render(request, 'detail/detalhe_municipio.html', contexto)

class MunicipioAPIView(viewsets.ReadOnlyModelViewSet):
    queryset = Municipio.objects.all().select_related(
        'conta_detalhada_percentil',
        'conta_especifica',
        'conta_especifica_percentil',
        'conta_mais_especifica',
        'conta_mais_especifica_percentil'
    )
    serializer_class = MunicipioPercentilSerializer
    lookup_field = 'id'