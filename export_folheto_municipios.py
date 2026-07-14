"""
Exporta, para cada municipio, um JSON com as informacoes necessarias para a
geracao do folheto (miolo). Tambem gera um arquivo unico `_metodologia.json`
com o texto da metodologia presente na landing page.

Saida:
    export_folheto/
        _metodologia.json
        <cod_ibge>_<slug-do-municipio>.json
        ...

Cada rubrica/categoria do payload inclui o campo `supera_pct_nacional`
(percentil entre 0 e 100), que representa a fracao de municipios com
per_capita estritamente MENOR para aquela mesma rubrica. Ex.: supera_pct=76
significa "este municipio supera 76% dos demais nessa rubrica".

Uso:
    python export_folheto_municipios.py [--limit N] [--cod_ibge 1100015,...]
"""
import argparse
import bisect
import json
import os
import re
import sys
import unicodedata

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from home.models import Municipio  # noqa: E402


# -------------------------- helpers --------------------------

def slugify(value: str) -> str:
    """Slug minimalista (sem dependencia de Django.utils)."""
    if value is None:
        return ''
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^A-Za-z0-9]+', '-', value).strip('-').lower()
    return value or 'sem-nome'


def faixa_porte_label(pop: int | None) -> str:
    """Replica a logica de `detail_mun.views.municipio_detalhe_view` para o porte."""
    pop = pop or 0
    if pop < 5000: return "Até 5 mil"
    if pop < 10000: return "5 mil a 10 mil"
    if pop < 20000: return "10 mil a 20 mil"
    if pop < 50000: return "20 mil a 50 mil"
    if pop < 100000: return "50 mil a 100 mil"
    if pop < 200000: return "100 mil a 200 mil"
    if pop < 500000: return "200 mil a 500 mil"
    return "Acima de 500 mil"


def rank(curr, total):
    """Empacota um par rank/total em dict (ou None se faltar dado)."""
    if curr is None or total is None:
        return None
    return {"posicao": curr, "total": total}


def delta_pct(novo, antigo):
    """Variacao percentual; None se nao puder calcular."""
    if not antigo or not novo or antigo <= 0:
        return None
    return round(((novo / antigo) - 1) * 100, 2)


# -------------------------- mapeamentos de receita --------------------------

# Estrutura da Receita - 4 principais grupos (ContaDetalhada).
GRUPOS_PRINCIPAIS = [
    ("imposto_taxas_contribuicoes", "Impostos, Taxas e Contribuições de Melhoria"),
    ("contribuicoes", "Contribuições"),
    ("transferencias_correntes", "Transferências Correntes"),
    ("outras_receita", "Outras Receitas"),
]

# Detalhamento (ContaEspecifica) - rubricas de 2o nivel.
DETALHE_ESPECIFICA = [
    ("imposto", "Impostos"),
    ("taxas", "Taxas"),
    ("contribuicoes_melhoria", "Contribuições de Melhoria"),
    ("contribuicoes_sociais", "Contribuições Sociais"),
    ("contribuicoes_iluminacao_publica", "Contribuição de Iluminação Pública"),
    ("outras_contribuicoes", "Outras Contribuições"),
    ("tranferencias_uniao", "Transferências da União"),
    ("tranferencias_estados", "Transferências dos Estados"),
    ("outras_tranferencias", "Outras Transferências"),
    ("receita_patrimonial", "Receita Patrimonial"),
    ("receita_agropecuaria", "Receita Agropecuária"),
    ("receita_industrial", "Receita Industrial"),
    ("receita_servicos", "Receita de Serviços"),
    ("outras_receitas", "Outras Receitas"),
]

