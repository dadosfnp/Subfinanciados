# Lições — Subfinanciados

Registro de erros e armadilhas encontrados, para não repetir.

---

## Django templates

### `{# … #}` não funciona em múltiplas linhas
**Erro:** comentários escritos como `{# texto \n mais texto #}` vazaram como
texto visível na página e destruíram o grid CSS da tabela.

**Causa:** a sintaxe `{# #}` é comentário **de uma linha só**. Django não
fecha o comentário na quebra de linha — o `#}` da linha seguinte vira conteúdo.

**Regra:** comentário de mais de uma linha usa sempre `{% comment %}` /
`{% endcomment %}`. `{# #}` só para uma linha.

### `runserver --noreload` não recarrega templates
**Erro:** duas rodadas de correção "sem efeito" porque o servidor servia os
templates carregados no boot.

**Regra:** ao validar mudança de template, ou subir sem `--noreload`, ou
reiniciar o processo depois de cada edição.

### `|json_script` sobre string já serializada gera JSON duplo
**Erro:** `chart_data_json` sai da view como `json.dumps(...)` (string) e o
filtro `|json_script` serializa **de novo**. No JS, `JSON.parse()` devolve uma
**string**, não o objeto — o gráfico ficava vazio sem lançar erro.

**Regra:** ao ler esses blocos, tolerar dupla codificação
(`if (typeof v === 'string') v = JSON.parse(v)`) ou passar o dict cru para o
filtro. Ver `lerJSON()` em `script_mun_folheto.js`.

---

## Validação visual

### Chrome `--headless` (modo antigo) mente sobre layout responsivo
**Erro:** screenshots em `--window-size=390` mostravam corte horizontal
inexistente. Passei dois ciclos "corrigindo" um overflow que não existia.

**Causa:** o headless antigo não aplica o `<meta viewport>` como um browser
real, e a captura corta em vez de reflowar.

**Regra:** para julgar responsivo, usar Playwright (mede
`scrollWidth` vs `clientWidth` de verdade). Quando o browser do Playwright não
baixar, apontar para o Chrome do sistema:
`p.chromium.launch(executable_path=r"C:/Program Files/Google/Chrome/Application/chrome.exe")`.

**Antes de afirmar que há overflow:** medir, não olhar screenshot.

---

## Design

### Cores do folheto impresso não passam direto para tela
**Contexto:** a paleta FNP de quintis (`FNP_Q1..Q5`) é usada em texto no folheto
impresso. Na web, o amarelo `#F4D01D` e o verde-claro `#6AC074` dão ~2:1 de
contraste sobre branco — ilegíveis.

**Regra:** manter a cor viva do folheto nas **barras e áreas preenchidas**, e
usar variantes escurecidas (`--fx-q*-txt`) para **texto**, todas ≥ 4.5:1.

---

## Escopo

### Bug pré-existente não vira escopo silencioso
**Contexto:** o header global (`base_templates/global/head.html`) estoura a
viewport em telas estreitas — a página pública tem o mesmo problema.

**Regra:** ao encontrar bug fora do escopo em arquivo compartilhado com
produção, **não corrigir por conta própria**: isolar o efeito no código novo,
documentar o motivo no CSS/código e reportar ao Pedro para decidir.
