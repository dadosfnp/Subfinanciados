"""
Gera a malha municipal compacta usada na animacao da landing
(/preview/inicio-animado/): ifem/static/ifem/dados/malha_municipios.json.

Fonte: API de malhas do IBGE (qualidade minima, um poligono por municipio).
Fica de fora da base do IFEM porque so a animacao usa contorno de municipio;
o resto do site trabalha com pontos (coordx/coordy).

Formato de saida, pensado para ser pequeno:
  {"escala": 200, "m": {"<cod_ibge>": [x0, y0, dx1, dy1, dx2, dy2, ...]}}
  x = round(lon * escala), y = round(lat * escala); a partir do segundo ponto,
  diferencas em relacao ao ponto anterior. So o anel externo do maior
  poligono de cada municipio (ilhas e buracos nao aparecem na escala do pais),
  simplificado por Douglas-Peucker com TOLERANCIA: a animacao redesenha todos
  os contornos a cada quadro, e cada ponto a menos deixa o movimento mais leve.

Uso:
  python export_malha_inicio.py                 # baixa do IBGE
  python export_malha_inicio.py caminho.geojson # usa um arquivo ja baixado
"""
import json
import sys
import urllib.request
from pathlib import Path

URL_IBGE = (
    'https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR'
    '?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=municipio'
)
ESCALA = 200  # 1/200 de grau, cerca de 550 m: abaixo de 1 px no mapa do pais
TOLERANCIA = 0.06  # graus (~6,7 km): cerca de 1 px no mapa do pais no desktop
MIN_PONTOS = 5
SAIDA = Path(__file__).resolve().parent / 'ifem' / 'static' / 'ifem' / 'dados' / 'malha_municipios.json'


def area(anel):
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(anel, anel[1:] + anel[:1]))) / 2


def anel_externo(geom):
    if geom['type'] == 'Polygon':
        return geom['coordinates'][0]
    return max((p[0] for p in geom['coordinates']), key=area)


def _dist_segmento(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return ((px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2) ** 0.5


def _dp(pts, tol):
    """Douglas-Peucker de uma linha aberta (mantem as pontas)."""
    manter = [False] * len(pts)
    manter[0] = manter[-1] = True
    pilha = [(0, len(pts) - 1)]
    while pilha:
        i, j = pilha.pop()
        maior, k = 0, None
        for m in range(i + 1, j):
            d = _dist_segmento(pts[m], pts[i], pts[j])
            if d > maior:
                maior, k = d, m
        if k is not None and maior > tol:
            manter[k] = True
            pilha += [(i, k), (k, j)]
    return [p for p, ok in zip(pts, manter) if ok]


def simplifica(anel, tol):
    """Anel fechado: parte no ponto mais distante do primeiro e simplifica as duas metades."""
    pts = anel[:-1] if anel[0] == anel[-1] else list(anel)
    if len(pts) <= MIN_PONTOS:
        return pts
    x0, y0 = pts[0]
    k = max(range(len(pts)), key=lambda m: (pts[m][0] - x0) ** 2 + (pts[m][1] - y0) ** 2)
    saida = _dp(pts[:k + 1], tol)[:-1] + _dp(pts[k:] + [pts[0]], tol)[:-1]
    # Municipio pequeno demais para a tolerancia: tenta de novo mais fino.
    return saida if len(saida) >= MIN_PONTOS else simplifica(anel, tol / 3) if tol > 1e-4 else pts


def compacta(anel):
    pts = []
    for lon, lat in simplifica(anel, TOLERANCIA):
        p = (round(lon * ESCALA), round(lat * ESCALA))
        if not pts or p != pts[-1]:
            pts.append(p)
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts.pop()
    saida = [pts[0][0], pts[0][1]]
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        saida += [xb - xa, yb - ya]
    return saida


def main():
    if len(sys.argv) > 1:
        bruto = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    else:
        with urllib.request.urlopen(URL_IBGE, timeout=300) as resp:
            bruto = json.load(resp)

    malha = {}
    for f in bruto['features']:
        cod = str(f['properties']['codarea'])
        malha[cod] = compacta(anel_externo(f['geometry']))

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps({'escala': ESCALA, 'm': malha}, separators=(',', ':')), encoding='utf-8')
    pontos = sum(len(v) // 2 for v in malha.values())
    print(f'{len(malha)} municipios, {pontos} pontos, {SAIDA.stat().st_size / 1024:.0f} KB em {SAIDA}')


if __name__ == '__main__':
    main()
