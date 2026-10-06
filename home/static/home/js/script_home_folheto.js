/* ============================================================================
 * script_home_folheto.js: complemento da preview da analise grafica
 * (/preview/analise/)
 * ----------------------------------------------------------------------------
 * Carregado ANTES do home/js/script.js, que continua dono de filtros, cards,
 * grafico e tabelas. Aqui so:
 *   1. (o pop-up de ajuda usa o bootstrap.Modal do head global, sem codigo aqui);
 *   2. titulo e chips do hero a partir dos filtros;
 *   3. faixa de cor do grupo no cabecalho das tabelas;
 *   4. filtros recolhiveis no celular e teclado nos botoes de ano.
 * ========================================================================== */
(function () {
  'use strict';

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
