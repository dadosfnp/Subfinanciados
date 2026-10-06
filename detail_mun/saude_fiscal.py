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
