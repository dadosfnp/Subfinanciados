/* ============================================================================
 * inicio_folheto.js: landing em formato de apresentacao (/preview/inicio/)
 * ----------------------------------------------------------------------------
 * 1. Scrollytelling: marca o passo que esta no meio da tela e mostra o visual
 *    dele no palco fixo.
 * 2. Desenha os visuais na primeira vez que o passo fica ativo (graficos com
 *    Chart.js, mapa em canvas, barras do diagrama de quintis).
 * 3. Busca de municipio da secao Plataforma (/api/busca-municipio/).
 *
 * Os dados vem do JSON #apresentacao-dados, montado no servidor a partir de
 * ifem/apresentacao.py. Um tipo de visual novo se ensina em DESENHAR.
 * ========================================================================== */
(function () {
  'use strict';

  var DADOS;
  try {
    DADOS = JSON.parse(document.getElementById('apresentacao-dados').textContent);
  } catch (erro) {
    console.error('[apresentacao] JSON #apresentacao-dados invalido', erro);
    return;
  }

  var QUINTIL = { 1: '#A81C21', 2: '#E47326', 3: '#F4D01D', 4: '#6AC074', 5: '#1C9148' };
  var fmt0 = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });
  var fmt1 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });

  if (window.Chart) {
    Chart.defaults.font.family = '"Inter", system-ui, sans-serif';
    Chart.defaults.color = '#5F6670';
    if (window.ChartDataLabels) Chart.register(ChartDataLabels);
  }

  // ==========================================================================
  // DESENHO DOS VISUAIS
  // ==========================================================================
  function opcoesBase(extra) {
    var base = {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 700 },
      plugins: {
        legend: { position: 'top', align: 'start', labels: { boxWidth: 12, boxHeight: 12, font: { size: 12 } } },
        tooltip: { callbacks: {} },
        datalabels: { display: false }
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 12, weight: '600' } } },
        y: { grid: { color: '#EEE9DF' }, border: { display: false }, ticks: { font: { size: 11 } } }
      }
    };
    return Object.assign(base, extra || {});
  }

  /** Barras agrupadas (populacao por quintil, FPM). */
  function desenharBarras(canvas, d) {
    return new Chart(canvas, {
      type: 'bar',
      data: {
        labels: d.rotulos,
        datasets: d.series.map(function (s) {
          return { label: s.nome, data: s.valores, backgroundColor: s.cor, borderRadius: 2, maxBarThickness: 46 };
        })
      },
      options: opcoesBase({
        plugins: {
          legend: { position: 'top', align: 'start', labels: { boxWidth: 12, boxHeight: 12 } },
          datalabels: {
            display: true, anchor: 'end', align: 'end', offset: 2,
            color: '#1E2530', font: { size: 11, weight: '700' },
            formatter: function (v) { return fmt1.format(v); }
          },
          tooltip: { callbacks: { label: function (c) { return ' ' + c.dataset.label + ': ' + fmt1.format(c.raw) + ' ' + (d.unidade || ''); } } }
        },
        layout: { padding: { top: 26 } }
      })
    });
  }

  /** Barras horizontais (crescimento por porte). Negativo em vermelho. */
  function desenharBarrasH(canvas, d) {
    return new Chart(canvas, {
      type: 'bar',
      data: {
        labels: d.rotulos,
        datasets: [{
          data: d.valores,
          backgroundColor: d.valores.map(function (v) { return v < 0 ? '#A81C21' : '#1B3A6B'; }),
          borderRadius: 2,
          maxBarThickness: 34
        }]
      },
      options: opcoesBase({
        indexAxis: 'y',
        plugins: {
          legend: { display: false },
          datalabels: {
            display: true, anchor: 'end', align: function (c) { return c.dataset.data[c.dataIndex] < 0 ? 'start' : 'end'; },
            color: '#1E2530', font: { size: 12, weight: '700' },
            formatter: function (v) { return fmt1.format(v) + '%'; }
          },
          tooltip: { callbacks: { label: function (c) { return ' ' + fmt1.format(c.raw) + '%'; } } }
        },
        scales: {
          x: { grid: { color: '#EEE9DF' }, border: { display: false }, ticks: { callback: function (v) { return v + '%'; } }, grace: '12%' },
          y: { grid: { display: false }, ticks: { font: { size: 12, weight: '600' } } }
        }
      })
    });
  }

  /** Barras 100% empilhadas (CAPAG, risco climatico). */
  function desenharEmpilhada(canvas, d) {
    return new Chart(canvas, {
      type: 'bar',
      data: {
        labels: d.rotulos,
        datasets: d.series.map(function (s) {
          return { label: s.nome, data: s.valores, backgroundColor: s.cor, borderColor: '#ffffff', borderWidth: 1, maxBarThickness: 70 };
        })
      },
      options: opcoesBase({
        plugins: {
          legend: { position: 'top', align: 'start', labels: { boxWidth: 12, boxHeight: 12 } },
          datalabels: {
            display: function (c) { return c.dataset.data[c.dataIndex] >= 7; },
            color: function (c) { return c.dataset.backgroundColor === '#F4D01D' || c.dataset.backgroundColor === '#6AC074' ? '#122747' : '#ffffff'; },
            font: { size: 11, weight: '700' },
            formatter: function (v) { return fmt1.format(v); }
          },
          tooltip: { callbacks: { label: function (c) { return ' ' + c.dataset.label + ': ' + fmt1.format(c.raw) + '%'; } } }
        },
        scales: {
          x: { stacked: true, grid: { display: false }, ticks: { font: { size: 12, weight: '600' } } },
          y: { stacked: true, max: 100, grid: { color: '#EEE9DF' }, border: { display: false }, ticks: { callback: function (v) { return v + '%'; } } }
        }
      })
    });
  }

  /** Diagrama dos quintis: as barras ja estao no HTML; aqui so crescem. */
  function desenharQuintis(figura) {
    figura.querySelectorAll('.ap-quintil-barra i').forEach(function (i) {
      var v = Number(i.getAttribute('data-largura')) || 0;
      var max = Number(i.getAttribute('data-max')) || 1;
      i.style.width = Math.min(v / max * 100, 100) + '%';
    });
    figura.querySelectorAll('[data-reais]').forEach(function (el) {
      el.textContent = 'R$ ' + fmt0.format(Number(el.getAttribute('data-reais')) || 0);
    });
  }

  /*
   * Mapa de pontos. Sem tiles nem biblioteca: os ~5.500 municipios, projetados
   * por longitude/latitude, ja desenham o contorno do pais. Projecao
   * equirretangular corrigida pelo cosseno da latitude central, que basta
   * para a escala do Brasil.
   */
  var LIMITES = { oeste: -74.2, leste: -34.6, norte: 5.4, sul: -33.9 };

  function desenharMapa(canvas, opcoes) {
    var mapa = DADOS.mapa;
    if (!mapa || !mapa.pontos) return null;

    var dpr = window.devicePixelRatio || 1;
    var w = canvas.clientWidth;
    var h = canvas.clientHeight;
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    var ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, w, h);

    var latC = (LIMITES.norte + LIMITES.sul) / 2;
    var kx = Math.cos(latC * Math.PI / 180);
    var larguraGeo = (LIMITES.leste - LIMITES.oeste) * kx;
    var alturaGeo = LIMITES.norte - LIMITES.sul;
    var escala = Math.min(w / larguraGeo, h / alturaGeo) * 0.96;
    var offX = (w - larguraGeo * escala) / 2;
    var offY = (h - alturaGeo * escala) / 2;

    function px(lon) { return offX + (lon - LIMITES.oeste) * kx * escala; }
    function py(lat) { return offY + (LIMITES.norte - lat) * escala; }

    var quintis = opcoes.quintis || [1, 2, 3, 4, 5];
    var so80 = opcoes.porte === 'acima_80_mil';
    var raioBase = Math.max(1.1, escala * 0.11);

    function destacado(p) {
      if (quintis.indexOf(p[2]) === -1) return false;
      if (so80 && p[3] < 80) return false;
      return true;
    }

    // Contexto em cinza claro primeiro: o pais inteiro sempre aparece, e o
    // recorte do passo se destaca por cima.
    ctx.fillStyle = 'rgba(140, 150, 164, 0.32)';
    mapa.pontos.forEach(function (p) {
      if (destacado(p)) return;
      ctx.beginPath();
      ctx.arc(px(p[0]), py(p[1]), raioBase * 0.8, 0, Math.PI * 2);
      ctx.fill();
    });

    // Com filtro de porte, o raio cresce com a populacao (raiz, para area).
    var pontos = mapa.pontos.filter(destacado).sort(function (a, b) { return b[3] - a[3]; });
    pontos.forEach(function (p) {
      var r = so80 ? Math.min(raioBase * 0.9 + Math.sqrt(p[3]) * escala * 0.012, raioBase * 9) : raioBase;
      ctx.beginPath();
      ctx.arc(px(p[0]), py(p[1]), r, 0, Math.PI * 2);
      ctx.fillStyle = QUINTIL[p[2]];
      ctx.globalAlpha = so80 ? 0.72 : 0.9;
      ctx.fill();
    });
    ctx.globalAlpha = 1;
    return { redesenhar: function () { desenharMapa(canvas, opcoes); } };
  }

  var DESENHAR = {
    barras: function (fig, cfg) { return desenharBarras(fig.querySelector('canvas'), cfg.dados); },
    barras_h: function (fig, cfg) { return desenharBarrasH(fig.querySelector('canvas'), cfg.dados); },
    empilhada: function (fig, cfg) { return desenharEmpilhada(fig.querySelector('canvas'), cfg.dados); },
    quintis: function (fig) { desenharQuintis(fig); return true; },
    mapa: function (fig, cfg) { return desenharMapa(fig.querySelector('canvas'), cfg.opcoes || {}); }
  };

  var desenhados = {};

  function garantirDesenho(id, figura) {
    if (desenhados[id]) return;
    var cfg = (DADOS.visuais || {})[id];
    var fn = cfg && DESENHAR[cfg.visual];
    if (!fn) { desenhados[id] = true; return; } // imagem, lista: ja prontos no HTML
    try {
      desenhados[id] = fn(figura, cfg) || true;
    } catch (erro) {
      console.error('[apresentacao] falha ao desenhar o visual do passo', id, erro);
      desenhados[id] = true;
    }
  }

  // ==========================================================================
  // SCROLLYTELLING
  // ==========================================================================
  function ativar(trilha, id) {
    trilha.querySelectorAll('.ap-passo').forEach(function (p) {
      p.classList.toggle('is-ativo', p.getAttribute('data-passo') === id);
    });
    trilha.querySelectorAll('.ap-visual').forEach(function (f) {
      var ativo = f.getAttribute('data-visual') === id;
      if (ativo) {
        f.setAttribute('data-ativo', '1');
        garantirDesenho(id, f);
      } else {
        f.removeAttribute('data-ativo');
      }
    });
  }

  var trilhas = document.querySelectorAll('.ap-trilha');
  trilhas.forEach(function (trilha) {
    var primeiro = trilha.querySelector('.ap-passo');
    if (primeiro) ativar(trilha, primeiro.getAttribute('data-passo'));
  });

  if ('IntersectionObserver' in window) {
    // Faixa estreita no meio da tela: o passo "ativo" e o que cruza o centro.
    var observador = new IntersectionObserver(function (entradas) {
      entradas.forEach(function (e) {
        if (!e.isIntersecting) return;
        var trilha = e.target.closest('.ap-trilha');
        ativar(trilha, e.target.getAttribute('data-passo'));
      });
    }, { rootMargin: '-45% 0px -45% 0px', threshold: 0 });
    document.querySelectorAll('.ap-passo').forEach(function (p) { observador.observe(p); });
  } else {
    // Navegador sem observer: tudo visivel e desenhado, sem animacao.
    document.querySelectorAll('.ap-visual').forEach(function (f) {
      f.setAttribute('data-ativo', '1');
      garantirDesenho(f.getAttribute('data-visual'), f);
    });
  }

  // O mapa e canvas puro: redesenha quando a largura muda (rotacao, janela).
  var timerResize;
  window.addEventListener('resize', function () {
    window.clearTimeout(timerResize);
    timerResize = window.setTimeout(function () {
      Object.keys(desenhados).forEach(function (id) {
        var d = desenhados[id];
        if (d && typeof d.redesenhar === 'function') d.redesenhar();
      });
    }, 200);
  });

  // ==========================================================================
  // BUSCA DE MUNICIPIO
  // ==========================================================================
  var input = document.getElementById('ap-busca-input');
  var lista = document.getElementById('ap-busca-resultados');
  if (input && lista) {
    var timerBusca;
    var ultimaConsulta = '';

    function limpar() { lista.innerHTML = ''; }

    input.addEventListener('input', function () {
      var q = input.value.trim();
      window.clearTimeout(timerBusca);
      if (q.length < 3) { limpar(); return; }
      timerBusca = window.setTimeout(async function () {
        ultimaConsulta = q;
        try {
          var resp = await fetch('/api/busca-municipio/?q=' + encodeURIComponent(q));
          if (!resp.ok) throw new Error('HTTP ' + resp.status);
          var json = await resp.json();
          if (q !== ultimaConsulta) return; // resposta atrasada de uma consulta antiga
          limpar();
          (json.results || []).forEach(function (m) {
            var li = document.createElement('li');
            var a = document.createElement('a');
            a.href = '/municipio/' + encodeURIComponent(m.id) + '/';
            a.setAttribute('role', 'option');
            a.textContent = m.nome;
            var info = document.createElement('small');
            info.textContent = (m.quintil ? m.quintil + ' · ' : '') + 'R$ ' + fmt0.format(m.rc_pc) + '/hab.';
            a.appendChild(info);
            li.appendChild(a);
            lista.appendChild(li);
          });
          if (!lista.children.length) {
            var vazio = document.createElement('li');
            vazio.innerHTML = '<a tabindex="-1">Nenhum município encontrado</a>';
            lista.appendChild(vazio);
          }
        } catch (erro) {
          console.error('[apresentacao] falha na busca de municipio', { q: q, erro: erro });
          limpar();
        }
      }, 250);
    });

    input.addEventListener('keydown', function (ev) {
      if (ev.key === 'ArrowDown') {
        var primeiro = lista.querySelector('a[href]');
        if (primeiro) { ev.preventDefault(); primeiro.focus(); }
      } else if (ev.key === 'Escape') {
        limpar();
      }
    });

    document.addEventListener('click', function (ev) {
      if (!ev.target.closest('.ap-busca')) limpar();
    });
  }
})();
