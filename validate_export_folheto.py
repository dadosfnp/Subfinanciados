"""
Validador do lote `export_folheto/` — confere se todos os JSONs municipais
estao no schema esperado:

 1. Top-level keys batem com o template.
 2. estrutura_receita_resumo / nivel_2_categorias / nivel_3_rubricas:
    todo item tem `field`, `supera_pct_nacional` (0-100) e `total_municipios_comparados` (>0).
 3. hierarquia_receitas com counts 4/14/28 e mesmos field/parent_field em TODOS os arquivos.
 4. Consistencia referencial: todo `field` usado existe na hierarquia.
 5. Distribuicao plausivel: amostra de 20 nao pode ter supera_pct todo 0/99/igual.
"""
import json
import os
import random
import sys

EXPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'export_folheto')

TOP_LEVEL_KEYS = {
    "identificacao", "populacao", "receita_corrente", "sus_dependente", "cadunico",
    "percentil", "estrutura_receita_resumo", "estrutura_receita_detalhada",
    "hierarquia_receitas", "sintese_fiscal_2000_2024", "posicao_historica",
}

EXPECTED_COUNTS = {"nivel_1": 4, "nivel_2": 14, "nivel_3": 28}


def is_municipal_file(name):
    if not name.endswith('.json'):
        return False
    if name.startswith('_'):
        return False
    return True


def validar_arquivo(path, hierarquia_referencia):
    """Retorna lista de erros (strings). Vazia se OK."""
    erros = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return [f'JSON invalido: {e}']

    # (1) top-level keys
    keys_atuais = set(data.keys())
    faltando = TOP_LEVEL_KEYS - keys_atuais
    if faltando:
        erros.append(f'top-level keys faltando: {sorted(faltando)}')

    # (3) hierarquia_receitas: counts e referencia comum
    hier = data.get('hierarquia_receitas')
    if not isinstance(hier, dict):
        erros.append('hierarquia_receitas ausente ou invalida')
    else:
        for nivel, esperado in EXPECTED_COUNTS.items():
            arr = hier.get(nivel)
            if not isinstance(arr, list) or len(arr) != esperado:
                erros.append(f'hierarquia_receitas.{nivel}: esperado {esperado}, obtido {len(arr) if isinstance(arr, list) else "n/a"}')
        if hierarquia_referencia is not None and erros == []:
            # Compara assinatura (campo + parent + label) com a referencia.
            for nivel in EXPECTED_COUNTS:
                ref_sig = [(x.get('field'), x.get('label'), x.get('parent_field')) for x in hierarquia_referencia.get(nivel, [])]
                cur_sig = [(x.get('field'), x.get('label'), x.get('parent_field')) for x in hier.get(nivel, [])]
                if ref_sig != cur_sig:
                    erros.append(f'hierarquia_receitas.{nivel} difere da referencia')

    # (2) items com field / supera_pct / total
    fields_hierarquia_2_3 = set()
    if isinstance(hier, dict):
        for nivel in ('nivel_2', 'nivel_3'):
            for item in hier.get(nivel, []) or []:
                f = item.get('field')
                if f:
                    fields_hierarquia_2_3.add(f)
        fields_hierarquia_1 = {x.get('field') for x in hier.get('nivel_1', []) or []}
    else:
        fields_hierarquia_2_3 = set()
        fields_hierarquia_1 = set()

    def checa_items(items, contexto, universos_validos):
        if not isinstance(items, list):
            erros.append(f'{contexto}: nao e lista')
            return
        for i, it in enumerate(items):
            if not isinstance(it, dict):
                erros.append(f'{contexto}[{i}]: nao e dict')
                continue
            field = it.get('field')
            sp = it.get('supera_pct_nacional')
            tot = it.get('total_municipios_comparados')
            if not field:
                erros.append(f'{contexto}[{i}]: sem field')
            elif universos_validos is not None and field not in universos_validos:
                erros.append(f'{contexto}[{i}]: field "{field}" nao existe em hierarquia')
            if not isinstance(sp, int) or not (0 <= sp <= 100):
                erros.append(f'{contexto}[{i}] field={field}: supera_pct_nacional invalido ({sp})')
            if not isinstance(tot, int) or tot <= 0:
                erros.append(f'{contexto}[{i}] field={field}: total_municipios_comparados invalido ({tot})')

    checa_items(data.get('estrutura_receita_resumo'), 'estrutura_receita_resumo', fields_hierarquia_1)
    detal = data.get('estrutura_receita_detalhada') or {}
    checa_items(detal.get('nivel_2_categorias'), 'estrutura_receita_detalhada.nivel_2_categorias', fields_hierarquia_2_3)
    checa_items(detal.get('nivel_3_rubricas'), 'estrutura_receita_detalhada.nivel_3_rubricas', fields_hierarquia_2_3)

    return erros


def main():
    arquivos = sorted([f for f in os.listdir(EXPORT_DIR) if is_municipal_file(f)])
    total = len(arquivos)
    print(f'Validando {total} arquivos municipais em {EXPORT_DIR}/ ...')

    # Pega hierarquia de referencia do primeiro arquivo valido.
    referencia = None
    for f in arquivos:
        try:
            with open(os.path.join(EXPORT_DIR, f), 'r', encoding='utf-8') as fh:
                referencia = json.load(fh).get('hierarquia_receitas')
            if referencia:
                print(f'Usando hierarquia de referencia: {f}')
                break
        except Exception:
            continue

    falhos = []
    for f in arquivos:
        erros = validar_arquivo(os.path.join(EXPORT_DIR, f), referencia)
        if erros:
            cod = f.split('_', 1)[0]
            falhos.append((cod, f, erros))

    # (5) distribuicao plausivel: amostra de 20
    random.seed(42)
    amostra = random.sample(arquivos, min(20, len(arquivos)))
    sp_values = []
    for f in amostra:
        with open(os.path.join(EXPORT_DIR, f), 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        for it in data.get('estrutura_receita_resumo', []) or []:
            sp_values.append(it.get('supera_pct_nacional'))
    distribuicao_ok = True
    motivos = []
    if not sp_values:
        distribuicao_ok = False
        motivos.append('amostra sem supera_pct_nacional')
    elif all(v == 0 for v in sp_values):
        distribuicao_ok = False
        motivos.append('amostra com supera_pct_nacional todos 0')
    elif all(v == 99 for v in sp_values):
        distribuicao_ok = False
        motivos.append('amostra com supera_pct_nacional todos 99')
    elif len(set(sp_values)) == 1:
        distribuicao_ok = False
        motivos.append(f'amostra com supera_pct_nacional todos iguais ({sp_values[0]})')

    print()
    print('=' * 60)
    print(f'Total de arquivos validados : {total}')
    print(f'Total de arquivos OK         : {total - len(falhos)}')
    print(f'Total de arquivos com erro   : {len(falhos)}')
    print(f'Distribuicao plausivel       : {"OK" if distribuicao_ok else "FALHOU - " + ", ".join(motivos)}')
    print(f'Amostra de supera_pct (n={len(sp_values)}): min={min(sp_values)} max={max(sp_values)} distintos={len(set(sp_values))}')
    print('=' * 60)

    if falhos:
        print('\nProblemas (primeiros 20):')
        for cod, name, erros in falhos[:20]:
            print(f'  [{cod}] {name}')
            for e in erros[:3]:
                print(f'      - {e}')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
