"""
Gera dois novos arquivos dentro de `export_folheto/`:

1. `_medias_receitas.json`  (arquivo unico de referencia)
   Medias e medianas (nacional + por UF + por porte) para cada rubrica de receita.
   Fonte: MediaNacionalReceita / MediaUfReceita / MediaPorteReceita
           MedianaNacionalReceita / MedianaUfReceita / MedianaPorteReceita

2. `<cod_ibge>_<slug>_sintese.json`  (um arquivo por municipio)
   Dados que alimentam a 'Sintese Fiscal e Demografica' do detalhe do municipio:
   - bolinhas (posicao em 2000 e 2024 nos modos Ranking/Percentil/Quintil/Decil)
   - frase (delta_rc_pc, delta_pop do municipio vs medias)
   - barra/ruler (totais p/ contexto + medias)

Uso:
    python export_folheto_complementares.py
        [--limit N]
        [--cod_ibge 1100015,...]
        [--out export_folheto]
        [--skip_medias]
        [--skip_sintese]
"""
import argparse
import json
import os
import re
import unicodedata

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from home.models import (  # noqa: E402
    Municipio,
    MediaNacionalReceita, MediaUfReceita, MediaPorteReceita,
    MedianaNacionalReceita, MedianaUfReceita, MedianaPorteReceita,
    CrescimentoMedioUf, CrescimentoMedioPorte,
)


# -------------------------- helpers --------------------------

def slugify(value: str) -> str:
    if value is None:
        return ''
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^A-Za-z0-9]+', '-', value).strip('-').lower()
    return value or 'sem-nome'


def faixa_porte_label(pop):
    pop = pop or 0
    if pop < 5000: return "Até 5 mil"
    if pop < 10000: return "5 mil a 10 mil"
    if pop < 20000: return "10 mil a 20 mil"
    if pop < 50000: return "20 mil a 50 mil"
    if pop < 100000: return "50 mil a 100 mil"
    if pop < 200000: return "100 mil a 200 mil"
    if pop < 500000: return "200 mil a 500 mil"
    return "Acima de 500 mil"


def round_or_none(v, ndigits=2):
    if v is None:
        return None
    try:
        return round(v, ndigits)
    except (TypeError, ValueError):
        return None


# -------------------------- rubricas de receita --------------------------