# Detalhamento mais granular (ContaMaisEspecifica) - rubricas de 3o nivel.
DETALHE_MAIS_ESPECIFICA = [
    ("iptu", "IPTU"),
    ("itbi", "ITBI"),
    ("iss", "ISS"),
    ("imposto_renda", "Imposto de Renda"),
    ("imposto_icms", "ICMS"),
    ("imposto_ipva", "IPVA"),
    ("outros_impostos", "Outros Impostos"),
    ("taxa_policia", "Taxa de Polícia"),
    ("taxa_prestacao_servico", "Taxa de Prestação de Serviço"),
    ("outras_taxas", "Outras Taxas"),
    ("contribuicao_melhoria_pavimento_obras", "Contribuição de Melhoria - Pavimentação/Obras"),
    ("contribuicao_melhoria_agua_potavel", "Contribuição de Melhoria - Água Potável"),
    ("contribuicao_melhoria_iluminacao_publica", "Contribuição de Melhoria - Iluminação Pública"),
    ("outras_contribuicoes_melhoria", "Outras Contribuições de Melhoria"),
    ("transferencia_uniao_fpm", "Transferência União - FPM"),
    ("transferencia_uniao_exploracao", "Transferência União - Exploração de Recursos"),
    ("transferencia_uniao_sus", "Transferência União - SUS"),
    ("transferencia_uniao_fnde", "Transferência União - FNDE"),
    ("transferencia_uniao_fundeb", "Transferência União - FUNDEB"),
    ("transferencia_uniao_fnas", "Transferência União - FNAS"),
    ("transferencia_uniao_fpe", "Transferência União - FPE"),
    ("outras_transferencias_uniao", "Outras Transferências da União"),
    ("transferencia_estado_icms", "Transferência Estado - ICMS"),
    ("transferencia_estado_ipva", "Transferência Estado - IPVA"),
    ("transferencia_estado_exploracao", "Transferência Estado - Exploração de Recursos"),
    ("transferencia_estado_sus", "Transferência Estado - SUS"),
    ("transferencia_estado_assistencia", "Transferência Estado - Assistência"),
    ("outras_transferencias_estado", "Outras Transferências do Estado"),
]


def _anexa_percentil(out, field, percentis_do_muni):
    """Se houver percentil pre-computado para o campo, anexa ao dict da rubrica."""
    if percentis_do_muni and field in percentis_do_muni:
        out["supera_pct_nacional"] = percentis_do_muni[field]["supera_pct"]
        out["total_municipios_comparados"] = percentis_do_muni[field]["total"]
    return out


def receita_grupo(cd, pop, label_field, percentis_do_muni=None):
    """Monta o dict para um grupo da ContaDetalhada (valor absoluto e per capita)."""
    if not cd:
        return None
    field, label = label_field
    absoluto = getattr(cd, field, None)
    if absoluto is None:
        return None
    per_capita = round(absoluto / pop, 2) if pop else None
    out = {
        "rubrica": label,
        "field": field,
        "valor_absoluto": round(absoluto, 2),
        "per_capita": per_capita,
    }
    return _anexa_percentil(out, field, percentis_do_muni)


def serializa_detalhe(modelo, pop, mapeamento, percentis_do_muni=None):
    """Itera o mapeamento e retorna lista de rubricas com valor absoluto e per capita."""
    if not modelo:
        return []
    itens = []
    for field, label in mapeamento:
        absoluto = getattr(modelo, field, None)
        if absoluto is None or absoluto == 0:
            continue
        per_capita = round(absoluto / pop, 2) if pop else None
        item = {
            "rubrica": label,
            "field": field,
            "valor_absoluto": round(absoluto, 2),
            "per_capita": per_capita,
        }
        itens.append(_anexa_percentil(item, field, percentis_do_muni))
    return itens


# Mapeamento pai (nivel_2 -> nivel_1) e (nivel_3 -> nivel_2). Permite que o
# folheto saiba qual categoria-mae empilha cada subcard estilo landing IFEM.
PARENT_DE_NIVEL_2 = {
    "imposto": "imposto_taxas_contribuicoes",
    "taxas": "imposto_taxas_contribuicoes",
    "contribuicoes_melhoria": "imposto_taxas_contribuicoes",
    "contribuicoes_sociais": "contribuicoes",
    "contribuicoes_iluminacao_publica": "contribuicoes",
    "outras_contribuicoes": "contribuicoes",
    "tranferencias_uniao": "transferencias_correntes",
    "tranferencias_estados": "transferencias_correntes",
    "outras_tranferencias": "transferencias_correntes",
    "receita_patrimonial": "outras_receita",
    "receita_agropecuaria": "outras_receita",
    "receita_industrial": "outras_receita",
    "receita_servicos": "outras_receita",
    "outras_receitas": "outras_receita",
}

