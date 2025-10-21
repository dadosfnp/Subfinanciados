// detail/static/detail/js/script_mun.js
document.addEventListener('DOMContentLoaded', function () {
  // ===== Config & helpers =====
  const DEBUG = false;
  const log  = (...a) => DEBUG && console.log('[detail-mun]', ...a);
  const warn = (...a) => DEBUG && console.warn('[detail-mun]', ...a);

  const $  = (sel, root=document) => root.querySelector(sel);
  const $$ = (sel, root=document) => Array.from(root.querySelectorAll(sel));

  // ----- leitura de JSON (rankings: ler texto e normalizar inteiros) -----
  function getJsonText(id){ const el = document.getElementById(id); return (el && el.textContent) ? el.textContent.trim() : ''; }
  function parseRankingDataFromText(id){
    const txt = getJsonText(id); if (!txt) return null;
    const keys = ['rank_nacional','total_nacional','rank_estadual','total_estadual','rank_faixa','total_faixa'];
    const out = {};
    for (const k of keys){
      const re = new RegExp(`"${k}"\\s*:\\s*([^,}\\n\\r]+)`); const m = txt.match(re);
      if (!m){ out[k] = null; continue; }
      const raw = m[1].trim(); if (/^null$/i.test(raw)) { out[k] = null; continue; }
      const unq = raw.replace(/^"(.*)"$/, '$1'); const digitsOnly = unq.replace(/\D+/g, '');
      out[k] = digitsOnly ? parseInt(digitsOnly, 10) : null;
    }
    return out;
  }

  function safeParseJSONById(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    const txt = el.textContent?.trim();
    if (!txt) return null;
    try { let v = JSON.parse(txt); if (typeof v === 'string') v = JSON.parse(v); return v; }
    catch { return null; }
  }

  // ===== Normalizadores =====
  const normalize = (str) => (str||'')
    .normalize('NFD').replace(/\p{Diacritic}/gu,'')
    .replace(/R\$\s?[\d\.,]+/g,' ')
    .replace(/[\d\.,]+/g,' ')
    .replace(/\s+/g,' ')
    .trim().toLowerCase();

  const cleanText = (h) => {
    if (!h) return '';
    const c = h.cloneNode(true);
    c.querySelectorAll('.valor-absoluto,.valor-per-capita,.ranking-indicator-container').forEach(n=>n.remove());
    return (c.textContent || h.textContent || '').trim();
  };

  // ===== Formatação numérica =====
  const fmtInt = (n) => (Number.isFinite(n) ? new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 }).format(n) : '—');

  // ===== Dados =====
  const allRevenueChartData = safeParseJSONById('chart-data');
  const percentileData      = safeParseJSONById('percentile-data');
  const municipioData       = parseRankingDataFromText('municipio-data'); // única fonte para ranking

  // 🔑 heading -> key de percentis
  const HEADING_TO_KEY = {
    'receita corrente': 'rc',
    'transferencias correntes': 'transferencias_correntes',
    'transferencias da uniao': 'transferencias_uniao',
    'transferencias dos estados': 'transferencias_estado',
    'outras transferencias': 'outras_transferencias',
    'impostos, taxas e contribuicoes de melhoria': 'imposto_taxas_contribuicoes',
    'impostos': 'imposto',
    'taxas': 'taxas',
    'contribuicoes de melhoria': 'contribuicoes_melhoria',
    'outras receitas correntes': 'outras_receitas',
    'contribuicoes': 'contribuicoes'
  };

  // ===== Indicador (cores + tooltip) =====
  function paintIndicator(container, percentile) {
    if (!container || !Number.isFinite(percentile)) return;
    const ind = container.querySelector('.ranking-indicator') || container;
    const tip = container.querySelector('.ranking-tooltip');

    ind.classList.remove('quintil-1','quintil-2','quintil-3','quintil-4','quintil-5');
    if (percentile <= 20) ind.classList.add('quintil-1');
    else if (percentile <= 40) ind.classList.add('quintil-2');
    else if (percentile <= 60) ind.classList.add('quintil-3');
    else if (percentile <= 80) ind.classList.add('quintil-4');
    else ind.classList.add('quintil-5');

    if (tip) tip.textContent = `O município supera ${percentile}% dos outros municípios`;
  }

  // ===== Toggle (setinhas) =====
  function handleToggleClick(e){
    e.stopPropagation();
    const id = this.dataset.target;
    const tgt = id && document.getElementById(id);
    if (tgt){ this.classList.toggle('open'); tgt.classList.toggle('hidden'); }
  }
  function initializeToggleListeners(scope=document){
    $$('.toggle-heading, .toggle-subheading', scope).forEach(el=>{
      el.removeEventListener('click', handleToggleClick);
      el.addEventListener('click', handleToggleClick);
    });
  }

  // ===== Ordenação =====
  const toNum = s => {
    if (!s) return 0;
    const n = parseFloat(String(s).replace('R$','').replace(/\./g,'').replace(',','.'));
    return Number.isFinite(n) ? n : 0;
  };
  function sortChildrenByValue(container, perCapita){
    const sel = perCapita ? '.valor-per-capita' : '.valor-absoluto';
    const kids = Array.from(container.children);
    kids.sort((a,b)=> toNum(b.querySelector(sel)?.textContent) - toNum(a.querySelector(sel)?.textContent));
    kids.forEach(k=>container.appendChild(k));
  }
  function sortAll(perCapita){
    $$('#main-revenue-details-container, [id^="detalhe-"]').forEach(c=>sortChildrenByValue(c, perCapita));
    initializeToggleListeners();
    buildHeadingIndex();
  }

  // ===== PC/VR =====
  const segmented = $('#valor-toggle');
  function showMode(m){
    const pc = m === 'pc';
    segmented?.querySelector('[data-mode="pc"]')?.classList.toggle('active', pc);
    segmented?.querySelector('[data-mode="vr"]')?.classList.toggle('active', !pc);
    $$('.valor-per-capita').forEach(el=>el.classList.toggle('hidden', !pc));
    $$('.valor-absoluto').forEach(el=>el.classList.toggle('hidden', pc));
    sortAll(pc);
  }
  segmented?.querySelector('[data-mode="pc"]')?.addEventListener('click', ()=>showMode('pc'));
  segmented?.querySelector('[data-mode="vr"]')?.addEventListener('click', ()=>showMode('vr'));

  // ===== Índice de headings =====
  let headingIndex = new Map();
  function buildHeadingIndex(scope=document){
    headingIndex.clear();
    $$('#main-revenue-details-container .toggle-heading, #main-revenue-details-container .toggle-subheading', scope)
      .forEach(h=>{
        const key = normalize(cleanText(h));
        const id  = h.dataset.target;
        const ct  = id ? document.getElementById(id) : null;
        if (key) headingIndex.set(key, { header: h, content: ct, targetId: id });
      });
  }

  function openByLabel(label){
    if (!label) return false;
    const needle = normalize(label);
    if (headingIndex.has(needle)) {
      const entry = headingIndex.get(needle);
      const parentToggle = entry.header.closest('.revenue-section')?.querySelector?.('.toggle-heading');
      if (parentToggle && parentToggle !== entry.header) {
        const pid = parentToggle.dataset.target;
        if (pid){ document.getElementById(pid)?.classList.remove('hidden'); parentToggle.classList.add('open'); }
      }
      entry.content?.classList.remove('hidden');
      entry.header.classList.add('open');
      entry.header.scrollIntoView({ behavior:'smooth', block:'center' });
      return true;
    }
    return false;
  }

  // ===== Ranking (cores + texto) =====
  function updateRankingUI(selected) {
    // cores (percentis)
    if (percentileData) {
      const headerBox = $('#header-quintil-indicator-container');
      const pHeader = percentileData.rc ? percentileData.rc[selected] : null;
      if (Number.isFinite(pHeader)) paintIndicator(headerBox, pHeader);

      $$('.revenue-item-wrapper').forEach(wrap => {
        let key = wrap.querySelector('[data-field-base]')?.dataset.fieldBase;
        if (!key) {
          const heading = wrap.querySelector('.toggle-heading');
          const txt = normalize(cleanText(heading));
          key = HEADING_TO_KEY[txt];
        }
        const pct = key && percentileData[key] ? percentileData[key][selected] : null;
        const container = wrap.querySelector('.ranking-indicator-container');
        if (Number.isFinite(pct)) {
          paintIndicator(container, pct);
        } else if (container) {
          const ind = container.querySelector('.ranking-indicator');
          ind?.classList.remove('quintil-1','quintil-2','quintil-3','quintil-4','quintil-5');
          const tip = container.querySelector('.ranking-tooltip');
          if (tip) tip.textContent = 'Ranking não disponível';
        }
      });
    }

    // texto “X / Y”
    const rankingValueEl = $('#ranking-value');
    if (rankingValueEl && municipioData) {
      const map = {
        nacional: ['rank_nacional','total_nacional'],
        estadual: ['rank_estadual','total_estadual'],
        faixa:    ['rank_faixa','total_faixa'],
      };
      const [rkKey, totKey] = map[selected] || map.nacional;
      const rk  = municipioData?.[rkKey];
      const tot = municipioData?.[totKey];
      if (Number.isFinite(rk) && Number.isFinite(tot)) {
        rankingValueEl.textContent = `${fmtInt(rk)} / ${fmtInt(tot)}`;
      } else {
        rankingValueEl.textContent = '—';
      }
    }
  }

  const rankingSelect = $('#ranking-select');
  rankingSelect?.addEventListener('change', () => updateRankingUI(rankingSelect.value || 'nacional'));

  // ===== Chart.js (COMPOSIÇÃO) =====
  const canvas = $('#myChart');
  if (!canvas){ console.error('Canvas #myChart não encontrado'); return; }
  if (!window.Chart){ console.error('Chart.js não carregado'); return; }
  canvas.style.cursor = 'pointer';
  const ctx = canvas.getContext('2d');

  const pretty = k => ({
    main_categories:'Categorias Principais',
    // imposto_taxas_contribuicoes REMOVIDO do select
    imposto:'___ Impostos',
    taxas:'___ Taxas',
    contribuicoes_melhoria:'___ Contribuições de Melhoria',
    contribuicoes:'Contribuições',
    transferencias_correntes:'Transferências Correntes',
    transferencias_uniao:'___ Transferências da União',
    transferencias_estado:'___ Transferências dos Estados',
    outras_receitas:'Outras Receitas'
  }[k] || k.replace(/_/g,' '));

  // cores fixas para as 4 principais
  const COLOR_BY_LABEL = {
    'ITC': '#1f77b4',
    'Contribuições': '#ff7f0e',
    'Transf. Correntes': '#2ca02c',
    'Outras': '#d62728'
  };
  const palette = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd','#8c564b','#e377c2','#7f7f7f','#bcbd22','#17becf'];

  // mapping clique -> chave do select
  const MAIN_TO_KEY = {
    'ITC': 'imposto',                        // agora abre ___ Impostos
    'Contribuições': 'contribuicoes',
    'Transf. Correntes': 'transferencias_correntes',
    'Outras': 'outras_receitas'
  };

  // chaves disponíveis (exclui 'imposto_taxas_contribuicoes')
  const order = [
    'main_categories','imposto','taxas','contribuicoes_melhoria','contribuicoes',
    'transferencias_correntes','transferencias_uniao','transferencias_estado','outras_receitas'
  ];
  const availableKeys = (() => {
    if (!allRevenueChartData || typeof allRevenueChartData !== 'object') return [];
    const first = order.filter(k => {
      const o = allRevenueChartData[k];
      return o && Array.isArray(o.labels) && o.labels.length &&
             Array.isArray(o.values) && o.values.length;
    });
    if (first.length) return first;
    return Object.entries(allRevenueChartData)
      .filter(([, o]) => o && Array.isArray(o.labels) && o.labels.length && Array.isArray(o.values) && o.values.length)
      .map(([k]) => k)
      .filter(k => k !== 'imposto_taxas_contribuicoes'); // garante a remoção
  })();

  // select de categorias
  const selectEl = document.getElementById('chart-category-select');
  if (selectEl) {
    selectEl.innerHTML = '';
    (availableKeys.length ? availableKeys : ['main_categories']).forEach(k => {
      const opt = document.createElement('option');
      opt.value = k; opt.textContent = pretty(k);
      selectEl.appendChild(opt);
    });
  }
  const initialKey = availableKeys.includes('main_categories') ? 'main_categories' : (availableKeys[0] || 'main_categories');
  if (selectEl) {
    selectEl.value = initialKey;
    selectEl.addEventListener('change', () => renderChart(selectEl.value));
  }

  let chart;
 
  function setCategoryAndSync(key){
    if (!selectEl) return;
    selectEl.value = key;
    renderChart(key);                                 // atualiza o gráfico de composição
    selectEl.dispatchEvent(new Event('change', {     // dispara p/ densidade redesenhar
      bubbles: true
    }));
  }
  
  // renderiza como BARRAS HORIZONTAIS (cada categoria é uma linha do eixo Y)
  function renderChart(key){
    const d = allRevenueChartData?.[key];
    if (!d){ warn('chave não encontrada no chart-data:', key); return; }
    if (!Array.isArray(d.labels) || !Array.isArray(d.values)){ warn('estrutura inesperada:', d); return; }

    const total = d.values.reduce((a,b)=>a+b,0);
    const perc  = d.values.map(v=> total ? (v/total)*100 : 0);

    // labels no eixo Y = cada categoria/item
    const labels = d.labels.slice();
    const background = labels.map((lbl,i)=> COLOR_BY_LABEL[lbl] || palette[i%palette.length]);

    const dataset = {
      label: pretty(key).toUpperCase(),
      data: perc,
      backgroundColor: background,
      borderWidth: 1,
    };

    if (chart) chart.destroy();
    chart = new Chart(ctx, {
      type:'bar',
      data:{ labels, datasets: [dataset] },
      options:{
        responsive:true, maintainAspectRatio:false, indexAxis:'y',
        scales:{
          x:{ min:0, max:100, ticks:{ callback:v=>v+'%' } },
          y:{ ticks:{ autoSkip:false } }
        },
        plugins:{
          legend:{ display:false }, // <<< legenda desligada
          tooltip:{ callbacks:{
            label:(ct)=>{
              const i = ct.dataIndex;
              const raw = d.values[i];
              const pct = ct.parsed.x || 0;
              return `${labels[i]}: ${pct.toFixed(1)}% (${new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(raw)})`;
            },
            footer:()=>`Total: ${new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(total)}`
          }}
        }
      }
    });

    // clique:
    canvas.onclick = (evt) => {
      const pts = chart.getElementsAtEventForMode(evt, 'nearest', { intersect: true }, true);
      if (!pts.length) return;
      const idx = pts[0].index;
      const clickedLabel = labels[idx];

      // === Categorias Principais ===
      if (key === 'main_categories') {
        const nextKey = MAIN_TO_KEY[clickedLabel];
        if (nextKey) {
          setCategoryAndSync(nextKey);
        }
        return;
      }

      // === Transferências Correntes ===
      if (key === 'transferencias_correntes') {
        const l = normalize(clickedLabel);
        if (l.includes('uniao')) {
          setCategoryAndSync('transferencias_uniao');
          return;
        }
        if (l.includes('estado') || l.includes('estados')) {
          setCategoryAndSync('transferencias_estado');
          return;
        }
        // outras transferências: mantém comportamento antigo (abrir seção)
        openByLabel(clickedLabel);
        return;
      }

      // demais chaves: manter atalho de abrir seção
      openByLabel(clickedLabel);
    };
  }

  // ===== Inicializações =====
  buildHeadingIndex();
  showMode('pc');
  renderChart(initialKey);
  initializeToggleListeners();
  updateRankingUI(rankingSelect?.value || 'nacional');
});
