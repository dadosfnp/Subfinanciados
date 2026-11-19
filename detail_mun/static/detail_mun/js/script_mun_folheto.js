/* ============================================================================
 * script_mun_folheto.js — complemento da página de preview do município
 * ----------------------------------------------------------------------------
 * NÃO substitui o script_mun.js: roda DEPOIS dele e cuida apenas do que é novo
 * nesta página. Tudo que já existia continua sendo responsabilidade do script
 * original, de propósito:
 *
 *   script_mun.js  → toggles (base / per capita / média-mediana), gráficos de
 *                    composição, densidade, síntese fiscal, ordenação das
 *                    rubricas por valor, sticky header, rankings.
 *   este arquivo   → tabela de barras do folheto (inclusive a linha de total)
 *                    e o hero: frases de comparação e posição, régua de quintis.
 *
 * A tabela reaproveita as classes que o script original já manipula
 * (.valor-per-capita / .valor-absoluto / .estatistica-media / .estatistica-mediana),
 * então os toggles de valor e de estatística funcionam aqui sem uma linha extra.
 * ========================================================================== */
(function () {
  'use strict';

  // ─── Paleta ───────────────────────────────────────────────────────────────
  // Espelha FNP_Q1..Q5 (folheto-ifem/python/core/tokens.py) e o REVENUE_COLORS
  // do script_mun.js. `txt` é a variante escurecida para texto: no papel o
  // número sai na cor da barra, mas amarelo e verde-claro sobre branco ficam
  // em ~2:1 de contraste. Ver o topo de style_mun_folheto.css.
  var QUINTIS = [
    { bar: '#A81C21', txt: '#A81C21' }, // 1 — supera até 20%
    { bar: '#E47326', txt: '#B0530E' }, // 2 — até 40%
    { bar: '#F4D01D', txt: '#8A6A00' }, // 3 — até 60%
    { bar: '#6AC074', txt: '#2E7D45' }, // 4 — até 80%
    { bar: '#1C9148', txt: '#167A3C' }  // 5 — acima de 80%
  ];
  var SEM_DADO = { bar: '#B9BFC7', txt: '#6B7280' };

  /**
   * Converte um percentil (0–100) no par de cores do quintil.
   * Faixas idênticas às de `cor_por_percentil` do folheto: <=20, <=40, <=60,
   * <=80, resto. Sem valor ou negativo cai no cinza de "sem dado".
   */
  function corPorPercentil(pct) {
    if (pct === null || pct === undefined || isNaN(pct) || pct < 0) return SEM_DADO;
    if (pct <= 20) return QUINTIS[0];
    if (pct <= 40) return QUINTIS[1];
    if (pct <= 60) return QUINTIS[2];
    if (pct <= 80) return QUINTIS[3];
    return QUINTIS[4];
  }

  var fmtInt = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });
  var fmt1 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });

  function reais(v) {
    if (v === null || v === undefined || isNaN(v)) return 'n/d';
    var abs = Math.abs(v);
    if (abs >= 1e9) return 'R$ ' + fmt1.format(v / 1e9) + ' bi';
    if (abs >= 1e6) return 'R$ ' + fmt1.format(v / 1e6) + ' mi';
    return 'R$ ' + fmtInt.format(v);
  }

  var DADOS = (function () {
    var el = document.getElementById('fx-data');
    if (!el) return null;
    try {
      return JSON.parse(el.textContent);
    } catch (erro) {
      console.error('[folheto] #fx-data inválido', erro);
      return null;
    }
  })();

  if (!DADOS) return;

  var ESCOPO = {
    nacional: { frase: 'dos municípios do país', curto: '% dos municípios do país', onde: 'no país', titulo: 'Posição no Brasil' },
    estadual: { frase: 'dos municípios do estado', curto: '% dos municípios do estado', onde: 'em ' + (DADOS.uf || '').toUpperCase(), titulo: 'Posição em ' + (DADOS.uf || '').toUpperCase() },
    faixa: { frase: 'dos municípios do mesmo porte', curto: '% dos municípios do mesmo porte', onde: 'no porte', titulo: 'Posição entre os de mesmo porte' }
  };

  var baseAtual = 'nacional';

  // ==========================================================================
  // 1. TABELA DE RECEITAS
  // ==========================================================================
  /**
   * Repinta uma linha conforme a base ativa. Barra, percentual e valor em R$
   * compartilham a cor, então basta escrever duas custom properties na linha e
   * deixar o CSS distribuir.
   */
  function pintarLinha(linha) {
    var bruto = linha.getAttribute('data-pct-' + baseAtual);
    // Com L10N ligado o Django escreve "66,0"; normaliza antes de converter.
    var pct = bruto === null || bruto === '' ? null : parseFloat(String(bruto).replace(',', '.'));
    var temDado = pct !== null && !isNaN(pct) && pct >= 0;
    var cor = corPorPercentil(temDado ? pct : null);

    linha.style.setProperty('--fx-cor', cor.bar);
    linha.style.setProperty('--fx-cor-txt', cor.txt);
    linha.setAttribute('data-sem-dado', temDado ? '0' : '1');

    var elPct = linha.querySelector('.fx-pct');
    var elBarra = linha.querySelector('.fx-bar-fill');
    var elSupera = linha.querySelector('.fx-supera');
    var nome = ((linha.querySelector('.fx-nome') || {}).textContent || 'esta rubrica').trim();

    if (elPct) elPct.textContent = temDado ? Math.round(pct) + '%' : 'n/d';
    if (elBarra) elBarra.style.width = temDado ? Math.max(pct, 0) + '%' : '0%';

    // Tooltip com as DUAS leituras: o percentual sozinho contava metade da
    // história — "supera 66%" não deixa claro que 34% ficam acima.
    if (elSupera) {
      elSupera.title = temDado
        ? 'Em ' + nome + ', arrecada mais que ' + Math.round(pct) + '% e menos que ' +
          (100 - Math.round(pct)) + '% ' + ESCOPO[baseAtual].frase + '.'
        : 'Sem dado comparativo para esta rubrica.';
    }
  }

  var linhas = Array.prototype.slice.call(document.querySelectorAll('.fx-row'));

  function pintarTabela() {
    linhas.forEach(pintarLinha);
  }

  // ---- Árvore expansível ----
  function alternarLinha(linha) {
    var alvo = linha.getAttribute('data-target');
    if (!alvo) return;
    var filhos = document.getElementById(alvo);
    if (!filhos) return;

    var abrindo = !filhos.classList.contains('is-open');
    filhos.classList.toggle('is-open', abrindo);
    linha.classList.toggle('is-open', abrindo);
    linha.setAttribute('aria-expanded', abrindo ? 'true' : 'false');
  }

  linhas.forEach(function (linha) {
    if (!linha.classList.contains('fx-clickable')) return;

    linha.addEventListener('click', function () { alternarLinha(linha); });

    // A linha é role="button": Enter e Espaço precisam agir como clique, senão
    // a árvore fica inacessível fora do mouse.
    linha.addEventListener('keydown', function (evento) {
      if (evento.key !== 'Enter' && evento.key !== ' ') return;
      evento.preventDefault();
      alternarLinha(linha);
    });
  });

  // ==========================================================================
  // 2. HERO
  // ==========================================================================
  var elVeredito = document.getElementById('fx-veredito-texto');
  var elVeredValor = document.getElementById('fx-veredito-valor');
  var elMarcador = document.getElementById('fx-regua-marcador');
  var elPosicaoTitulo = document.getElementById('fx-posicao-titulo');
  var elPosicaoTexto = document.getElementById('fx-posicao-texto');
  var elTotalLeitura = document.getElementById('fx-total-leitura');
  var elHeadEscopo = document.getElementById('fx-head-escopo');
  var elComoLerEscopo = document.getElementById('fx-como-ler-escopo');
  var quintisRegua = Array.prototype.slice.call(document.querySelectorAll('.fx-regua-q'));

  /**
   * Percentil geral do município na base ativa.
   *
   * O model só expõe o percentil nacional (percentil24_n). Estado e porte saem
   * da posição no ranking pela regra oficial do IFEM
   * (folheto-ifem/python/core/paleta_ranking.py):
   *     percentil = (total - posição) / total * 100
   * Posição 1 = maior receita por habitante, logo percentil ~100.
   */
  function percentilGeral() {
    if (baseAtual === 'nacional' && DADOS.percentil_nacional !== null && DADOS.percentil_nacional !== undefined) {
      return DADOS.percentil_nacional;
    }
    var r = (DADOS.rank || {})[baseAtual];
    if (!r || !r.total || !r.pos) return null;
    return (r.total - r.pos) / r.total * 100;
  }

  function atualizarHero() {
    var pct = percentilGeral();
    var temDado = pct !== null && !isNaN(pct);
    var cor = corPorPercentil(temDado ? pct : null);
    var esc = ESCOPO[baseAtual];

    if (elHeadEscopo) elHeadEscopo.textContent = esc.curto;
    if (elComoLerEscopo) elComoLerEscopo.textContent = esc.frase;
    if (elVeredValor) elVeredValor.textContent = reais(DADOS.receita.pc);

    if (elVeredito) {
      // Habitantes entram na frase, no lugar do card que ficava a direita.
      var trechoPop = DADOS.populacao
        ? ' e tem <strong>' + fmtInt.format(DADOS.populacao) + '</strong> habitantes'
        : '';
      // O quintil e o oficial do IFEM (nacional), qualquer que seja a base:
      // e a classificacao que o municipio tem no resto da plataforma. Fica em
      // frase propria para a primeira nao virar uma lista de tres clausulas.
      var quintil = parseInt(DADOS.quintil, 10);
      var fraseQuintil = quintil >= 1 && quintil <= 5
        ? ' Faz parte do <strong>' + quintil + 'º quintil</strong> de subfinanciamento.'
        : '';
      var fraseComparacao = temDado
        ? 'Arrecada mais que <strong style="color:' + cor.bar + '">' + Math.round(pct) + '%</strong> ' +
          esc.frase + trechoPop + '.'
        : '<span style="opacity:.7">Sem dado comparativo para esta base.</span>';
      elVeredito.innerHTML = fraseComparacao + fraseQuintil;
    }

    // Leitura da linha "Receita corrente" na tabela: mesma base do hero.
    if (elTotalLeitura) {
      elTotalLeitura.textContent = temDado
        ? 'supera ' + Math.round(pct) + '% ' + esc.frase
        : 'sem dado comparativo para esta base';
    }

    if (elMarcador) {
      elMarcador.style.left = (temDado ? Math.min(Math.max(pct, 0), 100) : 0) + '%';
      elMarcador.style.display = temDado ? '' : 'none';
    }

    var quintilAtivo = temDado ? Math.min(Math.floor(pct / 20) + 1, 5) : 0;
    quintisRegua.forEach(function (q) {
      q.classList.toggle('is-ativo', Number(q.getAttribute('data-q')) === quintilAtivo);
    });

    if (elPosicaoTitulo) elPosicaoTitulo.textContent = esc.titulo;
    if (elPosicaoTexto) elPosicaoTexto.innerHTML = frasePosicao(esc);
  }

  /**
   * Frase de posicao do lado direito do hero, na base ativa:
   *   "São Paulo está em 1.866º de 5.479 em receita por habitante,
   *    mas em população vai para 1º de 5.479!"
   *
   * O "mas ... !" so aparece quando as duas posicoes contam historias
   * diferentes (distancia de pelo menos 1/4 do ranking). Entre 10º e 12º o
   * contraste seria forcado, entao a frase vira "e em população está em".
   *
   * @param {Object} esc - entrada de ESCOPO da base ativa.
   * @returns {string} HTML da frase; nomes vem do JSON e sao escapados.
   */
  function frasePosicao(esc) {
    var rRec = (DADOS.rank || {})[baseAtual] || {};
    var rPop = (DADOS.rank_populacao || {})[baseAtual] || {};
    var nome = escaparHtml(DADOS.nome || 'O município');

    function pos(r) {
      return '<strong class="fx-pos-num">' + fmtInt.format(r.pos) + 'º</strong>' +
        (r.total ? ' de ' + fmtInt.format(r.total) : '');
    }

    if (!rRec.pos) return 'Sem ranking de receita disponível ' + esc.onde + '.';

    var frase = nome + ' está em ' + pos(rRec) + ' em receita por habitante';
    if (!rPop.pos) return frase + '.';

    var total = rRec.total || rPop.total || 0;
    var contraste = total && Math.abs(rRec.pos - rPop.pos) / total >= 0.25;
    return frase + (contraste
      ? ', mas em população vai para ' + pos(rPop) + '!'
      : ' e em população está em ' + pos(rPop) + '.');
  }

  function escaparHtml(texto) {
    return String(texto).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  // ==========================================================================
  // 3. SINCRONIA COM O TOGGLE DE BASE
  // ==========================================================================
  /*
   * O script_mun.js é dono do #global-base-toggle e já reage ao clique, mas a
   * função dele (updateGlobalBase) é interna ao escopo do arquivo e não emite
   * evento. Em vez de duplicar a lógica, escutamos o mesmo clique: cada script
   * atualiza o que é seu, sem um chamar o outro.
   */
  document.querySelectorAll('#global-base-toggle .segmented-option').forEach(function (botao) {
    botao.addEventListener('click', function () {
      var base = botao.getAttribute('data-base');
      if (!base || base === baseAtual) return;
      baseAtual = base;
      pintarTabela();
      atualizarHero();
    });
  });

  // ==========================================================================
  // 3b. SINCRONIA COM O TOGGLE DE MEDIA / MEDIANA
  // ==========================================================================
  /*
   * O script_mun.js ja troca os VALORES das colunas (.estatistica-media e
   * .estatistica-mediana), mas o cabecalho e a nota do card "Como ler" sao
   * desta pagina e continuavam dizendo "Media" com a mediana na tela.
   */
  var ROTULO_ESTATISTICA = {
    media: { cabecalho: 'Média', nota: 'médio' },
    mediana: { cabecalho: 'Mediana', nota: 'mediano' }
  };
  var elHeadMediasRot = document.getElementById('fx-head-medias-rot');
  var elComoLerEst = document.getElementById('fx-como-ler-est');

  function atualizarRotuloEstatistica(est) {
    var rotulo = ROTULO_ESTATISTICA[est];
    if (!rotulo) return;
    if (elHeadMediasRot) elHeadMediasRot.textContent = rotulo.cabecalho;
    if (elComoLerEst) elComoLerEst.textContent = rotulo.nota;
  }

  document.querySelectorAll('#estatistica-toggle .segmented-option').forEach(function (botao) {
    botao.addEventListener('click', function () {
      atualizarRotuloEstatistica(botao.getAttribute('data-est'));
    });
  });

  // ==========================================================================
  // 4. BOOT
  // ==========================================================================
  /*
   * Abre as rubricas de nível 0 na carga: o folheto impresso mostra os níveis
   * 1 e 2 sem exigir interação, e com tudo fechado a tabela fica com 4 linhas
   * ao lado de uma coluna de cards bem mais alta.
   */
  function abrirPrimeiroNivel() {
    document.querySelectorAll('.fx-row.fx-clickable[data-level="0"]').forEach(alternarLinha);
  }

  /*
   * A legenda do donut e desenhada DENTRO do canvas pelo Chart.js, entao CSS
   * nao a alcanca. Na pagina publica o card ocupa 40% de 1180px; aqui a coluna
   * e mais estreita e a mesma legenda saia desproporcional. Em vez de duplicar
   * a configuracao do grafico, ajustamos a instancia que o script_mun.js ja
   * criou.
   */
  function ajustarLegendasDosGraficos() {
    if (!window.Chart || !window.Chart.getChart) return;

    ['myChart', 'densidadeReceita'].forEach(function (id) {
      var canvas = document.getElementById(id);
      if (!canvas) return;
      var grafico = window.Chart.getChart(canvas);
      if (!grafico || !grafico.options || !grafico.options.plugins) return;

      var legenda = grafico.options.plugins.legend;
      if (!legenda || legenda.display === false) return;

      legenda.labels = Object.assign({}, legenda.labels, {
        font: { size: 10.5 },
        boxWidth: 9,
        boxHeight: 9,
        padding: 8
      });
      grafico.update('none'); // sem reanimar: o grafico ja esta na tela
    });
  }

  pintarTabela();
  atualizarHero();
  abrirPrimeiroNivel();

  // O script_mun.js cria os graficos no DOMContentLoaded dele; um tick a mais
  // garante que as instancias existam antes de mexer nelas.
  window.setTimeout(ajustarLegendasDosGraficos, 600);
})();
