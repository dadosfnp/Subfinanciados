/* ============================================================================
 * script_mun_folheto.js — página de preview do detalhe do município
 * ----------------------------------------------------------------------------
 * Autônomo de propósito. O script_mun.js está acoplado aos IDs do layout
 * antigo (kpi-card, cartesian-plane, timeline-ruler, chart-category-select) e
 * lançaria erros nesta página, que não tem nenhum deles.
 *
 * Responsabilidades:
 *   1. Estado único (base / modo de valor / estatística) e os 3 toggles
 *   2. Tabela de receitas — cor das barras e árvore expansível
 *   3. Hero — veredito, régua de quintis e ranking
 *   4. Donut de composição com drill-down
 *   5. Slopegraphs de trajetória 2000 → 2025
 * ========================================================================== */
(function () {
  'use strict';

  // ─── Paleta ───────────────────────────────────────────────────────────────
  // Espelha FNP_Q1..Q5 (folheto-ifem/python/core/tokens.py). `txt` é a variante
  // escurecida para texto — ver comentário no topo de style_mun_folheto.css.
  var QUINTIS = [
    { bar: '#A81C21', txt: '#A81C21' }, // 1 — supera até 20%
    { bar: '#E47326', txt: '#B0530E' }, // 2 — até 40%
    { bar: '#F4D01D', txt: '#8A6A00' }, // 3 — até 60%
    { bar: '#6AC074', txt: '#2E7D45' }, // 4 — até 80%
    { bar: '#1C9148', txt: '#167A3C' }  // 5 — acima de 80%
  ];
  var SEM_DADO = { bar: '#B9BFC7', txt: '#6B7280' };

  var AZUL_ESCURO = '#122747';
  var AZUL_MEDIO = '#3D6FA8';

  /**
   * Converte um percentil (0–100) no par de cores do quintil correspondente.
   * Faixas idênticas às de `cor_por_percentil` no folheto: <=20, <=40, <=60,
   * <=80, resto. Fora de faixa ou sem valor cai no cinza de "sem dado".
   */
  function corPorPercentil(pct) {
    if (pct === null || pct === undefined || isNaN(pct) || pct < 0) return SEM_DADO;
    if (pct <= 20) return QUINTIS[0];
    if (pct <= 40) return QUINTIS[1];
    if (pct <= 60) return QUINTIS[2];
    if (pct <= 80) return QUINTIS[3];
    return QUINTIS[4];
  }

  // ─── Formatação ───────────────────────────────────────────────────────────
  var fmtInt = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });
  var fmt1 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });

  /** R$ com abreviação de milhar/milhão, como `_reais` do folheto. */
  function reais(v) {
    if (v === null || v === undefined || isNaN(v)) return '—';
    var abs = Math.abs(v);
    if (abs >= 1e9) return 'R$ ' + fmt1.format(v / 1e9) + ' bi';
    if (abs >= 1e6) return 'R$ ' + fmt1.format(v / 1e6) + ' mi';
    return 'R$ ' + fmtInt.format(v);
  }

  // ─── Dados vindos do template ─────────────────────────────────────────────
  /**
   * Lê um <script type="application/json"> por id.
   *
   * Tolera dupla codificação: a view entrega `chart_data_json` já serializado
   * com json.dumps() e o filtro |json_script serializa de novo, então o
   * primeiro parse devolve uma string em vez do objeto. Parseia de novo
   * nesse caso em vez de exigir mudança na view, que é compartilhada com a
   * página pública.
   */
  function lerJSON(id) {
    var el = document.getElementById(id);
    if (!el) return null;
    try {
      var valor = JSON.parse(el.textContent);
      if (typeof valor === 'string') valor = JSON.parse(valor);
      return valor;
    } catch (erro) {
      console.error('[folheto] JSON inválido em #' + id, erro);
      return null;
    }
  }

  var DADOS = lerJSON('fx-data');
  var COMPOSICAO = lerJSON('fx-chart-data') || {};

  if (!DADOS) {
    console.error('[folheto] #fx-data ausente — a página não pode ser montada.');
    return;
  }

  // ─── Estado ───────────────────────────────────────────────────────────────
  var estado = { base: 'nacional', modo: 'pc', est: 'media' };

  var ROTULO_BASE = {
    nacional: { escopo: 'dos municípios do país', posicao: 'Posição no Brasil', curto: 'Brasil' },
    estadual: { escopo: 'dos municípios do estado', posicao: 'Posição em ' + (DADOS.uf || '').toUpperCase(), curto: (DADOS.uf || '').toUpperCase() },
    faixa: { escopo: 'dos municípios do mesmo porte', posicao: 'Posição no porte', curto: 'mesmo porte' }
  };

  // ==========================================================================
  // 1. TABELA DE RECEITAS
  // ==========================================================================
  var linhas = Array.prototype.slice.call(document.querySelectorAll('.fx-row'));

  /**
   * Repinta uma linha conforme a base ativa: barra, número do percentil e
   * valor em R$ compartilham a mesma cor, então basta escrever duas custom
   * properties no elemento e deixar o CSS distribuir.
   */
  function pintarLinha(linha) {
    var bruto = linha.getAttribute('data-pct-' + estado.base);
    var pct = bruto === null || bruto === '' ? null : parseFloat(String(bruto).replace(',', '.'));
    var temDado = pct !== null && !isNaN(pct) && pct >= 0;
    var cor = corPorPercentil(temDado ? pct : null);

    linha.style.setProperty('--fx-cor', cor.bar);
    linha.style.setProperty('--fx-cor-txt', cor.txt);
    linha.setAttribute('data-sem-dado', temDado ? '0' : '1');

    var elPct = linha.querySelector('.fx-pct');
    var elBarra = linha.querySelector('.fx-bar-fill');

    if (elPct) elPct.textContent = temDado ? Math.round(pct) + '%' : '—';
    if (elBarra) elBarra.style.width = temDado ? Math.max(pct, 0) + '%' : '0%';
  }

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

    linha.addEventListener('click', function () {
      alternarLinha(linha);
    });

    // Teclado: a linha é role="button", então Enter e Espaço precisam agir
    // como clique — sem isso a árvore fica inacessível fora do mouse.
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
  var elRankLabel = document.getElementById('fx-rank-label');
  var elRankValor = document.getElementById('fx-rank-valor');
  var elRankSub = document.getElementById('fx-rank-sub');
  var elCrescSub = document.getElementById('fx-cresc-sub');
  var quintisRegua = Array.prototype.slice.call(document.querySelectorAll('.fx-regua-q'));

  /**
   * Percentil geral do município na base ativa.
   *
   * O model só expõe o percentil nacional (percentil24_n). Para estado e porte
   * derivamos da posição no ranking pela regra oficial do IFEM
   * (folheto-ifem/python/core/paleta_ranking.py):
   *     percentil = (total - posição) / total * 100
   * Posição 1 = maior receita por habitante, logo percentil ~100.
   */
  function percentilGeral() {
    if (estado.base === 'nacional' && DADOS.percentil_nacional !== null && DADOS.percentil_nacional !== undefined) {
      return DADOS.percentil_nacional;
    }
    var r = (DADOS.rank || {})[estado.base];
    if (!r || !r.total || !r.pos) return null;
    return (r.total - r.pos) / r.total * 100;
  }

  function atualizarHero() {
    var pct = percentilGeral();
    var temDado = pct !== null && !isNaN(pct);
    var cor = corPorPercentil(temDado ? pct : null);
    var rotulos = ROTULO_BASE[estado.base];

    // Valor em destaque acompanha o toggle de per capita / total.
    if (elVeredValor) {
      elVeredValor.textContent = estado.modo === 'pc'
        ? reais(DADOS.receita.pc)
        : reais(DADOS.receita.total);
    }

    if (elVeredito) {
      var unidade = estado.modo === 'pc' ? 'por habitante em receita corrente' : 'de receita corrente';
      if (temDado) {
        var arredondado = Math.round(pct);
        // "apenas" só entra abaixo da mediana: acima dela a palavra soaria
        // como ressalva onde o dado é, na verdade, bom.
        var adverbio = arredondado > 50 ? '' : 'apenas ';
        elVeredito.innerHTML = unidade + '. Supera <strong style="color:' + cor.bar + '">' +
          adverbio + arredondado + '%</strong> ' + rotulos.escopo + '.';
      } else {
        elVeredito.innerHTML = unidade + '. <span style="opacity:.7">Sem dado comparativo para esta base.</span>';
      }
    }

    if (elMarcador) {
      elMarcador.style.left = (temDado ? Math.min(Math.max(pct, 0), 100) : 0) + '%';
      elMarcador.style.display = temDado ? '' : 'none';
    }

    // Acende só o quintil em que o município caiu; os outros ficam esmaecidos.
    var quintilAtivo = temDado ? Math.min(Math.floor(pct / 20) + 1, 5) : 0;
    quintisRegua.forEach(function (q) {
      q.classList.toggle('is-ativo', Number(q.getAttribute('data-q')) === quintilAtivo);
    });

    var r = (DADOS.rank || {})[estado.base];
    if (elRankLabel) elRankLabel.textContent = rotulos.posicao;
    if (elRankValor) {
      elRankValor.textContent = r && r.pos && r.total
        ? fmtInt.format(r.pos) + 'º'
        : '—';
    }
    if (elRankSub) {
      elRankSub.textContent = r && r.total
        ? 'de ' + fmtInt.format(r.total) + ' municípios'
        : 'sem ranking disponível';
    }

    // Comparação do crescimento contra o grupo da base ativa.
    if (elCrescSub) {
      var c = DADOS.crescimento || {};
      var mediaGrupo = { nacional: c.receita_nac, estadual: c.receita_est, faixa: c.receita_faixa }[estado.base];
      if (c.receita_mun !== null && mediaGrupo !== null && mediaGrupo !== undefined && !isNaN(mediaGrupo)) {
        var diferenca = c.receita_mun - mediaGrupo;
        elCrescSub.textContent = (diferenca >= 0 ? 'acima' : 'abaixo') + ' da média ' +
          rotulos.curto + ' (' + fmt1.format(mediaGrupo) + '%)';
        elCrescSub.className = 'fx-stat-sub ' + (diferenca >= 0 ? 'is-positivo' : 'is-negativo');
      } else {
        elCrescSub.textContent = 'sem comparativo';
        elCrescSub.className = 'fx-stat-sub';
      }
    }
  }

  // ==========================================================================
  // 3. DONUT DE COMPOSIÇÃO
  // ==========================================================================
  var TITULO_CHAVE = {
    main_categories: 'Receita corrente',
    imposto_taxas_contribuicoes: 'Impostos, Taxas e Contrib.',
    imposto: 'Impostos',
    taxas: 'Taxas',
    contribuicoes_melhoria: 'Contribuições de Melhoria',
    contribuicoes: 'Contribuições',
    transferencias_correntes: 'Transferências Correntes',
    transferencias_uniao: 'Transferências da União',
    transferencias_estado: 'Transferências dos Estados',
    outras_receitas: 'Outras Receitas'
  };

  // Qual fatia abre qual nível. Só as combinações que existem em chart_data —
  // fatia sem entrada aqui simplesmente não é clicável.
  var DRILL = {
    main_categories: {
      'Impostos, Taxas e Contribuições de Melhoria': 'imposto_taxas_contribuicoes',
      'Contribuições': 'contribuicoes',
      'Transf. Correntes': 'transferencias_correntes',
      'Outras': 'outras_receitas'
    },
    imposto_taxas_contribuicoes: {
      'Impostos': 'imposto',
      'Taxas': 'taxas',
      'Contrib. Melhoria': 'contribuicoes_melhoria'
    },
    transferencias_correntes: {
      'União': 'transferencias_uniao',
      'Estados': 'transferencias_estado'
    }
  };

  // Paleta do donut: azuis do folheto em degradê, com o amarelo da marca para
  // a última fatia. Categórica de verdade — a escala de quintis é semântica
  // (bom/ruim) e não pode ser reaproveitada onde a cor só separa rubricas.
  var CORES_DONUT = ['#1B3A6B', '#3D6FA8', '#6E9BC9', '#A8C3DE', '#C99A1F', '#E4C05F', '#8FA8BF', '#5C7A99'];

  var canvasDonut = document.getElementById('fx-donut');
  var elTrilha = document.getElementById('fx-trilha');
  var elLegenda = document.getElementById('fx-donut-legenda');
  var elTotal = document.getElementById('fx-donut-total');
  var elTotalLabel = document.getElementById('fx-donut-label');
  var donut = null;
  var caminho = ['main_categories']; // pilha de navegação do drill-down

  function temDados(chave) {
    var d = COMPOSICAO[chave];
    return !!(d && Array.isArray(d.labels) && d.labels.length);
  }

  function renderTrilha() {
    if (!elTrilha) return;
    elTrilha.innerHTML = '';

    caminho.forEach(function (chave, indice) {
      if (indice > 0) {
        var sep = document.createElement('span');
        sep.className = 'fx-trilha-sep';
        sep.textContent = '›';
        elTrilha.appendChild(sep);
      }

      var ultimo = indice === caminho.length - 1;
      if (ultimo) {
        var atual = document.createElement('span');
        atual.className = 'fx-trilha-atual';
        atual.textContent = TITULO_CHAVE[chave] || chave;
        elTrilha.appendChild(atual);
      } else {
        var botao = document.createElement('button');
        botao.type = 'button';
        botao.textContent = TITULO_CHAVE[chave] || chave;
        botao.addEventListener('click', function () {
          caminho = caminho.slice(0, indice + 1);
          renderDonut();
        });
        elTrilha.appendChild(botao);
      }
    });
  }

  function entrarEm(chaveFilha) {
    if (!temDados(chaveFilha)) return;
    caminho.push(chaveFilha);
    renderDonut();
  }

  function renderLegenda(labels, valores, total, chaveAtual) {
    if (!elLegenda) return;
    elLegenda.innerHTML = '';

    labels.forEach(function (label, i) {
      var filha = (DRILL[chaveAtual] || {})[label];
      var clicavel = !!(filha && temDados(filha));

      var item = document.createElement(clicavel ? 'button' : 'div');
      item.className = 'fx-legenda-item' + (clicavel ? ' is-clicavel' : '');
      if (clicavel) {
        item.type = 'button';
        item.addEventListener('click', function () { entrarEm(filha); });
      }

      var cor = document.createElement('span');
      cor.className = 'fx-legenda-cor';
      cor.style.background = CORES_DONUT[i % CORES_DONUT.length];

      var nome = document.createElement('span');
      nome.className = 'fx-legenda-nome';
      nome.textContent = label;

      var valor = document.createElement('span');
      valor.className = 'fx-legenda-valor';
      valor.textContent = reais(valores[i]);

      var pct = document.createElement('span');
      pct.className = 'fx-legenda-pct';
      pct.textContent = total > 0 ? fmt1.format(valores[i] / total * 100) + '%' : '—';

      item.appendChild(cor);
      item.appendChild(nome);
      item.appendChild(valor);
      item.appendChild(pct);
      elLegenda.appendChild(item);
    });
  }

  function renderDonut() {
    if (!canvasDonut || !window.Chart) return;

    var chaveAtual = caminho[caminho.length - 1];
    var dados = COMPOSICAO[chaveAtual] || { labels: [], values: [] };
    var labels = dados.labels || [];
    var valores = dados.values || [];
    var total = valores.reduce(function (a, b) { return a + (b || 0); }, 0);

    renderTrilha();
    renderLegenda(labels, valores, total, chaveAtual);

    if (elTotal) elTotal.textContent = reais(total);
    if (elTotalLabel) elTotalLabel.textContent = TITULO_CHAVE[chaveAtual] || 'Total';

    if (donut) donut.destroy();

    if (!labels.length) {
      if (elTotal) elTotal.textContent = '—';
      return;
    }

    donut = new window.Chart(canvasDonut.getContext('2d'), {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: valores,
          backgroundColor: labels.map(function (_, i) { return CORES_DONUT[i % CORES_DONUT.length]; }),
          borderColor: '#ffffff',
          borderWidth: 2,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '62%',
        plugins: {
          legend: { display: false }, // a lista abaixo do gráfico já é a legenda
          tooltip: {
            backgroundColor: AZUL_ESCURO,
            padding: 10,
            titleFont: { size: 12 },
            bodyFont: { size: 12 },
            callbacks: {
              label: function (ctx) {
                var v = ctx.raw || 0;
                var p = total > 0 ? fmt1.format(v / total * 100) + '%' : '—';
                return ' ' + reais(v) + ' · ' + p;
              }
            }
          }
        },
        onClick: function (_evento, elementos) {
          if (!elementos.length) return;
          var label = labels[elementos[0].index];
          var filha = (DRILL[chaveAtual] || {})[label];
          if (filha) entrarEm(filha);
        },
        onHover: function (evento, elementos) {
          if (!evento.native) return;
          var label = elementos.length ? labels[elementos[0].index] : null;
          var filha = label ? (DRILL[chaveAtual] || {})[label] : null;
          evento.native.target.style.cursor = filha && temDados(filha) ? 'pointer' : 'default';
        }
      }
    });
  }

  // ==========================================================================
  // 4. SLOPEGRAPHS — trajetória 2000 → 2025
  // ==========================================================================
  /*
   * Por que índice base 100 e não os valores em R$:
   * o contexto da view entrega o CRESCIMENTO percentual do município e a média
   * de crescimento do grupo (media_nacional_rc_pc = 316,73% etc.), mas não a
   * média nacional em R$ de 2000 e de 2025. Normalizar as duas séries em 100
   * responde exatamente a pergunta da seção — quem cresceu mais — sem
   * inventar valores nem exigir query nova. O R$ real do município aparece
   * na nota abaixo do gráfico.
   */
  function montarSlope(canvasId, notaId, deltaMun, deltaGrupo, unidade) {
    var canvas = document.getElementById(canvasId);
    if (!canvas || !window.Chart) return null;
    if (deltaMun === null || deltaMun === undefined || isNaN(deltaMun)) return null;

    var temGrupo = deltaGrupo !== null && deltaGrupo !== undefined && !isNaN(deltaGrupo);
    var finalMun = 100 * (1 + deltaMun / 100);
    var finalGrupo = temGrupo ? 100 * (1 + deltaGrupo / 100) : null;
    var acima = temGrupo ? deltaMun >= deltaGrupo : true;

    var datasets = [{
      label: DADOS.nome,
      data: [100, finalMun],
      borderColor: acima ? '#1C9148' : '#A81C21',
      backgroundColor: acima ? '#1C9148' : '#A81C21',
      borderWidth: 3,
      pointRadius: 5,
      pointHoverRadius: 7,
      tension: 0
    }];

    if (temGrupo) {
      datasets.push({
        label: 'Média ' + ROTULO_BASE[estado.base].curto,
        data: [100, finalGrupo],
        borderColor: AZUL_MEDIO,
        backgroundColor: AZUL_MEDIO,
        borderWidth: 2,
        borderDash: [5, 4],
        pointRadius: 4,
        pointHoverRadius: 6,
        tension: 0
      });
    }

    var nota = document.getElementById(notaId);
    if (nota) {
      if (temGrupo) {
        var dif = deltaMun - deltaGrupo;
        nota.innerHTML = '<strong>' + DADOS.nome + '</strong> cresceu ' + fmt1.format(deltaMun) +
          '% em ' + unidade + ', ' + (dif >= 0 ? 'acima' : 'abaixo') + ' da média ' +
          ROTULO_BASE[estado.base].curto + ' (' + fmt1.format(deltaGrupo) + '%) — uma diferença de ' +
          fmt1.format(Math.abs(dif)) + ' pontos percentuais.';
      } else {
        nota.innerHTML = '<strong>' + DADOS.nome + '</strong> cresceu ' + fmt1.format(deltaMun) +
          '% em ' + unidade + '. Sem média comparável para esta base.';
      }
    }

    return new window.Chart(canvas.getContext('2d'), {
      type: 'line',
      data: { labels: ['2000', '2025'], datasets: datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        layout: { padding: { right: 12, top: 8 } },
        plugins: {
          legend: {
            display: true,
            position: 'bottom',
            labels: { boxWidth: 12, boxHeight: 2, font: { size: 11 }, color: '#6B6B6B' }
          },
          tooltip: {
            backgroundColor: AZUL_ESCURO,
            padding: 10,
            callbacks: {
              label: function (ctx) {
                return ' ' + ctx.dataset.label + ': índice ' + fmtInt.format(ctx.raw);
              }
            }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { color: '#6B6B6B', font: { size: 12, weight: '600' } }
          },
          y: {
            grid: { color: '#EFEAE0' },
            border: { display: false },
            ticks: { color: '#9AA3AE', font: { size: 10 }, maxTicksLimit: 5 }
          }
        }
      }
    });
  }

  var slopeReceita = null;
  var slopePop = null;

  function renderSlopes() {
    var c = DADOS.crescimento || {};
    var mediaReceita = { nacional: c.receita_nac, estadual: c.receita_est, faixa: c.receita_faixa }[estado.base];
    var mediaPop = { nacional: c.pop_nac, estadual: c.pop_est, faixa: c.pop_faixa }[estado.base];

    if (slopeReceita) slopeReceita.destroy();
    if (slopePop) slopePop.destroy();

    slopeReceita = montarSlope('fx-slope-receita', 'fx-nota-receita', c.receita_mun, mediaReceita, 'receita por habitante');
    slopePop = montarSlope('fx-slope-pop', 'fx-nota-pop', c.pop_mun, mediaPop, 'população');
  }

  // ==========================================================================
  // 5. TOGGLES
  // ==========================================================================
  var elHeadUnidade = document.getElementById('fx-head-unidade');
  var elHeadMediasRot = document.getElementById('fx-head-medias-rot');
  var elHeadMediasUnidade = document.getElementById('fx-head-medias-unidade');

  /** Marca o botão ativo dentro de um grupo e devolve o valor escolhido. */
  function ativar(container, botao) {
    Array.prototype.forEach.call(container.querySelectorAll('button'), function (b) {
      b.classList.toggle('active', b === botao);
    });
  }

  function aplicarModoValor() {
    var perCapita = estado.modo === 'pc';

    document.querySelectorAll('.valor-per-capita').forEach(function (el) {
      el.classList.toggle('hidden', !perCapita);
    });
    document.querySelectorAll('.valor-absoluto').forEach(function (el) {
      el.classList.toggle('hidden', perCapita);
    });

    // Em valores totais as colunas de média saem: comparar a média per capita
    // dos municípios com o valor absoluto deste não diria nada.
    document.querySelectorAll('.fx-media').forEach(function (el) {
      el.style.display = perCapita ? '' : 'none';
    });

    if (elHeadUnidade) elHeadUnidade.textContent = perCapita ? 'R$ por habitante' : 'R$ total';
    if (elHeadMediasUnidade) elHeadMediasUnidade.textContent = 'R$ por habitante';
  }

  function aplicarEstatistica() {
    var media = estado.est === 'media';

    document.querySelectorAll('.estatistica-media').forEach(function (el) {
      el.classList.toggle('invisible-by-est', !media);
    });
    document.querySelectorAll('.estatistica-mediana').forEach(function (el) {
      el.classList.toggle('invisible-by-est', media);
    });

    if (elHeadMediasRot) elHeadMediasRot.textContent = media ? 'Média' : 'Mediana';

    // O modo de valor decide se as colunas aparecem; reaplicar evita que a
    // troca de estatística ressuscite colunas escondidas por "Totais".
    aplicarModoValor();
  }

  function ligarToggle(id, chave, aoMudar) {
    var container = document.getElementById(id);
    if (!container) return;

    container.addEventListener('click', function (evento) {
      var botao = evento.target.closest('button');
      if (!botao || botao.classList.contains('active')) return;

      estado[chave] = botao.getAttribute('data-base') ||
                      botao.getAttribute('data-mode') ||
                      botao.getAttribute('data-est');
      ativar(container, botao);
      aoMudar();
    });
  }

  ligarToggle('fx-base-toggle', 'base', function () {
    pintarTabela();
    atualizarHero();
    renderSlopes();
  });

  ligarToggle('fx-valor-toggle', 'modo', function () {
    aplicarModoValor();
    atualizarHero();
  });

  ligarToggle('fx-est-toggle', 'est', aplicarEstatistica);

  // ==========================================================================
  // 6. BOOT
  // ==========================================================================
  /*
   * Abre as rubricas de nível 0 já na carga.
   *
   * Duas razões: o folheto impresso mostra os níveis 1 e 2 juntos, sem exigir
   * interação; e com tudo fechado a tabela fica com 4 linhas ao lado de um
   * card de composição duas vezes mais alto, deixando um vazio grande na
   * coluna da esquerda. Os níveis mais profundos seguem fechados.
   */
  function abrirPrimeiroNivel() {
    document.querySelectorAll('.fx-row.fx-clickable[data-level="0"]').forEach(alternarLinha);
  }

  pintarTabela();
  atualizarHero();
  aplicarEstatistica();
  abrirPrimeiroNivel();
  renderDonut();
  renderSlopes();
})();