PARENT_DE_NIVEL_3 = {
    "iptu": "imposto", "itbi": "imposto", "iss": "imposto",
    "imposto_renda": "imposto", "imposto_icms": "imposto",
    "imposto_ipva": "imposto", "outros_impostos": "imposto",
    "taxa_policia": "taxas", "taxa_prestacao_servico": "taxas", "outras_taxas": "taxas",
    "contribuicao_melhoria_pavimento_obras": "contribuicoes_melhoria",
    "contribuicao_melhoria_agua_potavel": "contribuicoes_melhoria",
    "contribuicao_melhoria_iluminacao_publica": "contribuicoes_melhoria",
    "outras_contribuicoes_melhoria": "contribuicoes_melhoria",
    "transferencia_uniao_fpm": "tranferencias_uniao",
    "transferencia_uniao_exploracao": "tranferencias_uniao",
    "transferencia_uniao_sus": "tranferencias_uniao",
    "transferencia_uniao_fnde": "tranferencias_uniao",
    "transferencia_uniao_fundeb": "tranferencias_uniao",
    "transferencia_uniao_fnas": "tranferencias_uniao",
    "transferencia_uniao_fpe": "tranferencias_uniao",
    "outras_transferencias_uniao": "tranferencias_uniao",
    "transferencia_estado_icms": "tranferencias_estados",
    "transferencia_estado_ipva": "tranferencias_estados",
    "transferencia_estado_exploracao": "tranferencias_estados",
    "transferencia_estado_sus": "tranferencias_estados",
    "transferencia_estado_assistencia": "tranferencias_estados",
    "outras_transferencias_estado": "tranferencias_estados",
}


def compute_percentis_por_categoria(municipios_all):
    """
    Calcula o percentil de cada municipio em cada rubrica (todos os 3 niveis).

    Percentil = fracao de municipios com per_capita ESTRITAMENTE menor naquela
    rubrica. Municipios com mesmo per_capita compartilham o percentil (ties
    quebrados por bisect_left).

    Retorna: { cod_ibge: { field: {"supera_pct": int 0-100, "total": int} } }
    """
    mapeamentos = [
        ('conta_detalhada',       GRUPOS_PRINCIPAIS),
        ('conta_especifica',      DETALHE_ESPECIFICA),
        ('conta_mais_especifica', DETALHE_MAIS_ESPECIFICA),
    ]

    # 1) Coleta (per_capita, cod_ibge) para cada campo.
    valores_por_campo = {}
    for m in municipios_all:
        pop = m.populacao24
        if not pop or pop <= 0:
            continue
        for attr, mapping in mapeamentos:
            modelo = getattr(m, attr, None)
            if not modelo:
                continue
            for field, _ in mapping:
                v = getattr(modelo, field, None)
                if v is None:
                    continue
                pc = v / pop
                valores_por_campo.setdefault(field, []).append((pc, m.cod_ibge))

    # 2) Ordena cada lista por per_capita asc.
    for field in valores_por_campo:
        valores_por_campo[field].sort(key=lambda x: x[0])

    # 3) Para cada muni em cada campo: bisect_left na lista ordenada -> # estritamente menores.
    resultado = {}
    for field, lista in valores_por_campo.items():
        total = len(lista)
        valores_sorted = [pc for pc, _ in lista]
        for pc, cod in lista:
            n_menores = bisect.bisect_left(valores_sorted, pc)
            supera_pct = round(n_menores / total * 100) if total > 0 else 0
            resultado.setdefault(cod, {})[field] = {
                "supera_pct": supera_pct,
                "total": total,
            }
    return resultado


# -------------------------- montagem do JSON do municipio --------------------------

