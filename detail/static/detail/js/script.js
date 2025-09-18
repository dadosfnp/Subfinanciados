document.addEventListener('DOMContentLoaded', function() {
  // ======================== HELPERS ========================
  function parsePossiblyMultiSerialized(text) {
    let out = text;
    try { out = JSON.parse(out); } catch { return text; }
    while (typeof out === 'string') {
      try { out = JSON.parse(out); } catch { break; }
    }
    return out;
  }

  function handleToggleClick(event) {
    event.stopPropagation();
    const targetId = this.dataset.target;
    if (!targetId) return;
    const targetElement = document.getElementById(targetId);
    if (targetElement) {
      this.classList.toggle('open');
      targetElement.classList.toggle('hidden');
    }
  }

  function initializeToggleListeners(scopeElement = document) {
    const toggleElements = scopeElement.querySelectorAll('.toggle-heading, .toggle-subheading');
    toggleElements.forEach(el => {
      el.removeEventListener('click', handleToggleClick);
      el.addEventListener('click', handleToggleClick);
    });
  }

  function parseCurrencyValue(str) {
    if (!str) return 0;
    return parseFloat(str.replace('R$', '').replace(/\./g, '').replace(',', '.').trim());
  }

  function sortChildrenByValue(container, isPerCapita) {
    const children = Array.from(container.children);
    children.sort((a, b) => {
      const sel = isPerCapita ? '.valor-per-capita' : '.valor-absoluto';
      const valA = parseCurrencyValue(a.querySelector(sel)?.textContent);
      const valB = parseCurrencyValue(b.querySelector(sel)?.textContent);
      return valB - valA;
    });
    children.forEach(child => container.appendChild(child));
  }

  function sortAllRevenueSections(isPerCapita) {
    const containers = document.querySelectorAll('#main-revenue-details-container, [id^="detalhe-"]');
    containers.forEach(container => sortChildrenByValue(container, isPerCapita));
    initializeToggleListeners();
  }

  // Preserva seleção se existir; senão cai para 'todos'
  function restoreSelectValue(selectEl, value) {
    const has = Array.from(selectEl.options).some(o => o.value === value);
    selectEl.value = has ? value : 'todos';
  }

  // ======================== ELEMENTOS DA PÁGINA ========================
  const dataEl = document.getElementById('chart-data');
  if (!dataEl) {
    console.error("[chart] #chart-data não encontrado");
    return;
  }

  const filtroRegiao = document.getElementById('filtro-regiao');
  const filtroUf     = document.getElementById('filtro-uf');
  const filtroPorte  = document.getElementById('filtro-porte');
  const filtroRm     = document.getElementById('filtro-rm');

  const toggleBtn = document.getElementById('valor-toggle-btn');
  let isShowingPerCapita = true;

  // ======================== JSON INICIAL ========================
  let initialChartData = null;
  try {
    initialChartData = parsePossiblyMultiSerialized(dataEl.textContent);
  } catch (e) {
    console.error('[chart] Falha ao parsear JSON inicial:', e);
    return;
  }

  // ======================== TOGGLE VALOR/PER CAPITA ========================
  if (toggleBtn) {
    toggleBtn.addEventListener('click', function() {
      isShowingPerCapita = !isShowingPerCapita;
      this.textContent = isShowingPerCapita ? 'Valores Reais' : 'Per Capita';
      const valoresAbsolutos = document.querySelectorAll('.valor-absoluto');
      const valoresPerCapita = document.querySelectorAll('.valor-per-capita');
      valoresAbsolutos.forEach(el => el.classList.toggle('hidden', isShowingPerCapita));
      valoresPerCapita.forEach(el => el.classList.toggle('hidden', !isShowingPerCapita));
      sortAllRevenueSections(isShowingPerCapita);
    });
  }

  // ======================== FILTROS / KPIs / DETALHES ========================
  // Agora SEMPRE usa lista completa e NÃO existe município
  async function updateDependentFilters() {
    if (!filtroRegiao || !filtroUf || !filtroRm) return;

    const regiaoAtual = filtroRegiao.value;
    const ufAtual     = filtroUf.value;
    const rmAtual     = filtroRm.value;

    try {
      // IMPORTANTE: alguns backends só devolvem listas “cheias” se você mandar os 3 = todos
      const url = '/api/get-dependent-filters/?regiao=todos&uf=todos&rm=todos';
      const response = await fetch(url);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      // debug opcional:
      // console.log('[dependent-filters]', data);

      // Região
      filtroRegiao.innerHTML = '<option value="todos">Todas</option>';
      (data.regioes || []).forEach(item => filtroRegiao.add(new Option(item, item)));
      restoreSelectValue(filtroRegiao, regiaoAtual);

      // RM
      filtroRm.innerHTML = '<option value="todos">Todos</option>';
      (data.rms || []).forEach(item => filtroRm.add(new Option(item, item)));
      restoreSelectValue(filtroRm, rmAtual);

      // UF
      filtroUf.innerHTML = '<option value="todos">Todas</option>';
      (data.ufs || []).forEach(item => filtroUf.add(new Option(item, item)));
      restoreSelectValue(filtroUf, ufAtual);

    } catch (error) {
      console.error("[filtros] Erro ao atualizar filtros (listas completas):", error);
    }
  }

  // Monta params (sem município)
  function buildParams() {
    const params = new URLSearchParams();
    params.set('porte',   filtroPorte?.value  || 'todos');
    params.set('rm',      filtroRm?.value     || 'todos');
    params.set('regiao',  filtroRegiao?.value || 'todos');
    params.set('uf',      filtroUf?.value     || 'todos');
    return params;
  }

  async function updateKPIs() {
    try {
      const response = await fetch(`/api/dados-detalhados/?${buildParams()}`);
      const data = await response.json();
      document.getElementById('kpi-populacao').textContent =
        (data.kpis?.populacao || 0).toLocaleString('pt-BR');
      document.getElementById('kpi-quantidade').textContent =
        (data.kpis?.quantidade || 0).toLocaleString('pt-BR');
      document.getElementById('kpi-receita-per-capita').textContent =
        (data.kpis?.receita_per_capita || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
      document.getElementById('kpi-diferenca-media').textContent =
        (data.kpis?.diferenca_media || 0).toLocaleString('pt-BR', { style: 'percent', minimumFractionDigits: 2 });
    } catch (error) {
      console.error("[kpis] Erro:", error);
    }
  }

  async function updateFiscalDetails() {
    try {
      const response = await fetch(`/api/fiscal-details/?${buildParams()}`);
      if (!response.ok) throw new Error('Falha ao buscar detalhes fiscais.');
      const data = await response.json();
      const container = document.getElementById('main-revenue-details-container');
      container.innerHTML = data.html;
      initializeToggleListeners(container);
      sortAllRevenueSections(isShowingPerCapita);
    } catch (error) {
      console.error("[detalhes] Erro:", error);
      const cont = document.getElementById('main-revenue-details-container');
      if (cont) cont.innerHTML = '<p class="text-red-500 text-center py-4">Erro ao carregar os dados.</p>';
    }
  }

  // ======================== GRÁFICO (Chart.js) ========================
  const canvas = document.getElementById('myChart');
  if (!canvas) {
    console.warn('[chart] Canvas #myChart não encontrado');
    return;
  }
  const ctx = canvas.getContext('2d');
  const selectEl = document.getElementById('chart-category-select');
  const palette = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd','#8c564b','#e377c2','#7f7f7f','#bcbd22','#17becf'];
  let chartInstance = null;
  let currentChartData = initialChartData; // Inicia com os dados da página

  async function updateChart() {
    try {
      const response = await fetch(`/api/conjunto-chart-data/?${buildParams()}`);
      if (!response.ok) throw new Error('Falha ao buscar dados do gráfico.');
      currentChartData = await response.json();
      renderChart(selectEl.value, currentChartData);
    } catch (error) {
      console.error("[chart] Erro ao atualizar dados do gráfico:", error);
    }
  }

  function renderChart(categoryKey, allRevenueChartData) {
    if (!allRevenueChartData) {
      console.error('[chart] Dados do gráfico não disponíveis.');
      return;
    }
    const dataObj = allRevenueChartData[categoryKey];
    if (!dataObj || !Array.isArray(dataObj.labels) || !Array.isArray(dataObj.values)) {
      console.error(`[chart] Estrutura inesperada em ${categoryKey}`, dataObj);
      if (chartInstance) chartInstance.destroy();
      return;
    }

    const rawValues = dataObj.values.map(v => Number(v) || 0);
    const total = rawValues.reduce((a, b) => a + b, 0);

    const filteredData = dataObj.labels.map((label, i) => ({
      label, value: rawValues[i]
    })).filter(item => item.value > 0);
    
    const finalLabels = filteredData.map(item => item.label);
    const finalValues = filteredData.map(item => item.value);
    const percValues = finalValues.map(v => total ? (v / total) * 100 : 0);

    const datasets = finalLabels.map((label, i) => ({
      label,
      data: [percValues[i]],
      backgroundColor: palette[i % palette.length],
      borderWidth: 1
    }));

    if (chartInstance) chartInstance.destroy();

    chartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: [(selectEl?.options[selectEl.selectedIndex]?.text || 'Categoria').toUpperCase()],
        datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        scales: {
          x: { stacked: true, min: 0, max: 100, ticks: { callback: v => v + '%' } },
          y: { stacked: true }
        },
        plugins: {
          legend: { position: 'bottom' },
          tooltip: {
            callbacks: {
              label: (ctx) => {
                const dsIdx = ctx.datasetIndex;
                const pct = ctx.parsed.x ?? 0;
                const raw = finalValues[dsIdx];
                const fmtBRL = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });
                return `${ctx.dataset.label}: ${pct.toFixed(1)}% (${fmtBRL.format(raw)})`;
              },
              footer: () => {
                const fmtBRL = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });
                return `Total: ${fmtBRL.format(total)}`;
              }
            }
          }
        }
      }
    });
  }

  if (selectEl) {
    selectEl.addEventListener('change', () => renderChart(selectEl.value, currentChartData));
  }
  
  // Renderiza o gráfico inicial
  renderChart(selectEl?.value || 'main_categories', initialChartData);

  // ======================== FUNÇÃO PRINCIPAL DE ATUALIZAÇÃO ========================
  async function applyFilters() {
    await Promise.all([
      updateKPIs(),
      updateFiscalDetails(),
      updateChart()
    ]);
  }

  // ======================== INICIALIZAÇÃO ========================
  // Mudanças: NÃO repovoar selects; apenas atualizar dados
  if (filtroRegiao) filtroRegiao.addEventListener('change', () => { applyFilters(); });
  if (filtroUf)     filtroUf.addEventListener('change',     () => { applyFilters(); });
  if (filtroRm)     filtroRm.addEventListener('change',     () => { applyFilters(); });
  if (filtroPorte)  filtroPorte.addEventListener('change',  applyFilters);

  const btnLimpar = document.getElementById('btn-limpar-filtros');
  if (btnLimpar) {
    btnLimpar.addEventListener('click', function() {
      if (filtroRegiao) filtroRegiao.value = 'todos';
      if (filtroRm)     filtroRm.value     = 'todos';
      if (filtroUf)     filtroUf.value     = 'todos';
      if (filtroPorte)  filtroPorte.value  = 'todos';
      updateDependentFilters(); // repovoa com listas completas
      applyFilters();
    });
  }

  // Primeira carga: popula listas completas e aplica filtros
  updateDependentFilters();
  applyFilters();
});
