"""Saúde Fiscal de um município: monta as linhas da tabela do detalhe.

Lê apenas campos já carregados em `DadosAtuais` (planilhas da CAPAG, do RGF e
do indicador de equilíbrio, importadas por 01_importar_municipios). Nada aqui
é calculado a partir de outro dado: cada linha é um campo do banco com a sua
classificação.

As faixas do RGF e do equilíbrio são as MESMAS do gráfico por Saúde Fiscal da
home (home/views.py, funções get_lrf_pessoal, get_lrf_divida e get_equilibrio).
Lá elas são funções aninhadas na view; se uma faixa mudar, mude nos dois
lugares (ou extraia aquelas funções para cá e importe na home).
"""

# Paleta: as mesmas cores dos quintis do IFEM, do melhor (verde) ao pior
# (vermelho). Classes arbitrárias do Tailwind, como a tabela do AdaptaBrasil,
# porque as duas páginas carregam o Tailwind pelo CDN.
_VERDE_ESCURO = 'bg-[#1C9148] text-white'
_VERDE = 'bg-[#6AC074] text-[#103758]'
_AMARELO = 'bg-[#F4D01D] text-[#103758]'
_LARANJA = 'bg-[#E47326] text-white'
_VERMELHO = 'bg-[#A81C21] text-white'
_CINZA = 'bg-slate-400 text-white'

_COR_NOTA_CAPAG = {'A': _VERDE_ESCURO, 'B': _VERDE, 'C': _LARANJA, 'D': _VERMELHO}


def _pct(valor, casas=1):
    """Formata em % no padrão brasileiro. `valor` já em pontos percentuais."""
    if valor is None:
        return 'n/d'
    return f'{valor:.{casas}f}%'.replace('.', ',')


def _nota_capag(bruto):
    """Normaliza a nota da CAPAG para A, B, C ou D.

    A planilha do Tesouro traz variações ('B+', 'n.d.', 'n.e.'); só a letra
    inicial importa para a classificação. Qualquer outra coisa é sem nota.
    """
    if not bruto:
        return None
    letra = str(bruto).strip().upper()[:1]
    return letra if letra in _COR_NOTA_CAPAG else None


def _situacao_capag(bruto):
    letra = _nota_capag(bruto)
    if letra is None:
        return 'Sem nota', _CINZA
    return f'Nota {letra}', _COR_NOTA_CAPAG[letra]


# Comprometimento com pessoal (% da RCL). Teto da LRF para o Executivo
# municipal: 54%; prudencial em 95% do teto (51,3%); alerta em 90% (48,6%).
def _situacao_pessoal(valor):
    if valor is None:
        return 'Sem dados', _CINZA
    if valor >= 54:
        return 'Acima do limite máximo', _VERMELHO
    if valor >= 51.3:
        return 'Acima do limite prudencial', _LARANJA
    if valor >= 48.6:
        return 'Acima do limite de alerta', _AMARELO
    return 'Regular', _VERDE_ESCURO


# Dívida Consolidada Líquida (% da RCL). Teto de 120%, alerta dos TCEs em 108%.
# DCL negativa: o caixa disponível é maior que a dívida.
def _situacao_divida(valor):
    if valor is None:
        return 'Sem dados', _CINZA
    if valor > 120:
        return 'Acima do limite', _VERMELHO
    if valor >= 108:
        return 'Em alerta (TCE)', _LARANJA
    if valor >= 0:
        return 'Regular', _VERDE
    return 'Caixa positivo (DCL negativa)', _VERDE_ESCURO


# Equilíbrio fiscal: (despesa corrente + amortizações) / receita corrente, em
# FRAÇÃO (0,9435 = 94,35%). Só o corte de 100% tem lastro na fonte; os demais
# são editoriais, ver o comentário de get_equilibrio em home/views.py.
def _situacao_equilibrio(valor):
    if valor is None:
        return 'Sem dados', _CINZA
    if valor >= 1.00:
        return 'Sem margem', _VERMELHO
    if valor >= 0.95:
        return 'Margem mínima', _LARANJA
    if valor >= 0.90:
        return 'Margem baixa', _AMARELO
    if valor >= 0.85:
        return 'Margem moderada', _VERDE
    return 'Margem alta', _VERDE_ESCURO