# Fontes dos campos nas tabelas Media*/Mediana*  (mesmo nome em nacional/uf/porte).
RUBRICAS = [
    # nivel 1 - Conta Detalhada (4 grandes grupos)
    ("imposto_taxas_contribuicoes", "Impostos, Taxas e Contribuições de Melhoria", "nivel_1"),
    ("contribuicoes", "Contribuições", "nivel_1"),
    ("transferencias_correntes", "Transferências Correntes", "nivel_1"),
    ("outras_receita", "Outras Receitas", "nivel_1"),

    # nivel 2 - Conta Especifica
    ("imposto", "Impostos", "nivel_2"),
    ("taxas", "Taxas", "nivel_2"),
    ("contribuicoes_melhoria", "Contribuições de Melhoria", "nivel_2"),
    ("contribuicoes_sociais", "Contribuições Sociais", "nivel_2"),
    ("contribuicoes_iluminacao_publica", "Contribuição de Iluminação Pública", "nivel_2"),
    ("outras_contribuicoes", "Outras Contribuições", "nivel_2"),
    ("tranferencias_uniao", "Transferências da União", "nivel_2"),
    ("tranferencias_estados", "Transferências dos Estados", "nivel_2"),
    ("outras_tranferencias", "Outras Transferências", "nivel_2"),
    ("receita_patrimonial", "Receita Patrimonial", "nivel_2"),
    ("receita_agropecuaria", "Receita Agropecuária", "nivel_2"),
    ("receita_industrial", "Receita Industrial", "nivel_2"),
    ("receita_servicos", "Receita de Serviços", "nivel_2"),
    ("outras_receitas", "Outras Receitas (Nível 2)", "nivel_2"),

    # nivel 3 - Conta Mais Especifica
    ("iptu", "IPTU", "nivel_3"),
    ("itbi", "ITBI", "nivel_3"),
    ("iss", "ISS", "nivel_3"),
    ("imposto_renda", "Imposto de Renda", "nivel_3"),
    ("outros_impostos", "Outros Impostos", "nivel_3"),
    ("taxa_policia", "Taxa de Polícia", "nivel_3"),
    ("taxa_prestacao_servico", "Taxa de Prestação de Serviço", "nivel_3"),
    ("outras_taxas", "Outras Taxas", "nivel_3"),
    ("contribuicao_melhoria_pavimento_obras", "Contribuição de Melhoria - Pavimentação/Obras", "nivel_3"),
    ("contribuicao_melhoria_agua_potavel", "Contribuição de Melhoria - Água Potável", "nivel_3"),
    ("contribuicao_melhoria_iluminacao_publica", "Contribuição de Melhoria - Iluminação Pública", "nivel_3"),
    ("outras_contribuicoes_melhoria", "Outras Contribuições de Melhoria", "nivel_3"),
    ("transferencia_uniao_fpm", "Transferência União - FPM", "nivel_3"),
    ("transferencia_uniao_exploracao", "Transferência União - Exploração de Recursos", "nivel_3"),
    ("transferencia_uniao_sus", "Transferência União - SUS", "nivel_3"),
    ("transferencia_uniao_fnde", "Transferência União - FNDE", "nivel_3"),
    ("transferencia_uniao_fundeb", "Transferência União - FUNDEB", "nivel_3"),
    ("transferencia_uniao_fnas", "Transferência União - FNAS", "nivel_3"),
    ("outras_transferencias_uniao", "Outras Transferências da União", "nivel_3"),
    ("transferencia_estado_icms", "Transferência Estado - ICMS", "nivel_3"),
    ("transferencia_estado_ipva", "Transferência Estado - IPVA", "nivel_3"),
    ("transferencia_estado_exploracao", "Transferência Estado - Exploração de Recursos", "nivel_3"),
    ("transferencia_estado_sus", "Transferência Estado - SUS", "nivel_3"),
    ("transferencia_estado_assistencia", "Transferência Estado - Assistência", "nivel_3"),
    ("outras_transferencias_estado", "Outras Transferências do Estado", "nivel_3"),
]

PORTES_VALIDOS = [
    "Até 5 mil", "5 mil a 10 mil", "10 mil a 20 mil", "20 mil a 50 mil",
    "50 mil a 100 mil", "100 mil a 200 mil", "200 mil a 500 mil", "Acima de 500 mil",
]


def serializar_objeto_medias(obj):
    """Para um objeto Media*/Mediana*, retorna {field: valor} para cada rubrica."""
    if obj is None:
        return {field: None for field, _, _ in RUBRICAS}
    return {field: round_or_none(getattr(obj, field, None)) for field, _, _ in RUBRICAS}


def montar_medias_receitas(ano=2024):
    """Monta o JSON de medias/medianas (nacional, por UF, por porte)."""
    media_nac = MediaNacionalReceita.objects.filter(ano_referencia=ano).first()
    mediana_nac = MedianaNacionalReceita.objects.filter(ano_referencia=ano).first()

    ufs = sorted({m.uf for m in MediaUfReceita.objects.filter(ano_referencia=ano)})
    medias_por_uf = {}
    for uf in ufs:
        media = MediaUfReceita.objects.filter(ano_referencia=ano, uf=uf).first()
        mediana = MedianaUfReceita.objects.filter(ano_referencia=ano, uf=uf).first()
        medias_por_uf[uf] = {
            "media": serializar_objeto_medias(media),
            "mediana": serializar_objeto_medias(mediana),
        }

    medias_por_porte = {}
    for porte in PORTES_VALIDOS:
        media = MediaPorteReceita.objects.filter(ano_referencia=ano, porte=porte).first()
        mediana = MedianaPorteReceita.objects.filter(ano_referencia=ano, porte=porte).first()
        medias_por_porte[porte] = {
            "media": serializar_objeto_medias(media),
            "mediana": serializar_objeto_medias(mediana),
        }

    return {
        "ano_referencia": ano,
        "observacao": (
            "Médias e medianas pré-calculadas, em valores per capita (R$/hab), para cada "
            "rubrica de receita. Use 'nacional' para a referência global, 'por_uf' para o "
            "comparativo estadual e 'por_porte' para o comparativo por faixa populacional."
        ),
        "rubricas": [
            {"field": field, "label": label, "nivel": nivel}
            for field, label, nivel in RUBRICAS
        ],
        "nacional": {
            "media": serializar_objeto_medias(media_nac),
            "mediana": serializar_objeto_medias(mediana_nac),
        },
        "por_uf": medias_por_uf,
        "por_porte": medias_por_porte,
    }


