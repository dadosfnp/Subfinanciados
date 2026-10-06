from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Avg
from home.models import Municipio

import logging

from home.models import Noticia

from .apresentacao import montar_apresentacao

logger = logging.getLogger(__name__)


def inicio_preview(request):
    """Landing em formato de apresentacao (/preview/inicio/), fora do menu.

    A narrativa vem de ifem/apresentacao.py (modulos) e os numeros, do banco,
    via ifem/apresentacao_dados.py. Abaixo dela, plataforma, FAQ e noticias.
    """
    blocos, compartilhados = montar_apresentacao()

    # Dados que o JS precisa para desenhar os visuais, indexados pelo id do passo.
    visuais = {}
    for bloco in blocos:
        for passo in bloco.get('passos', []):
            visuais[passo['id']] = {
                'visual': passo['visual'],
                'opcoes': passo['opcoes'],
                'dados': passo['dados'],
            }

    try:
        noticias = list(Noticia.objects.order_by('-data')[:8])
    except Exception:
        # Noticias sao acessorias: sem elas, a pagina ainda conta a historia.
        logger.exception('Falha ao carregar noticias da landing de preview')
        noticias = []

    return render(request, 'ifem/inicio_folheto.html', {
        'blocos': blocos,
        'apresentacao_json': {'visuais': visuais, 'mapa': compartilhados.get('mapa')},
        'noticias': noticias,
    })


def landing_page(request):
    return render(request, 'ifem/index.html')

def busca_municipio_simples_api(request):
    """
    Endpoint otimizado para o autocomplete da Landing Page do IFEM.
    """
    query = request.GET.get('q', '').strip()

    if len(query) < 3:
        return JsonResponse({'results': [], 'national_avg': 0})

    # Busca até 10 municípios que contenham o termo digitado e possuam receita atual
    qs = Municipio.objects.filter(
        name_muni_uf__icontains=query, 
        dados_atuais__rc_atual_pc__isnull=False
    ).order_by('name_muni_uf')[:10]

    # Média nacional de Receita per Capita
    national_avg = Municipio.objects.filter(dados_atuais__rc_atual_pc__isnull=False).aggregate(avg_rc=Avg('dados_atuais__rc_atual_pc'))['avg_rc'] or 0

    results = []
    for m in qs:
            results.append({
                'id': m.cod_ibge,
                'nome': m.name_muni_uf,
                'rc_pc': float(m.rc_24_pc or 0),
                'quintil': str(m.quintil24) if m.quintil24 else "",
                'decil': str(m.decil24) if m.decil24 else "",
            })

    return JsonResponse({
            'national_avg': float(national_avg),
            'results': results
        })
