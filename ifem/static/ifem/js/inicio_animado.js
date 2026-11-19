/* ============================================================================
 * inicio_animado.js: landing animada (/preview/inicio-animado/)
 * ----------------------------------------------------------------------------
 * Uma animacao em canvas guiada pelo scroll. Cada municipio e uma forma que
 * passa por treze ESTADOS, um por cartao de texto:
 *
 *   0 brasil    contorno do municipio, todos na mesma cor
 *   1 grandes   o mesmo mapa; em destaque so os com mais de 80 mil habitantes
 *   2 maioria   fatia da barra "grandes" ou "demais", altura = populacao 2025
 *   3 mapa      contorno do municipio; verde se declarou receita em 2025
 *   4 grade     um quadrado por municipio, do menor para o maior receita/hab.
 *   5 quintis   a mesma grade aberta em cinco blocos (so desce ou sobe)
 *   6 2000      fatia da barra do seu quintil de 2000, altura = populacao
 *   7 2025      fatia da barra de 2025; a de 2000 fica ao lado, hachurada
 *   8 porte     quadradinho no grupo do seu porte; graficos de crescimento
 *   9 transf.   grade pela parcela da receita que vem de transferencias
 *  10 regras    o mapa de volta; as cidades com mais de 80 mil em azul
 *  11 oposta    o mesmo mapa; as cidades com mais de 80 mil na cor do quintil
 *  12 fpm       fatia da barra de 2025 ao lado da simulacao com +R$ 50 bi
 *
 * A forma de cada municipio e um anel de n pontos. O mesmo anel e desenhado
 * como poligono (mapa), quadrado ou retangulo (grade e barras): como os tres
 * tem os mesmos n pontos, a transicao e so interpolar ponto a ponto. Cada
 * municipio comeca a se mover com um pequeno atraso proprio, e o scroll e
 * suavizado, para o movimento nunca dar tranco.
 *
 * Dados: JSON #animacao-dados (ifem/apresentacao_dados.municipios_animacao) e
 * a malha static/ifem/dados/malha_municipios.json (export_malha_inicio.py).
 * ========================================================================== */
