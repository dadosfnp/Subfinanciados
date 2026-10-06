"""Apresentação da landing (/preview/inicio/), montada em módulos.

COMO ACRESCENTAR UM MÓDULO
--------------------------
A apresentação é a lista `BLOCOS`, na ordem em que aparece na página. Há três
tipos de bloco:

  - `Capa`: abertura de tela cheia (título, subtítulo, imagem de fundo);
  - `Capitulo`: tela de transição com uma pergunta, como os slides de título;
  - `Trilha`: o scrollytelling. Uma lista de `Passo`; o texto de cada passo
    rola à esquerda e o visual dele fica fixo à direita.

Um `Passo` declara:
  - `dados`: função de ifem/apresentacao_dados.py (ou None). Roda a cada
    montagem; é ela que liga o passo ao banco.
  - `texto`: função que recebe o dict de `dados` e devolve o HTML do texto.
    Função, e não string com {chaves}, para o texto poder escolher a frase
    conforme o número ("menos de um terço" ou "metade").
  - `visual`: o tipo de visual que o JS sabe desenhar (ver VISUAIS abaixo) e
    `opcoes` para ele.

Para um gráfico novo: escreva o fornecedor em apresentacao_dados.py, crie o
Passo aqui e, se for um tipo de visual novo, ensine o
static/ifem/js/inicio_folheto.js a desenhá-lo.

FALHAS
------
Um passo que falhar (dado ausente, erro de query) é registrado no log e sai
da página sozinho; o resto da apresentação continua de pé.
"""
import logging
from dataclasses import dataclass, field
from typing import Callable, Optional

from django.core.cache import cache
from django.utils.html import escape

from . import apresentacao_dados as dados

logger = logging.getLogger(__name__)

# Tipos de visual que o static/ifem/js/inicio_folheto.js desenha.
VISUAIS = {
    'imagem',        # uma foto (opcoes: src, alt, legenda)
    'imagem_dupla',  # duas fotos lado a lado (opcoes: imagens=[{src, alt, legenda}])
    'lista',         # frase grande com tópicos (opcoes: titulo, itens)
    'quintis',       # diagrama dos cinco grupos (dados: resumo_quintis)
    'barras',        # barras agrupadas (dados: rotulos + series)
    'barras_h',      # barras horizontais (dados: rotulos + valores)
    'empilhada',     # barras 100% empilhadas (dados: rotulos + series)
    'mapa',          # pontos dos municípios (dados: pontos_do_mapa; opcoes: quintis, porte)
    'rosca',         # rosca de duas fatias (dados: rotulos + valores + cores)
    'descompasso',   # população do 1º e do 5º quintil, 2000 x 2025 (dados: descompasso)
    'pilha_h',       # barras horizontais 100% empilhadas (dados: rotulos + series)
}

# A montagem roda ~10 consultas agregadas. Cache curto: a base muda raramente,
# e meia hora de atraso depois de um recriar_banco é aceitável numa landing.
CACHE_CHAVE = 'ifem:apresentacao:v2'
CACHE_SEGUNDOS = 30 * 60


# `secao` (em Hero, Capitulo, Trilha e Fechamento) é o nome que aparece no
# navegador de seções (global/js/fx-secoes.js). Blocos vizinhos com o mesmo
# nome viram um item só: um capítulo e a trilha que ele abre, por exemplo.

@dataclass
class Hero:
    """Abertura com vídeo de fundo: a cara do IFEM desde a landing antiga."""
    titulo: str
    subtitulo: str
    video: str
    botao: str = 'Começar a história'
    secao: str = 'Início'
    tipo: str = 'hero'


@dataclass
class Capitulo:
    """Tela de transição. `titulo` aceita <mark> para o destaque amarelo dos slides."""
    titulo: str
    secao: str = ''
    imagem: str = 'ifem/apresentacao/cidade-azul.webp'
    tipo: str = 'capitulo'


@dataclass
class Passo:
    id: str
    titulo: str
    texto: Callable[[dict], str]
    visual: str
    dados: Optional[Callable[[], dict]] = None
    opcoes: dict = field(default_factory=dict)
    fonte: str = ''
    nota: str = ''

    def __post_init__(self):
        if self.visual not in VISUAIS:
            raise ValueError(f'Passo {self.id}: visual desconhecido {self.visual!r}')


@dataclass
class Trilha:
    id: str
    passos: list
    secao: str = ''
    tipo: str = 'trilha'