# -------------------------- sintese fiscal demografica --------------------------

def delta_pct(novo, antigo):
    if not antigo or not novo or antigo <= 0:
        return None
    return round(((novo / antigo) - 1) * 100, 2)


def montar_sintese_municipio(m: Municipio, crescimentos_uf: dict, crescimentos_porte: dict):
    porte = faixa_porte_label(m.populacao24)
    cresc_uf = crescimentos_uf.get(m.uf)
    cresc_porte = crescimentos_porte.get(porte)

    # medias nacionais (hardcoded em detail_mun.views — mantemos paridade)
    media_nacional_rc_pc = 316.74
    media_nacional_pop = 16.04

    delta_rc_pc = delta_pct(m.rc_24_pc, m.rc_00_pc) or 0.0
    delta_populacao = delta_pct(m.populacao24, m.populacao00) or 0.0

    # ---- bolinhas: valores por modo (Ranking/Percentil/Quintil/Decil) em 2000 e 2024
    bolinhas = {
        "2000": {
            "ranking": {
                "posicao": m.rank_nacional_00,
                "total": m.total_nacional_00 or 5305,
                "label": f"{m.rank_nacional_00}º" if m.rank_nacional_00 else None,
            },
            "percentil": {
                "valor": m.percentil00_n,
                "label": m.percentil00,
            },
            "quintil": {"label": m.quintil00},
            "decil": {"label": m.decil00},
        },
        "2024": {
            "ranking": {
                "posicao": m.rank_nacional,
                "total": m.total_nacional or 5479,
                "label": f"{m.rank_nacional}º" if m.rank_nacional else None,
            },
            "percentil": {
                "valor": m.percentil24_n,
                "label": m.percentil24,
            },
            "quintil": {"label": m.quintil24},
            "decil": {"label": m.decil24},
        },
    }

    # ---- frase: variacoes do municipio + medias para comparar
    frase = {
        "municipio": m.name_muni,
        "receita_per_capita": {
            "delta_municipio_pct": round(delta_rc_pc, 2),
            "delta_media_nacional_pct": media_nacional_rc_pc,
            "delta_media_estadual_pct": round_or_none(cresc_uf.receita) if cresc_uf else None,
            "delta_media_porte_pct": round_or_none(cresc_porte.receita) if cresc_porte else None,
            "direcao": "cresceu" if delta_rc_pc >= 0 else "caiu",
            "texto_padrao": (
                f"A Receita por Habitante {'cresceu' if delta_rc_pc >= 0 else 'caiu'} "
                f"{abs(delta_rc_pc):.1f}% entre 2000 e 2024. No mesmo período, a média "
                f"dos municípios variou {media_nacional_rc_pc:.0f}%."
            ),
        },
        "populacao": {
            "delta_municipio_pct": round(delta_populacao, 2),
            "delta_media_nacional_pct": media_nacional_pop,
            "delta_media_estadual_pct": round_or_none(cresc_uf.populacao) if cresc_uf else None,
            "delta_media_porte_pct": round_or_none(cresc_porte.populacao) if cresc_porte else None,
            "direcao": "aumentou" if delta_populacao >= 0 else "teve queda de",
            "texto_padrao": (
                f"A População do município "
                f"{'aumentou' if delta_populacao >= 0 else 'teve queda de'} "
                f"{abs(delta_populacao):.1f}% neste intervalo. Enquanto o crescimento "
                f"populacional médio dos municípios foi de {media_nacional_pop:.0f}%."
            ),
        },
    }

    # ---- barra/ruler: totais p/ contexto da regua (modo ranking)
    barra_ruler = {
        "2000": {
            "rank_nacional": m.rank_nacional_00,
            "total_nacional": m.total_nacional_00 or 5305,
            "percentual_de_baixo": (
                round((1 - m.rank_nacional_00 / (m.total_nacional_00 or 5305)) * 100, 1)
                if m.rank_nacional_00 and (m.total_nacional_00 or 5305) else None
            ),
        },
        "2024": {
            "rank_nacional": m.rank_nacional,
            "total_nacional": m.total_nacional or 5479,
            "percentual_de_baixo": (
                round((1 - m.rank_nacional / (m.total_nacional or 5479)) * 100, 1)
                if m.rank_nacional and (m.total_nacional or 5479) else None
            ),
        },
    }

    return {
        "identificacao": {
            "cod_ibge": m.cod_ibge,
            "municipio": m.name_muni,
            "uf": m.uf,
            "name_muni_uf": m.name_muni_uf,
            "porte": porte,
        },
        "has_2000_data": bool(m.populacao00 or m.rc_00_pc),
        "bolinhas_posicao_no_tempo": bolinhas,
        "frase_evolucao": frase,
        "barra_ruler_ranking": barra_ruler,
        "observacao": (
            "Valores financeiros corrigidos pela inflação para 2024. "
            "O componente da síntese (timeline) admite 4 modos no toggle: "
            "Ranking, Percentil, Quintil e Decil — todos disponíveis aqui."
        ),
    }


