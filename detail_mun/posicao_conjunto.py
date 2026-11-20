"""Posicao de um conjunto de municipios nos rankings nacionais.

Usado pelo hero da preview do agregado (/preview/agregado/), que repete o texto
aprovado do hero do municipio: "ocupa o Xº lugar em porte populacional" e
"em receita corrente per capita". Um conjunto nao tem lugar oficial no
ranking, entao a conta trata o conjunto como se fosse um municipio so:

- populacao: soma da populacao do conjunto contra a populacao de cada
  municipio do pais;
- receita: a receita corrente por habitante do conjunto (o mesmo valor do
  destaque do hero) contra a de cada municipio com receita.

Posicao = quantos municipios tem valor MAIOR + 1, a mesma convencao dos
rankings gravados na base (1º = maior). O percentil segue a regra do IFEM
usada no municipio: (total - posicao) / total * 100.
"""
import logging

from home.models import Municipio

logger = logging.getLogger(__name__)


def _ranking(campo, valor):
    """Posicao de `valor` entre os municipios com `campo` > 0.

    Retorna dict {pos, total, percentil} ou None quando nao ha valor/base.
    Duas contagens indexaveis por consulta; nada de carregar a lista inteira.
    """
    if valor is None or valor <= 0:
        return None
    base = Municipio.objects.filter(**{f'{campo}__gt': 0})
    total = base.count()
    if not total:
        return None
    pos = base.filter(**{f'{campo}__gt': valor}).count() + 1
    return {'pos': pos, 'total': total, 'percentil': round((total - pos) / total * 100, 2)}


def posicao_do_conjunto(populacao, receita_pc):
    """Posicao do conjunto em porte populacional e em receita corrente per capita.

    Args:
        populacao: soma da populacao atual do conjunto.
        receita_pc: receita corrente por habitante do conjunto.

    Returns:
        {'populacao': {...} | None, 'receita': {...} | None}. Em erro de banco
        devolve os dois como None e registra: o hero cai no texto sem posicao
        em vez de derrubar a API inteira dos KPIs.
    """
    try:
        return {
            'populacao': _ranking('dados_atuais__populacao_atual', populacao),
            'receita': _ranking('dados_atuais__rc_atual_pc', receita_pc),
        }
    except Exception:
        logger.exception('Falha ao calcular posicao do conjunto',
                         extra={'populacao': populacao, 'receita_pc': receita_pc})
        return {'populacao': None, 'receita': None}
