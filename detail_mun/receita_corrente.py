"""Linha "Receita corrente" no topo da Estrutura de Receitas (preview do municipio).

Por que um modulo proprio, e nao mais um `_prepare_revenue_item`:

- As tabelas de media pre-calculadas (MediaNacionalReceita, MediaUfReceita...)
  vem de planilhas e so tem as rubricas, nao o total. Media e mediana do total
  saem aqui, direto de `IndicadoresAtuais.rc_atual_pc`, com a mesma regra
  (media simples dos per capita) que a home ja usa para "receita media".
- O total nao pode entrar na `revenue_tree`: o script_mun.js reordena tudo que
  esta dentro da arvore por valor (o total sempre iria para o topo, mas por
  acidente) e manda o `field_base` para /api/distribuicao/, cuja allowlist nao
  conhece "receita corrente" com esse nome.

O dicionario devolvido tem o mesmo formato de um item da arvore, para o
template reaproveitar as mesmas colunas.
"""
import logging
import statistics

from django.core.cache import cache

from home.models import Municipio

logger = logging.getLogger(__name__)

# A distribuicao so muda quando a base e reimportada (recriar_banco); 30 min
# segue o cache da apresentacao (ifem/apresentacao.py). v1 no nome permite
# invalidar mudando a chave, sem precisar limpar o cache inteiro.
CACHE_CHAVE = 'ifem:receita_corrente:estatisticas:v1'
CACHE_SEGUNDOS = 30 * 60


def _estatisticas_por_uf():
    """Media e mediana de `rc_atual_pc` no Brasil e em cada UF.

    Uma consulta so (~5.500 pares uf/valor) e o calculo em Python: o Postgres
    teria mediana via percentile_cont, mas o ORM nao expoe isso sem SQL cru, e
    o volume e pequeno. O resultado vai para o cache, entao a conta roda uma
    vez por janela, nao por pageview.

    Returns:
        dict: {'nacional': {'media', 'mediana'}, 'uf': {'SP': {...}, ...}}
    """
    em_cache = cache.get(CACHE_CHAVE)
    if em_cache is not None:
        return em_cache

    pares = (Municipio.objects
             .filter(dados_atuais__rc_atual_pc__isnull=False)
             .values_list('uf', 'dados_atuais__rc_atual_pc'))

    todos, por_uf = [], {}
    for uf, valor in pares:
        todos.append(valor)
        por_uf.setdefault((uf or '').upper(), []).append(valor)

    def resumo(valores):
        if not valores:
            return {'media': None, 'mediana': None}
        return {'media': statistics.fmean(valores), 'mediana': statistics.median(valores)}

    resultado = {
        'nacional': resumo(todos),
        'uf': {uf: resumo(valores) for uf, valores in por_uf.items()},
    }
    cache.set(CACHE_CHAVE, resultado, CACHE_SEGUNDOS)
    return resultado


def _percentil_por_ranking(posicao, total):
    """Regra oficial do IFEM (folheto-ifem/python/core/paleta_ranking.py).

    percentil = (total - posicao) / total * 100. Posicao 1 = maior receita por
    habitante, logo ~100. Mesma conta que o script_mun_folheto.js faz no hero,
    para a linha e o hero nunca discordarem.
    """
    if not posicao or not total:
        return None
    return round((total - posicao) / total * 100, 1)


def montar_receita_corrente(municipio):
    """Monta a linha de total da Estrutura de Receitas.

    Args:
        municipio: instancia de Municipio com `dados_atuais` carregado.

    Returns:
        dict no formato de um item da revenue_tree (value_pc, value_abs,
        percentiles, media_*/mediana_*), ou None se o municipio nao tem receita
        corrente. Falha ao calcular as medias nao derruba a pagina: a linha sai
        com as caixas de media vazias.
    """
    valor_pc = municipio.rc_24_pc
    if valor_pc is None:
        return None

    try:
        estatisticas = _estatisticas_por_uf()
    except Exception:
        logger.exception('Falha ao calcular media/mediana da receita corrente',
                         extra={'cod_ibge': municipio.cod_ibge})
        estatisticas = {'nacional': {}, 'uf': {}}

    nacional = estatisticas.get('nacional') or {}
    estadual = (estatisticas.get('uf') or {}).get((municipio.uf or '').upper()) or {}

    def arred(v):
        # Arredonda antes do br_integer, que trunca: sem isto a linha mostraria
        # R$ 9.084 com o hero (que arredonda no JS) dizendo R$ 9.085.
        return round(v) if v is not None else None

    return {
        'name': 'Receita corrente',
        'value_pc': arred(valor_pc),
        'value_abs': municipio.rc_2024,
        'percentiles': {
            # Nacional: o percentil oficial gravado na base, o mesmo do hero.
            'nacional': municipio.percentil24_n,
            'estadual': _percentil_por_ranking(municipio.rank_estadual, municipio.total_estadual),
            'faixa': _percentil_por_ranking(municipio.rank_faixa, municipio.total_faixa),
        },
        'media_nacional': arred(nacional.get('media')),
        'media_estadual': arred(estadual.get('media')),
        'mediana_nacional': arred(nacional.get('mediana')),
        'mediana_estadual': arred(estadual.get('mediana')),
    }