# -------------------------- main --------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--cod_ibge', type=str, default=None)
    parser.add_argument('--out', type=str, default='export_folheto')
    parser.add_argument('--skip_medias', action='store_true')
    parser.add_argument('--skip_sintese', action='store_true')
    args = parser.parse_args()

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.out)
    os.makedirs(out_dir, exist_ok=True)

    # 1. medias/medianas de receita
    if not args.skip_medias:
        payload = montar_medias_receitas(ano=2024)
        path = os.path.join(out_dir, '_medias_receitas.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f'[ok] {path}')

    # 2. sintese fiscal demografica por municipio
    if not args.skip_sintese:
        # carrega crescimentos (UF e porte) em dicts pra evitar N+1
        crescimentos_uf = {c.uf: c for c in CrescimentoMedioUf.objects.all()}
        crescimentos_porte = {c.porte: c for c in CrescimentoMedioPorte.objects.all()}

        qs = Municipio.objects.order_by('uf', 'name_muni')
        if args.cod_ibge:
            codigos = [c.strip() for c in args.cod_ibge.split(',') if c.strip()]
            qs = qs.filter(cod_ibge__in=codigos)
        if args.limit:
            qs = qs[:args.limit]

        total = qs.count() if not args.limit else min(args.limit, qs.count() or args.limit)
        print(f'Sintese fiscal: gerando para {total} municipios em {out_dir}/ ...')

        feitos = 0
        for m in qs.iterator(chunk_size=300):
            payload = montar_sintese_municipio(m, crescimentos_uf, crescimentos_porte)
            slug = slugify(m.name_muni_uf or m.name_muni)
            fname = f'{m.cod_ibge}_{slug}_sintese.json'
            fpath = os.path.join(out_dir, fname)
            with open(fpath, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            feitos += 1
            if feitos % 500 == 0:
                print(f'  ... {feitos} sinteses geradas')

        print(f'[ok] Sintese concluida: {feitos} arquivos em {out_dir}/')


if __name__ == '__main__':
    main()
