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


# Faixas da landing animada (/preview/inicio-animado/). Comecam no corte de
# 80 mil habitantes, o de "cidade grande" no resto do IFEM. Com 80 a 200 mil
# (escolha da equipe, out/2026), a receita por habitante dessa faixa cresce
# mais que a de 30 a 80 mil: a queda por porte nao e continua a partir de 30
# mil. So 80 a 500 mil numa faixa unica mantinha essa ordem.
_FAIXAS_PORTE_ANIMACAO = [
    (0, 5_000, 'Até 5 mil'),
    (5_000, 10_000, '5 a 10 mil'),
    (10_000, 30_000, '10 a 30 mil'),
    (30_000, 80_000, '30 a 80 mil'),
    (80_000, 200_000, '80 a 200 mil'),
    (200_000, 500_000, '200 a 500 mil'),
    (500_000, 10 ** 10, 'Acima de 500 mil'),
]


def crescimento_por_porte(faixas=_FAIXAS_PORTE):
    """Crescimento da população 2000 a 2025 por faixa de porte (população de 2025).

    Taxa do agregado (soma de 2025 / soma de 2000 - 1), não a média das taxas
    municipais: a média dava o mesmo peso a uma cidade de 3 mil e a uma de 3
    milhões, e não reproduz o slide.
    """
    soma = defaultdict(lambda: [0, 0])
    for p00, p25 in _universo().values_list('dados_2000__populacao_00', 'dados_atuais__populacao_atual'):
        if not p00 or not p25:
            continue
        for ini, fim, nome in faixas:
            if ini <= p25 < fim:
                soma[nome][0] += p00
                soma[nome][1] += p25
                break
    valores = []
    for _, _, nome in faixas:
        p00, p25 = soma[nome]
        valores.append(round((p25 / p00 - 1) * 100, 1) if p00 else None)
    return {'rotulos': [n for _, _, n in faixas], 'valores': valores, 'unidade': '%'}


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


# ---------------------------------------------------------------------------
# Módulos vindos da landing antiga (ifem/index.html)
# ---------------------------------------------------------------------------
def composicao_receita():
    """Quanto da receita corrente dos municípios vem de transferências (%).

    Mesma conta da view da landing antiga (home.views.index): transferências
    correntes contra impostos + contribuições + outras receitas, somadas no país.
    """
    from home.models import ContaDetalhada

    agg = ContaDetalhada.objects.aggregate(
        trf=Sum('transferencias_correntes'),
        imp=Sum('imposto_taxas_contribuicoes'),
        con=Sum('contribuicoes'),
        out=Sum('outras_receita'),
    )
    trf = agg['trf'] or 0
    propria = (agg['imp'] or 0) + (agg['con'] or 0) + (agg['out'] or 0)
    total = trf + propria
    pct_trf = round(trf / total * 100) if total else 0
    return {
        'rotulos': ['Transferências', 'Arrecadação própria'],
        'valores': [pct_trf, 100 - pct_trf],
        'cores': ['#1B3A6B', '#FFC72C'],
        'pct_transferencias': pct_trf,
        'pct_propria': 100 - pct_trf,
    }


def descompasso():
    """População do 1º e do 5º quintil em 2000 e 2025, com a variação (%)."""
    d = populacao_por_quintil()

    def var(a, b):
        return round((b / a - 1) * 100, 1) if a else None

    return {
        'q1': {'p2000': d['pop_1q_2000'], 'p2025': d['pop_1q_2025'], 'var': var(d['pop_1q_2000'], d['pop_1q_2025'])},
        'q5': {'p2000': d['pop_5q_2000'], 'p2025': d['pop_5q_2025'], 'var': var(d['pop_5q_2000'], d['pop_5q_2025'])},
    }


