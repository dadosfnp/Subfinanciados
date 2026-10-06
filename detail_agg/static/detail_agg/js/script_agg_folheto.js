/* ============================================================================
 * script_agg_folheto.js: complemento da preview do agregado (/preview/agregado/)
 * ----------------------------------------------------------------------------
 * Roda DEPOIS do detail_agg/js/script.js e nao substitui nada dele. O script
 * original continua dono de filtros, KPIs, arvore, graficos e sintese. Este
 * arquivo cuida apenas do que a pagina nova acrescenta:
 *   1. titulo e chips do hero a partir dos filtros ativos;
 *   2. numeros grandes da sintese (o script.js escreve frases, aqui sao cards);
 *   3. filtros recolhiveis no celular;
 *   4. botao Baixar (impressao do navegador).
 * ========================================================================== */
(function () {
  'use strict';

  var fmt1 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });

  function pct(v, comSinal) {
    var n = Number(v);
    if (!isFinite(n)) return 'n/d';
    return (comSinal && n > 0 ? '+' : '') + fmt1.format(n) + '%';
  }

  // Ordem importa: do recorte mais especifico para o mais amplo. O titulo usa
  // o primeiro filtro ativo; os demais viram chips abaixo dele.
  var FILTROS = [
    { id: 'filtro-consorcio', rotulo: function (t) { return t; } },
    { id: 'filtro-rm', rotulo: function (t) { return t; } },
    { id: 'filtro-uf', rotulo: function (t) { return 'Municípios de ' + t; } },
    { id: 'filtro-regiao', rotulo: function (t) { return 'Região ' + t; } },
    { id: 'filtro-porte', rotulo: function (t) { return 'Municípios de ' + t.toLowerCase(); } },
    { id: 'filtro-subgrupo', rotulo: function (t) { return t; } }
  ];

  function textoSelecionado(sel) {
    if (!sel || !sel.value || sel.value === 'todos') return null;
    var opt = sel.options[sel.selectedIndex];
    return opt ? opt.text.trim() : sel.value;
  }

  var elTitulo = document.getElementById('fx-agg-titulo');
  var elChips = document.getElementById('fx-agg-chips');
  var elBarraTitulo = document.getElementById('fx-agg-barra-titulo');

  /** Reescreve titulo, chips e destaque dos selects conforme os filtros. */
  function atualizarCabecalho() {
    var ativos = [];
    FILTROS.forEach(function (f) {
      var sel = document.getElementById(f.id);
      var txt = textoSelecionado(sel);
      if (sel) sel.classList.toggle('is-ativo', !!txt);
      if (txt) ativos.push({ txt: txt, titulo: f.rotulo(txt) });
    });

    var titulo = ativos.length ? ativos[0].titulo : 'Todos os municípios do Brasil';
    if (elTitulo) elTitulo.textContent = titulo;
    if (elBarraTitulo) elBarraTitulo.textContent = ativos.length ? ativos[0].txt : 'Análise agregada';
    document.querySelectorAll('.fx-agg-nome-curto').forEach(function (el) {
      el.textContent = ativos.length ? ativos[0].txt : 'Brasil';
    });

    if (elChips) {
      elChips.innerHTML = '';
      // O primeiro filtro ja esta no titulo; os chips mostram so os demais.
      var resto = ativos.slice(1);
      if (!ativos.length) {
        var neutro = document.createElement('span');
        neutro.className = 'fx-agg-chip fx-agg-chip--neutro';
        neutro.textContent = 'Use os filtros acima para recortar o conjunto';
        elChips.appendChild(neutro);
      }
      resto.forEach(function (a) {
        var chip = document.createElement('span');
        chip.className = 'fx-agg-chip';
        chip.textContent = a.txt;
        elChips.appendChild(chip);
      });
    }
  }

  // Os selects sao repovoados pelo script.js depois de cada fetch de filtros
  // dependentes; escutar 'change' cobre a escolha do usuario, e o evento abaixo
  // cobre o repovoamento (o valor pode voltar a 'todos' sem 'change').
  document.querySelectorAll('#filters select').forEach(function (sel) {
    sel.addEventListener('change', atualizarCabecalho);
  });

  var btnLimpar = document.getElementById('btn-limpar-filtros');
  if (btnLimpar) {
    // O script.js zera os selects no proprio clique; um tick depois le o estado.
    btnLimpar.addEventListener('click', function () { window.setTimeout(atualizarCabecalho, 0); });
  }

  // ---- Sintese: numeros grandes ----
  var elDeltaRc = document.getElementById('fx-agg-delta-rc');
  var elMediaRc = document.getElementById('fx-agg-media-rc');
  var elDeltaPop = document.getElementById('fx-agg-delta-pop');
  var elMediaPop = document.getElementById('fx-agg-media-pop');

  function pintar(el, v) {
    if (!el) return;
    el.textContent = pct(v, true);
    el.classList.toggle('is-positivo', Number(v) >= 0);
    el.classList.toggle('is-negativo', Number(v) < 0);
  }

  /*
   * O script.js dispara este evento depois de cada /api/fiscal-details/, com o
   * hist_data da resposta. E o mesmo dado que ele usa para as frases e os
   * graficos da pagina publica, entao os numeros nunca divergem das barras.
   */
  document.addEventListener('agregado:dados-atualizados', function (ev) {
    var h = (ev.detail || {}).hist || {};
    pintar(elDeltaRc, h.delta_rc_pc);
    pintar(elDeltaPop, h.delta_pop);
    if (elMediaRc) elMediaRc.textContent = pct(h.media_nacional_rc_pc, true);
    if (elMediaPop) elMediaPop.textContent = pct(h.media_nacional_pop, true);
    atualizarCabecalho();
  });

  // ---- Filtros no celular ----
  var barra = document.querySelector('.fx-controles--agg');
  var btnFiltros = document.getElementById('fx-agg-abrir-filtros');
  if (barra && btnFiltros) {
    btnFiltros.addEventListener('click', function () {
      var aberto = barra.classList.toggle('is-filtros-abertos');
      btnFiltros.setAttribute('aria-expanded', aberto ? 'true' : 'false');
    });
    // Escolheu um filtro no celular: recolhe, para a pessoa ver o resultado.
    document.querySelectorAll('#filters select').forEach(function (sel) {
      sel.addEventListener('change', function () {
        if (window.innerWidth > 860) return;
        barra.classList.remove('is-filtros-abertos');
        btnFiltros.setAttribute('aria-expanded', 'false');
      });
    });
  }

  // ---- Baixar ----
  // window.print(), como na preview do municipio. A arvore inteira e aberta
  // antes: rubrica recolhida nao sai no papel.
  var btnBaixar = document.getElementById('fx-baixar');
  if (btnBaixar) {
    btnBaixar.addEventListener('click', function () {
      document.querySelectorAll('.fx-row[data-target]').forEach(function (linha) {
        var alvo = document.getElementById(linha.getAttribute('data-target'));
        if (alvo && alvo.classList.contains('hidden')) {
          alvo.classList.remove('hidden');
          linha.classList.add('open');
        }
      });
      window.setTimeout(function () { window.print(); }, 350);
    });
  }

  // O script.js escreve a diferenca sem sinal ("2,7%"). Acima da media, o "+"
  // deixa a leitura imediata, como nos demais numeros da pagina.
  var elDiff = document.getElementById('kpi-diferenca-media');
  if (elDiff && window.MutationObserver) {
    new MutationObserver(function () {
      var t = elDiff.textContent.trim();
      if (elDiff.classList.contains('pos') && t.charAt(0) !== '+') elDiff.textContent = '+' + t;
    }).observe(elDiff, { childList: true, characterData: true, subtree: true });
  }

  atualizarCabecalho();
})();
