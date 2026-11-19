/* ============================================================================
 * script_home_folheto.js: complemento da preview da analise grafica
 * (/preview/analise/)
 * ----------------------------------------------------------------------------
 * Carregado ANTES do home/js/script.js, que continua dono de filtros, cards,
 * grafico e tabelas. Aqui so:
 *   1. (o pop-up de ajuda usa o bootstrap.Modal do head global, sem codigo aqui);
 *   2. titulo e chips do hero a partir dos filtros;
 *   3. faixa de cor do grupo no cabecalho das tabelas;
 *   4. filtros recolhiveis no celular e teclado nos botoes de ano;
 *   5. hero em texto e mapa de calor das tabelas, a partir do evento
 *      'ifem:dados-dashboard' que o script.js dispara com a resposta da API.
 * ========================================================================== */
(function () {
  'use strict';

  var fmtInt = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });
  var fmtPct = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 });

  // Mesmas variantes claras do hero do municipio (QUINTIS.escuro em
  // script_mun_folheto.js): legiveis sobre o azul escuro.
  var VERDE_ESCURO = '#3DCB73';
  var VERMELHO_ESCURO = '#FF6B66';

  /**
   * Rampa quente do mapa de calor: creme (poucos municipios) ate vermelho
   * escuro (muitos). Sequencial de proposito: o que se le aqui e quantidade,
   * nao bom/ruim, entao nao reaproveita a paleta divergente dos quintis.
   */
  var RAMPA_CALOR = [
    [0, [255, 246, 224]],
    [0.2, [254, 227, 162]],
    [0.45, [253, 184, 99]],
    [0.7, [240, 123, 63]],
    [1, [178, 34, 44]]
  ];

  /**
   * Cor da rampa para t em [0, 1], interpolando em RGB entre as paradas.
   * @param {number} t intensidade normalizada pelo maior valor da matriz
   * @returns {string} cor rgb() pronta para o CSS
   */
  function corCalor(t) {
    t = Math.max(0, Math.min(1, t));
    for (var i = 1; i < RAMPA_CALOR.length; i++) {
      var b = RAMPA_CALOR[i];
      if (t > b[0]) continue;
      var a = RAMPA_CALOR[i - 1];
      var f = (t - a[0]) / (b[0] - a[0] || 1);
      var rgb = a[1].map(function (c, k) { return Math.round(c + (b[1][k] - c) * f); });
      return 'rgb(' + rgb.join(',') + ')';
    }
    return 'rgb(' + RAMPA_CALOR[RAMPA_CALOR.length - 1][1].join(',') + ')';
  }

  /** Le "1.088", "67,5%" ou "n/d" da celula; NaN quando nao ha numero. */
  function numeroDaCelula(td) {
    var txt = (td.textContent || '').trim().replace(/\./g, '').replace(',', '.').replace('%', '');
    return txt === '' ? NaN : Number(txt);
  }

  /**
   * Pinta o miolo das tabelas visiveis (sem a coluna de faixa, a coluna Total
   * e a linha Total Geral) numa escala unica. Com 2000 e 2025 na tela, o
   * maior valor e o das duas juntas: a mesma cor vale a mesma quantidade nos
   * dois anos, senao a comparacao lado a lado enganaria.
   */
  function pintarMapaDeCalor() {
    var celulas = [];
    ['#table-2025', '#table-2000'].forEach(function (sel) {
      var tabela = document.querySelector(sel);
      if (!tabela || tabela.closest('.d-none')) return;
      tabela.classList.add('fx-home-tabela--calor');
      tabela.querySelectorAll('tbody tr').forEach(function (tr) {
        var tds = tr.querySelectorAll('td');
        // O script.js so marca .linha-total quando a coluna se chama
        // "Faixas"; aqui ela vem como "Faixas Populacionais" (ou outro
        // rotulo de agrupamento). Reconhece pelo texto e marca, senao o
        // Total Geral entra na escala e vira o maximo.
        var rotulo = tds[0] ? tds[0].textContent.trim() : '';
        if (/^Total/i.test(rotulo)) tr.classList.add('linha-total');
        if (tr.classList.contains('linha-total')) return;
        for (var i = 1; i < tds.length - 1; i++) celulas.push(tds[i]);
      });
    });

    var max = 0;
    celulas.forEach(function (td) {
      var v = numeroDaCelula(td);
      if (isFinite(v) && v > max) max = v;
    });

    celulas.forEach(function (td) {
      var v = numeroDaCelula(td);
      td.classList.add('fx-calor');
      if (!isFinite(v) || max <= 0) {
        td.classList.add('fx-calor--nd');
        return;
      }
      var t = v / max;
      td.style.setProperty('--calor', corCalor(t));
      // Acima de ~55% da rampa o fundo ja e laranja forte: texto branco.
      td.classList.toggle('fx-calor--forte', t > 0.55);
      td.classList.toggle('fx-calor--zero', v === 0);
    });

    var fim = document.getElementById('fx-calor-legenda-fim');
    var pct = document.getElementById('formatPorcentagem');
    if (fim) fim.textContent = pct && pct.checked ? 'maior parcela da faixa' : 'mais municípios';
  }

  /** Numero destacado do hero, com cor opcional (inline: varia com o dado). */
  function num(texto, cor) {
    return '<strong class="fx-pos-num"' + (cor ? ' style="color:' + cor + '"' : '') + '>' + texto + '</strong>';
  }

  /**
   * Monta o hero em frases a partir de summaryCards da API:
   * esquerda = media em destaque + quantidade; direita = distancia da media
   * nacional e dispersao (coeficiente de variacao) dentro da selecao.
   */
  function preencherHero(resumo) {
    if (!resumo) return;
    var elMedia = document.getElementById('fx-home-media');
    var elQtd = document.getElementById('fx-home-quantidade');
    var elComp = document.getElementById('fx-home-comparacao');

    var total = Number(resumo.totalMunicipios) || 0;
    var perc = Number(resumo.percTotalMunicipios) || 0;
    var media = Number(resumo.mediaReceitaPerCapita);
    var diff = Number(resumo.diffMediaNacional);
    var cv = Number(resumo.giniIndex);

    if (elMedia) elMedia.textContent = isFinite(media) && total > 0 ? 'R$ ' + fmtInt.format(Math.round(media)) : 'Sem dados';

    if (elQtd) {
      var qtd = '<span class="fx-hero-pop">' + fmtInt.format(total) + '</span>';
      if (total === 0) {
        elQtd.textContent = 'Nenhum município com dados de receita nesta seleção.';
      } else if (perc >= 99.95) {
        elQtd.innerHTML = 'São ' + qtd + ' municípios, todos os que têm dados de receita no país.';
      } else {
        elQtd.innerHTML = (total === 1 ? 'É ' + qtd + ' município, ' : 'São ' + qtd + ' municípios, ') +
          fmtPct.format(perc) + '% dos que têm dados de receita no país.';
      }
    }

    if (!elComp) return;
    if (total === 0) { elComp.textContent = ''; return; }

    var frase;
    if (!isFinite(diff) || Math.abs(diff) < 0.05) {
      frase = 'A média da seleção é a própria média nacional.';
    } else {
      var acima = diff > 0;
      frase = 'Essa média fica ' + num(fmtPct.format(Math.abs(diff)) + '% ' + (acima ? 'acima' : 'abaixo'),
        acima ? VERDE_ESCURO : VERMELHO_ESCURO) + ' da média nacional.';
    }

    // Com um municipio so nao ha dispersao a medir.
    if (total > 1 && isFinite(cv)) {
      var leitura = cv >= 30 ? 'sinal de alta desigualdade entre os municípios.'
        : cv >= 15 ? 'desigualdade moderada entre os municípios.'
          : 'receitas por habitante parecidas entre os municípios.';
      frase += ' Dentro da seleção, o coeficiente de variação da receita por habitante é de ' +
        num(fmtPct.format(cv) + '%', '#FFC72C') + ', ' + leitura;
    }
    elComp.innerHTML = frase;
  }

  document.addEventListener('ifem:dados-dashboard', function (ev) {
    var data = ev.detail || {};
    try {
      preencherHero(data.summaryCards);
      pintarMapaDeCalor();
    } catch (error) {
      // Falha aqui nao pode derrubar o resto da pagina (grafico e tabelas ja
      // foram desenhados pelo script.js); registra com o que chegou.
      console.error('[analise-folheto] falha ao montar hero/mapa de calor', { resumo: data.summaryCards, error: error });
    }
  });

  // Paleta dos grupos: a mesma do grafico e da preview do municipio.
  var QUINTIS = { 1: '#A81C21', 2: '#E47326', 3: '#F4D01D', 4: '#6AC074', 5: '#1C9148' };
  var DECIS = {
    1: '#960E16', 2: '#CF3026', 3: '#EB6630', 4: '#F8A555', 5: '#FCE182',
    6: '#DDEC88', 7: '#9DD57D', 8: '#60BA69', 9: '#2D964D', 10: '#076931'
  };

  /** Pinta a faixa de cor sob cada "Nº quintil/decil" do cabecalho. */
  function colorirCabecalho(thead) {
    thead.querySelectorAll('th').forEach(function (th) {
      var m = th.textContent.match(/(\d+)\s*º?\s*(quintil|decil)/i);
      if (!m) return;
      var tabela = m[2].toLowerCase() === 'decil' ? DECIS : QUINTIS;
      var cor = tabela[Number(m[1])];
      if (!cor) return;
      th.setAttribute('data-cor', cor);
      th.style.setProperty('--fx-th-cor', cor);
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    // ---- 3. Cabecalho das tabelas ----
    // O script.js reescreve o <thead> a cada atualizacao; o observer repinta.
    ['#table-2025 thead', '#table-2000 thead'].forEach(function (sel) {
      var thead = document.querySelector(sel);
      if (!thead || !window.MutationObserver) return;
      new MutationObserver(function () { colorirCabecalho(thead); }).observe(thead, { childList: true, subtree: true });
    });

    // ---- 2. Titulo e chips ----
    var FILTROS = [
      { id: 'filtro-consorcio', titulo: function (t) { return t; } },
      { id: 'filtro-rm', titulo: function (t) { return t; } },
      { id: 'filtro-uf', titulo: function (t) { return 'Municípios de ' + t; } },
      { id: 'filtro-regiao', titulo: function (t) { return 'Região ' + t; } },
      { id: 'filtro-porte', titulo: function (t) { return 'Municípios de ' + t.toLowerCase(); } }
    ];
    var elTitulo = document.getElementById('fx-home-titulo');
    var elBarra = document.getElementById('fx-home-barra-titulo');
    var elChips = document.getElementById('fx-agg-chips');

    function atualizarCabecalho() {
      var ativos = [];
      FILTROS.forEach(function (f) {
        var sel = document.getElementById(f.id);
        if (!sel) return;
        var ativo = sel.value && sel.value !== 'todos';
        sel.classList.toggle('is-ativo', !!ativo);
        if (!ativo) return;
        var txt = (sel.options[sel.selectedIndex] || {}).text || sel.value;
        ativos.push({ txt: txt.trim(), titulo: f.titulo(txt.trim()) });
      });
      if (elTitulo) elTitulo.textContent = ativos.length ? ativos[0].titulo : 'Todos os municípios do Brasil';
      if (elBarra) elBarra.textContent = ativos.length ? ativos[0].txt : 'Análise gráfica';
      if (elChips) {
        elChips.innerHTML = '';
        ativos.slice(1).forEach(function (a) {
          var chip = document.createElement('span');
          chip.className = 'fx-agg-chip';
          chip.textContent = a.txt;
          elChips.appendChild(chip);
        });
      }
    }

    document.querySelectorAll('#filters select').forEach(function (sel) {
      sel.addEventListener('change', atualizarCabecalho);
    });
    var btnLimpar = document.getElementById('btn-limpar-filtros');
    if (btnLimpar) btnLimpar.addEventListener('click', function () { window.setTimeout(atualizarCabecalho, 0); });
    atualizarCabecalho();

    // ---- 4a. Filtros no celular ----
    var barra = document.querySelector('.fx-controles--agg');
    var btnFiltros = document.getElementById('fx-agg-abrir-filtros');
    if (barra && btnFiltros) {
      btnFiltros.addEventListener('click', function () {
        var aberto = barra.classList.toggle('is-filtros-abertos');
        btnFiltros.setAttribute('aria-expanded', aberto ? 'true' : 'false');
      });
      document.querySelectorAll('#filters select').forEach(function (sel) {
        sel.addEventListener('change', function () {
          if (window.innerWidth > 860) return;
          barra.classList.remove('is-filtros-abertos');
          btnFiltros.setAttribute('aria-expanded', 'false');
        });
      });
    }

    // ---- 4b. Teclado ----
    // Os botoes de ano e de criterio sao <span> (o script.js os seleciona
    // assim); Enter e Espaco precisam agir como clique.
    document.querySelectorAll('.fx-seg .toggle-option').forEach(function (opt) {
      opt.addEventListener('keydown', function (ev) {
        if (ev.key !== 'Enter' && ev.key !== ' ') return;
        ev.preventDefault();
        opt.click();
      });
    });
  });
})();