def receita_por_porte(faixas=_FAIXAS_PORTE):
    """Crescimento real da receita por habitante (2000 a 2025) por porte, em
    relação ao crescimento do país (%).

    Receita por habitante de cada faixa = soma da receita / soma da população,
    em 2000 e em 2025 (valores de 2000 já corrigidos para 2025 na base). O
    número é quanto a faixa cresceu ACIMA (+) ou ABAIXO (-) do Brasil:
    (1 + crescimento da faixa) / (1 + crescimento do país) - 1.
    """
    soma = defaultdict(lambda: [0, 0, 0, 0])  # pop00, pop25, rc00, rc25
    tot = [0, 0, 0, 0]
    linhas = _universo().values_list(
        'dados_2000__populacao_00', 'dados_atuais__populacao_atual', 'dados_2000__rc_00', 'dados_atuais__rc_atual'
    )
    for p00, p25, r00, r25 in linhas:
        if not (p00 and p25 and r00 and r25):
            continue
        for ini, fim, nome in faixas:
            if ini <= p25 < fim:
                for i, v in enumerate((p00, p25, r00, r25)):
                    soma[nome][i] += v
                    tot[i] += v
                break
    if not tot[0]:
        return {'rotulos': [], 'valores': []}
    cresc_pais = (tot[3] / tot[1]) / (tot[2] / tot[0])
    valores = []
    for _, _, nome in faixas:
        p00, p25, r00, r25 = soma[nome]
        valores.append(round(((r25 / p25) / (r00 / p00) / cresc_pais - 1) * 100, 1) if p00 and p25 and r00 else None)
    return {'rotulos': [n for _, _, n in faixas], 'valores': valores, 'unidade': '%'}


def participacao_80_mil():
    """Parcela da população em municípios acima e abaixo de 80 mil habitantes, 2000 e 2025.

    O corte usa a população de cada ano: um município que passou de 80 mil
    entre 2000 e 2025 muda de grupo, que é justamente o movimento retratado.
    """
    acima = {'2000': 0, '2025': 0}
    total = {'2000': 0, '2025': 0}
    for p00, p25 in Municipio.objects.values_list('dados_2000__populacao_00', 'dados_atuais__populacao_atual'):
        for ano, p in (('2000', p00), ('2025', p25)):
            if not p:
                continue
            total[ano] += p
            if p > 80_000:
                acima[ano] += p
    pct = {ano: round(acima[ano] / total[ano] * 100, 1) if total[ano] else 0 for ano in total}
    return {
        'rotulos': ['2000', '2025'],
        'series': [
            {'nome': 'Acima de 80 mil habitantes', 'valores': [pct['2000'], pct['2025']], 'cor': '#122747'},
            {'nome': 'Até 80 mil habitantes', 'valores': [round(100 - pct['2000'], 1), round(100 - pct['2025'], 1)], 'cor': '#EEAF19'},
        ],
        'acima_2000': pct['2000'],
        'acima_2025': pct['2025'],
    }


def medias_decis():
    """Receita média por habitante de cada decil (para o passo "ordenar para entender")."""
    linhas = dict(
        _universo().values_list('dados_atuais__decil_atual').annotate(m=Avg('dados_atuais__rc_atual_pc'))
    )

    def chave(nome):
        try:
            return int(str(nome).split('º')[0])
        except (TypeError, ValueError):
            return 99

    ordem = sorted(linhas, key=chave)
    return [{'decil': d, 'media': round(linhas[d] or 0)} for d in ordem if chave(d) <= 10]


# ---------------------------------------------------------------------------
# Landing animada (/preview/inicio-animado/)
# ---------------------------------------------------------------------------
def _num_quintil(valor):
    """'1º quintil' -> 1. Sem quintil -> 0."""
    try:
        return int(str(valor)[0])
    except (TypeError, ValueError):
        return 0


_LIMITE_GRANDES = 80000

# Passo "2023 a 2025": população (milhões) de cada quintil, ano a ano, do
# gráfico "Distribuição da população entre 2023 e 2025 (IBGE) por grupo de
# subfinanciamento dos municípios". Números fixos, como a simulação do FPM:
# o 2025 daqui difere um pouco do de populacao_por_quintil (passo anterior).
_POP_QUINTIL_ANOS = {
    2023: [74.4, 51.2, 35.1, 34.5, 13.8],
    2024: [81.9, 51.9, 33.7, 30.1, 13.2],
    2025: [93.0, 46.0, 30.6, 28.1, 12.9],
}