def build_municipio_payload(m: Municipio, percentis_do_muni: dict | None = None) -> dict:
    pop = m.populacao24
    porte = faixa_porte_label(pop)

    # Conta detalhada (4 grupos principais), ordenada por valor descendente.
    cd = getattr(m, 'conta_detalhada', None)
    estrutura_resumo = [
        item for item in
        (receita_grupo(cd, pop, lf, percentis_do_muni) for lf in GRUPOS_PRINCIPAIS)
        if item
    ]
    estrutura_resumo.sort(key=lambda x: x["valor_absoluto"], reverse=True)

    cs = getattr(m, 'conta_especifica', None)
    cme = getattr(m, 'conta_mais_especifica', None)

    # Sintese fiscal: variacoes 2000 -> 2024.
    sintese_fiscal = {
        "delta_receita_per_capita_pct": delta_pct(m.rc_24_pc, m.rc_00_pc),
        "delta_populacao_pct": delta_pct(m.populacao24, m.populacao00),
        "media_nacional_delta_receita_per_capita_pct": 316.74,
        "media_nacional_delta_populacao_pct": 16.04,
        "observacao": "Valores financeiros corrigidos pela inflacao para 2024.",
    }

    payload = {
        "identificacao": {
            "cod_ibge": m.cod_ibge,
            "municipio": m.name_muni,
            "uf": m.uf,
            "name_muni_uf": m.name_muni_uf,
            "regiao": m.regiao,
            "regiao_metropolitana": m.rm.nome if m.rm else None,
            "porte": porte,
            "coordenadas": {"x": m.coordx, "y": m.coordy},
        },
        "populacao": {
            "ano": 2024,
            "valor": pop,
            "ranking_nacional": rank(m.populacao24_rank_nacional, m.populacao24_total_nacional),
            "ranking_estadual": rank(m.populacao24_rank_estadual, m.populacao24_total_estadual),
            "ranking_por_porte": rank(m.populacao24_rank_faixa, m.populacao24_total_faixa),
        },
        "receita_corrente": {
            "ano": 2024,
            "valor_absoluto": m.rc_2024,
            "per_capita": m.rc_24_pc,
            "ranking_por_per_capita": {
                "nacional": rank(m.rank_nacional, m.total_nacional),
                "estadual": rank(m.rank_estadual, m.total_estadual),
                "por_porte": rank(m.rank_faixa, m.total_faixa),
            },
        },
        "sus_dependente": {
            "percentual_populacao": m.sus_dependente,
            "descricao": "Percentual da populacao dependente exclusivamente do SUS.",
        },
        "cadunico": {
            "qtd_pessoas_cadastradas": m.cadunico,
            "ranking_nacional": rank(m.cadunico_rank_nacional, m.cadunico_total_nacional),
            "ranking_estadual": rank(m.cadunico_rank_estadual, m.cadunico_total_estadual),
            "ranking_por_porte": rank(m.cadunico_rank_faixa, m.cadunico_total_faixa),
        },
        "percentil": {
            "ano": 2024,
            "percentil_label": m.percentil24,
            "percentil_numero": m.percentil24_n,
            "quintil": m.quintil24,
            "decil": m.decil24,
        },
        "estrutura_receita_resumo": estrutura_resumo,
        "estrutura_receita_detalhada": {
            "nivel_2_categorias": serializa_detalhe(cs, pop, DETALHE_ESPECIFICA, percentis_do_muni),
            "nivel_3_rubricas": serializa_detalhe(cme, pop, DETALHE_MAIS_ESPECIFICA, percentis_do_muni),
        },
        "hierarquia_receitas": {
            # Mapeia field -> label (utilitario para o folheto agrupar nivel_2 sob nivel_1 etc.)
            "nivel_1": [{"field": f, "label": l} for f, l in GRUPOS_PRINCIPAIS],
            "nivel_2": [
                {"field": f, "label": l, "parent_field": PARENT_DE_NIVEL_2.get(f)}
                for f, l in DETALHE_ESPECIFICA
            ],
            "nivel_3": [
                {"field": f, "label": l, "parent_field": PARENT_DE_NIVEL_3.get(f)}
                for f, l in DETALHE_MAIS_ESPECIFICA
            ],
        },
        "sintese_fiscal_2000_2024": sintese_fiscal,
        "posicao_historica": {
            "ano_2000": {
                "populacao": m.populacao00,
                "receita_corrente_absoluta": m.rc_2000,
                "receita_per_capita": m.rc_00_pc,
                "quintil": m.quintil00,
                "decil": m.decil00,
                "percentil_label": m.percentil00,
                "percentil_numero": m.percentil00_n,
                "ranking_nacional": rank(m.rank_nacional_00, m.total_nacional_00),
            },
            "ano_2024": {
                "populacao": m.populacao24,
                "receita_corrente_absoluta": m.rc_2024,
                "receita_per_capita": m.rc_24_pc,
                "quintil": m.quintil24,
                "decil": m.decil24,
                "percentil_label": m.percentil24,
                "percentil_numero": m.percentil24_n,
                "ranking_nacional": rank(m.rank_nacional, m.total_nacional),
            },
        },
    }
    return payload


# -------------------------- metodologia --------------------------

