// --- JS do detalhamento do municipio (robusto a dados ausentes)
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

  // ---------- DATA PARSING (sem travar a página) ----------
  const allRevenueChartData = safeParseJSONById('chart-data');       // pode ser null
  const percentileData      = safeParseJSONById('percentile-data');  // pode ser null
  const municipioData       = safeParseJSONById('municipio-data');   // pode ser null

  // ---------- Toggle (setinhas) ----------
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
    const elements = scopeElement.querySelectorAll('.toggle-heading, .toggle-subheading');
    elements.forEach(el => {
      el.removeEventListener('click', handleToggleClick);
      el.addEventListener('click', handleToggleClick);
    });
  }

  // ---------- Ordenação ----------
  function parseCurrencyValue(str) {
    if (!str) return 0;
    return parseFloat(String(str).replace('R$', '').replace(/\./g, '').replace(',', '.').trim()) || 0;
  }

  function sortChildrenByValue(container, isPerCapita) {
    const children = Array.from(container.children);
    const selector = isPerCapita ? '.valor-per-capita' : '.valor-absoluto';
    children.sort((a, b) => parseCurrencyValue(b.querySelector(selector)?.textContent) - parseCurrencyValue(a.querySelector(selector)?.textContent));
    children.forEach(ch => container.appendChild(ch));
  }

  function sortAllRevenueSections(isPerCapita) {
    const containers = document.querySelectorAll('#main-revenue-details-container, [id^="detalhe-"]');
    containers.forEach(c => sortChildrenByValue(c, isPerCapita));
    initializeToggleListeners();
  }

  // ---------- Botão Per Capita / Valores Reais ----------
  let isShowingPerCapita = true;
  const toggleBtn = document.getElementById('valor-toggle-btn');
  const valoresAbsolutos = $$('.valor-absoluto');
  const valoresPerCapita = $$('.valor-per-capita');

  if (toggleBtn) {
    toggleBtn.addEventListener('click', function () {
      isShowingPerCapita = !isShowingPerCapita;
      toggleBtn.textContent = isShowingPerCapita ? 'Valores Reais' : 'Per Capita';
      valoresAbsolutos.forEach(el => el.classList.toggle('hidden', isShowingPerCapita));
      valoresPerCapita.forEach(el => el.classList.toggle('hidden', !isShowingPerCapita));
      sortAllRevenueSections(isShowingPerCapita);
    });
  }

  // Ordena já no load
  sortAllRevenueSections(isShowingPerCapita);

  // ---------- Ranking (só ativa se tiver os dados) ----------
  const rankingSelect = document.getElementById('ranking-select');
  const rankingValueElement = document.getElementById('ranking-value');
  const headerQuintilContainer = document.getElementById('header-quintil-indicator-container');

  function updateQuintilIndicator(element, percentile) {
    if (!element) return;
    element.classList.remove('quintil-1','quintil-2','quintil-3','quintil-4','quintil-5');
    if (percentile <= 20) element.classList.add('quintil-1');
    else if (percentile <= 40) element.classList.add('quintil-2');
    else if (percentile <= 60) element.classList.add('quintil-3');
    else if (percentile <= 80) element.classList.add('quintil-4');
    else element.classList.add('quintil-5');
  }

  function updateRankingUI(selectedRanking) {
    if (!rankingValueElement || !municipioData) return;

    let rank = 'N/A', total = 'N/A';
    if (selectedRanking === 'nacional') { rank = municipioData.rank_nacional; total = municipioData.total_nacional; }
    else if (selectedRanking === 'estadual') { rank = municipioData.rank_estadual; total = municipioData.total_estadual; }
    else if (selectedRanking === 'faixa') { rank = municipioData.rank_faixa; total = municipioData.total_faixa; }

    rankingValueElement.textContent = `${rank} / ${total}`;

    // Atualiza indicadores por item (se houver percentis)
    if (percentileData) {
      document.querySelectorAll('.revenue-item-wrapper').forEach(itemWrapper => {
        const fieldBase = itemWrapper.querySelector('[data-field-base]')?.dataset.fieldBase;
        const indicatorContainer = itemWrapper.querySelector('.ranking-indicator-container');
        const indicator = indicatorContainer?.querySelector('.ranking-indicator');
        const tooltip = indicatorContainer?.querySelector('.ranking-tooltip');

        const p = fieldBase && percentileData[fieldBase] ? percentileData[fieldBase][selectedRanking] : null;
        if (p != null) {
          updateQuintilIndicator(indicator, p);
          if (tooltip) tooltip.textContent = `O município supera ${p}% dos outros municípios`;
        } else {
          indicator?.classList.remove('quintil-1','quintil-2','quintil-3','quintil-4','quintil-5');
          if (tooltip) tooltip.textContent = 'Ranking não disponível';
        }
      });

      // Indicador principal (rc)
      const headerIndicator = headerQuintilContainer?.querySelector('.ranking-indicator');
      const headerTooltip   = headerQuintilContainer?.querySelector('.ranking-tooltip');
      const mainP = percentileData['rc'] ? percentileData['rc'][selectedRanking] : null;
      if (mainP != null) {
        updateQuintilIndicator(headerIndicator, mainP);
        if (headerTooltip) headerTooltip.textContent = `O município supera ${mainP}% dos outros municípios`;
      }
    }
  }

  if (rankingSelect) {
    rankingSelect.addEventListener('change', () => updateRankingUI(rankingSelect.value));
    // inicia UI (só se houver municipioData; se não houver, não quebra nada)
    updateRankingUI(rankingSelect.value || 'nacional');
  }
});