# Passo das transferências: azul quando elas passam desta parcela da receita
# corrente (0,7 = 70% transferências, 30% arrecadação própria).
_CORTE_TRANSF = 0.7

# Parcela da população (%) nos municípios com mais de 80 mil habitantes, ano a
# ano. 2000 a 2024: transcritos do gráfico enviado pela equipe (a série anual
# por município não está em base_datas). 2025 é calculado em
# municipios_animacao, com a mesma base dos outros passos.
_PCT_GRANDES_POR_ANO = {
    2000: 55.2, 2001: 55.9, 2002: 56.4, 2003: 56.6, 2004: 57.0,
    2005: 57.4, 2006: 57.6, 2007: 57.8, 2008: 58.1, 2009: 58.4,
    2010: 58.7, 2011: 59.0, 2012: 59.3, 2013: 59.6, 2014: 59.8,
    2015: 60.0, 2016: 60.3, 2017: 60.5, 2018: 60.7, 2019: 61.0,
    2020: 61.2, 2021: 61.3, 2022: 61.4, 2023: 61.6, 2024: 61.7,
}

# Tipos de risco do AdaptaBrasil, na ordem e com os nomes do seletor da aba
# Gráficos (home_folheto.html, riscoTipoSelect): (campo da API, nome, grupo).
# O primeiro é o que abre.
_RISCOS_CLIMATICOS = [
    ('media_ponderada', 'Risco climático médio', None),
    ('bio_int_bio', 'Integridade do Bioma', 'Biodiversidade'),
    ('des_des_ter', 'Deslizamento de Terra', 'Desastres Geo-hidrológicos'),
    ('des_in_enx_ala', 'Inundações e Alagamentos', 'Desastres Geo-hidrológicos'),
    ('rec_ris_est_hid', 'Risco de Estresse Hídrico', 'Recursos Hídricos'),
    ('sau_arb', 'Arboviroses (Dengue, Zika, Chikungunya)', 'Saúde'),
    ('sau_lei_teg_ame', 'Leishmaniose Tegumentar Americana', 'Saúde'),
    ('sau_lei_vis', 'Leishmaniose Visceral', 'Saúde'),
    ('sau_mal', 'Malária', 'Saúde'),
    ('seg_ali_ace_con_ali', 'Acesso e Consumo de Alimentos', 'Segurança Alimentar'),
    ('seg_ali_dis', 'Disponibilidade de Alimentos', 'Segurança Alimentar'),
    ('seg_ene_ace', 'Acesso à Energia', 'Segurança Energética'),
    ('seg_ene_dis', 'Disponibilidade de Energia', 'Segurança Energética'),
]

# Passo "Outros indicadores": os gráficos da aba Gráficos (/analise/), com o
# seletor de variável. Cada indicador tem uma ou mais opções (o segundo
# seletor do cartão, com o rótulo 'sub_rotulo'). Cada opção: a consulta à API,
# o nome no segundo seletor e o grupo (optgroup), 'pct' para a frequência
# relativa (% dos municípios de cada quintil), o título do gráfico (o curto
# entra quando o longo não cabe), a nota de leitura e as faixas somadas na
# frase do cartão, com o jeito de chamá-las. As notas resumem o "Como ler" da aba.
_NOTA_RISCO = ('Frequência relativa: a parcela dos municípios de cada quintil em cada nível de risco '
               'do AdaptaBrasil, um índice de 0 a 1 (alto a partir de 0,6; muito alto a partir de 0,8). '
               'Cada quintil soma 100%.')

