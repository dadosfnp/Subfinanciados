from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Avg
from home.models import Municipio

import logging

from home.models import Noticia

from django.core.cache import cache

from . import apresentacao_dados
from .apresentacao import br, montar_apresentacao

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


INICIO_ANIMADO_CACHE = 'ifem:inicio_animado:v15'


def _faixa(rotulo):
    """'Acima de 500 mil' -> 'com mais de 500 mil habitantes'; '30 a 100 mil' -> 'de 30 a 100 mil habitantes'."""
    r = rotulo.lower()
    hab = ' de habitantes' if r.endswith('milhão') else ' habitantes'  # "1 milhão de habitantes"
    if r.startswith('acima de '):
        return 'com mais de ' + r[len('acima de '):] + hab
    if r.startswith('até '):
        return 'com até ' + r[len('até '):] + hab
    return 'de ' + r + hab


def _sem_hab(texto):
    return texto.replace(' de habitantes', '').replace(' habitantes', '')


def _mi(v):
    """Milhoes como no slide da FNP: 93 e 42,4 (sem ",0")."""
    texto = br(v, 1)
    return texto[:-2] if texto.endswith(',0') else texto


def _em_relacao_ao_pais(v):
    return f'{br(abs(v), 1)}% {"acima" if v >= 0 else "abaixo"}'


def _texto_porte_receita(d):
    """Dois paragrafos do passo de porte, escolhidos pelo dado.

    1) as faixas cuja populacao cresceu acima do pais; 2) quanto a receita por
    habitante delas cresceu em relacao ao pais, contra a faixa que menos cresceu
    em populacao. Devolve dict com os dois textos (HTML) ou None sem dados.
    """
    rot, pop, rec, br_pop = d['rotulos'], d['populacao'], d['receita'], d['populacao_brasil']
    idx = [i for i in range(len(rot)) if pop[i] is not None and rec[i] is not None]
    if not idx or br_pop is None:
        return None
    acima = sorted((i for i in idx if pop[i] > br_pop), key=lambda i: -pop[i])
    if not acima:
        return None
    devagar = min(idx, key=lambda i: pop[i])

    def cidades(i, curto=False):
        # Da segunda mencao em diante: "nas de 30 a 100 mil", sem repetir "cidades" e "habitantes".
        return 'nas ' + _sem_hab(_faixa(rot[i])) if curto else 'nas cidades ' + _faixa(rot[i])

    def junta(itens):
        return ', '.join(itens[:-1]) + ' e ' + itens[-1] if len(itens) > 1 else itens[0]

    p1 = (f'Entre 2000 e 2025, a população do país cresceu {br(br_pop, 1)}%. Cresceu mais '
          + junta([f'{cidades(i, k > 0)} ({br(pop[i], 1)}%)' for k, i in enumerate(acima)]) + '.')
    # "Nao acompanhou" so vale para quem cresceu menos em receita por habitante
    # do que a faixa que menos ganhou gente; as outras entram como excecao.
    ref = rec[devagar] if devagar not in acima else min(rec[i] for i in idx)
    nao = [i for i in acima if rec[i] < ref]
    exc = [i for i in acima if rec[i] >= ref]

    def valor(i):
        return f'<strong class="fx-num-destaque">{_em_relacao_ao_pais(rec[i])}</strong> {cidades(i, True)}'

    if not nao:
        p2 = ('Em relação ao país, a receita por habitante ficou '
              + junta([valor(i) for i in acima]) + '.')
        return {'p1': p1, 'p2': p2}
    p2 = (('Mas a receita por habitante não acompanhou' if not exc else
           'Mas, ' + ('na maioria' if len(nao) > len(exc) else 'em parte') + ' delas, a receita por habitante não acompanhou')
          + ': em relação ao país, ficou ' + junta([valor(i) for i in nao]))
    if devagar not in acima:
        verbo = 'encolheu' if pop[devagar] < 0 else 'quase não cresceu'
        p2 += (f', contra {_em_relacao_ao_pais(rec[devagar])} {cidades(devagar)}, onde a população {verbo}')
    p2 += '.'
    if exc:
        faixas = junta([f'{_sem_hab(_faixa(rot[i]))} ({_em_relacao_ao_pais(rec[i])})' for i in exc])
        p2 += (f' A exceção é a faixa {faixas}.' if len(exc) == 1 else f' As exceções são as faixas {faixas}.')
    return {'p1': p1, 'p2': p2}