@dataclass
class Fechamento:
    titulo: str
    grupos: list  # [{'titulo': ..., 'itens': [...]}]
    imagem: str = 'ifem/apresentacao/palha.webp'
    secao: str = 'O que fazer'
    tipo: str = 'fechamento'


# ---------------------------------------------------------------------------
# Formatação (pt-BR) usada pelos textos
# ---------------------------------------------------------------------------
def br(valor, casas=0):
    """Número no formato brasileiro: 1.234,5."""
    if valor is None:
        return 'n/d'
    texto = f'{valor:,.{casas}f}'
    return texto.replace(',', 'X').replace('.', ',').replace('X', '.')


def destaque(texto):
    """Número em destaque no texto do passo (vermelho FNP, como no site de referência)."""
    return f'<strong class="fx-num-destaque">{texto}</strong>'


def _fracao_da_media(fracao):
    if fracao is None:
        return 'bem abaixo da média nacional'
    if fracao < 0.34:
        return 'menos de um terço da média nacional'
    if fracao < 0.5:
        return 'menos da metade da média nacional'
    return f'{br(fracao * 100)}% da média nacional'


def _pct(parte, total):
    return round(parte / total * 100) if total else 0


def _texto_porte(d):
    """Cita as duas faixas que mais cresceram e a de menor crescimento, pelo dado."""
    pares = [(v, r) for v, r in zip(d['valores'], d['rotulos']) if v is not None]
    if not pares:
        return '<p>Sem dados de crescimento por porte.</p>'
    ordem = sorted(pares, reverse=True)
    (v1, r1), (v2, r2) = ordem[0], ordem[1] if len(ordem) > 1 else ordem[0]
    vmin, rmin = ordem[-1]
    return (
        f'<p>Entre 2000 e 2025, a população cresceu mais nas {destaque(_cidades(r1))} ({br(v1, 1)}%) '
        f'e nas {_cidades(r2)} ({br(v2, 1)}%).</p>'
        f'<p>Nas {_cidades(rmin)}, a variação foi de {br(vmin, 1)}%.</p>'
    )


def _cidades(rotulo):
    """'Acima de 500 mil' -> 'cidades com mais de 500 mil habitantes'."""
    r = rotulo.lower()
    if r.startswith('acima de '):
        return 'cidades com mais de ' + r[len('acima de '):] + ' habitantes'
    if r.startswith('até '):
        return 'cidades com até ' + r[len('até '):] + ' habitantes'
    return 'cidades de ' + r + ' habitantes'


def _texto_paradoxo(d):
    """Contrasta as faixas que ganharam receita relativa com as que perderam, pelo dado."""
    pares = [(v, r) for v, r in zip(d.get('valores', []), d.get('rotulos', [])) if v is not None]
    if not pares:
        return '<p>Sem dados de receita por porte.</p>'
    vmax, rmax = max(pares)
    vmin, rmin = min(pares)
    texto = (
        '<p>O modelo atual aumenta a receita por habitante onde a população estagna e a reduz onde ela cresce.</p>'
        f'<p>Nas {_cidades(rmax)}, a receita por habitante cresceu '
        f'{destaque(br(vmax, 1) + "%")} acima do país. '
    )
    if vmin < 0:
        texto += f'Nas {_cidades(rmin)}, ficou {destaque(br(abs(vmin), 1) + "%")} abaixo.</p>'
    else:
        texto += f'Nas {_cidades(rmin)}, só {br(vmin, 1)}% acima.</p>'
    return texto


FONTE_IFEM = 'Fonte: IFEM (FNP), com dados do Siconfi/STN e do IBGE.'