(function () {
  'use strict';

  var secao = document.querySelector('.an-scrolly');
  if (!secao) return;
  var canvas = secao.querySelector('.an-canvas');
  var ctx = canvas.getContext('2d');
  var passos = Array.prototype.slice.call(secao.querySelectorAll('.an-passo'));

  var DADOS;
  try {
    DADOS = JSON.parse(document.getElementById('animacao-dados').textContent);
    if (typeof DADOS === 'string') DADOS = JSON.parse(DADOS); // ver tasks/lessons.md
  } catch (erro) {
    console.error('[inicio_animado] JSON #animacao-dados invalido', erro);
    return;
  }

  // --------------------------------------------------------------------------
  // Constantes
  // --------------------------------------------------------------------------
  var COR_Q = [null, [168, 28, 33], [228, 115, 38], [244, 208, 29], [106, 192, 116], [28, 145, 72]];
  var COR_Q_TXT = [null, '#A81C21', '#B5520F', '#8A6D00', '#2F7D3A', '#157A3A']; // texto, >= 4.5:1
  var VERDE = [28, 145, 72];
  var CINZA = [197, 202, 209];
  var AZUL = [27, 58, 107];          // transferencias (mesma cor da rosca da apresentacao)
  var AMARELO = [255, 199, 44];      // arrecadacao propria
  var NEUTRO = [142, 154, 171];      // mapa de abertura: todos os municipios
  var AZUL_GRANDE = [27, 58, 107];   // mais de 80 mil habitantes
  var CLARO = [220, 223, 228];       // os demais, ao lado das grandes
  var PAPEL = '#F8F6F1';
  var TINTA = '#1E2530';
  var CINZA_TXT = '#5F6670';
  var FONTE = '"Inter", system-ui, -apple-system, sans-serif';
  var N_ESTADOS = 13;
  var ATRASO = 0.4;           // fatia do tempo de transicao usada para escalonar a partida
  var SUAVIZACAO = 0.14;      // segundos: quanto o desenho "persegue" o scroll
  var REDUZIR = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var fmt0 = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });
  var fmt1 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });

  function css(c) { return 'rgb(' + (c[0] | 0) + ',' + (c[1] | 0) + ',' + (c[2] | 0) + ')'; }

  // --------------------------------------------------------------------------
  // Municipios e agrupamentos
  // --------------------------------------------------------------------------
  var MUN = DADOS.municipios.map(function (l) {
    return { cod: l[0], lon: l[1], lat: l[2], rc: l[3], q25: l[4], p25: l[5], q00: l[6], p00: l[7], tr: l[8] };
  });
  var N = MUN.length;
  var indices = MUN.map(function (m, i) { return i; });

  // Ordem da grade: quintil e, dentro dele, receita por habitante.
  var GRADE = indices
    .filter(function (i) { return MUN[i].q25 > 0; })
    .sort(function (a, b) { return (MUN[a].q25 - MUN[b].q25) || (MUN[a].rc - MUN[b].rc); });
  var posGrade = new Int32Array(N).fill(-1);
  GRADE.forEach(function (i, j) { posGrade[i] = j; });
  var NG = GRADE.length;
  var ordemGrade = function (a, b) {
    var pa = posGrade[a] < 0 ? 1e9 : posGrade[a];
    var pb = posGrade[b] < 0 ? 1e9 : posGrade[b];
    return pa - pb;
  };

  var porQ25 = [[], [], [], [], [], []];
  var porQ00 = [[], [], [], [], [], []];
  var soma25 = [0, 0, 0, 0, 0, 0];
  var soma00 = [0, 0, 0, 0, 0, 0];
  MUN.forEach(function (m, i) {
    if (m.q25) { porQ25[m.q25].push(i); soma25[m.q25] += m.p25; }
    if (m.q00) { porQ00[m.q00].push(i); soma00[m.q00] += m.p00; }
  });
  for (var q = 1; q <= 5; q++) { porQ25[q].sort(ordemGrade); porQ00[q].sort(ordemGrade); }

  // Abertura: cidades com mais de 80 mil habitantes x demais, da maior para a
  // menor (as maiores ficam na base da barra).
  var GR = DADOS.grandes || { limite: 80000, n: 0, pct_populacao: 0, populacao: 0, populacao_total: 0 };
  var grande = MUN.map(function (m) { return m.p25 > GR.limite; });
  var porPop = function (a, b) { return MUN[b].p25 - MUN[a].p25; };
  var GRANDES = indices.filter(function (i) { return grande[i]; }).sort(porPop);
  var DEMAIS = indices.filter(function (i) { return !grande[i]; }).sort(porPop);
  var popGrandes = 0, popDemais = 0;
  GRANDES.forEach(function (i) { popGrandes += MUN[i].p25; });
  DEMAIS.forEach(function (i) { popDemais += MUN[i].p25; });

  // Porte (populacao de 2025), com os mesmos limites do servidor.
  var PORTE = DADOS.porte || { limites: [], rotulos: [], populacao: [], receita: [] };
  var NF = PORTE.limites.length;
  var faixa = new Int8Array(N).fill(-1);
  var porFaixa = PORTE.limites.map(function () { return []; });
  GRADE.forEach(function (i) {
    var p = MUN[i].p25;
    for (var f = 0; f < NF; f++) {
      if (p >= PORTE.limites[f][0] && p < PORTE.limites[f][1]) { faixa[i] = f; porFaixa[f].push(i); break; }
    }
  });

  // Transferencias: da maior para a menor dependencia.
  var TRANSF = GRADE.filter(function (i) { return MUN[i].tr !== null && MUN[i].tr !== undefined; })
    .sort(function (a, b) { return MUN[b].tr - MUN[a].tr; });
  var posTransf = new Int32Array(N).fill(-1);
  TRANSF.forEach(function (i, j) { posTransf[i] = j; });
  var NT = TRANSF.length;
  var nMaioria = TRANSF.filter(function (i) { return MUN[i].tr > 0.5; }).length;

  // Simulacao do FPM: numeros fixos da FNP (milhoes). As fatias de 2025 sao
  // reescaladas para a barra bater com o numero da simulacao.
  var FPM = DADOS.fpm || { series: [{ valores: [0, 0, 0, 0, 0] }, { valores: [0, 0, 0, 0, 0] }] };
  var fpmAntes = [0].concat(FPM.series[0].valores);
  var fpmDepois = [0].concat(FPM.series[1].valores);
  var fatorFpm = [0, 1, 2, 3, 4, 5].map(function (q) { return q && soma25[q] ? fpmAntes[q] * 1e6 / soma25[q] : 0; });

  // Sorteio com semente: o mesmo "acaso" a cada visita.
  var semente = 2025;
  function sorteio() {
    semente = (semente + 0x6D2B79F5) | 0;
    var t = Math.imul(semente ^ (semente >>> 15), 1 | semente);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }

  // Atraso de partida de cada municipio, por transicao (estado k -> k+1).
  var ATRASOS = [];
  (function () {
    for (var k = 0; k < N_ESTADOS - 1; k++) ATRASOS.push(new Float32Array(N));
    for (var i = 0; i < N; i++) {
      var r = sorteio();
      var frac = posGrade[i] >= 0 ? posGrade[i] / Math.max(NG - 1, 1) : r;
      var fracT = posTransf[i] >= 0 ? posTransf[i] / Math.max(NT - 1, 1) : r;
      var q25 = MUN[i].q25 || 3;
      ATRASOS[0][i] = ATRASO * r;                                  // as grandes acendem espalhadas pelo mapa
      ATRASOS[1][i] = ATRASO * (0.5 * r + (grande[i] ? 0 : 0.5));  // as grandes saem do mapa primeiro
      ATRASOS[2][i] = ATRASO * r;                                  // as fatias voltam ao mapa
      ATRASOS[3][i] = ATRASO * (0.45 * r + 0.55 * frac);          // a grade se enche de cima para baixo
      ATRASOS[4][i] = ATRASO * 0.25 * r;                           // os blocos se abrem juntos
      ATRASOS[5][i] = ATRASO * (0.8 * frac + 0.2 * r);             // os quintis descem para as barras na ordem
      ATRASOS[6][i] = ATRASO * (0.5 * r + 0.5 * (q25 - 1) / 4);
      ATRASOS[7][i] = ATRASO * (0.6 * r + 0.4 * Math.max(faixa[i], 0) / Math.max(NF - 1, 1));
      ATRASOS[8][i] = ATRASO * (0.7 * fracT + 0.3 * r);
      ATRASOS[9][i] = ATRASO * r;                                  // a grade se desfaz de volta no mapa
      ATRASOS[10][i] = ATRASO * r;                                 // as grandes trocam de cor espalhadas pelo mapa
      ATRASOS[11][i] = ATRASO * (0.5 * r + 0.5 * (q25 - 1) / 4);
    }
  })();

  // --------------------------------------------------------------------------
  // Formas: anel do poligono (coordenadas locais) e anel do quadrado unitario
  // --------------------------------------------------------------------------
  var LAT_C = -14;
  var KX = Math.cos(LAT_C * Math.PI / 180);
  var poliX = new Array(N), poliY = new Array(N), quadX = new Array(N), quadY = new Array(N);
  var geoX = new Float32Array(N), geoY = new Float32Array(N);
  var GEO = null; // limites do pais em unidades geograficas projetadas

  /** Garante pelo menos `min` pontos, partindo a aresta mais longa ao meio. */
  function adensa(xs, ys, min) {
    while (xs.length < min) {
      var maior = 0, k = 0;
      for (var j = 0; j < xs.length; j++) {
        var j2 = (j + 1) % xs.length;
        var d = Math.pow(xs[j2] - xs[j], 2) + Math.pow(ys[j2] - ys[j], 2);
        if (d > maior) { maior = d; k = j; }
      }
      var k2 = (k + 1) % xs.length;
      xs.splice(k + 1, 0, (xs[k] + xs[k2]) / 2);
      ys.splice(k + 1, 0, (ys[k] + ys[k2]) / 2);
    }
  }

  /**
   * Quadrado unitario ([-1, 1]) com n pontos, no mesmo sentido e com o mesmo
   * ponto de partida do anel do poligono (o ponto mais a direita, indo para
   * baixo na tela). Os quatro cantos caem exatamente em pontos do anel.
   */
  function quadradoUnitario(n) {
    var xs = new Float32Array(n), ys = new Float32Array(n);
    for (var j = 0; j < n; j++) {
      var s = j * 8 / n;
      if (s < 1) { xs[j] = 1; ys[j] = s; }
      else if (s < 3) { xs[j] = 1 - (s - 1); ys[j] = 1; }
      else if (s < 5) { xs[j] = -1; ys[j] = 1 - (s - 3); }
      else if (s < 7) { xs[j] = -1 + (s - 5); ys[j] = -1; }
      else { xs[j] = 1; ys[j] = -1 + (s - 7); }
    }
    [[1, 1, 1], [3, -1, 1], [5, -1, -1], [7, 1, -1]].forEach(function (c) {
      var j = Math.round(c[0] * n / 8) % n;
      xs[j] = c[1]; ys[j] = c[2];
    });
    return [xs, ys];
  }

  function preparaFormas(malha) {
    var escala = malha ? malha.escala : 1;
    var x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    for (var i = 0; i < N; i++) {
      var m = MUN[i];
      var bruto = malha && malha.m[m.cod];
      var xs = [], ys = [], k;
      if (bruto && bruto.length >= 6) {
        var lon = bruto[0], lat = bruto[1];
        for (k = 0; k < bruto.length; k += 2) {
          if (k > 0) { lon += bruto[k]; lat += bruto[k + 1]; }
          xs.push(lon / escala * KX);
          ys.push(-lat / escala);
        }
      }
      var bx0 = Infinity, bx1 = -Infinity, by0 = Infinity, by1 = -Infinity;
      for (k = 0; k < xs.length; k++) {
        bx0 = Math.min(bx0, xs[k]); bx1 = Math.max(bx1, xs[k]);
        by0 = Math.min(by0, ys[k]); by1 = Math.max(by1, ys[k]);
      }
      var cx, cy;
      if (xs.length >= 3 && bx1 > bx0 && by1 > by0) {
        cx = (bx0 + bx1) / 2; cy = (by0 + by1) / 2;
        for (k = 0; k < xs.length; k++) { xs[k] -= cx; ys[k] -= cy; }
        adensa(xs, ys, 8);
        // sentido unico (area com sinal positivo na tela, y para baixo)
        var a = 0;
        for (k = 0; k < xs.length; k++) {
          var k2 = (k + 1) % xs.length;
          a += xs[k] * ys[k2] - xs[k2] * ys[k];
        }
        if (a < 0) { xs.reverse(); ys.reverse(); }
        // comeca no ponto mais a direita
        var ini = 0;
        for (k = 1; k < xs.length; k++) if (xs[k] > xs[ini]) ini = k;
        xs = xs.slice(ini).concat(xs.slice(0, ini));
        ys = ys.slice(ini).concat(ys.slice(0, ini));
        bx0 -= cx; bx1 -= cx; by0 -= cy; by1 -= cy;
      } else {
        // Sem contorno (malha ausente ou municipio minusculo): um quadradinho no ponto da sede.
        cx = (m.lon || -54) * KX; cy = -(m.lat || -14);
        var u = quadradoUnitario(8);
        xs = Array.prototype.map.call(u[0], function (v) { return v * 0.04; });
        ys = Array.prototype.map.call(u[1], function (v) { return v * 0.04; });
        bx0 = by0 = -0.04; bx1 = by1 = 0.04;
      }
      geoX[i] = cx; geoY[i] = cy;
      poliX[i] = Float32Array.from(xs);
      poliY[i] = Float32Array.from(ys);
      var qd = quadradoUnitario(xs.length);
      quadX[i] = qd[0]; quadY[i] = qd[1];
      x0 = Math.min(x0, cx + bx0); x1 = Math.max(x1, cx + bx1);
      y0 = Math.min(y0, cy + by0); y1 = Math.max(y1, cy + by1);
    }
    GEO = { x0: x0, x1: x1, y0: y0, y1: y1 };
  }

  // --------------------------------------------------------------------------
  // Layout e estados
  // --------------------------------------------------------------------------
  var W = 0, H = 0, DPR = 1, MOBILE = false;
  var CAIXA, GRID, BARRAS, GRANDES_L, PORTE_L, TRANSF_L, FPM_L;
  var ESTADOS = [];

  function novoEstado() {
    return {
      cx: new Float32Array(N), cy: new Float32Array(N),
      hw: new Float32Array(N), hh: new Float32Array(N),
      tipo: new Uint8Array(N), // 0 poligono, 1 retangulo
      r: new Float32Array(N), g: new Float32Array(N), b: new Float32Array(N),
      a: new Float32Array(N),
      css: new Array(N)        // cor pronta, para os quadros parados nao montarem string
    };
  }

  function copia(dest, orig, i, alfa) {
    dest.cx[i] = orig.cx[i]; dest.cy[i] = orig.cy[i];
    dest.hw[i] = orig.hw[i]; dest.hh[i] = orig.hh[i]; dest.tipo[i] = orig.tipo[i];
    dest.r[i] = orig.r[i]; dest.g[i] = orig.g[i]; dest.b[i] = orig.b[i]; dest.css[i] = orig.css[i];
    dest.a[i] = alfa;
  }

  function pinta(e, i, cor, alfa) {
    e.r[i] = cor[0]; e.g[i] = cor[1]; e.b[i] = cor[2]; e.css[i] = css(cor); e.a[i] = alfa;
  }

  function retangulo(e, i, cx, cy, hw, hh) {
    e.cx[i] = cx; e.cy[i] = cy; e.hw[i] = hw; e.hh[i] = hh; e.tipo[i] = 1;
  }

  function corGradiente(f) {
    var x = Math.max(0, Math.min(1, f)) * 4;
    var k = Math.min(Math.floor(x), 3);
    var t = x - k, c0 = COR_Q[k + 1], c1 = COR_Q[k + 2];
    return [c0[0] + (c1[0] - c0[0]) * t, c0[1] + (c1[1] - c0[1]) * t, c0[2] + (c1[2] - c0[2]) * t];
  }

  /** Maior celula quadrada que acomoda n itens numa area larg x alt. */
  function encaixa(n, larg, alt) {
    var melhor = { cols: 1, cel: 0 };
    for (var cols = 4; cols <= 400; cols++) {
      var cel = Math.min(larg / cols, alt / Math.ceil(n / cols));
      if (cel > melhor.cel) melhor = { cols: cols, cel: cel };
    }
    return melhor;
  }

  function calculaLayout() {
    W = canvas.clientWidth; H = canvas.clientHeight;
    DPR = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(W * DPR); canvas.height = Math.round(H * DPR);
    MOBILE = window.matchMedia ? window.matchMedia('(max-width: 860px)').matches : W <= 860; // mesmo corte do CSS

    if (MOBILE) {
      CAIXA = { x0: 16, x1: W - 16, y0: H * 0.05, y1: H * 0.52 };
    } else {
      var pad = Math.max(24, Math.min(64, W * 0.04));
      var cartao = Math.min(400, W * 0.32);
      CAIXA = { x0: pad + cartao + 56, x1: W - 40, y0: H * 0.09, y1: H * 0.93 };
    }
    var cw = CAIXA.x1 - CAIXA.x0, ch = CAIXA.y1 - CAIXA.y0;

    // ---- maioria (estado 2): duas barras, grandes e demais ----
    var plotG = {
      x0: CAIXA.x0, x1: CAIXA.x1,
      y0: CAIXA.y0 + (MOBILE ? 46 : 64), y1: CAIXA.y1 - (MOBILE ? 40 : 54)
    };
    GRANDES_L = {
      plot: plotG,
      slot: (plotG.x1 - plotG.x0) / 2,
      larg: Math.min((plotG.x1 - plotG.x0) * 0.24, 170),
      yMax: Math.max(popGrandes, popDemais) * 1.12
    };

    // ---- grade (estados 4 e 5): a mesma grade; nos quintis so abre vaos ----
    var resEsq = MOBILE ? 46 : 74, resDir = MOBILE ? 72 : 118, resV = MOBILE ? 20 : 28;
    var gap = MOBILE ? 8 : 14;
    var g = encaixa(NG, cw - resEsq - resDir, ch - 2 * resV - 4 * gap);
    var largGrade = g.cols * g.cel;
    var altG = Math.ceil(NG / g.cols) * g.cel;
    var meioY = (CAIXA.y0 + CAIXA.y1) / 2;
    GRID = {
      cols: g.cols, cel: g.cel, gap: gap, altG: altG,
      x0: CAIXA.x0 + resEsq + (cw - resEsq - resDir - largGrade) / 2,
      y0G: meioY - altG / 2,
      y0Q: meioY - (altG + 4 * gap) / 2
    };
    GRID.x1 = GRID.x0 + largGrade;

    // ---- barras (estados 6, 7 e 12) ----
    var plot = {
      x0: CAIXA.x0 + (MOBILE ? 34 : 52), x1: CAIXA.x1,
      y0: CAIXA.y0 + (MOBILE ? 46 : 64), y1: CAIXA.y1 - (MOBILE ? 26 : 34)
    };
    var slot = (plot.x1 - plot.x0) / 5;
    var max00 = Math.max.apply(null, soma00.slice(1));
    var max25 = Math.max.apply(null, soma25.slice(1));
    BARRAS = {
      plot: plot, slot: slot,
      larg3: Math.min(slot * 0.5, 130),
      larg4: Math.min(slot * 0.36, 92),
      vao4: Math.min(slot * 0.06, 8),
      yMax3: max00 * 1.12,
      yMax4: Math.max(max00, max25) * 1.1
    };
    // FPM: o mesmo plano e a mesma escala de folga das barras de 2000 x 2025.
    FPM_L = {
      plot: plot,
      yMax: Math.max.apply(null, fpmAntes.concat(fpmDepois)) * 1e6 * 1.1
    };

    // ---- porte (estado 8): dois graficos e, entre eles, os municipios de cada faixa ----
    var slotP = cw / Math.max(NF, 1);
    // No celular o cartao deste passo e mais alto que o dos outros: o visual
    // termina antes (36% da tela) e fica so com os dois graficos, sem os
    // quadradinhos de cada faixa.
    var chP = MOBILE ? Math.min(ch, H * 0.36 - CAIXA.y0) : ch;
    var yFimP = CAIXA.y0 + chP;
    var yTopo = CAIXA.y0 + (MOBILE ? 26 : 34);
    var yBaseTopo = CAIXA.y0 + chP * (MOBILE ? 0.46 : 0.36);
    var yW0 = yBaseTopo + (MOBILE ? 26 : 40), yW1 = MOBILE ? yW0 : CAIXA.y0 + chP * 0.62;
    var yTit2 = yW1 + (MOBILE ? 14 : 38);
    var nMax = Math.max.apply(null, porFaixa.map(function (l) { return l.length; }).concat([1]));
    var w = MOBILE ? { cel: 0, cols: 1 } : encaixa(nMax, slotP * 0.82, yW1 - yW0);
    PORTE_L = {
      slot: slotP, cel: w.cel, cols: w.cols,
      yTit1: CAIXA.y0 + 8, yTopo: yTopo, yBaseTopo: yBaseTopo,
      yRot: yBaseTopo + (MOBILE ? 12 : 16), yW0: yW0, yW1: yW1,
      yTit2: yTit2, yB0: yTit2 + (MOBILE ? 14 : 22), yB1: yFimP - 6
    };

    // ---- transferencias (estado 9): barra 100% em cima, grade embaixo ----
    var yBarra0 = CAIXA.y0 + (MOBILE ? 22 : 30), yBarra1 = yBarra0 + (MOBILE ? 28 : 40);
    var yG0 = yBarra1 + (MOBILE ? 22 : 34), yG1 = CAIXA.y1 - (MOBILE ? 34 : 44);
    var t = encaixa(NT, cw, yG1 - yG0);
    TRANSF_L = {
      yBarra0: yBarra0, yBarra1: yBarra1, cols: t.cols, cel: t.cel,
      x0: CAIXA.x0 + (cw - t.cols * t.cel) / 2, y0: yG0, yLeg: CAIXA.y1 - (MOBILE ? 14 : 18)
    };

    montaEstados();
  }

  function centroSlot(q) { return BARRAS.plot.x0 + BARRAS.slot * (q - 0.5); }
  function x2000(q) { return centroSlot(q) - BARRAS.larg4 / 2 - BARRAS.vao4 / 2; }
  function x2025(q) { return centroSlot(q) + BARRAS.larg4 / 2 + BARRAS.vao4 / 2; }
  function centroFaixa(f) { return CAIXA.x0 + PORTE_L.slot * (f + 0.5); }
  function centroGrandes(k) { return GRANDES_L.plot.x0 + GRANDES_L.slot * (k + 0.5); }

  /** Posicao vertical de um quadrado da grade (estado 4) ou dos quintis (estado 5). */
  function yGrade(j, quintis) {
    var linha = Math.floor(j / GRID.cols);
    var base = quintis ? GRID.y0Q + (MUN[GRADE[j]].q25 - 1) * GRID.gap : GRID.y0G;
    return base + (linha + 0.5) * GRID.cel;
  }

  function montaEstados() {
    var E = [];
    for (var k = 0; k < N_ESTADOS; k++) E.push(novoEstado());
    var i, j, q;

    // 0, 1, 3, 10 e 11. o mesmo mapa, com cores diferentes
    var cw = CAIXA.x1 - CAIXA.x0, ch = CAIXA.y1 - CAIXA.y0;
    var gw = GEO.x1 - GEO.x0, gh = GEO.y1 - GEO.y0;
    var s = Math.min(cw / gw, ch / gh) * 0.98;
    var ox = CAIXA.x0 + (cw - gw * s) / 2, oy = CAIXA.y0 + (ch - gh * s) / 2;
    [[0, function () { return NEUTRO; }],
     [1, function (i) { return grande[i] ? AZUL_GRANDE : CLARO; }],
     [3, function (i) { return MUN[i].q25 ? VERDE : CINZA; }],
     [10, function (i) { return grande[i] ? AZUL_GRANDE : CLARO; }],
     [11, function (i) { return !grande[i] ? CLARO : (MUN[i].q25 ? COR_Q[MUN[i].q25] : CINZA); }]].forEach(function (par) {
      var e = E[par[0]];
      for (i = 0; i < N; i++) {
        e.cx[i] = ox + (geoX[i] - GEO.x0) * s;
        e.cy[i] = oy + (geoY[i] - GEO.y0) * s;
        e.hw[i] = e.hh[i] = s;
        e.tipo[i] = 0;
        pinta(e, i, par[1](i), 1);
      }
    });

    // 4 e 5. a mesma grade; nos quintis cada bloco so desce ou sobe
    var meio = GRID.cel * 0.41;
    for (i = 0; i < N; i++) {
      j = posGrade[i];
      if (j < 0) { copia(E[4], E[3], i, 0); copia(E[5], E[3], i, 0); continue; }
      var x = GRID.x0 + (j % GRID.cols + 0.5) * GRID.cel;
      retangulo(E[4], i, x, yGrade(j, false), meio, meio);
      pinta(E[4], i, corGradiente(j / Math.max(NG - 1, 1)), 1);
      retangulo(E[5], i, x, yGrade(j, true), meio, meio);
      pinta(E[5], i, COR_Q[MUN[i].q25], 1);
    }

    // 2, 6, 7 e 12. barras: cada municipio vira uma fatia, altura proporcional a populacao
    var P = BARRAS.plot, alt = P.y1 - P.y0;
    function empilha(est, lista, cor, pop, x, larg, yMax, base, altura) {
      lista.forEach(function (idx) {
        var h = pop(MUN[idx]) / yMax * altura;
        retangulo(est, idx, x, base - h / 2, larg / 2, Math.max(h / 2, 0.01));
        pinta(est, idx, cor, 1);
        base -= h;
      });
    }
    var G = GRANDES_L.plot;
    empilha(E[2], GRANDES, AZUL_GRANDE, function (m) { return m.p25; }, centroGrandes(0), GRANDES_L.larg, GRANDES_L.yMax, G.y1, G.y1 - G.y0);
    empilha(E[2], DEMAIS, CLARO, function (m) { return m.p25; }, centroGrandes(1), GRANDES_L.larg, GRANDES_L.yMax, G.y1, G.y1 - G.y0);
    var F = FPM_L.plot;
    for (q = 1; q <= 5; q++) {
      empilha(E[6], porQ00[q], COR_Q[q], function (m) { return m.p00; }, centroSlot(q), BARRAS.larg3, BARRAS.yMax3, P.y1, alt);
      empilha(E[7], porQ25[q], COR_Q[q], function (m) { return m.p25; }, x2025(q), BARRAS.larg4, BARRAS.yMax4, P.y1, alt);
      var fq = fatorFpm[q];
      empilha(E[12], porQ25[q], COR_Q[q], function (m) { return m.p25 * fq; }, x2000(q), BARRAS.larg4, FPM_L.yMax, F.y1, F.y1 - F.y0);
    }

    // 8. porte: quadradinhos de cada faixa, na cor do quintil
    var Lp = PORTE_L, mp = Lp.cel * 0.4;
    porFaixa.forEach(function (lista, f) {
      var x0 = centroFaixa(f) - Lp.cols * Lp.cel / 2;
      lista.sort(ordemGrade).forEach(function (idx, k) {
        if (MOBILE) { copia(E[8], E[7], idx, 0); return; } // sem espaco: os quadrados saem de cena
        retangulo(E[8], idx, x0 + (k % Lp.cols + 0.5) * Lp.cel, Lp.yW0 + (Math.floor(k / Lp.cols) + 0.5) * Lp.cel, mp, mp);
        pinta(E[8], idx, COR_Q[MUN[idx].q25], 1);
      });
    });

    // 9. transferencias: azul quando mais da metade da receita vem delas
    var Lt = TRANSF_L, mt = Lt.cel * 0.41;
    TRANSF.forEach(function (idx, k) {
      retangulo(E[9], idx, Lt.x0 + (k % Lt.cols + 0.5) * Lt.cel, Lt.y0 + (Math.floor(k / Lt.cols) + 0.5) * Lt.cel, mt, mt);
      pinta(E[9], idx, MUN[idx].tr > 0.5 ? AZUL : AMARELO, 1);
    });

    // Quem nao entra num estado aparece ou some no lugar, sem viajar.
    for (i = 0; i < N; i++) {
      var m = MUN[i];
      if (!m.q00) {
        if (m.q25) copia(E[6], E[7], i, 0); else copia(E[6], E[5], i, 0);
      }
      if (!m.q25) copia(E[7], E[6], i, 0);
      if (faixa[i] < 0) copia(E[8], E[7], i, 0);
      if (posTransf[i] < 0) copia(E[9], E[8], i, 0);
      if (!m.q25) copia(E[12], E[11], i, 0);
    }

    ESTADOS = E;
  }

  // --------------------------------------------------------------------------
  // Tempo e interpolacao
  // --------------------------------------------------------------------------
  function corta(t) { return t < 0 ? 0 : (t > 1 ? 1 : t); }
  function suave(t) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }
  function sai(t) { return 1 - suave(corta(t / 0.35)); }
  function entra(t) { return suave(corta((t - 0.6) / 0.4)); }
  function lerp(a, b, t) { return a + (b - a) * t; }

  function segmento(p) {
    var seg = Math.min(Math.floor(p), N_ESTADOS - 2);
    return { seg: seg, t: p - seg };
  }

  /** Peso de cada estado na posicao p: textos e eixos de cada um. */
  function peso(k, p) {
    var s = segmento(p);
    if (k === s.seg) return sai(s.t);
    if (k === s.seg + 1) return entra(s.t);
    return 0;
  }

  /**
   * Opacidade de um elemento que existe nos estados [de, ate]: entra no fim da
   * transicao que chega em `de` (quando as formas ja chegaram) e sai rapido no
   * comeco da transicao que deixa `ate` (antes de as formas irem embora).
   */
  function presenca(p, de, ate, inicioEntrada) {
    if (p >= de && p <= ate) return 1;
    var s = segmento(p);
    if (s.seg === de - 1) return suave(corta((s.t - inicioEntrada) / (1 - inicioEntrada)));
    if (s.seg === ate) return 1 - suave(corta(s.t / 0.15));
    return 0;
  }

  // --------------------------------------------------------------------------
  // Desenho
  // --------------------------------------------------------------------------
  var hachura = null;
  function padraoHachura() {
    if (hachura) return hachura;
    var c = document.createElement('canvas');
    c.width = c.height = 8;
    var g = c.getContext('2d');
    g.strokeStyle = 'rgba(255, 255, 255, 0.75)';
    g.lineWidth = 2;
    g.beginPath();
    g.moveTo(-2, 10); g.lineTo(10, -2);
    g.moveTo(-2, 2); g.lineTo(2, -2);
    g.moveTo(6, 10); g.lineTo(10, 6);
    g.stroke();
    hachura = ctx.createPattern(c, 'repeat');
    return hachura;
  }

  function texto(str, x, y, opt) {
    ctx.font = (opt.peso || 400) + ' ' + opt.tam + 'px ' + FONTE;
    ctx.fillStyle = opt.cor || TINTA;
    ctx.textAlign = opt.alinha || 'left';
    ctx.textBaseline = opt.base || 'middle';
    ctx.fillText(str, x, y);
  }

  /** Texto que quebra em duas linhas se nao couber na largura. */
  function textoQuebrado(str, x, y, larg, opt) {
    ctx.font = (opt.peso || 400) + ' ' + opt.tam + 'px ' + FONTE;
    if (ctx.measureText(str).width <= larg || str.indexOf(' ') < 0) { texto(str, x, y, opt); return; }
    var pal = str.split(' '), meio = Math.ceil(pal.length / 2);
    texto(pal.slice(0, meio).join(' '), x, y, opt);
    texto(pal.slice(meio).join(' '), x, y + opt.tam * 1.15, opt);
  }

  function desenhaMunicipios(p) {
    var s = segmento(p), t = s.t;
    var A = ESTADOS[s.seg], B = ESTADOS[s.seg + 1], D = ATRASOS[s.seg];
    var escalaT = 1 - ATRASO;
    var alfaAtual = -1;

    for (var i = 0; i < N; i++) {
      var e = suave(corta((t - D[i]) / escalaT));
      var alfa = A.a[i] + (B.a[i] - A.a[i]) * e;
      if (alfa < 0.004) continue;
      if (alfa !== alfaAtual) { ctx.globalAlpha = alfa; alfaAtual = alfa; }

      // Parado num dos lados: cor pronta e, se for retangulo, um fillRect.
      var E = e === 0 ? A : (e === 1 ? B : null);
      if (E) {
        ctx.fillStyle = E.css[i];
        if (E.tipo[i] === 1) {
          ctx.fillRect(E.cx[i] - E.hw[i], E.cy[i] - E.hh[i], E.hw[i] * 2, E.hh[i] * 2);
          continue;
        }
      } else {
        ctx.fillStyle = 'rgb(' + ((A.r[i] + (B.r[i] - A.r[i]) * e) | 0) + ',' + ((A.g[i] + (B.g[i] - A.g[i]) * e) | 0) + ',' + ((A.b[i] + (B.b[i] - A.b[i]) * e) | 0) + ')';
      }
      var cx = A.cx[i] + (B.cx[i] - A.cx[i]) * e, cy = A.cy[i] + (B.cy[i] - A.cy[i]) * e;

      if (A.tipo[i] === 1 && B.tipo[i] === 1) {
        var hw = A.hw[i] + (B.hw[i] - A.hw[i]) * e, hh = A.hh[i] + (B.hh[i] - A.hh[i]) * e;
        ctx.fillRect(cx - hw, cy - hh, hw * 2, hh * 2);
        continue;
      }
      // Pelo menos um dos lados e o contorno do municipio: interpola o anel.
      var ax = A.tipo[i] === 0 ? poliX[i] : quadX[i], ay = A.tipo[i] === 0 ? poliY[i] : quadY[i];
      var bx = B.tipo[i] === 0 ? poliX[i] : quadX[i], by = B.tipo[i] === 0 ? poliY[i] : quadY[i];
      var awx = A.hw[i] * (1 - e), awy = A.hh[i] * (1 - e), bwx = B.hw[i] * e, bwy = B.hh[i] * e;
      var n = ax.length;
      ctx.beginPath();
      ctx.moveTo(cx + ax[0] * awx + bx[0] * bwx, cy + ay[0] * awy + by[0] * bwy);
      for (var k = 1; k < n; k++) {
        ctx.lineTo(cx + ax[k] * awx + bx[k] * bwx, cy + ay[k] * awy + by[k] * bwy);
      }
      ctx.closePath();
      ctx.fill();
      // Divisa entre municipios: so com o mapa parado. Em movimento ela nao se
      // ve e dobraria o custo do quadro mais pesado (5.570 contornos).
      if (E && E.tipo[i] === 0) ctx.stroke();
    }
    ctx.globalAlpha = 1;
  }

  /** Estado 2: barras de fundo, valores e rotulos das cidades grandes x demais. */
  function desenhaGrandes(p) {
    var a = peso(2, p);
    if (a < 0.01) return;
    var L = GRANDES_L, P = L.plot, alt = P.y1 - P.y0;
    var aBase = presenca(p, 2, 2, 0.85);
    var total = popGrandes + popDemais || 1;
    var grupos = [
      { pop: popGrandes, cor: AZUL_GRANDE, n: GRANDES.length, rot: 'Mais de ' + fmt0.format(GR.limite / 1000) + ' mil habitantes' },
      { pop: popDemais, cor: CLARO, n: DEMAIS.length, rot: 'Até ' + fmt0.format(GR.limite / 1000) + ' mil habitantes' }
    ];
    ctx.globalAlpha = a;
    texto('População em 2025', P.x0, P.y0 - (MOBILE ? 30 : 42), { tam: MOBILE ? 11 : 13, peso: 700, cor: TINTA });
    ctx.strokeStyle = '#B9B2A4'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(P.x0, P.y1 + 0.5); ctx.lineTo(P.x1, P.y1 + 0.5); ctx.stroke();

    grupos.forEach(function (g, k) {
      var x = centroGrandes(k), h = g.pop / L.yMax * alt;
      if (aBase > 0.01) {
        ctx.globalAlpha = a * aBase;
        ctx.fillStyle = css(g.cor);
        ctx.fillRect(x - L.larg / 2, P.y1 - h, L.larg, h);
      }
      ctx.globalAlpha = a;
      var yv = P.y1 - h - (MOBILE ? 10 : 14);
      texto(fmt1.format(g.pop / total * 100) + '%', x, yv - (MOBILE ? 16 : 22), { tam: MOBILE ? 18 : 26, peso: 700, cor: k === 0 ? css(AZUL_GRANDE) : CINZA_TXT, alinha: 'center' });
      texto(fmt1.format(g.pop / 1e6) + ' milhões de pessoas', x, yv, { tam: MOBILE ? 10 : 13, cor: TINTA, alinha: 'center' });
      texto(fmt0.format(g.n) + ' municípios', x, P.y1 + (MOBILE ? 14 : 20), { tam: MOBILE ? 11 : 14, peso: 700, cor: TINTA, alinha: 'center' });
      texto(g.rot, x, P.y1 + (MOBILE ? 28 : 38), { tam: MOBILE ? 9 : 12, cor: CINZA_TXT, alinha: 'center' });
    });
    ctx.globalAlpha = 1;
  }

  function desenhaGrade(p) {
    var a1 = peso(4, p), a2 = peso(5, p);
    var tamR = MOBILE ? 11 : 13;

    if (a1 > 0.01) {
      ctx.globalAlpha = a1;
      var topo = GRID.y0G, base = GRID.y0G + GRID.altG, xs = GRID.x1 + (MOBILE ? 10 : 16);
      texto('Menos dinheiro por habitante', GRID.x0, topo - (MOBILE ? 9 : 13), { tam: tamR, peso: 700, cor: COR_Q_TXT[1] });
      texto('Mais dinheiro por habitante', xs, base + (MOBILE ? 10 : 14), { tam: tamR, peso: 700, cor: COR_Q_TXT[5], alinha: 'right' });
      // seta vertical ao lado da grade
      ctx.strokeStyle = CINZA_TXT; ctx.fillStyle = CINZA_TXT; ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.moveTo(xs, topo); ctx.lineTo(xs, base - 6); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(xs - 4, base - 7); ctx.lineTo(xs + 4, base - 7); ctx.lineTo(xs, base); ctx.closePath(); ctx.fill();
    }

    if (a2 > 0.01) {
      ctx.globalAlpha = a2;
      for (var q = 1; q <= 5; q++) {
        var lista = porQ25[q];
        if (!lista.length) continue;
        var j0 = posGrade[lista[0]], j1 = posGrade[lista[lista.length - 1]];
        var y0 = yGrade(j0, true) - GRID.cel / 2, y1 = yGrade(j1, true) + GRID.cel / 2, ym = (y0 + y1) / 2;
        var xb = GRID.x0 - (MOBILE ? 6 : 10);
        // colchete a esquerda do bloco, como na arte dos quintis
        ctx.strokeStyle = '#B9B2A4'; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(xb + 4, y0); ctx.lineTo(xb, y0); ctx.lineTo(xb, y1); ctx.lineTo(xb + 4, y1); ctx.stroke();
        texto('20%', xb - (MOBILE ? 5 : 9), ym - (MOBILE ? 6 : 8), { tam: MOBILE ? 13 : 17, peso: 700, cor: TINTA, alinha: 'right' });
        texto(q + 'º quintil', xb - (MOBILE ? 5 : 9), ym + (MOBILE ? 8 : 11), { tam: MOBILE ? 9 : 11, peso: 600, cor: COR_Q_TXT[q], alinha: 'right' });
        var xd = GRID.x1 + (MOBILE ? 8 : 14);
        texto(fmt0.format(lista.length), xd, ym - (MOBILE ? 6 : 8), { tam: MOBILE ? 13 : 17, peso: 700, cor: TINTA });
        texto('municípios', xd, ym + (MOBILE ? 8 : 11), { tam: MOBILE ? 9 : 11, cor: CINZA_TXT });
      }
    }
    ctx.globalAlpha = 1;
  }

  /** Linhas horizontais do eixo Y, a cada `passo`, na escala yMax. */
  function eixoY(P, yMax, passo, alfa) {
    var alt = P.y1 - P.y0;
    ctx.globalAlpha = alfa;
    ctx.lineWidth = 1;
    for (var v = passo; v <= yMax * 1.0001; v += passo) {
      var y = P.y1 - v / yMax * alt;
      if (y < P.y0) break;
      ctx.strokeStyle = '#E9E3D7';
      ctx.beginPath(); ctx.moveTo(P.x0, y); ctx.lineTo(P.x1, y); ctx.stroke();
      texto(fmt0.format(v / 1e6) + 'M', P.x0 - 8, y, { tam: MOBILE ? 9 : 11, cor: CINZA_TXT, alinha: 'right' });
    }
    ctx.strokeStyle = '#B9B2A4';
    ctx.beginPath(); ctx.moveTo(P.x0, P.y1 + 0.5); ctx.lineTo(P.x1, P.y1 + 0.5); ctx.stroke();
    texto('0', P.x0 - 8, P.y1, { tam: MOBILE ? 9 : 11, cor: CINZA_TXT, alinha: 'right' });
  }

  /** Estados 6 e 7: eixos, barras de fundo (2000 hachurada e 2025 solida), valores e legenda. */
  function desenhaBarras(p) {
    if (p <= 5 || p >= 8) return;
    var P = BARRAS.plot, alt = P.y1 - P.y0;
    var s = segmento(p), t = s.t;

    var aEixo = p < 6 ? entra(t) : (p <= 7 ? 1 : sai(t));
    var t34 = p <= 6 ? 0 : (p >= 7 ? 1 : suave(t));
    var yMax = lerp(BARRAS.yMax3, BARRAS.yMax4, t34);
    // A barra de 2000 se fecha quando as fatias terminam de chegar.
    var aBase00 = presenca(p, 6, 7, 0.82);
    var aBase25 = presenca(p, 7, 7, 0.85);

    eixoY(P, yMax, 10e6, aEixo);
    for (var q = 1; q <= 5; q++) {
      texto(q + 'º quintil', centroSlot(q), P.y1 + (MOBILE ? 13 : 18), { tam: MOBILE ? 10 : 12, peso: 700, cor: TINTA, alinha: 'center' });
    }

    // legenda / titulo do grafico
    var a3 = peso(6, p), a4 = peso(7, p);
    var yLeg = P.y0 - (MOBILE ? 30 : 42);
    if (a3 > 0.01) {
      ctx.globalAlpha = a3;
      texto('População em 2000, por quintil de receita por habitante', P.x0, yLeg, { tam: MOBILE ? 11 : 13, peso: 600, cor: TINTA });
    }
    if (a4 > 0.01) {
      ctx.globalAlpha = a4;
      var xl = P.x0;
      ctx.fillStyle = '#7C8591'; ctx.fillRect(xl, yLeg - 6, 22, 12);
      ctx.fillStyle = padraoHachura(); ctx.fillRect(xl, yLeg - 6, 22, 12);
      texto('2000', xl + 28, yLeg, { tam: MOBILE ? 11 : 13, peso: 600, cor: TINTA });
      xl += MOBILE ? 72 : 86;
      ctx.fillStyle = '#4A5260'; ctx.fillRect(xl, yLeg - 6, 22, 12);
      texto('2025', xl + 28, yLeg, { tam: MOBILE ? 11 : 13, peso: 600, cor: TINTA });
      texto('milhões de habitantes', xl + (MOBILE ? 66 : 80), yLeg, { tam: MOBILE ? 10 : 12, cor: CINZA_TXT });
    }

    // barras de fundo e valores
    for (q = 1; q <= 5; q++) {
      var corCss = css(COR_Q[q]);
      var h00 = soma00[q] / yMax * alt;
      var larg00 = lerp(BARRAS.larg3, BARRAS.larg4, t34);
      var xc00 = lerp(centroSlot(q), x2000(q), t34);
      if (aBase00 > 0.01) {
        ctx.globalAlpha = aBase00;
        ctx.fillStyle = corCss;
        ctx.fillRect(xc00 - larg00 / 2, P.y1 - h00, larg00, h00);
        ctx.fillStyle = padraoHachura();
        ctx.fillRect(xc00 - larg00 / 2, P.y1 - h00, larg00, h00);
        // No celular, com duas barras por quintil, o valor perde o " mi" para caber.
        texto(fmt1.format(soma00[q] / 1e6) + (MOBILE && t34 > 0.5 ? '' : ' mi'), xc00, P.y1 - h00 - (MOBILE ? 8 : 11), {
          tam: lerp(MOBILE ? 11 : 14, MOBILE ? 8.5 : 12, t34), peso: 700, cor: t34 > 0.5 ? CINZA_TXT : TINTA, alinha: 'center'
        });
      }
      if (aBase25 > 0.01) {
        var h25 = soma25[q] / yMax * alt, xc25 = x2025(q);
        ctx.globalAlpha = aBase25;
        ctx.fillStyle = corCss;
        ctx.fillRect(xc25 - BARRAS.larg4 / 2, P.y1 - h25, BARRAS.larg4, h25);
        texto(fmt1.format(soma25[q] / 1e6) + (MOBILE ? '' : ' mi'), xc25, P.y1 - h25 - (MOBILE ? 8 : 11), {
          tam: MOBILE ? 9 : 13, peso: 700, cor: TINTA, alinha: 'center'
        });
      }
    }
    ctx.globalAlpha = 1;
  }

  /** Estado 8: crescimento da populacao (em cima) e da receita por habitante (embaixo), por porte. */
  function desenhaPorte(p) {
    var a = peso(8, p);
    if (a < 0.01 || !NF) return;
    var L = PORTE_L;
    var cresce = suave(corta(a)); // as barras crescem enquanto aparecem
    var tamT = MOBILE ? 11 : 13, tamV = MOBILE ? 9 : 12, tamR = MOBILE ? 9 : 11;
    var pop = PORTE.populacao, rec = PORTE.receita, brPop = PORTE.populacao_brasil;
    var largBarra = Math.min(L.slot * 0.5, 64);
    ctx.globalAlpha = a;

    // --- em cima: crescimento da populacao ---
    texto('População: crescimento de 2000 a 2025', CAIXA.x0, L.yTit1, { tam: tamT, peso: 700, cor: TINTA });
    var maxPop = Math.max.apply(null, pop.filter(function (v) { return v !== null; }).concat([brPop || 0])) * 1.25;
    var escTopo = (L.yBaseTopo - L.yTopo) / maxPop;
    for (var f = 0; f < NF; f++) {
      var x = centroFaixa(f);
      if (pop[f] !== null) {
        var h = pop[f] * escTopo * cresce;
        ctx.fillStyle = brPop !== null && pop[f] > brPop ? '#1B3A6B' : '#B8C2CF';
        ctx.fillRect(x - largBarra / 2, L.yBaseTopo - Math.max(h, 0), largBarra, Math.abs(h));
        texto(fmt1.format(pop[f]) + '%', x, L.yBaseTopo - Math.max(h, 0) - (MOBILE ? 7 : 9), { tam: tamV, peso: 700, cor: TINTA, alinha: 'center' });
      }
      textoQuebrado(PORTE.rotulos[f], x, L.yRot, L.slot - 4, { tam: tamR, peso: 600, cor: TINTA, alinha: 'center' });
      if (!MOBILE) texto(fmt0.format(porFaixa[f].length) + ' mun.', x, L.yW1 + 12, { tam: tamR - 1, cor: CINZA_TXT, alinha: 'center' });
    }
    ctx.strokeStyle = '#B9B2A4'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(CAIXA.x0, L.yBaseTopo + 0.5); ctx.lineTo(CAIXA.x1, L.yBaseTopo + 0.5); ctx.stroke();
    if (brPop !== null) {
      // media do pais: linha tracejada
      var yBr = L.yBaseTopo - brPop * escTopo * cresce;
      ctx.setLineDash([4, 4]); ctx.strokeStyle = '#A81C21';
      ctx.beginPath(); ctx.moveTo(CAIXA.x0, yBr); ctx.lineTo(CAIXA.x1, yBr); ctx.stroke();
      ctx.setLineDash([]);
      // rotulo a esquerda, sobre as faixas pequenas, onde as barras sao baixas
      texto('Brasil: ' + fmt1.format(brPop) + '%', CAIXA.x0, yBr - (MOBILE ? 7 : 9), { tam: tamR, peso: 700, cor: '#A81C21' });
    }

    // --- embaixo: receita por habitante em relacao ao pais ---
    texto('Receita por habitante: crescimento acima (+) ou abaixo (−) do país', CAIXA.x0, L.yTit2, { tam: tamT, peso: 700, cor: TINTA });
    var vals = rec.filter(function (v) { return v !== null; });
    var hi = Math.max.apply(null, vals.concat([0])) * 1.3, lo = Math.min.apply(null, vals.concat([0])) * 1.3;
    var y0 = L.yB0 + 10, y1 = L.yB1 - 10;
    var yZero = y0 + hi / (hi - lo || 1) * (y1 - y0);
    var esc = (y1 - y0) / (hi - lo || 1);
    ctx.strokeStyle = '#B9B2A4';
    ctx.beginPath(); ctx.moveTo(CAIXA.x0, yZero + 0.5); ctx.lineTo(CAIXA.x1, yZero + 0.5); ctx.stroke();
    for (f = 0; f < NF; f++) {
      if (rec[f] === null) continue;
      var xr = centroFaixa(f), hr = rec[f] * esc * cresce;
      ctx.fillStyle = rec[f] < 0 ? '#A81C21' : '#7C8BA1';
      ctx.fillRect(xr - largBarra / 2, hr >= 0 ? yZero - hr : yZero, largBarra, Math.abs(hr));
      texto((rec[f] > 0 ? '+' : '') + fmt1.format(rec[f]) + '%', xr, hr >= 0 ? yZero - hr - (MOBILE ? 7 : 9) : yZero - hr + (MOBILE ? 8 : 10), {
        tam: tamV, peso: 700, cor: rec[f] < 0 ? '#A81C21' : TINTA, alinha: 'center'
      });
    }
    ctx.globalAlpha = 1;
  }

  /** Estado 9: barra 100% (transferencias x arrecadacao propria) e legenda da grade. */
  function desenhaTransf(p) {
    var a = peso(9, p);
    if (a < 0.01) return;
    var L = TRANSF_L, comp = DADOS.composicao || { pct_transferencias: 0, pct_propria: 0 };
    var cw = CAIXA.x1 - CAIXA.x0, tam = MOBILE ? 11 : 14;
    ctx.globalAlpha = a;
    texto('Receita corrente de todos os municípios, 2025', CAIXA.x0, CAIXA.y0 + 6, { tam: MOBILE ? 11 : 13, peso: 700, cor: TINTA });
    var larg = cw * comp.pct_transferencias / 100 * suave(corta(a));
    ctx.fillStyle = css(AZUL); ctx.fillRect(CAIXA.x0, L.yBarra0, larg, L.yBarra1 - L.yBarra0);
    ctx.fillStyle = css(AMARELO); ctx.fillRect(CAIXA.x0 + larg, L.yBarra0, cw - larg, L.yBarra1 - L.yBarra0);
    var ym = (L.yBarra0 + L.yBarra1) / 2;
    texto('Transferências ' + comp.pct_transferencias + '%', CAIXA.x0 + 10, ym, { tam: tam, peso: 700, cor: '#ffffff' });
    texto('Própria ' + comp.pct_propria + '%', CAIXA.x1 - 10, ym, { tam: tam, peso: 700, cor: '#122747', alinha: 'right' });

    var tamL = MOBILE ? 10 : 12, xl = CAIXA.x0;
    ctx.fillStyle = css(AZUL); ctx.fillRect(xl, L.yLeg - 5, 10, 10);
    var t1 = 'Mais da metade vem de transferências (' + fmt0.format(nMaioria) + ')';
    texto(t1, xl + 15, L.yLeg, { tam: tamL, cor: TINTA });
    ctx.font = '400 ' + tamL + 'px ' + FONTE;
    xl += 15 + ctx.measureText(t1).width + (MOBILE ? 10 : 18);
    var t2 = 'Metade ou menos (' + fmt0.format(NT - nMaioria) + ')';
    if (MOBILE && xl + 15 + ctx.measureText(t2).width > CAIXA.x1) { xl = CAIXA.x0; L = { yLeg: L.yLeg + 15 }; }
    ctx.fillStyle = css(AMARELO); ctx.fillRect(xl, L.yLeg - 5, 10, 10);
    texto(t2, xl + 15, L.yLeg, { tam: tamL, cor: TINTA });
    ctx.globalAlpha = 1;
  }

  /**
   * Estado 12: simulacao do FPM no mesmo padrao das barras de 2000 x 2025.
   * As fatias assentam na barra de 2025 (hachurada, a esquerda, como 2000 la);
   * a barra com mais R$ 50 bi (solida) cresce do eixo ao lado.
   */
  function desenhaFpm(p) {
    var a = peso(12, p);
    if (a < 0.01) return;
    var L = FPM_L, P = L.plot, alt = P.y1 - P.y0;
    var s = segmento(p);
    var cresce = p >= 12 ? 1 : suave(corta((s.t - 0.55) / 0.45));
    var aBase = presenca(p, 12, 12, 0.85);
    eixoY(P, L.yMax, 10e6, a);
    ctx.globalAlpha = a;

    for (var q = 1; q <= 5; q++) {
      texto(q + 'º quintil', centroSlot(q), P.y1 + (MOBILE ? 13 : 18), { tam: MOBILE ? 10 : 12, peso: 700, cor: TINTA, alinha: 'center' });
    }

    // legenda: hachurada = 2025 hoje; solida = com mais R$ 50 bi
    var yLeg = P.y0 - (MOBILE ? 30 : 42), xl = P.x0, tamL = MOBILE ? 11 : 13;
    ctx.fillStyle = '#7C8591'; ctx.fillRect(xl, yLeg - 6, 22, 12);
    ctx.fillStyle = padraoHachura(); ctx.fillRect(xl, yLeg - 6, 22, 12);
    texto('2025', xl + 28, yLeg, { tam: tamL, peso: 600, cor: TINTA });
    xl += MOBILE ? 72 : 86;
    ctx.fillStyle = '#4A5260'; ctx.fillRect(xl, yLeg - 6, 22, 12);
    var rotDepois = 'Com mais R$ 50 bi no FPM';
    texto(rotDepois, xl + 28, yLeg, { tam: tamL, peso: 600, cor: TINTA });
    ctx.font = '600 ' + tamL + 'px ' + FONTE;
    var xUn = xl + 28 + ctx.measureText(rotDepois).width + (MOBILE ? 10 : 14);
    var unidade = 'milhões de habitantes, simulação';
    ctx.font = '400 ' + (MOBILE ? 10 : 12) + 'px ' + FONTE;
    if (xUn + ctx.measureText(unidade).width > P.x1) {
      texto(unidade, P.x0, yLeg + (MOBILE ? 15 : 19), { tam: MOBILE ? 10 : 12, cor: CINZA_TXT });
    } else {
      texto(unidade, xUn, yLeg, { tam: MOBILE ? 10 : 12, cor: CINZA_TXT });
    }

    // No celular, com duas barras por quintil, o valor perde o " mi" para caber.
    var mi = MOBILE ? '' : ' mi';
    for (q = 1; q <= 5; q++) {
      var corCss = css(COR_Q[q]);
      // 2025: fundo hachurado quando as fatias assentam
      var h1 = fpmAntes[q] * 1e6 / L.yMax * alt, x1 = x2000(q);
      if (aBase > 0.01) {
        ctx.globalAlpha = a * aBase;
        ctx.fillStyle = corCss;
        ctx.fillRect(x1 - BARRAS.larg4 / 2, P.y1 - h1, BARRAS.larg4, h1);
        ctx.fillStyle = padraoHachura();
        ctx.fillRect(x1 - BARRAS.larg4 / 2, P.y1 - h1, BARRAS.larg4, h1);
        texto(fmt1.format(fpmAntes[q]) + mi, x1, P.y1 - h1 - (MOBILE ? 8 : 11), {
          tam: MOBILE ? 8.5 : 12, peso: 700, cor: CINZA_TXT, alinha: 'center'
        });
      }
      // com mais R$ 50 bi: solida, cresce do eixo
      ctx.globalAlpha = a;
      var h2 = fpmDepois[q] * 1e6 / L.yMax * alt * cresce, x2 = x2025(q);
      ctx.fillStyle = corCss;
      ctx.fillRect(x2 - BARRAS.larg4 / 2, P.y1 - h2, BARRAS.larg4, h2);
      if (cresce > 0.98) {
        texto(fmt1.format(fpmDepois[q]) + mi, x2, P.y1 - h2 - (MOBILE ? 8 : 11), {
          tam: MOBILE ? 9 : 13, peso: 700, cor: TINTA, alinha: 'center'
        });
      }
    }
    ctx.globalAlpha = 1;
  }

  function desenha(p) {
    p = Math.max(0, Math.min(p, N_ESTADOS - 1));
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    ctx.globalAlpha = 1;
    ctx.fillStyle = PAPEL;
    ctx.fillRect(0, 0, W, H);
    ctx.strokeStyle = PAPEL;
    ctx.lineWidth = MOBILE ? 0.3 : 0.45;
    ctx.lineJoin = 'round';
    desenhaMunicipios(p);
    desenhaGrandes(p);
    desenhaGrade(p);
    desenhaBarras(p);
    desenhaPorte(p);
    desenhaTransf(p);
    desenhaFpm(p);
  }

  // --------------------------------------------------------------------------
  // Scroll
  // --------------------------------------------------------------------------
  var topos = [];
  function mede() {
    var base = secao.getBoundingClientRect().top + window.scrollY;
    topos = passos.map(function (el) { return el.getBoundingClientRect().top + window.scrollY - base; });
  }

  /** Posicao alvo (0 a N_ESTADOS - 1) a partir do scroll, com pausa em cada estado. */
  function alvo() {
    var s = -secao.getBoundingClientRect().top;
    if (s <= topos[0]) return 0;
    for (var k = 0; k < topos.length - 1; k++) {
      if (s < topos[k + 1]) {
        var f = (s - topos[k]) / (topos[k + 1] - topos[k]);
        return k + corta((f - 0.15) / 0.7);
      }
    }
    return topos.length - 1;
  }

  var pAtual = 0, pAlvo = 0, rodando = false, ultimo = 0, pronto = false, passoAtivo = -1;

  function marcaPasso(p) {
    var k = Math.round(p);
    if (k === passoAtivo) return;
    passoAtivo = k;
    passos.forEach(function (el, j) { el.classList.toggle('is-ativo', j === k); });
    var rot = passos[k] && passos[k].getAttribute('data-rotulo');
    if (rot) canvas.setAttribute('aria-label', rot);
  }

  function quadro(agora) {
    // O rAF pode trazer um instante anterior ao performance.now() do disparo: dt nunca negativo.
    var dt = Math.max(0, Math.min((agora - ultimo) / 1000, 0.1));
    ultimo = agora;
    var dif = pAlvo - pAtual;
    if (REDUZIR || Math.abs(dif) < 0.0005) pAtual = pAlvo;
    else pAtual += dif * (1 - Math.exp(-dt / SUAVIZACAO));
    desenha(pAtual);
    if (pAtual !== pAlvo) requestAnimationFrame(quadro);
    else rodando = false;
  }

  function aoRolar() {
    if (!pronto) return;
    pAlvo = alvo();
    marcaPasso(pAlvo);
    if (!rodando && pAlvo !== pAtual) {
      rodando = true;
      ultimo = performance.now();
      requestAnimationFrame(quadro);
    }
  }

  function aoRedimensionar() {
    if (!pronto) return;
    calculaLayout();
    mede();
    pAlvo = pAtual = alvo();
    desenha(pAtual);
  }

  function inicia(malha) {
    if (passos.length !== N_ESTADOS) {
      console.error('[inicio_animado] o template tem', passos.length, 'cartoes, mas a animacao tem', N_ESTADOS, 'estados');
    }
    preparaFormas(malha);
    pronto = true;
    secao.classList.add('is-pronto');
    calculaLayout();
    mede();
    pAlvo = pAtual = alvo();
    marcaPasso(pAtual);
    desenha(pAtual);
    window.addEventListener('scroll', aoRolar, { passive: true });
    var timer;
    window.addEventListener('resize', function () {
      window.clearTimeout(timer);
      timer = window.setTimeout(aoRedimensionar, 150);
    });
    // A fonte do canvas pode chegar depois do primeiro desenho.
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { desenha(pAtual); });
  }

  fetch(secao.getAttribute('data-malha'))
    .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then(inicia)
    .catch(function (erro) {
      // Sem a malha, a historia continua: cada municipio vira um ponto na sede.
      console.error('[inicio_animado] falha ao carregar a malha dos municipios', erro);
      inicia(null);
    });
})();