def inicio_animado_preview(request):
    """Landing animada (/preview/inicio-animado/), fora do menu.

    Abre com o hero da landing publica e conta o metodo dos quintis numa unica
    animacao guiada pelo scroll: mapa dos municipios que declararam receita,
    grade ordenada pela receita por habitante, os cinco quintis e a populacao
    de cada quintil em 2000 e 2025. Desenho em static/ifem/js/inicio_animado.js;
    o contorno dos municipios vem de static/ifem/dados/malha_municipios.json
    (gerado por export_malha_inicio.py).
    """
    dados = cache.get(INICIO_ANIMADO_CACHE)
    if dados is None:
        dados = apresentacao_dados.municipios_animacao()
        cache.set(INICIO_ANIMADO_CACHE, dados, 30 * 60)

    q, pop, gr, tend, mig = dados['quintis'], dados['populacao'], dados['grandes'], dados['tendencia'], dados['migracao']
    anos = dados['pop_anos']  # séries por ano, cada uma do 1º ao 5º quintil
    textos = {
        'total': br(dados['total']),
        'grandes_n': br(gr['n']),
        'grandes_limite': br(gr['limite'] // 1000),
        'grandes_pct_mun': br(gr['pct_municipios'], 1),
        'grandes_pop': br(gr['populacao'] / 1e6, 1),
        'grandes_pct_pop': br(gr['pct_populacao'], 1),
        'tend_ano_ini': str(tend['anos'][0]),  # texto: o template poria separador de milhar ("2.000")
        'tend_ano_fim': str(tend['anos'][-1]),
        'tend_pct_ini': br(tend['pct'][0], 1),
        'tend_pct_fim': br(tend['pct'][-1], 1),
        'tend_sobe_todo_ano': all(b > a for a, b in zip(tend['pct'], tend['pct'][1:])),
        'grandes_q1': br(gr['por_quintil'][1]),
        'grandes_q5': br(gr['por_quintil'][5]),
        'declarantes': br(dados['declarantes']),
        'pct_declarantes': br(dados['pct_declarantes'], 1),
        'por_grupo': br(q['por_grupo']),
        'por_grupo_2000': br(dados['por_grupo_2000']),
        'media_1q': br(q['media_1q']),
        'media_5q': br(q['media_5q']),
        'razao': br(q['razao_5q_1q'], 1),
        'mig_mudou': br(mig['mudou_pct'], 1),
        'mig_fica_1q': br(mig['continua_pct'][1] or 0),
        'mig_fica_5q': br(mig['continua_pct'][5] or 0),
        'p1_2000': br(pop['pop_1q_2000'], 1),
        'p5_2000': br(pop['pop_5q_2000'], 1),
        'p1_2025': br(pop['pop_1q_2025'], 1),
        'p5_2025': br(pop['pop_5q_2025'], 1),
        'q1_cresceu': pop['pop_1q_2025'] > pop['pop_1q_2000'],
        'anos_ini': str(anos['anos'][0]),
        'anos_fim': str(anos['anos'][-1]),
        'anos_1q_ini': _mi(anos['series'][0][0]),
        'anos_1q_fim': _mi(anos['series'][-1][0]),
        'anos_1q_ganho': _mi(anos['series'][-1][0] - anos['series'][0][0]),
        'anos_5q_ini': _mi(anos['series'][0][4]),
        'anos_5q_fim': _mi(anos['series'][-1][4]),
        'anos_5q_caiu': anos['series'][-1][4] < anos['series'][0][4],
        'indicadores': [(ind['id'], ind['nome']) for ind in dados['indicadores']],
        'porte': _texto_porte_receita(dados['porte']),
        'pct_transf': dados['composicao']['pct_transferencias'],
        'pct_propria': dados['composicao']['pct_propria'],
        'transf_corte': br(dados['transf_corte'] * 100),
        'transf_acima': br(dados['transf_acima']),
        'transf_total': br(dados['transf_total']),
        'pct_transf_acima': br(dados['transf_acima'] / dados['transf_total'] * 100) if dados['transf_total'] else '0',
        'fpm': dados['fpm'],
        'fpm_1q_antes': _mi(dados['fpm']['series'][0]['valores'][0]),
        'fpm_1q_depois': _mi(dados['fpm']['series'][1]['valores'][0]),
        'fpm_5q_antes': _mi(dados['fpm']['series'][0]['valores'][4]),
        'fpm_5q_depois': _mi(dados['fpm']['series'][1]['valores'][4]),
        'fpm_piora': dados['fpm']['series'][1]['valores'][0] > dados['fpm']['series'][0]['valores'][0],
    }

    return render(request, 'ifem/inicio_animado.html', {
        't': textos,
        'animacao_json': dados,
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