_INDICADORES_ANALISE = [
    {'id': 'receita_media', 'nome': 'Receita média por habitante', 'opcoes': [
        {'consulta': 'variavel_analisada=receita_media',
         'nota': 'Média simples da receita corrente por habitante dos municípios do grupo, em 2025.'},
    ]},
    {'id': 'risco_climatico', 'nome': 'Risco climático', 'sub_rotulo': 'Tipo de risco', 'opcoes': [
        {'id': campo, 'nome': nome, 'grupo': grupo, 'pct': True,
         'consulta': f'variavel_analisada=risco_climatico&risco_campo={campo}&display_format=porcentagem',
         'titulo': f'Municípios por nível de risco (%): {nome}',
         'titulo_curto': 'Municípios por nível de risco (%)',
         'nota': _NOTA_RISCO, 'destaque': ['Muito alto', 'Alto'], 'destaque_txt': 'com risco alto ou muito alto'}
        for campo, nome, grupo in _RISCOS_CLIMATICOS
    ]},
    {'id': 'saude_fiscal', 'nome': 'CAPAG', 'opcoes': [
        {'consulta': 'variavel_analisada=saude_fiscal&display_format=porcentagem', 'pct': True,
         'titulo': 'Municípios por nota da CAPAG (%)',
         'nota': 'Frequência relativa: a parcela dos municípios de cada quintil em cada nota da Capacidade '
                 'de Pagamento (CAPAG), do Tesouro Nacional. A e B incluem A+ e B+; "D e outros" junta a '
                 'nota D e quem não tem nota (n.d., n.e.). Cada quintil soma 100%.',
         'destaque': ['A'], 'destaque_txt': 'com nota A na CAPAG'},
    ]},
    {'id': 'educacao', 'nome': 'IDEB', 'sub_rotulo': 'Mostrar', 'opcoes': [
        {'id': 'media', 'nome': 'Nota média', 'consulta': 'variavel_analisada=educacao',
         'nota': 'Nota média no IDEB das escolas municipais, anos iniciais do ensino fundamental. '
                 'Municípios sem nota ficam fora.'},
        {'id': 'faixas', 'nome': 'Municípios por faixa de nota (%)', 'pct': True,
         'consulta': 'variavel_analisada=educacao&educacao_tipo=faixas&display_format=porcentagem',
         'titulo': 'Municípios por faixa de nota no IDEB (%)',
         'nota': 'Frequência relativa: a parcela dos municípios de cada quintil em cada faixa de nota no IDEB '
                 '(escolas municipais, anos iniciais). A meta nacional é 6. Só entram os municípios com nota, '
                 'e cada quintil soma 100%.',
         'destaque': ['7 ou acima', 'Entre 6 e 6,9'], 'destaque_txt': 'com nota 6 ou mais'},
    ]},
    {'id': 'renda', 'nome': 'Renda média das famílias', 'opcoes': [
        {'consulta': 'variavel_analisada=renda',
         'nota': 'Rendimento médio mensal domiciliar por habitante (Censo 2022, IBGE), ponderado pela população.'},
    ]},
    {'id': 'seguranca', 'nome': 'Segurança pública', 'opcoes': [
        {'consulta': 'variavel_analisada=seguranca',
         'nota': 'Homicídios por 100 mil habitantes (Atlas da Violência), ponderados pela população.'},
    ]},
]


