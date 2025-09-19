// --- JS do detalhamento do município (sem inline template) ---
document.addEventListener('DOMContentLoaded', function () {
  // ---------- Helpers ----------
  const $  = (sel, root=document) => root.querySelector(sel);
  const $$ = (sel, root=document) => Array.from(root.querySelectorAll(sel));

  function safeParseJSONById(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    try {
      let v = JSON.parse(el.textContent);
      if (typeof v === 'string') v = JSON.parse(v); // tolera dupla serialização
      return v;
    } catch (e) {
      console.warn(`Falha ao parsear #${id}:`, e);
      return null;
    }
  }

  // ---------- DATA ----------
  const allRevenueChartData = safeParseJSONById('chart-data');       // objeto com labels/values por categoria
  const percentileData      = safeParseJSONById('percentile-data');  // percentis por ranking
  const municipioData       = safeParseJSONById('municipio-data');   // ranks (nacional/estadual/faixa)

  // ---------- Toggle (setinhas abre/fecha) ----------
  function handleToggleClick(event) {
    event.stopPropagation();
    const targetId = this.dataset.target;
    if (!targetId) return;
    const target = document.getElementById(targetId);
    if (target) {
      this.classList.toggle('open');
      target.classList.toggle('hidden');
    }
  }
  function initializeToggleListeners(scope = document) {
    $$('.toggle-heading, .toggle-subheading', scope).forEach(el => {
      el.removeEventListener('click', handleToggleClick);
      el.addEventListener('click', handleToggleClick);
    });
  }

  // ---------- Ordenação ----------
  function parseCurrencyValue(str) {
    if (!str) return 0;
    const n = parseFloat(String(str).replace('R$', '').replace(/\./g, '').replace(',', '.').trim());
    return Number.isFinite(n) ? n : 0;
  }
  function sortChildrenByValue(container, isPerCapita) {
    const children = Array.from(container.children);
    const selector = isPerCapita ? '.valor-per-capita' : '.valor-absoluto';
    children.sort((a, b) =>
      parseCurrencyValue(b.querySelector(selector)?.textContent) -
      parseCurrencyValue(a.querySelector(selector)?.textContent)
    );
    children.forEach(ch => container.appendChild(ch));
  }
  function sortAllRevenueSections(isPerCapita) {
    $$('#main-revenue-details-container, [id^="detalhe-"]').forEach(c => sortChildrenByValue(c, isPerCapita));
    initializeToggleListeners();
  }

  // ---------- Per Capita / Valores Reais ----------
  const valoresAbsolutos = $$('.valor-absoluto');
  const valoresPerCapita = $$('.valor-per-capita');

  const segmented = $('#valor-toggle');          // caso futuro (mesmo look do conjunto)
  const btnSimple = $('#valor-toggle-btn');      // botão atual
  let currentMode = 'pc';                        // 'pc' | 'vr'

  function applyMode(mode) {
    currentMode = mode;

    // Visual (se existir toggle segmentado)
    if (segmented) {
      const btnPc = segmented.querySelector('[data-mode="pc"]');
      const btnVr = segmented.querySelector('[data-mode="vr"]');
      btnPc?.classList.toggle('active', mode === 'pc');
      btnVr?.classList.toggle('active', mode === 'vr');
    }

    // Visual (se existir botão simples)
    if (btnSimple) btnSimple.textContent = (mode === 'pc') ? 'Valores Reais' : 'Per Capita';

    // Mostrar/ocultar valores
    valoresPerCapita.forEach(el => el.classList.toggle('hidden', mode !== 'pc'));
    valoresAbsolutos.forEach(el => el.classList.toggle('hidden', mode !== 'vr'));

    // Ordena de acordo com o modo
    sortAllRevenueSections(mode === 'pc');
  }

  // listeners (suporta os dois formatos)
  if (segmented) {
    segmented.querySelector('[data-mode="pc"]')?.addEventListener('click', () => applyMode('pc'));
    segmented.querySelector('[data-mode="vr"]')?.addEventListener('click', () => applyMode('vr'));
  }
  if (btnSimple) {
    btnSimple.addEventListener('click', () => applyMode(currentMode === 'pc' ? 'vr' : 'pc'));
  }
  // estado inicial
  applyMode('pc');

  // ---------- Ranking ----------
  const rankingSelect = $('#ranking-select');
  const rankingValue  = $('#ranking-value');
  const headerQuintil = $('#header-quintil-indicator-container');

  function updateQuintilIndicator(el, percentile) {
    if (!el) return;
    const box = el.querySelector('.ranking-indicator') || el;
    box.classList.remove('quintil-1','quintil-2','quintil-3','quintil-4','quintil-5');
    if (percentile <= 20) box.classList.add('quintil-1');
    else if (percentile <= 40) box.classList.add('quintil-2');
    else if (percentile <= 60) box.classList.add('quintil-3');
    else if (percentile <= 80) box.classList.add('quintil-4');
    else box.classList.add('quintil-5');
  }

  function updateRankingUI(selected) {
    if (!rankingValue || !municipioData) return;

    let rank = 'N/A', total = 'N/A';
    if (selected === 'nacional') { rank = municipioData.rank_nacional; total = municipioData.total_nacional; }
    else if (selected === 'estadual') { rank = municipioData.rank_estadual; total = municipioData.total_estadual; }
    else if (selected === 'faixa')   { rank = municipioData.rank_faixa;   total = municipioData.total_faixa;   }
    rankingValue.textContent = `${rank} / ${total}`;

    // indicadores por item
    if (percentileData) {
      $$('.revenue-item-wrapper').forEach(w => {
        const fieldBase = w.querySelector('[data-field-base]')?.dataset.fieldBase;
        const container = w.querySelector('.ranking-indicator-container');
        const indicator = container?.querySelector('.ranking-indicator');
        const tooltip   = container?.querySelector('.ranking-tooltip');

        const p = fieldBase && percentileData[fieldBase] ? percentileData[fieldBase][selected] : null;
        if (p != null) {
          updateQuintilIndicator(container, p);
          if (tooltip) tooltip.textContent = `O município supera ${p}% dos outros municípios`;
        } else {
          indicator?.classList.remove('quintil-1','quintil-2','quintil-3','quintil-4','quintil-5');
          if (tooltip) tooltip.textContent = 'Ranking não disponível';
        }
      });

      // indicador principal (rc)
      const headerIndicator = headerQuintil?.querySelector('.ranking-indicator');
      const headerTooltip   = headerQuintil?.querySelector('.ranking-tooltip');
      const mainP = percentileData['rc'] ? percentileData['rc'][selected] : null;
      if (mainP != null) {
        updateQuintilIndicator(headerQuintil, mainP);
        if (headerTooltip) headerTooltip.textContent = `O município supera ${mainP}% dos outros municípios`;
      }
    }
  }

  if (rankingSelect) {
    rankingSelect.addEventListener('change', () => updateRankingUI(rankingSelect.value));
    updateRankingUI(rankingSelect.value || 'nacional');
  }

  // ---------- Gráfico empilhado horizontal ----------
  (function renderChartInit() {
    const canvas = $('#myChart');
    if (!canvas || !allRevenueChartData) return;
    const ctx = canvas.getContext('2d');

    // ordem e labels bonitinhas
    const preferredOrder = [
      'main_categories','imposto','taxas','contribuicoes',
      'transferencias_correntes','transferencias_uniao','transferencias_estado','outras_receitas'
    ];
    const pretty = k => ({
      main_categories:'Categorias Principais', imposto:'Impostos', taxas:'Taxas',
      contribuicoes:'Contribuições', transferencias_correntes:'Transferências Correntes',
      transferencias_uniao:'Transferências da União', transferencias_estado:'Transferências dos Estados',
      outras_receitas:'Outras Receitas'
    }[k] || k.replace(/_/g,' '));

    const availableKeys = preferredOrder.filter(k => {
      const o = allRevenueChartData[k];
      return o && Array.isArray(o.labels) && o.labels.length && Array.isArray(o.values) && o.values.length;
    });
    const selectEl = $('#chart-category-select');
    if (selectEl) {
      selectEl.innerHTML = '';
      (availableKeys.length ? availableKeys : ['main_categories']).forEach(k => {
        const opt = document.createElement('option');
        opt.value = k; opt.textContent = pretty(k);
        selectEl.appendChild(opt);
      });
    }

    const palette = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd','#8c564b','#e377c2','#7f7f7f','#bcbd22','#17becf'];
    let chart;

    function renderChart(key) {
      const o = allRevenueChartData[key]; if (!o) return;
      const total = o.values.reduce((a,b)=>a+b,0);
      const perc = o.values.map(v => total ? (v/total)*100 : 0);
      const datasets = o.labels.map((label,i)=>({
        label, data:[perc[i]], backgroundColor: palette[i % palette.length], borderWidth:1
      }));
      if (chart) chart.destroy();
      chart = new Chart(ctx, {
        type: 'bar',
        data: { labels: [pretty(key).toUpperCase()], datasets },
        options: {
          responsive:true, maintainAspectRatio:false, indexAxis:'y',
          scales:{ x:{ stacked:true, min:0, max:100, ticks:{ callback:v=>v+'%' } }, y:{ stacked:true } },
          plugins:{
            legend:{ position:'bottom' },
            tooltip:{
              callbacks:{
                label: (ct) => {
                  const dsIdx = ct.datasetIndex;
                  const pct   = ct.parsed.x || 0;
                  const raw   = o.values[dsIdx];
                  return `${ct.dataset.label}: ${pct.toFixed(1)}% (${new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(raw)})`;
                },
                footer: () => `Total: ${new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(total)}`
              }
            }
          }
        }
      });
    }

    const initialKey = availableKeys.includes('main_categories') ? 'main_categories' : (availableKeys[0] || 'main_categories');
    if (selectEl) {
      selectEl.value = initialKey;
      selectEl.addEventListener('change', () => renderChart(selectEl.value));
    }
    renderChart(initialKey);
  })();

  // ---------- Inicializações finais ----------
  initializeToggleListeners();
});

