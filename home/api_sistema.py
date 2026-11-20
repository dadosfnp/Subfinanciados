"""API de leitura dos indicadores municipais para o Sistema FNP (2026-11-04).

O Sistema FNP (sistema.fnp.org.br) usa os indicadores do IFEM nos painéis das
reuniões online e das instâncias: receita corrente per capita com quintil,
decil e percentil, CAPAG, indicadores fiscais do RGF, risco climático do
AdaptaBrasil, CadÚnico e dependência do SUS. Antes, esse dado só chegava por
planilha enviada à mão; agora o sistema busca daqui, uma vez por mês.

Regras do endereço:

- **Só leitura e só GET.** Nada aqui grava no banco do IFEM.
- **Token no cabeçalho** ``Authorization: Bearer <token>``, comparado em tempo
  constante com ``IFEM_API_TOKEN`` do ``.env``. O dado é público, mas o token
  impede que o endereço vire uma forma barata de raspar a base inteira. Sem a
  variável configurada, o endereço responde 503 (desligado), nunca aberto.
- **Nada de dado pessoal**: só número por município.
- ``?ibge=3550308,3304557`` restringe a alguns municípios; sem o parâmetro,
  vem a base inteira (cerca de 5.570 linhas, poucos MB de JSON).
"""

import hmac
import os

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from home.models import Municipio

#: Versão do formato da resposta. Muda só se um campo sair ou mudar de sentido;
#: campo novo não muda a versão (o Sistema FNP ignora o que não conhece).
VERSAO = 1

#: Campos de ``IndicadoresAtuais`` publicados, com o nome usado na resposta.
CAMPOS_ATUAIS = (
    'populacao_atual', 'capag', 'capag_indicador_I', 'capag_indicador_I_nota',
    'capag_indicador_II', 'capag_indicador_II_nota', 'capag_indicador_III',
    'capag_indicador_III_nota', 'capag_qualidade_fiscal',
    'rgf_comprometimento_pessoal', 'rgf_divida_consolidada_liquida',
    'indicador_equilibrio_fiscal', 'rc_atual', 'rc_atual_pc', 'quintil_atual',
    'decil_atual', 'percentil_atual', 'percentil_atual_n', 'rank_nacional',
    'total_nacional', 'rank_estadual', 'total_estadual', 'rank_faixa', 'total_faixa',
)

#: Índices do AdaptaBrasil (0 a 1) e a média ponderada.
CAMPOS_ADAPTA = (
    'bio_int_bio', 'des_des_ter', 'des_in_enx_ala', 'rec_ris_est_hid', 'sau_arb',
    'sau_lei_teg_ame', 'sau_lei_vis', 'sau_mal', 'seg_ali_ace_con_ali', 'seg_ali_dis',
    'seg_ene_ace', 'seg_ene_dis', 'media_ponderada',
)


def _autorizado(request):
    """Confere o token do cabeçalho contra o ``IFEM_API_TOKEN`` (vazio = desligado)."""
    esperado = os.environ.get('IFEM_API_TOKEN', '')
    if not esperado:
        return None
    cabecalho = request.headers.get('Authorization', '')
    if not cabecalho.startswith('Bearer '):
        return False
    return hmac.compare_digest(cabecalho[7:].strip().encode(), esperado.encode())


def _valores(objeto, campos):
    """Dicionário campo -> valor de um registro relacionado, ou None se não houver."""
    if objeto is None:
        return None
    return {campo: getattr(objeto, campo) for campo in campos}


def _relacionado(municipio, nome):
    """Registro OneToOne do município, sem levantar exceção quando falta."""
    try:
        return getattr(municipio, nome)
    except Exception:  # RelatedObjectDoesNotExist de cada model
        return None


@require_GET
def indicadores_municipais(request):
    """Indicadores de todos os municípios (ou dos ``?ibge=`` pedidos), em JSON."""
    autorizado = _autorizado(request)
    if autorizado is None:
        return JsonResponse({'erro': 'API desligada: IFEM_API_TOKEN não configurado.'}, status=503)
    if not autorizado:
        return JsonResponse({'erro': 'Token ausente ou inválido.'}, status=401)

    municipios = (Municipio.objects
                  .select_related('dados_atuais', 'dados_adapta_brasil', 'sus_dependente', 'cadunico')
                  .order_by('cod_ibge'))
    pedidos = [c.strip() for c in request.GET.get('ibge', '').split(',') if c.strip()]
    if pedidos:
        if not all(c.isdigit() and len(c) in (6, 7) for c in pedidos):
            return JsonResponse({'erro': 'ibge: use códigos de 6 ou 7 dígitos separados por vírgula.'},
                                status=400)
        municipios = municipios.filter(cod_ibge__in=pedidos)

    linhas = []
    for municipio in municipios:
        sus = _relacionado(municipio, 'sus_dependente')
        cad = _relacionado(municipio, 'cadunico')
        linhas.append({
            'ibge': municipio.cod_ibge,
            'nome': municipio.name_muni,
            'uf': municipio.uf,
            'regiao': municipio.regiao,
            'atuais': _valores(_relacionado(municipio, 'dados_atuais'), CAMPOS_ATUAIS),
            'adapta_brasil': _valores(_relacionado(municipio, 'dados_adapta_brasil'), CAMPOS_ADAPTA),
            'sus_dependente': sus.sus_dependente if sus else None,
            'cadunico': cad.cadunico if cad else None,
        })

    resposta = JsonResponse({
        'versao': VERSAO,
        'gerado_em': timezone.now().isoformat(),
        'total': len(linhas),
        'municipios': linhas,
    }, json_dumps_params={'ensure_ascii': False})
    resposta['Cache-Control'] = 'no-store'
    return resposta