def indicadores_analise():
    """Os gráficos da aba Gráficos para a landing animada, por indicador e opção.

    Os números saem da própria API da aba (home.views.api_get_dashboard_data),
    com os filtros padrão dela (país inteiro, quintis) mais os da opção. Assim
    os dois gráficos não divergem. Cada indicador: id, nome, sub_rotulo e as
    opções; cada opção: id, nome, grupo, tipo ('media' = uma barra por quintil;
    'contagem' = municípios por faixa, empilhados), pct, unidade, títulos e as
    séries, na ordem da pilha (de baixo para cima).
    """
    import json
    from django.http import HttpRequest, QueryDict
    from home.views import api_get_dashboard_data

    def grafico(consulta):
        req = HttpRequest()
        req.method = 'GET'
        req.GET = QueryDict(consulta)
        return json.loads(api_get_dashboard_data(req).content)['chartData']

    saida = []
    for ind in _INDICADORES_ANALISE:
        opcoes = []
        for op in ind['opcoes']:
            g = grafico(op['consulta'])
            series = [{'rotulo': ds['label'].replace(' (2025)', ''), 'valores': ds['data']}
                      for ds in g.get('datasets', [])]
            if op.get('pct'):
                # Em % a API divide por todos os municípios do quintil: quem não tem o
                # dado vira uma faixa própria, para a pilha fechar em 100%.
                falta = [100 - sum(v or 0 for v in col) for col in zip(*(s['valores'] for s in series))]
                if any(f > 0.05 for f in falta):
                    series.insert(0, {'rotulo': 'Sem dados', 'valores': [round(max(f, 0), 2) for f in falta]})
            opcoes.append({
                'id': op.get('id', ind['id']), 'nome': op.get('nome'), 'grupo': op.get('grupo'),
                'tipo': g.get('tipo'), 'pct': bool(op.get('pct')), 'unidade': g.get('unidade'),
                'titulo': op.get('titulo') or g.get('yAxisTitle'), 'titulo_curto': op.get('titulo_curto'),
                'nota': op['nota'], 'series': series,
                'destaque': op.get('destaque'), 'destaque_txt': op.get('destaque_txt'),
            })
        saida.append({'id': ind['id'], 'nome': ind['nome'], 'sub_rotulo': ind.get('sub_rotulo'), 'opcoes': opcoes})
    return saida