METODOLOGIA = {
    "titulo": "Indicadores de Financiamento e Equidade Municipal (IFEM)",
    "resumo": (
        "Para comparar contextos tao distintos, o IFEM utiliza um metodo simples e justo: "
        "ordenar para entender. Calculamos quanto cada municipio tem de receita para cada "
        "morador, dividindo a receita corrente pela populacao. Depois, organizamos todos os "
        "municipios do menor para o maior valor por habitante e os dividimos em grupos iguais "
        "para comparar situacoes semelhantes."
    ),
    "topicos": [
        {
            "pergunta": "Qual a base de dados utilizada?",
            "resposta": (
                "O IFEM e calculado a partir da Receita Corrente dos municipios. Os dados sao "
                "oficiais, extraidos dos relatorios fiscais (Siconfi/Tesouro Nacional), "
                "garantindo a integridade da analise."
            ),
        },
        {
            "pergunta": "Por que 'per capita'?",
            "resposta": (
                "Para comparar cidades de tamanhos diferentes de forma justa. Dividimos a "
                "receita total pela populacao de cada municipio, encontrando o valor real "
                "disponivel para cada habitante."
            ),
        },
        {
            "pergunta": "Como os grupos sao divididos?",
            "resposta": (
                "Ordenamos os municipios, com dados disponiveis, do menor para o maior valor "
                "de receita. Em seguida, fatiamos essa lista em grupos com a mesma quantidade "
                "de cidades: Quintis (5 grupos, cada um com 20% dos municipios) e Decis "
                "(10 grupos, cada um com 10% dos municipios)."
            ),
        },
    ],
    "passos": [
        {
            "ordem": 1,
            "titulo": "Ordenamos todos os municipios",
            "descricao": "Da menor para a maior receita per capita.",
        },
        {
            "ordem": 2,
            "titulo": "Distribuimos em grupos iguais",
            "descricao": (
                "Aproximadamente 1.100 municipios em cada quintil (20%) e 550 em cada decil (10%)."
            ),
            "grupos": {
                "quintis": [
                    {"ordem": 1, "faixa": "0% a 20% (menor receita)"},
                    {"ordem": 2, "faixa": "20% a 40%"},
                    {"ordem": 3, "faixa": "40% a 60%"},
                    {"ordem": 4, "faixa": "60% a 80%"},
                    {"ordem": 5, "faixa": "80% a 100% (maior receita)"},
                ],
                "decis": [
                    {"ordem": i, "faixa": f"{(i-1)*10}% a {i*10}%"} for i in range(1, 11)
                ],
            },
        },
    ],
}


# -------------------------- main --------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=None,
                        help='Exporta apenas os primeiros N municipios (debug).')
    parser.add_argument('--cod_ibge', type=str, default=None,
                        help='Lista (separada por virgula) de cod_ibge a exportar.')
    parser.add_argument('--out', type=str, default='export_folheto',
                        help='Diretorio de saida.')
    args = parser.parse_args()

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.out)
    os.makedirs(out_dir, exist_ok=True)

    # Metodologia (uma so vez).
    metodologia_path = os.path.join(out_dir, '_metodologia.json')
    with open(metodologia_path, 'w', encoding='utf-8') as f:
        json.dump(METODOLOGIA, f, ensure_ascii=False, indent=2)
    print(f'[ok] {metodologia_path}')

    # 1) Carrega TODOS os municipios em memoria para calcular o percentil
    #    de cada um em cada rubrica/categoria (precisa do universo completo).
    print('Carregando todos os municipios para calculo de percentis ...')
    qs_all = Municipio.objects.select_related('rm').prefetch_related(
        'conta_detalhada', 'conta_especifica', 'conta_mais_especifica'
    ).order_by('uf', 'name_muni')
    todos = list(qs_all)
    print(f'  {len(todos)} municipios carregados.')

    print('Calculando percentis por categoria ...')
    percentis_globais = compute_percentis_por_categoria(todos)
    print(f'  percentis prontos para {len(percentis_globais)} municipios.')

    # 2) Aplica filtros (apos calcular percentis para refletir o universo completo).
    if args.cod_ibge:
        codigos = set(c.strip() for c in args.cod_ibge.split(',') if c.strip())
        municipios_export = [m for m in todos if m.cod_ibge in codigos]
    else:
        municipios_export = todos
    if args.limit:
        municipios_export = municipios_export[:args.limit]

    total = len(municipios_export)
    print(f'Exportando {total} municipios para {out_dir}/ ...')

    feitos = 0
    for m in municipios_export:
        payload = build_municipio_payload(m, percentis_globais.get(m.cod_ibge))
        slug = slugify(m.name_muni_uf or m.name_muni)
        fname = f'{m.cod_ibge}_{slug}.json'
        fpath = os.path.join(out_dir, fname)
        with open(fpath, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        feitos += 1
        if feitos % 250 == 0:
            print(f'  ... {feitos} municipios exportados')

    print(f'[ok] Exportacao concluida: {feitos} municipios em {out_dir}/')


if __name__ == '__main__':
    main()
