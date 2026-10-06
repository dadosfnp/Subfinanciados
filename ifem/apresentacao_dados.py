"""Fornecedores de dados da apresentação da landing (/preview/inicio/).

Cada função devolve um dict pronto para o JSON da página e lê o banco na hora,
para a apresentação acompanhar qualquer atualização da base sem tocar em
código. A exceção declarada é `fpm_mais_50_bi`, que devolve números fixos até
a simulação existir no banco; trocar a fonte é trocar só aquela função.

Universo: os mesmos municípios que o resto do IFEM usa (receita corrente
informada, `dados_atuais__rc_atual > 0`), para os números baterem com as
páginas de Gráficos e Agregado.

As contas foram conferidas contra a apresentação "IFEM - Poá - O desafio da
sustentabilidade fiscal" (out/2026): população por quintil em 2025, CAPAG por
quintil e risco climático por quintil batem com os slides; o crescimento por
porte difere em décimos porque o slide usou uma base de população anterior.
"""
from collections import defaultdict

from django.db.models import Avg, Count, Sum

from detail_mun.saude_fiscal import _nota_capag
from home.models import Municipio

QUINTIS = ['1º quintil', '2º quintil', '3º quintil', '4º quintil', '5º quintil']
ROTULOS_QUINTIS = ['1º quintil', '2º quintil', '3º quintil', '4º quintil', '5º quintil']


def _universo():
    return Municipio.objects.filter(dados_atuais__rc_atual__gt=0)


def _milhoes(valor):
    return round((valor or 0) / 1_000_000, 1)


def populacao_por_quintil():
    """População (milhões) em cada quintil de receita por habitante, 2000 e 2025.

    Cada ano usa os SEUS quintis: em 2000, os quintis da receita de 2000. É a
    leitura do slide: onde a população morava em cada momento, e não para onde
    foram as pessoas de um mesmo grupo.
    """
    p25 = dict(
        _universo().values_list('dados_atuais__quintil_atual')
        .annotate(p=Sum('dados_atuais__populacao_atual'))
    )
    p00 = dict(
        Municipio.objects.filter(dados_2000__rc_00__gt=0)
        .values_list('dados_2000__quintil_00')
        .annotate(p=Sum('dados_2000__populacao_00'))
    )
    return {
        'rotulos': ROTULOS_QUINTIS,
        'series': [
            {'nome': '2000', 'valores': [_milhoes(p00.get(q)) for q in QUINTIS], 'cor': '#EEAF19'},
            {'nome': '2025', 'valores': [_milhoes(p25.get(q)) for q in QUINTIS], 'cor': '#1B3A6B'},
        ],
        'unidade': 'milhões de habitantes',
        'pop_1q_2000': _milhoes(p00.get(QUINTIS[0])),
        'pop_1q_2025': _milhoes(p25.get(QUINTIS[0])),
        'pop_5q_2000': _milhoes(p00.get(QUINTIS[4])),
        'pop_5q_2025': _milhoes(p25.get(QUINTIS[4])),
    }


def resumo_quintis():
    """Quantos municípios há em cada quintil e a receita média por habitante deles."""
    linhas = (
        _universo().values('dados_atuais__quintil_atual')
        .annotate(n=Count('cod_ibge'), media=Avg('dados_atuais__rc_atual_pc'))
    )
    por_q = {l['dados_atuais__quintil_atual']: l for l in linhas}
    grupos = []
    for q in QUINTIS:
        l = por_q.get(q, {})
        grupos.append({'quintil': q, 'n': l.get('n', 0), 'media': round(l.get('media') or 0)})
    total = sum(g['n'] for g in grupos)
    return {
        'grupos': grupos,
        'total': total,
        'por_grupo': round(total / 5) if total else 0,
        'media_1q': grupos[0]['media'],
        'media_5q': grupos[4]['media'],
        'razao_5q_1q': round(grupos[4]['media'] / grupos[0]['media'], 1) if grupos[0]['media'] else None,
    }