def montar_saude_fiscal(dados):
    """Monta as linhas da tabela de Saúde Fiscal de um município.

    Args:
        dados: instância de `DadosAtuais` do município (ou None).

    Returns:
        Lista de dicts com `grupo`, `indicador`, `descricao`, `valor` (texto
        já formatado), `situacao` e `cor` (classes Tailwind do selo). Lista
        vazia quando o município não tem nenhum dado de saúde fiscal, para o
        template esconder a seção inteira em vez de mostrar uma tabela de
        "Sem dados".
    """
    if dados is None:
        return []

    def nota_e_valor(nota, valor_fracao):
        # Os valores dos indicadores da CAPAG vêm em fração (0,374 = 37,4%).
        valor = _pct(valor_fracao * 100) if valor_fracao is not None else 'n/d'
        return valor, *_situacao_capag(nota)

    linhas = []

    def add(grupo, indicador, descricao, valor, situacao, cor):
        linhas.append({
            'grupo': grupo, 'indicador': indicador, 'descricao': descricao,
            'valor': valor, 'situacao': situacao, 'cor': cor,
        })

    capag = 'CAPAG (Tesouro Nacional)'
    add(capag, 'Nota geral', 'Capacidade de pagamento atribuída pelo Tesouro',
        '', *_situacao_capag(dados.capag))
    add(capag, 'Endividamento', 'Indicador I: dívida consolidada sobre a receita corrente líquida',
        *nota_e_valor(dados.capag_indicador_I, dados.capag_indicador_I_nota))
    add(capag, 'Poupança corrente', 'Indicador II: despesa corrente sobre a receita corrente ajustada',
        *nota_e_valor(dados.capag_indicador_II, dados.capag_indicador_II_nota))
    add(capag, 'Liquidez relativa', 'Indicador III: obrigações financeiras sobre a disponibilidade de caixa',
        *nota_e_valor(dados.capag_indicador_III, dados.capag_indicador_III_nota))

    lrf = 'LRF (Relatório de Gestão Fiscal)'
    add(lrf, 'Despesa com pessoal', 'Em % da receita corrente líquida; teto de 54%',
        _pct(dados.rgf_comprometimento_pessoal), *_situacao_pessoal(dados.rgf_comprometimento_pessoal))
    add(lrf, 'Dívida consolidada líquida', 'Em % da receita corrente líquida; teto de 120%',
        _pct(dados.rgf_divida_consolidada_liquida), *_situacao_divida(dados.rgf_divida_consolidada_liquida))

    eq = dados.indicador_equilibrio_fiscal
    add('Equilíbrio fiscal', 'Indicador de equilíbrio',
        'Despesa corrente mais amortizações sobre a receita corrente',
        _pct(eq * 100) if eq is not None else 'n/d', *_situacao_equilibrio(eq))

    # Se nenhuma linha tem dado, a seção não aparece.
    if all(l['situacao'] in ('Sem nota', 'Sem dados') for l in linhas):
        return []
    return linhas


# ---------------------------------------------------------------------------
# Distribuição para um CONJUNTO de municípios (página do Agregado)
# ---------------------------------------------------------------------------
# Num conjunto não existe "a" nota: o que informa é quantos municípios caem em
# cada situação. As classificações são as mesmas funções acima, aplicadas a
# cada município do conjunto, para que município e agregado nunca divirjam.

