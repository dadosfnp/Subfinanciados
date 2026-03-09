# em seu_app/templatetags/currency_filters.py

from django import template

register = template.Library()

@register.filter(name='br_integer') # Corrigi o nome para 'br_integer'
def br_integer(value):
    """
    Formata um número como um inteiro com pontos como separador de milhar.
    Exemplo: 1234567.89 -> 1.234.567
    """
    try:
        # Converte para float primeiro (para aceitar "123.45") e depois para int
        # para remover (truncar) qualquer casa decimal.
        value = int(float(value))
    except (ValueError, TypeError):
        # Se não for um número, retorna o valor como está.
        return value

    # 1. Formata o número com o separador de milhar padrão (vírgula).
    # Ex: 1234567 -> "1,234,567"
    formatted_value = f'{value:,}'

    # 2. Substitui a vírgula pelo ponto. É só isso!
    # Ex: "1,234,567" -> "1.234.567"
    final_value = formatted_value.replace(',', '.')

    return final_value


@register.filter(name='br_float')
def br_float(value):
    """
    Formata um número para o padrão de moeda brasileira.
    - Adiciona 'R$ '
    - Usa ',' como separador decimal.
    - Usa '.' como separador de milhar.
    Exemplo: 12345.67 -> R$ 12.345,67
    """
    try:
        # Tenta converter o valor para um número float
        value = float(value)
    except (ValueError, TypeError):
        # Se não for um número, retorna o valor como está
        return value

    # Formata o número com 2 casas decimais e vírgula para milhares
    # Ex: 12345.678 -> "12,345.68"
    formatted_value = f'{value:,.2f}'

    # Agora, trocamos os separadores para o padrão brasileiro.
    # Para não haver conflito, usamos um placeholder temporário.
    # "12,345.68" -> "12.345,68"
    final_value = formatted_value.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')

    return f"{final_value}"


@register.filter(name='br_abrev')
def br_abrev(value):
    """
    Abrevia números grandes no padrão brasileiro.
    Ex:
    1500 -> 1,5 mil
    2500000 -> 2,5 mi
    3200000000 -> 3,2 bi
    """
    try:
        value = float(value)
    except (ValueError, TypeError):
        return value

    if abs(value) >= 1_000_000_000:
        num = value / 1_000_000_000
        sufixo = " bi"
    elif abs(value) >= 1_000_000:
        num = value / 1_000_000
        sufixo = " mi"
    elif abs(value) >= 1_000:
        num = value / 1_000
        sufixo = " mil"
    else:
        return f"{value:.0f}"

    formatted = f"{num:.1f}".replace('.', ',')
    return f"{formatted}{sufixo}"