def municipio_exemplo(cod_ibge='3510609'):
    """O município usado como exemplo na abertura (padrão: Carapicuíba-SP).

    Parametrizado para a apresentação poder trocar de exemplo sem mexer no
    texto: o texto lê nome, população e receita daqui.
    """
    m = (
        Municipio.objects.select_related('dados_atuais')
        .filter(cod_ibge=cod_ibge).first()
    )
    media = _universo().aggregate(m=Avg('dados_atuais__rc_atual_pc'))['m'] or 0
    if m is None or not getattr(m, 'dados_atuais', None):
        return {'ok': False, 'media_nacional': round(media)}
    rc = m.dados_atuais.rc_atual_pc or 0
    return {
        'ok': True,
        'nome': m.name_muni_uf,
        'populacao_mil': round((m.dados_atuais.populacao_atual or 0) / 1000),
        'receita_pc': round(rc),
        'receita_pc_mes': round(rc / 12, 1),
        'media_nacional': round(media),
        'fracao_da_media': round(rc / media, 2) if media else None,
    }


# Faixas de população de 2025, as mesmas do slide "Taxa de crescimento
# populacional por porte".
_FAIXAS_PORTE = [
    (0, 5_000, 'Até 5 mil'),
    (5_000, 10_000, '5 a 10 mil'),
    (10_000, 30_000, '10 a 30 mil'),
    (30_000, 100_000, '30 a 100 mil'),
    (100_000, 500_000, '100 a 500 mil'),
    (500_000, 10 ** 10, 'Acima de 500 mil'),
]


def crescimento_por_porte():
    """Crescimento da população 2000 a 2025 por faixa de porte (população de 2025).

    Taxa do agregado (soma de 2025 / soma de 2000 - 1), não a média das taxas
    municipais: a média dava o mesmo peso a uma cidade de 3 mil e a uma de 3
    milhões, e não reproduz o slide.
    """
    soma = defaultdict(lambda: [0, 0])
    for p00, p25 in _universo().values_list('dados_2000__populacao_00', 'dados_atuais__populacao_atual'):
        if not p00 or not p25:
            continue
        for ini, fim, nome in _FAIXAS_PORTE:
            if ini <= p25 < fim:
                soma[nome][0] += p00
                soma[nome][1] += p25
                break
    valores = []
    for _, _, nome in _FAIXAS_PORTE:
        p00, p25 = soma[nome]
        valores.append(round((p25 / p00 - 1) * 100, 1) if p00 else None)
    return {'rotulos': [n for _, _, n in _FAIXAS_PORTE], 'valores': valores, 'unidade': '%'}


def capag_por_quintil():
    """Parcela dos municípios de cada quintil em cada nota da CAPAG (%).

    "D e abaixo" junta D e os sem nota (n.d., n.e.), como no slide e no gráfico
    da home ("D e outros").
    """
    cont = defaultdict(lambda: defaultdict(int))
    for q, nota in _universo().values_list('dados_atuais__quintil_atual', 'dados_atuais__capag'):
        letra = _nota_capag(nota)
        cont[q]['D' if letra in (None, 'D') else letra] += 1

    def pct(q, chave):
        total = sum(cont[q].values())
        return round(cont[q][chave] / total * 100, 1) if total else 0

    cores = {'A': '#1C9148', 'B': '#6AC074', 'C': '#E47326', 'D': '#A81C21'}
    nomes = {'A': 'Nota A', 'B': 'Nota B', 'C': 'Nota C', 'D': 'D e abaixo'}
    series = [{'nome': nomes[k], 'valores': [pct(q, k) for q in QUINTIS], 'cor': cores[k]} for k in 'ABCD']
    alta = [round(series[0]['valores'][i] + series[1]['valores'][i], 1) for i in range(5)]
    return {
        'rotulos': ROTULOS_QUINTIS,
        'series': series,
        'unidade': '% dos municípios',
        'nota_alta_1q': alta[0],
        'nota_alta_5q': alta[4],
    }