# ---------------------------------------------------------------------------
# A apresentação
# ---------------------------------------------------------------------------
BLOCOS = [
    Hero(
        titulo='O dinheiro na <mark>contramão</mark><br>da população.',
        subtitulo='Cidades mudaram, a distribuição de recursos não.',
        video='ifem/videos/videohero.mp4',
    ),

    Trilha('problema', secao='O problema', passos=[
        Passo(
            id='contramao',
            titulo='O dinheiro na contramão',
            dados=dados.composicao_receita,
            texto=lambda d: (
                '<p>O sistema de transferências para os municípios brasileiros apoia-se em regras da '
                '<strong>década de 1960</strong>. O Brasil mudou, o contexto das cidades mudou, mas as regras '
                'de financiamento não acompanharam.</p>'
                f'<p>E elas pesam: {destaque(br(d["pct_transferencias"]) + "%")} da receita corrente dos '
                'municípios vem de transferências da União e dos estados. Só '
                f'{br(d["pct_propria"])}% é arrecadação própria.</p>'
            ),
            visual='rosca',
            opcoes={'titulo': 'De onde vem a receita dos municípios', 'subtitulo': 'Receita corrente de todos os municípios, 2025'},
            fonte=FONTE_IFEM,
        ),
        Passo(
            id='descompasso',
            titulo='O descompasso',
            dados=dados.descompasso,
            texto=lambda d: (
                '<p>Em 2000, os 20% de municípios com menor receita por habitante reuniam '
                f'{br(d["q1"]["p2000"], 1)} milhões de pessoas. Em 2025, {destaque(br(d["q1"]["p2025"], 1) + " milhões")}.</p>'
                f'<p>No outro extremo, os 20% com maior receita por habitante foram de {br(d["q5"]["p2000"], 1)} '
                f'para {br(d["q5"]["p2025"], 1)} milhões. Como os dois grupos têm o mesmo número de municípios, '
                'o resultado é claro: cada vez mais brasileiros vivem em municípios estruturalmente subfinanciados.</p>'
            ),
            visual='descompasso',
            fonte='Fonte: IFEM (FNP), com população do IBGE.',
        ),
    ]),

    Trilha('cidades', secao='As cidades mudaram', passos=[
        Passo(
            id='1960',
            titulo='O Brasil de 1960',
            texto=lambda d: (
                '<p>Em 1960, as <strong>cidades grandes</strong> eram as mais dinâmicas e tinham mais recursos '
                'por habitante. As <strong>pequenas</strong>, as que tinham poucos recursos.</p>'
                '<p>O sistema de repasses foi desenhado para aquele tempo, e as regras são praticamente '
                'as mesmas até hoje: regras antigas, contexto novo.</p>'
            ),
            visual='imagem_dupla',
            opcoes={'imagens': [
                {'src': 'ifem/apresentacao/1960-cidade-grande.webp', 'alt': 'Avenida movimentada de cidade grande nos anos 1960', 'legenda': 'Cidade grande, 1960'},
                {'src': 'ifem/apresentacao/1960-cidade-pequena.webp', 'alt': 'Cidade pequena entre morros nos anos 1960', 'legenda': 'Cidade pequena, 1960'},
            ]},
        ),
        Passo(
            id='2025',
            titulo='O Brasil de 2025',
            dados=dados.municipio_exemplo,
            texto=lambda d: (
                f'<p>Hoje o retrato é outro. {escape(d["nome"])} tem {destaque(br(d["populacao_mil"]) + " mil")} '
                f'habitantes e {destaque("R$ " + br(d["receita_pc"]))} de receita por habitante ao ano: '
                f'{_fracao_da_media(d["fracao_da_media"])} (R$ {br(d["media_nacional"])}).</p>'
                '<p>As cidades que mais cresceram ficaram com a menor parte do dinheiro.</p>'
            ) if d.get('ok') else '<p>Hoje o retrato é outro: as cidades que mais cresceram ficaram com a menor parte do dinheiro.</p>',
            visual='imagem',
            opcoes={'src': 'ifem/apresentacao/carapicuiba-2025.webp', 'alt': 'Vista aérea de Carapicuíba, SP', 'legenda': 'Carapicuíba (SP), 2025'},
            fonte=FONTE_IFEM,
        ),
        Passo(
            id='subfinanciados',
            titulo='Municípios subfinanciados',
            texto=lambda d: (
                '<p>São os municípios com <strong>pouca receita por habitante</strong>, '
                '<strong>população crescendo rápido</strong> e uma população que '
                '<strong>depende muito de serviços públicos</strong>.</p>'
            ),
            visual='lista',
            opcoes={'titulo': 'Municípios subfinanciados', 'itens': [
                'Baixa receita corrente por habitante',
                'Crescimento populacional acelerado',
                'População altamente demandante de políticas públicas',
            ]},
        ),
    ]),

    Capitulo(titulo='Igualdade <mark>≠</mark> <mark>Equidade</mark>', secao='Igualdade e equidade'),

    Trilha('equidade', secao='Igualdade e equidade', passos=[
        Passo(
            id='equidade',
            titulo='Tratar igual quem é diferente',
            dados=dados.municipio_exemplo,
            texto=lambda d: (
                '<p>Dar a mesma coisa a todos não deixa todos no mesmo lugar. Quem começa com '
                'menos precisa de mais para enxergar por cima do muro.</p>'
                + (f'<p>Como gerir uma cidade com {destaque("R$ " + br(d["receita_pc_mes"], 1))} '
                   'por habitante por mês?</p>' if d.get('ok') else '')
            ),
            visual='imagem',
            opcoes={'src': 'ifem/apresentacao/igualdade-equidade.webp', 'alt': 'Ilustração: igualdade dá a mesma caixa a todos; equidade dá a cada um o que precisa para ver por cima do muro', 'legenda': 'Igualdade e equidade'},
        ),
    ]),

    Capitulo(titulo='Receita municipal: <mark>proporcional ou desigual</mark>?', secao='Receita desigual'),

    Trilha('quintis', secao='Receita desigual', passos=[
        Passo(
            id='quintis',
            titulo='Cinco grupos do mesmo tamanho',
            dados=dados.resumo_quintis,
            texto=lambda d: (
                '<p>Para comparar contextos tão diferentes, o IFEM usa um método simples: '
                '<strong>ordenar para entender</strong>.</p>'
                f'<p>Ordenamos os {destaque(br(d["total"]))} municípios pela receita corrente por habitante '
                f'e dividimos em cinco grupos de cerca de {br(d["por_grupo"])} cada: os <strong>quintis</strong>. '
                'Em mais detalhe, dez grupos: os decis.</p>'
                f'<p>No 1º quintil, a média é de R$ {br(d["media_1q"])} por habitante ao ano. No 5º, '
                f'R$ {br(d["media_5q"])}: {destaque(br(d["razao_5q_1q"], 1) + " vezes mais")}.</p>'
            ),
            visual='quintis',
            fonte=FONTE_IFEM,
        ),
        Passo(
            id='populacao',
            titulo='Para onde foi a população',
            dados=dados.populacao_por_quintil,
            texto=lambda d: (
                f'<p>Em 2000, {br(d["pop_1q_2000"], 1)} milhões de pessoas viviam nos municípios do 1º quintil. '
                f'Em 2025, são {destaque(br(d["pop_1q_2025"], 1) + " milhões")}.</p>'
                f'<p>No 5º quintil, o caminho foi o inverso: de {br(d["pop_5q_2000"], 1)} para '
                f'{br(d["pop_5q_2025"], 1)} milhões.'
                + (' Cada vez mais gente mora onde há menos dinheiro por habitante.'
                   if d["pop_1q_2025"] > d["pop_1q_2000"] else '')
                + '</p>'
            ),
            visual='barras',
            opcoes={'titulo': 'População por quintil de receita por habitante', 'subtitulo': 'Milhões de habitantes, 2000 e 2025'},
            fonte='Fonte: IFEM (FNP), com população do IBGE. Cada ano usa os quintis daquele ano.',
        ),
        Passo(
            id='porte',
            titulo='Quem mais cresceu',
            dados=dados.crescimento_por_porte,
            texto=lambda d: _texto_porte(d),
            visual='barras_h',
            opcoes={'titulo': 'Crescimento da população por porte', 'subtitulo': '2000 a 2025, em %, pela população de 2025'},
            fonte='Fonte: IBGE (censos e estimativas), organizado pelo IFEM.',
        ),
        Passo(
            id='paradoxo',
            titulo='O paradoxo do crescimento',
            dados=dados.receita_por_porte,
            texto=lambda d: _texto_paradoxo(d),
            visual='barras_h',
            opcoes={'titulo': 'Receita por habitante: crescimento em relação ao país', 'subtitulo': '2000 a 2025, em %, valores corrigidos pela inflação'},
            fonte=FONTE_IFEM,
        ),
        Passo(
            id='participacao',
            titulo='Onde vive a maioria',
            dados=dados.participacao_80_mil,
            texto=lambda d: (
                f'<p>Em 2000, {br(d["acima_2000"], 1)}% dos brasileiros viviam em municípios com mais de 80 mil '
                f'habitantes. Em 2025, {destaque(br(d["acima_2025"], 1) + "%")}.</p>'
                '<p>Cada vez mais gente vive nas cidades maiores, e menos gente nas menores. '
                'Os recursos públicos seguem o caminho oposto.</p>'
            ),
            visual='pilha_h',
            opcoes={'titulo': 'Participação da população', 'subtitulo': '% da população em municípios acima e até 80 mil habitantes'},
            fonte='Fonte: IBGE, organizado pelo IFEM.',
        ),
    ]),

    Capitulo(titulo='E como isso impacta a <mark>Capacidade de Pagamento</mark> dos municípios (CAPAG)?', secao='CAPAG'),

    Trilha('capag', secao='CAPAG', passos=[
        Passo(
            id='capag',
            titulo='Menos dinheiro, nota pior',
            dados=dados.capag_por_quintil,
            texto=lambda d: (
                f'<p>No 1º quintil, só {destaque(br(d["nota_alta_1q"], 1) + "%")} dos municípios têm nota '
                f'A ou B na CAPAG do Tesouro. No 5º quintil, são {destaque(br(d["nota_alta_5q"], 1) + "%")}.</p>'
                '<p>Nota C ou pior impede contratar crédito com garantia da União: quem tem menos '
                'receita também tem menos acesso a financiamento.</p>'
            ),
            visual='empilhada',
            opcoes={'titulo': 'Nota da CAPAG por quintil', 'subtitulo': '% dos municípios de cada quintil'},
            fonte='Fonte: Tesouro Nacional (CAPAG), organizado pelo IFEM.',
        ),
    ]),

    Capitulo(titulo='Qual a relação entre <mark>subfinanciamento</mark> e <mark>riscos climáticos</mark>?', secao='Riscos climáticos'),

    Trilha('clima', secao='Riscos climáticos', passos=[
        Passo(
            id='clima',
            titulo='Os mais pobres, os mais expostos',
            dados=dados.risco_por_quintil,
            texto=lambda d: (
                f'<p>{destaque(br(d["alto_1q"], 1) + "%")} dos municípios do 1º quintil estão em risco '
                f'climático alto ou muito alto. No 5º quintil, {destaque(br(d["alto_5q"], 1) + "%")}.</p>'
                '<p>Os municípios com menos dinheiro são justamente os mais expostos a enchentes, '
                'secas e doenças ligadas ao clima.</p>'
            ),
            visual='empilhada',
            opcoes={'titulo': 'Risco climático por quintil', 'subtitulo': '% dos municípios, média ponderada do AdaptaBrasil'},
            fonte='Fonte: AdaptaBrasil (MCTI), organizado pelo IFEM.',
        ),
    ]),

    Capitulo(titulo='E se magicamente o FPM aumentasse em <mark>R$ 50 bi</mark>?', secao='E se o FPM aumentasse?'),

    Trilha('fpm', secao='E se o FPM aumentasse?', passos=[
        Passo(
            id='fpm',
            titulo='Mais dinheiro, mesma lógica',
            dados=dados.fpm_mais_50_bi,
            texto=lambda d: (
                '<p>Distribuídos pelas regras atuais, mais R$ 50 bilhões no Fundo de Participação '
                'dos Municípios '
                + ('<strong>aumentariam</strong>' if d["series"][1]["valores"][0] > d["series"][0]["valores"][0] else 'mudariam')
                + ' a população do 1º quintil: de '
                f'{br(d["series"][0]["valores"][0], 1)} para {destaque(br(d["series"][1]["valores"][0], 1) + " milhões")}.</p>'
                + ('<p>Dinheiro novo pela regra antiga aprofunda a desigualdade em vez de corrigi-la.</p>'
                   if d["series"][1]["valores"][0] > d["series"][0]["valores"][0] else '')
            ),
            visual='barras',
            opcoes={'titulo': 'População por quintil com mais R$ 50 bi no FPM', 'subtitulo': 'Milhões de habitantes, simulação'},
            fonte='Fonte: simulação da FNP.',
            nota='Números da simulação apresentada pela FNP; ainda não vêm da base do IFEM.',
        ),
    ]),

    Trilha('mapa', secao='O mapa', passos=[
        Passo(
            id='mapa-todos',
            titulo='O mapa da desigualdade',
            dados=dados.pontos_do_mapa,
            texto=lambda d: (
                f'<p>Cada ponto é um dos {destaque(br(len(d["pontos"])))} municípios, na cor do seu quintil: '
                'do vermelho (1º, menor receita por habitante) ao verde (5º, maior).</p>'
            ),
            visual='mapa',
            opcoes={'quintis': [1, 2, 3, 4, 5]},
            fonte=FONTE_IFEM,
        ),
        Passo(
            id='mapa-1q',
            titulo='Onde está o 1º quintil',
            dados=dados.pontos_do_mapa,
            texto=lambda d: (
                f'<p>{destaque(br(d["resumo"]["q1"]["pct_norte_nordeste"]) + "%")} dos '
                f'{br(d["resumo"]["q1"]["n"])} municípios do 1º quintil ficam no Norte e no Nordeste.</p>'
            ),
            visual='mapa',
            opcoes={'quintis': [1]},
        ),
        Passo(
            id='mapa-5q',
            titulo='Onde está o 5º quintil',
            dados=dados.pontos_do_mapa,
            texto=lambda d: (
                f'<p>No 5º quintil, só {destaque(br(d["resumo"]["q5"]["pct_norte_nordeste"]) + "%")} estão no Norte e '
                f'no Nordeste. E {br(_pct(d["resumo"]["q5"]["abaixo_80_mil"], d["resumo"]["q5"]["n"]))}% deles '
                'têm menos de 80 mil habitantes.</p>'
            ),
            visual='mapa',
            opcoes={'quintis': [5]},
        ),
        Passo(
            id='mapa-80mil',
            titulo='Tamanho importa',
            dados=dados.pontos_do_mapa,
            texto=lambda d: (
                f'<p>Entre os municípios com mais de 80 mil habitantes, {destaque(br(d["resumo"]["q1"]["acima_80_mil"]))} '
                f'estão no 1º quintil e só {destaque(br(d["resumo"]["q5"]["acima_80_mil"]))} no 5º.</p>'
                + ('<p>O tamanho do ponto mostra a população: o subfinanciamento pesa mais nas cidades grandes.</p>'
                   if d["resumo"]["q1"]["acima_80_mil"] > d["resumo"]["q5"]["acima_80_mil"] else '')
            ),
            visual='mapa',
            opcoes={'quintis': [1, 5], 'porte': 'acima_80_mil'},
        ),
    ]),

    Fechamento(
        titulo='Se o cenário muda, <mark>a lógica precisa acompanhar</mark>',
        grupos=[
            {'titulo': 'Curto prazo', 'itens': [
                'Tratamento diferenciado e prioritário em políticas públicas para municípios subfinanciados.',
            ]},
            {'titulo': 'Médio e longo prazo', 'itens': [
                'Rever as regras do federalismo fiscal brasileiro para torná-lo mais justo, com transição.',
            ]},
        ],
    ),
]