def municipios_animacao():
    """Um registro por município do país, para a animação mapa > grade > barras.

    Cada linha: [cod_ibge, lon, lat, receita por hab. 2025, quintil 2025,
    população 2025, quintil 2000, população 2000, parcela das transferências
    na receita corrente (0 a 1, ou None)]. Quintil 0 = fora do universo
    daquele ano (sem receita corrente informada), com as mesmas regras de
    `populacao_por_quintil`: as barras desenhadas no navegador somam os mesmos
    totais do texto e da página de Gráficos.

    Também leva os números dos passos finais: crescimento por porte, origem
    da receita e a simulação do FPM.
    """
    from home.models import ContaDetalhada

    transf = {}
    for cod, trf, imp, con, out in ContaDetalhada.objects.values_list(
        'municipio__cod_ibge', 'transferencias_correntes', 'imposto_taxas_contribuicoes',
        'contribuicoes', 'outras_receita',
    ):
        total = (trf or 0) + (imp or 0) + (con or 0) + (out or 0)
        if total > 0:
            transf[str(cod)] = round((trf or 0) / total, 3)

    linhas = Municipio.objects.values_list(
        'cod_ibge', 'coordx', 'coordy',
        'dados_atuais__rc_atual', 'dados_atuais__rc_atual_pc', 'dados_atuais__quintil_atual',
        'dados_atuais__populacao_atual',
        'dados_2000__rc_00', 'dados_2000__quintil_00', 'dados_2000__populacao_00',
    )
    municipios = []
    for cod, x, y, rc25, rc25_pc, q25, p25, rc00, q00, p00 in linhas:
        q25 = _num_quintil(q25) if rc25 and rc25 > 0 else 0
        q00 = _num_quintil(q00) if rc00 and rc00 > 0 else 0
        municipios.append([
            str(cod),
            round(x, 3) if x is not None else None,
            round(y, 3) if y is not None else None,
            round(rc25_pc, 2) if q25 and rc25_pc is not None else None,
            q25, p25 or 0, q00, p00 or 0,
            transf.get(str(cod)) if q25 else None,
        ])

    # Crescimento da população do país, no mesmo universo de crescimento_por_porte.
    p00_tot = p25_tot = 0
    for p00, p25 in _universo().values_list('dados_2000__populacao_00', 'dados_atuais__populacao_atual'):
        if p00 and p25:
            p00_tot += p00
            p25_tot += p25

    com_transf = [m[8] for m in municipios if m[8] is not None]
    total = len(municipios)
    declarantes = sum(1 for m in municipios if m[4])

    # Passos de abertura: as cidades com mais de 80 mil habitantes em 2025 (o
    # mesmo corte "acima de 80 mil" dos filtros) e quanto da população vive nelas.
    pop_total = sum(m[5] for m in municipios)
    pop_grandes = sum(m[5] for m in municipios if m[5] > _LIMITE_GRANDES)
    n_grandes = sum(1 for m in municipios if m[5] > _LIMITE_GRANDES)
    # Quantas delas caem em cada quintil de 2025 (índice 0 = sem receita declarada).
    grandes_quintil = [0] * 6
    for m in municipios:
        if m[5] > _LIMITE_GRANDES:
            grandes_quintil[m[4]] += 1
    pct_grandes = round(pop_grandes / pop_total * 100, 1) if pop_total else 0
    anos = sorted(_PCT_GRANDES_POR_ANO)

    # Passo "As cidades mudam de quintil": quintil de 2000 x quintil de 2025,
    # entre os municípios com receita declarada nos dois anos.
    ambos = [(m[6], m[4]) for m in municipios if m[6] and m[4]]
    continua_pct = [None]  # índice = quintil de 2000
    for q in range(1, 6):
        do_q = [q25 for q00, q25 in ambos if q00 == q]
        continua_pct.append(round(do_q.count(q) / len(do_q) * 100, 1) if do_q else None)
    return {
        'municipios': municipios,
        'total': total,
        'declarantes': declarantes,
        'pct_declarantes': round(declarantes / total * 100, 1) if total else 0,
        'grandes': {
            'limite': _LIMITE_GRANDES,
            'n': n_grandes,
            'pct_municipios': round(n_grandes / total * 100, 1) if total else 0,
            'populacao': pop_grandes,
            'populacao_total': pop_total,
            'pct_populacao': pct_grandes,
            'por_quintil': grandes_quintil,
        },
        # Passo "Onde moram os brasileiros?": a mesma parcela, de 2000 a 2025.
        'tendencia': {
            'anos': anos + [2025],
            'pct': [_PCT_GRANDES_POR_ANO[a] for a in anos] + [pct_grandes],
        },
        'migracao': {
            'mudou_pct': round(sum(1 for q00, q25 in ambos if q00 != q25) / len(ambos) * 100, 1) if ambos else 0,
            'continua_pct': continua_pct,
        },
        # Municípios por quintil em 2000 (os de 2025 estão em quintis['por_grupo']).
        'por_grupo_2000': round(sum(1 for m in municipios if m[6]) / 5),
        'quintis': resumo_quintis(),
        'populacao': populacao_por_quintil(),
        'porte': {
            # Limites das faixas, para o navegador agrupar os municípios igual.
            'limites': [[ini, fim] for ini, fim, _ in _FAIXAS_PORTE_ANIMACAO],
            'rotulos': [nome for _, _, nome in _FAIXAS_PORTE_ANIMACAO],
            'populacao': crescimento_por_porte(_FAIXAS_PORTE_ANIMACAO)['valores'],
            'receita': receita_por_porte(_FAIXAS_PORTE_ANIMACAO)['valores'],
            'populacao_brasil': round((p25_tot / p00_tot - 1) * 100, 1) if p00_tot else None,
        },
        'composicao': composicao_receita(),
        'pop_anos': {
            'anos': sorted(_POP_QUINTIL_ANOS),
            'series': [_POP_QUINTIL_ANOS[a] for a in sorted(_POP_QUINTIL_ANOS)],  # uma lista por ano, do 1º ao 5º quintil
        },
        'indicadores': indicadores_analise(),
        'transf_corte': _CORTE_TRANSF,
        'transf_acima': sum(1 for v in com_transf if v > _CORTE_TRANSF),
        'transf_total': len(com_transf),
        'fpm': fpm_mais_50_bi(),
    }