def risco_por_quintil():
    """Parcela dos municípios de cada quintil em cada nível de risco climático (%).

    Usa a média ponderada do AdaptaBrasil, com os mesmos cortes da tabela do
    município: abaixo de 0,4 baixo, até 0,6 médio, 0,6 ou mais alto.
    """
    cont = defaultdict(lambda: defaultdict(int))
    for q, r in _universo().values_list('dados_atuais__quintil_atual', 'dados_adapta_brasil__media_ponderada'):
        if r is None:
            continue
        cont[q]['baixo' if r < 0.4 else ('medio' if r < 0.6 else 'alto')] += 1

    def pct(q, chave):
        total = sum(cont[q].values())
        return round(cont[q][chave] / total * 100, 1) if total else 0

    series = [
        {'nome': 'Alto e muito alto', 'valores': [pct(q, 'alto') for q in QUINTIS], 'cor': '#A81C21'},
        {'nome': 'Médio', 'valores': [pct(q, 'medio') for q in QUINTIS], 'cor': '#F4D01D'},
        {'nome': 'Baixo e muito baixo', 'valores': [pct(q, 'baixo') for q in QUINTIS], 'cor': '#1C9148'},
    ]
    return {
        'rotulos': ROTULOS_QUINTIS,
        'series': series,
        'unidade': '% dos municípios',
        'alto_1q': series[0]['valores'][0],
        'alto_5q': series[0]['valores'][4],
    }


def fpm_mais_50_bi():
    """Simulação: população por quintil com mais R$ 50 bi no FPM.

    FONTE FIXA. Números da apresentação da FNP (slide "Resultado da análise da
    distribuição da população de 2025 + R$ 50 bi de FPM"). Quando a simulação
    estiver no banco, só esta função muda; o módulo e o texto continuam iguais.
    """
    return {
        'rotulos': ROTULOS_QUINTIS,
        'series': [
            {'nome': '2025', 'valores': [93, 46, 30.6, 28.1, 13.2], 'cor': '#1B3A6B'},
            {'nome': '2025 com mais R$ 50 bi no FPM', 'valores': [99, 42.4, 31.3, 25.5, 12.3], 'cor': '#1C9148'},
        ],
        'unidade': 'milhões de habitantes',
        'fonte_fixa': True,
    }


def pontos_do_mapa():
    """Um ponto por município: [lon, lat, quintil (1 a 5), população em mil, região].

    Coordenadas com 2 casas (cerca de 1 km), o bastante para um mapa de pontos
    do país e menos da metade do tamanho do JSON.
    """
    cod_regiao = {}
    pontos = []
    linhas = _universo().filter(coordx__isnull=False, coordy__isnull=False).values_list(
        'coordx', 'coordy', 'dados_atuais__quintil_atual', 'dados_atuais__populacao_atual', 'regiao'
    )
    for x, y, q, pop, regiao in linhas:
        try:
            nq = int(str(q)[0])
        except (TypeError, ValueError):
            continue
        r = cod_regiao.setdefault(regiao, len(cod_regiao))
        pontos.append([round(x, 2), round(y, 2), nq, round((pop or 0) / 1000), r])

    # Resumo do 1º e do 5º quintil para os textos dos passos do mapa.
    regioes = list(cod_regiao)
    idx_norte_nordeste = {i for i, nome in enumerate(regioes) if nome in ('Norte', 'Nordeste')}
    resumo = {}
    for q in (1, 5):
        doq = [p for p in pontos if p[2] == q]
        n = len(doq)
        resumo[f'q{q}'] = {
            'n': n,
            'pct_norte_nordeste': round(sum(1 for p in doq if p[4] in idx_norte_nordeste) / n * 100) if n else 0,
            'acima_80_mil': sum(1 for p in doq if p[3] >= 80),
            'abaixo_80_mil': sum(1 for p in doq if p[3] < 80),
        }
    return {'pontos': pontos, 'regioes': regioes, 'resumo': resumo}
