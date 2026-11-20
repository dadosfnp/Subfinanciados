# Layout folheto IFEM: páginas públicas

Registro do redesenho que levou o visual do folheto IFEM para as páginas de
**Município**, **Agregado** e **Gráficos**, aprovado pela diretoria e publicado
em novembro de 2026 (PRs #108 a #119). Serve para quem for mexer nessas
páginas: o que existe, onde está, por que foi feito assim e o que não pode
quebrar.

## 1. Rotas

| Página | Rota pública | Preview (noindex) | Template | View |
|---|---|---|---|---|
| Município | `/municipio/<cod_ibge>/` | `/preview/municipio/<cod_ibge>/` | `detail_mun/detalhe_municipio_folheto.html` | `detail_mun.views.municipio_detalhe_view` |
| Agregado | `/analise-municipal/` | `/preview/agregado/` | `detail_agg/detalhe_conjunto_folheto.html` | `detail_agg.views.conjunto_detalhe_view` |
| Gráficos | `/analise/` | `/preview/analise/` | `home/home_folheto.html` | `home.views.home` |

- A rota pública e a preview usam **a mesma view**; o template vem do dict
  `{'template_name': ...}` em `config/urls.py`.
- O layout antigo (`detalhe_municipio.html`, `detalhe_conjunto.html`,
  `home.html`) continua no repositório e é o default das views.
  **Rollback:** tirar o `{'template_name': ...}` da rota pública em
  `config/urls.py` e publicar.
- O `<meta name="robots" content="noindex">` só sai quando a URL contém
  `/preview/` (`{% if '/preview/' in request.path %}`).
- Landing (`/`), Mapa e Metodologia **não** mudaram de layout.

## 2. Como as páginas são montadas

Princípio: **reaproveitar, não reescrever.** Os scripts antigos continuam donos
de filtros, gráficos, árvore de receitas e chamadas de API. Cada página nova
acrescenta um script `*_folheto.js` que roda depois e cuida só do que é novo.

| Página | Script original (dono dos dados) | Complemento do folheto | CSS |
|---|---|---|---|
| Município | `detail_mun/js/script_mun.js` | `detail_mun/js/script_mun_folheto.js` | `detail_mun/css/style_mun_folheto.css` |
| Agregado | `detail_agg/js/script.js` | `detail_agg/js/script_agg_folheto.js` | `style_mun_folheto.css` + `detail_agg/css/style_agg_folheto.css` |
| Gráficos | `home/js/script.js` | `home/js/script_home_folheto.js` | `style_mun_folheto.css` + `style_agg_folheto.css` + `home/css/style_home_folheto.css` |

Regras que evitam regressão:

- **IDs que os scripts antigos escrevem sem checar** (`kpi-*`, `summary-*`)
  precisam existir na página. Quando o texto visível passou a ser frase, eles
  ficaram num `<div hidden>`.
- **`style_mun_folheto.css` é a base das três páginas.** Antes de remover
  qualquer classe `fx-*`, procure o uso em `detail_mun`, `detail_agg`, `home`
  e `ifem`. (No #108 a remoção de `.fx-stat` e `.fx-btn-baixar` quebrou o
  agregado e os gráficos; corrigido no #113.)
- **Não redefinir classes do Bootstrap soltas.** Um `.d-none` global no CSS da
  análise anulava o `.d-lg-flex` do menu do topo, que sumia no desktop. Hoje
  ele vale só dentro de `.fx-page` e `.fx-modal` (#118).
- **Comentário de template com várias linhas usa `{% comment %}`.** `{# #}`
  só funciona numa linha; em várias, o texto vaza na página.

### Eventos entre os scripts

Os scripts originais disparam eventos depois de desenhar. Na página antiga
ninguém escuta, então nada muda lá.

| Evento | Quem dispara | Quando | `detail` | Quem usa |
|---|---|---|---|---|
| `ifem:dados-dashboard` | `home/js/script.js` | depois de desenhar gráfico e tabelas | resposta de `/api/dashboard-data/` | hero e mapa de calor dos Gráficos |
| `ifem:kpis-conjunto` | `detail_agg/js/script.js` | depois de `/api/dados-detalhados/` | `kpis` da resposta | hero e linha Receita corrente do Agregado |
| `agregado:dados-atualizados` | `detail_agg/js/script.js` | depois de `/api/fiscal-details/` | `hist` | síntese do Agregado |

## 3. Município

**Topo (hero)**
- Valor em destaque: receita corrente por habitante, com o rótulo
  "por habitante em receita corrente."
- Frase: "São N habitantes e possuem a receita per capita maior que X% dos
  municípios do país." Abaixo de 50% entra **"apenas"**. O percentual vem
  na cor do quintil.
- Tag do quintil IFEM ao lado do nome (`.fx-tag-quintil`). Nomes com mais de
  24 caracteres usam fonte menor (`.fx-hero-nome--longo`).
- Régua dos quintis com marcador no percentil.
- Coluna "Posição no Brasil": população primeiro, receita depois, cada uma no
  seu ranking ("ocupa o Xº lugar entre N"). **Nunca "cai" ou "sobe"**: são
  dois rankings diferentes. A cor de cada posição é o quintil em que ela cai
  no ranking geral, não o quintil IFEM do município.
- Nota final conforme a distância entre as posições (≥ 25% do ranking):
  descompasso que o IFEM mede, o inverso do subfinanciamento, ou posições que
  caminham juntas.
- O botão Baixar saiu; o Ctrl+P continua usando o CSS de impressão.

**Estrutura de Receitas**
- Primeira linha, em destaque: **Receita corrente** total, com "supera X% dos
  municípios" e as médias/medianas de UF e Brasil
  (`detail_mun/receita_corrente.py`, cache de 30 min).
- A linha fica **fora** de `#main-revenue-details-container` porque o
  `script_mun.js` reordena por valor tudo o que está lá dentro.

## 4. Agregado

Mesmo topo do município, adaptado a um conjunto:

- "São N habitantes em M municípios e possuem a receita per capita maior que
  [apenas] X% dos municípios do país." + régua.
- "Posição no Brasil" com o verbo no condicional (**"ocuparia"**, decisão da
  diretoria): o conjunto não tem lugar oficial, a conta o trata como se fosse
  um município só.
  - População: soma do conjunto contra a população de cada município.
  - Receita: receita por habitante do conjunto contra a de cada município.
  - Código: `detail_mun/posicao_conjunto.py`, exposto em `kpis.posicao` de
    `/api/dados-detalhados/`.
- Sem filtro o conjunto é o país inteiro; a coluna convida a escolher um
  recorte.
- Linha **Receita corrente** no topo da Estrutura de Receitas, com a mesma
  barra divergente das outras linhas (mesmas faixas: -60/-20/20/60) e a média
  Brasil (`kpis.media_nacional_receita_pc`).
- Sem botão Baixar.

## 5. Gráficos

**Topo**
- Título na largura toda; valor e coluna da direita alinhados pelo topo.
- Esquerda: média em destaque e "São N municípios, X% dos que têm dados de
  receita no país."
- Direita, "Como os grupos são formados": a frase muda com o toggle
  **Quintis do país / do filtro** e com **Quintil / Decil**. Com filtro, soma a
  distância da média nacional.

**Faixas populacionais: matriz de calor**
- Células coloridas numa rampa quente (creme → vermelho), número centralizado.
- Com 2000 e 2025 na tela a escala é **a mesma** nas duas tabelas.
- Funciona em número e em %. Total Geral e coluna Total ficam neutros.
- No celular a coluna da faixa fica presa à esquerda.

## 6. Topo do site fixo

Nas páginas com barra de filtros (`.fx-controles`), o menu do site
(`.page-header`, do `global/head.html`) gruda no topo junto com a barra, para
trocar de página sem rolar até o início.

- Código: `iniciarTopoFixo()` em `base_statics/global/js/fx-secoes.js` e o
  bloco "Topo fixo" de `base_statics/global/css/fx-secoes.css`.
- Ao rolar mais de 40px o menu fica compacto (logos menores); volta abaixo de
  10px. A barra se encaixa embaixo pela variável `--fx-topo-h`.
- A navegação entre seções desconta menu + barra, para o título não ficar
  escondido.
- Landing, Mapa e Metodologia não têm barra de filtros e não mudam.

## 7. Vídeos da landing e da metodologia

Problema: o vídeo de fundo (`ifem/static/ifem/videos/videohero.mp4`, 48 MB)
tinha o índice (`moov`) no fim do arquivo, e o servidor não atende pedidos
por partes (Range). O navegador baixava os 48 MB antes do primeiro quadro.

- O arquivo foi reorganizado com o índice no início, **sem recodificar**
  (mesmos bytes de vídeo, conferido quadro a quadro). Primeiro quadro: de
  **20,3 s para 0,5 s** a 20 Mbps.
- A landing usa `{% static %}` no vídeo: o nome ganha hash, e trocar o arquivo
  invalida o cache da Cloudflare.
- Os três vídeos dos cards (53 MB) só carregam e tocam quando o card aparece
  na tela (`data-video-lazy` + IntersectionObserver em `ifem/js/landing.js`).

**Ao trocar um vídeo:** gere o arquivo já com o índice no início
(`ffmpeg -i entrada.mp4 -movflags +faststart ...`). Pendente: recomprimir o
vídeo de fundo (dá para chegar perto de 4 MB) e os dos cards.

## 8. Vocabulário dos textos

- "com menor receita por habitante" / "com maior receita por habitante",
  **nunca** "pobre" e "rico".
- Não usar "seleção" para o recorte filtrado: "municípios do filtro",
  "desses municípios".
- Rankings diferentes: "ocupa o Xº lugar"; "cai/sobe" só para o mesmo ranking
  em anos diferentes.
- Sem travessão nos textos visíveis.
- Estatística técnica (ex.: coeficiente de variação) só com pedido explícito.

## 9. Conhecido e pendente

- **Título da aba:** o `global/head.html` tem um `<title>` fixo antes do
  bloco `extra_head`, então todas as páginas mostram "Dashboard de Receitas
  Municipais". Vale para o site todo, inclusive o layout antigo.
- **Total da população:** o município usa o ranking gravado na base (5.570);
  o agregado conta os municípios com população na base (5.479).
- O pop-up "Como ler" dos Gráficos ainda fala em "seleção atual" (texto
  compartilhado com o layout antigo).
- Recompressão dos vídeos (item 7).

## 10. Como validar uma mudança

1. `./venv/Scripts/python.exe manage.py runserver 8899`.
2. Abrir as três páginas no desktop (1280px) e no celular (390px). Conferir
   que não há rolagem lateral (`document.documentElement.scrollWidth`) nem erro
   no console.
3. Município: testar SP (3550308), um abaixo de 50% (Açailândia 2100055) e
   um nome longo (Vila Bela da Santíssima Trindade 5105507).
4. Agregado: sem filtro, com UF e com região metropolitana.
5. Gráficos: 2025, "2000 e 2025", número e %, quintis do país e do filtro,
   quintil e decil.
6. Rolar a página e confirmar o menu e a barra encaixados no topo.