# Cor sólida de cada classe, para as barras empilhadas (largura via style).
_HEX = {
    _VERDE_ESCURO: '#1C9148', _VERDE: '#6AC074', _AMARELO: '#F4D01D',
    _LARANJA: '#E47326', _VERMELHO: '#A81C21', _CINZA: '#B9BFC7',
}
# Texto escuro sobre as cores claras, branco sobre as escuras (contraste AA).
_HEX_TEXTO = {
    _VERDE_ESCURO: '#ffffff', _VERDE: '#103758', _AMARELO: '#103758',
    _LARANJA: '#ffffff', _VERMELHO: '#ffffff', _CINZA: '#103758',
}

_NOTAS = ['Nota A', 'Nota B', 'Nota C', 'Nota D', 'Sem nota']

# (grupo, indicador, campo em DadosAtuais, classificador, ordem das situações
# da melhor para a pior). O classificador recebe o valor cru do banco.
_INDICADORES_CONJUNTO = [
    ('CAPAG', 'Nota geral', 'capag', _situacao_capag, _NOTAS),
    ('CAPAG', 'Endividamento (indicador I)', 'capag_indicador_I', _situacao_capag, _NOTAS),
    ('CAPAG', 'Poupança corrente (indicador II)', 'capag_indicador_II', _situacao_capag, _NOTAS),
    ('CAPAG', 'Liquidez relativa (indicador III)', 'capag_indicador_III', _situacao_capag, _NOTAS),
    ('LRF', 'Despesa com pessoal', 'rgf_comprometimento_pessoal', _situacao_pessoal,
     ['Regular', 'Acima do limite de alerta', 'Acima do limite prudencial',
      'Acima do limite máximo', 'Sem dados']),
    ('LRF', 'Dívida consolidada líquida', 'rgf_divida_consolidada_liquida', _situacao_divida,
     ['Caixa positivo (DCL negativa)', 'Regular', 'Em alerta (TCE)', 'Acima do limite', 'Sem dados']),
    ('Equilíbrio', 'Indicador de equilíbrio fiscal', 'indicador_equilibrio_fiscal', _situacao_equilibrio,
     ['Margem alta', 'Margem moderada', 'Margem baixa', 'Margem mínima', 'Sem margem', 'Sem dados']),
]


def distribuir_saude_fiscal(queryset):
    """Distribui os municípios de um conjunto pelas situações de cada indicador.

    Args:
        queryset: QuerySet de `Municipio` já filtrado.

    Returns:
        Lista de dicts (um por indicador) com `grupo`, `indicador`, `total` e
        `segmentos`, cada segmento com `situacao`, `n`, `pct` (float), `pct_txt`,
        `hex` e `hex_texto`. Situações sem município ficam de fora. Lista vazia
        se o conjunto está vazio.
    """
    campos = [c for _, _, c, _, _ in _INDICADORES_CONJUNTO]
    # Uma query só, com as 7 colunas; no máximo ~5.500 linhas de floats/letras.
    linhas = list(queryset.values_list(*[f'dados_atuais__{c}' for c in campos]))
    total = len(linhas)
    if total == 0:
        return []

    resultado = []
    for idx, (grupo, indicador, _campo, classificar, ordem) in enumerate(_INDICADORES_CONJUNTO):
        contagem = {}
        cor_por_situacao = {}
        for linha in linhas:
            situacao, cor = classificar(linha[idx])
            contagem[situacao] = contagem.get(situacao, 0) + 1
            cor_por_situacao[situacao] = cor

        segmentos = []
        for situacao in ordem:
            n = contagem.get(situacao, 0)
            if not n:
                continue
            pct = n / total * 100
            cor = cor_por_situacao[situacao]
            segmentos.append({
                'situacao': situacao, 'n': n, 'pct': round(pct, 2),
                'pct_txt': _pct(pct, 0) if pct >= 1 else '<1%',
                'hex': _HEX[cor], 'hex_texto': _HEX_TEXTO[cor],
            })
        resultado.append({'grupo': grupo, 'indicador': indicador, 'total': total, 'segmentos': segmentos})
    return resultado
