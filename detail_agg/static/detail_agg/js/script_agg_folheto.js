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

  // ---- Hero no formato do municipio ----
  // Texto aprovado no hero do municipio (script_mun_folheto.js), adaptado
  // para conjunto. Duplicado de proposito: as duas previews ainda vao para a
  // diretoria e podem divergir; quando virarem padrao, extrair para global/.
  var fmtInt = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });

  // Variantes claras dos quintis para texto sobre o azul (QUINTIS.escuro do municipio).
  var QUINTIS_ESCURO = ['#FF6B66', '#FF9F5A', '#F4D01D', '#7FD48A', '#3DCB73'];
  var SEM_DADO_ESCURO = '#AABBCC';

  /** Cor do quintil de um percentil 0-100 (faixas <=20, <=40, <=60, <=80, resto). */
  function corPercentil(p) {
    if (p === null || p === undefined || !isFinite(p) || p < 0) return SEM_DADO_ESCURO;
    return QUINTIS_ESCURO[p <= 20 ? 0 : p <= 40 ? 1 : p <= 60 ? 2 : p <= 80 ? 3 : 4];
  }

  function posNum(r) {
    return '<strong class="fx-pos-num" style="color:' + corPercentil(r.percentil) + '">' +
      fmtInt.format(r.pos) + 'º</strong>';
  }

  /**
   * Frase de posicao: mesma estrutura e mesmas leituras do municipio, com o
   * verbo no condicional ("ocuparia"), porque um conjunto nao tem lugar
   * oficial no ranking; a conta o trata como se fosse um municipio so.
   */
  function frasePosicaoConjunto(pos) {
    var rPop = pos && pos.populacao;
    var rRec = pos && pos.receita;
    if (!rRec) return 'Sem ranking de receita disponível para este conjunto.';
    var lugarRec = ' ocuparia o ' + posNum(rRec) + ' lugar entre ' + fmtInt.format(rRec.total) + '.';
    if (!rPop) {
      return 'Em receita corrente per capita, o conjunto ocuparia o ' + posNum(rRec) +
        ' lugar entre ' + fmtInt.format(rRec.total) + ' municípios do país.';
    }
    var abertura = 'Em porte populacional, o conjunto ocuparia o ' + posNum(rPop) +
      ' lugar entre ' + fmtInt.format(rPop.total) + ' municípios do país.';
    var total = rRec.total || rPop.total || 0;
    var distancia = total ? (rRec.pos - rPop.pos) / total : 0;
    if (distancia >= 0.25) {
      return abertura + ' Já em receita corrente per capita,' + lugarRec +
        '<span class="fx-pos-leitura">A distância entre as duas posições expõe o descompasso que o IFEM mede: ' +
        'a demanda por serviços públicos cresce com a população, mas a capacidade de financiamento ' +
        'por habitante não acompanha.</span>';
    }
    if (distancia <= -0.25) {
      return abertura + ' Já em receita corrente per capita,' + lugarRec +
        '<span class="fx-pos-leitura">O inverso do subfinanciamento: uma base populacional menor concentra ' +
        'mais receita corrente por habitante e amplia a capacidade de financiar os serviços públicos.</span>';
    }
    return abertura + ' Em receita corrente per capita,' + lugarRec +
      '<span class="fx-pos-leitura">As duas posições caminham juntas: a capacidade de financiamento ' +
      'por habitante acompanha o porte do conjunto.</span>';
  }

  var elVeredito = document.getElementById('fx-agg-veredito-texto');
  var elPosicao = document.getElementById('fx-agg-posicao-texto');
  var elMarcador = document.getElementById('fx-agg-regua-marcador');
  var quintisRegua = document.querySelectorAll('.fx-regua-q');

  var fmt1Abrev = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });

  /** Valor total abreviado, como o filtro br_abrev das outras linhas. */
  function reaisAbrev(v) {
    var n = Number(v);
    if (!isFinite(n)) return 'n/d';
    var a = Math.abs(n);
    if (a >= 1e9) return 'R$ ' + fmt1Abrev.format(n / 1e9) + ' bi';
    if (a >= 1e6) return 'R$ ' + fmt1Abrev.format(n / 1e6) + ' mi';
    if (a >= 1e3) return 'R$ ' + fmt1Abrev.format(n / 1e3) + ' mil';
    return 'R$ ' + fmtInt.format(n);
  }

  /**
   * Linha "Receita corrente" no topo da Estrutura de Receitas.
   * Barra e faixa de cor com a MESMA regra das outras linhas do agregado
   * (_prepare_revenue_item_aggregated em detail_agg/views.py): metade do
   * trilho para cada lado saturando em +-100%; faixas -60/-20/20/60.
   * A leitura repete a do municipio: "supera X% dos municipios do pais".
   */
  function preencherLinhaTotal(k, percentil) {
    var linha = document.getElementById('fx-agg-total');
    if (!linha) return;
    var pc = Number(k.receita_per_capita);
    var media = Number(k.media_nacional_receita_pc);
    var diffPct = Number(k.diferenca_media) * 100;
    var ok = isFinite(diffPct);
    var faixa = !ok ? 0 : diffPct <= -60 ? 1 : diffPct <= -20 ? 2 : diffPct <= 20 ? 3 : diffPct <= 60 ? 4 : 5;

    linha.style.setProperty('--fx-cor', 'var(--fx-q' + faixa + ')');
    linha.style.setProperty('--fx-cor-txt', QUINTIS_ESCURO[faixa - 1] || SEM_DADO_ESCURO);

    var elPct = document.getElementById('fx-agg-total-pct');
    if (elPct) elPct.textContent = ok ? (diffPct > 0 ? '+' : '') + fmtInt.format(Math.round(diffPct)) + '%' : '';
    var elBarra = document.getElementById('fx-agg-total-barra');
    if (elBarra) {
      elBarra.style.width = (ok ? Math.min(Math.abs(diffPct), 100) / 2 : 0) + '%';
      elBarra.classList.toggle('is-neg', diffPct < 0);
      elBarra.classList.toggle('is-pos', !(diffPct < 0));
    }
    var elPc = document.getElementById('fx-agg-total-pc');
    if (elPc) elPc.textContent = isFinite(pc) ? 'R$ ' + fmtInt.format(Math.round(pc)) : 'n/d';
    var elAbs = document.getElementById('fx-agg-total-abs');
    if (elAbs) elAbs.textContent = reaisAbrev(k.receita_corrente);
    var elMedia = document.getElementById('fx-agg-total-media');
    if (elMedia) elMedia.textContent = isFinite(media) && media > 0 ? 'R$ ' + fmtInt.format(Math.round(media)) : '';
    var elLeit = document.getElementById('fx-agg-total-leitura');
    if (elLeit) {
      elLeit.textContent = percentil !== null
        ? 'supera ' + Math.round(percentil) + '% dos municípios do país'
        : 'sem dado comparativo';
    }
  }

  /** Disparado pelo script.js depois de cada /api/dados-detalhados/. */
  document.addEventListener('ifem:kpis-conjunto', function (ev) {
    var k = ev.detail || {};
    try {
      var pop = Number(k.populacao) || 0;
      var qtd = Number(k.quantidade) || 0;
      var rRec = k.posicao && k.posicao.receita;
      var p = rRec ? rRec.percentil : null;
      var temDado = p !== null && p !== undefined && isFinite(p);

      if (elVeredito) {
        // Mesma frase do municipio, com a quantidade de municipios porque aqui
        // ha mais de um. Abaixo de 50% entra o "apenas" (ver script_mun_folheto).
        var n = Math.round(p);
        elVeredito.innerHTML = qtd === 0
          ? 'Nenhum município com dados de receita neste filtro.'
          : 'São <span class="fx-hero-pop">' + fmtInt.format(pop) + '</span> habitantes em ' +
            fmtInt.format(qtd) + (qtd === 1 ? ' município' : ' municípios') +
            (temDado
              ? ' e possuem a receita per capita maior que ' + (n < 50 ? 'apenas ' : '') +
                '<strong style="color:' + corPercentil(p) + '">' + n + '%</strong> dos municípios do país.'
              : '.');
      }

      if (elMarcador) {
        elMarcador.style.left = (temDado ? Math.min(Math.max(p, 0), 100) : 0) + '%';
        elMarcador.style.display = temDado ? '' : 'none';
      }
      var ativo = temDado ? Math.min(Math.floor(p / 20) + 1, 5) : 0;
      quintisRegua.forEach(function (q) {
        q.classList.toggle('is-ativo', Number(q.getAttribute('data-q')) === ativo);
      });

      preencherLinhaTotal(k, temDado ? p : null);

      if (elPosicao) {
        // Sem filtro o conjunto e o pais inteiro: 1º em populacao por
        // definicao, comparacao sem sentido. Convida a recortar.
        var semFiltro = k.quantidade_pais && qtd >= k.quantidade_pais;
        elPosicao.innerHTML = semFiltro
          ? 'Escolha um recorte nos filtros acima para ver o lugar que o conjunto ocuparia entre os ' +
            'municípios do país, em porte populacional e em receita corrente per capita.'
          : frasePosicaoConjunto(k.posicao);
      }
    } catch (error) {
      console.error('[agregado-folheto] falha ao montar o hero', { kpis: k, error: error });
    }
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