def _montar_passo(passo, memo):
    """Resolve dados e texto de um passo. None se falhar (o passo sai da página).

    `memo` guarda o resultado de cada fornecedor durante uma montagem: vários
    passos do mapa e do município de exemplo usam a mesma função.
    """
    try:
        if passo.dados is None:
            d = {}
        else:
            if passo.dados not in memo:
                memo[passo.dados] = passo.dados()
            d = memo[passo.dados]
        return {
            'id': passo.id,
            'titulo': passo.titulo,
            'texto': passo.texto(d),
            'visual': passo.visual,
            'opcoes': passo.opcoes,
            # Os pontos do mapa vão uma vez só, no bloco de dados compartilhados.
            'dados': None if passo.visual == 'mapa' else d,
            'fonte': passo.fonte,
            'nota': passo.nota,
        }
    except Exception:
        logger.exception('Falha ao montar o passo %s da apresentação', passo.id)
        return None


def montar_apresentacao():
    """Resolve todos os blocos. Devolve (blocos, dados_compartilhados).

    `dados_compartilhados` leva o que mais de um passo usa e é pesado para
    repetir no HTML (hoje, os pontos do mapa).
    """
    em_cache = cache.get(CACHE_CHAVE)
    if em_cache is not None:
        return em_cache

    blocos = []
    usa_mapa = False
    memo = {}
    for bloco in BLOCOS:
        if isinstance(bloco, Trilha):
            passos = [p for p in (_montar_passo(p, memo) for p in bloco.passos) if p]
            if not passos:
                continue
            usa_mapa = usa_mapa or any(p['visual'] == 'mapa' for p in passos)
            blocos.append({'tipo': 'trilha', 'id': bloco.id, 'secao': bloco.secao, 'passos': passos})
        else:
            blocos.append(dict(bloco.__dict__))

    compartilhados = {}
    if usa_mapa:
        try:
            if dados.pontos_do_mapa not in memo:
                memo[dados.pontos_do_mapa] = dados.pontos_do_mapa()
            compartilhados['mapa'] = memo[dados.pontos_do_mapa]
        except Exception:
            logger.exception('Falha ao montar os pontos do mapa da apresentação')

    resultado = (blocos, compartilhados)
    cache.set(CACHE_CHAVE, resultado, CACHE_SEGUNDOS)
    return resultado
