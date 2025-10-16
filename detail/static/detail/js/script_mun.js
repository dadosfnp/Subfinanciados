// detail/static/detail/js/script_mun.js
document.addEventListener('DOMContentLoaded', function () {
  // ===== Config & helpers =====
  const DEBUG = false;
  const log  = (...a) => DEBUG && console.log('[detail-mun]', ...a);
  const warn = (...a) => DEBUG && console.warn('[detail-mun]', ...a);

  const $  = (sel, root=document) => root.querySelector(sel);
  const $$ = (sel, root=document) => Array.from(root.querySelectorAll(sel));

  function safeParseJSONById(id) {
    const el = document.getElementById(id);
    if (!el) { warn(`Elemento #${id} não encontrado`); return null; }
    const txt = el.textContent?.trim();
    if (!txt) { warn(`#${id} vazio`); return null; }
    try {
      let v = JSON.parse(txt);
      if (typeof v === 'string') v = JSON.parse(v); // tolera dupla serialização
      return v;
    } catch (e) {
      console.error(`Falha ao parsear #${id}:`, e, txt.slice(0, 120) + '...');
      return null;
    }
  }

  // normaliza textos de headings
  const normalize = (str) => (str||'')
    .normalize('NFD').replace(/\p{Diacritic}/gu,'')
    .replace(/R\$\s?[\d\.,]+/g,' ')   // tira valores
    .replace(/[\d\.,]+/g,' ')
    .replace(/\s+/g,' ')
    .trim().toLowerCase();

  const cleanText = (h) => {
    if (!h) return '';
    const c = h.cloneNode(true);
    c.querySelectorAll('.valor-absoluto,.valor-per-capita,.ranking-indicator-container').forEach(n=>n.remove());
    return (c.textContent || h.textContent || '').trim();
  };

  // 🔑 mapa heading -> chave do JSON de percentis
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

  // pinta a caixinha + tooltip conforme percentil
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

  // ===== Dados =====
  const allRevenueChartData = safeParseJSONById('chart-data');
  const percentileData      = safeParseJSONById('percentile-data');
  log('chart-data keys:', allRevenueChartData && Object.keys(allRevenueChartData));

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
    log('headings indexados:', Array.from(headingIndex.keys()));
  }

  function openByLabel(label){
    if (!label) return false;
    const needle = normalize(label);

    // 1) match exato direto no índice
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

    // 2) ranking de similaridade (whole-word > startsWith > includes)
    let best = null;
    let bestScore = Infinity;

    // util: score do match
    const scoreFor = (k) => {
      const K = ` ${k} `;
      const N = ` ${needle} `;
      if (K.includes(N)) return 1;                      // palavra inteira
      if (k.startsWith(needle) || needle.startsWith(k)) return 2;
      if (k.includes(needle)) return 3;
      return 99;
    };

    for (const [k, v] of headingIndex) {
      // evita confundir "Contribuições" com "Contribuições de Melhoria"
      if (needle === 'contribuicoes' && k.includes('contribuicoes de melhoria')) continue;

      const s = scoreFor(k);
      if (s < bestScore || (s === bestScore && k.length < (best?.key.length || 1))) {
        best = { entry: v, key: k, score: s };
        bestScore = s;
      }
    }

    if (!best || bestScore >= 99) { 
      warn('heading não encontrado p/ label:', label); 
      return false; 
    }

    // abre alvo + pai se precisar
    const entry = best.entry;
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


  // ===== Ranking (pinta os quadradinhos) =====
  function updateRankingUI(selected) {
    if (!percentileData) return;

    // Header (RC)
    const headerBox = $('#header-quintil-indicator-container');
    const pHeader = percentileData.rc ? percentileData.rc[selected] : null;
    if (Number.isFinite(pHeader)) paintIndicator(headerBox, pHeader);

    // Linhas
    $$('.revenue-item-wrapper').forEach(wrap => {
      // 1) se existir, usa data-field-base
      let key = wrap.querySelector('[data-field-base]')?.dataset.fieldBase;

      // 2) senão, deriva pelo texto do heading
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

  const rankingSelect = $('#ranking-select');
  console.log('rankingSelect:', rankingSelect);
  rankingSelect?.addEventListener('change', () => updateRankingUI(rankingSelect.value || 'nacional'));

  // ===== Chart.js =====
  const canvas = $('#myChart');
  if (!canvas){ console.error('Canvas #myChart não encontrado'); return; }
  if (!window.Chart){ console.error('Chart.js não carregado'); return; }
  canvas.style.cursor = 'pointer';
  const ctx = canvas.getContext('2d');

  const pretty = k => ({
    main_categories:'Categorias Principais',
    imposto_taxas_contribuicoes:'Impostos, Taxas e Contribuições de Melhoria',
    imposto:'___ Impostos',
    taxas:'___ Taxas',
    contribuicoes_melhoria:'___ Contribuições de Melhoria',
    contribuicoes:'Contribuições',
    transferencias_correntes:'Transferências Correntes',
    transferencias_uniao:'___ Transferências da União',
    transferencias_estado:'___ Transferências dos Estados',
    outras_receitas:'Outras Receitas'
  }[k] || k.replace(/_/g,' '));

  const order = [
    'main_categories','imposto_taxas_contribuicoes','imposto','taxas', 'contribuicoes_melhoria', 'contribuicoes',
    'transferencias_correntes','transferencias_uniao','transferencias_estado','outras_receitas'
  ];

  // chaves disponíveis
  const availableKeys = (() => {
    if (!allRevenueChartData || typeof allRevenueChartData !== 'object') return [];
    const first = order.filter(k => {
      const o = allRevenueChartData[k];
      return o && Array.isArray(o.labels) && o.labels.length &&
             Array.isArray(o.values) && o.values.length;
    });
    if (first.length) return first;
    return Object.entries(allRevenueChartData)
      .filter(([, o]) =>
        o && Array.isArray(o.labels) && o.labels.length &&
        Array.isArray(o.values) && o.values.length
      )
      .map(([k]) => k);
  })();

  console.log('availableKeys:', availableKeys);

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

  const initialKey = availableKeys.includes('main_categories')
    ? 'main_categories'
    : (availableKeys[0] || 'main_categories');

  if (selectEl) {
    selectEl.value = initialKey;
    selectEl.addEventListener('change', () => renderChart(selectEl.value));
  }

  // “caminho” para abrir a seção ao clicar no gráfico
  const PATH_HINTS = {
    'CATEGORIAS PRINCIPAIS': {
      'ITC':['Impostos, Taxas e Contribuições de Melhoria'],
      'Contribuições':['Contribuições'],
      'Transf. Correntes':['Transferências Correntes'],
      'Outras':['Outras Receitas Correntes'],
    },
    'IMPOSTOS': {
      'IPTU':['Impostos','IPTU'],
      'ITBI':['Impostos','ITBI'],
      'ISS':['Impostos','ISS'],
      'Outros':['Impostos','Outros'],
    },
    'TAXAS': {
      'Taxas pela Prestação de Serviços':['Impostos, Taxas e Contribuições de Melhoria','Taxas','Taxas pela Prestação de Serviços'],
      'Taxas pelo Exercício do Poder de Polícia':['Impostos, Taxas e Contribuições de Melhoria','Taxas','Taxas pelo Exercício do Poder de Polícia'],
      'Outras Taxas':['Impostos, Taxas e Contribuições de Melhoria','Taxas','Outras Taxas'],
    },
    'CONTRIBUIÇÕES': { 'Outras':['Contribuições'] },
    'TRANSFERÊNCIAS CORRENTES': {
      'Transferências da União':['Transferências Correntes','Transferências da União'],
      'Transferências dos Estados':['Transferências Correntes','Transferências dos Estados'],
      'Outras Transferências':['Transferências Correntes','Outras Transferências'],
    },
    'OUTRAS RECEITAS': {
      'Receita Patrimonial':['Outras Receitas Correntes','Receita Patrimonial'],
      'Outras Receitas':['Outras Receitas Correntes','Outras Receitas'],
      'Receita de Serviços':['Outras Receitas Correntes','Receita de Serviços'],
      'Receita Agropecuária':['Outras Receitas Correntes','Receita Agropecuária'],
      'Receita Industrial':['Outras Receitas Correntes','Receita Industrial'],
    }
  };

  function resolvePath(groupLabel, segmentLabel){
    const g = normalize(groupLabel).toUpperCase();
    let key;
    if (g.includes('CATEGORIAS PRINCIPAIS')) key = 'CATEGORIAS PRINCIPAIS';
    else if (g.includes('IMPOSTOS')) key = 'IMPOSTOS';
    else if (g.includes('TAXAS')) key = 'TAXAS';
    else if (g.includes('CONTRIBUI')) key = 'CONTRIBUIÇÕES';
    else if (g.includes('TRANSFER')) key = 'TRANSFERÊNCIAS CORRENTES';
    else if (g.includes('OUTRAS')) key = 'OUTRAS RECEITAS';

    const table = key && PATH_HINTS[key];
    if (table){
      for (const k of Object.keys(table)){
        if (normalize(k) === normalize(segmentLabel)) return table[k];
      }
      for (const k of Object.keys(table)){
        if (normalize(k).includes(normalize(segmentLabel)) || normalize(segmentLabel).includes(normalize(k)))
          return table[k];
      }
      if (key === 'IMPOSTOS') return ['Impostos'];
      if (key === 'TAXAS') return ['Impostos, Taxas e Contribuições de Melhoria','Taxas'];
      if (key === 'CONTRIBUIÇÕES') return ['Contribuições'];
      if (key === 'TRANSFERÊNCIAS CORRENTES') return ['Transferências Correntes'];
      if (key === 'OUTRAS RECEITAS') return ['Outras Receitas Correntes'];
      if (key === 'CATEGORIAS PRINCIPAIS') return ['Impostos, Taxas e Contribuições de Melhoria'];
    }
    return null;
  }

  // ===== Chart render =====
  const palette = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd','#8c564b','#e377c2','#7f7f7f','#bcbd22','#17becf'];
  let chart;

  function renderChart(key){
    const d = allRevenueChartData?.[key];
    if (!d){ warn('chave não encontrada no chart-data:', key); return; }
    if (!Array.isArray(d.labels) || !Array.isArray(d.values)){ warn('estrutura inesperada:', d); return; }

    const total = d.values.reduce((a,b)=>a+b,0);
    const perc  = d.values.map(v=> total ? (v/total)*100 : 0);
    const datasets = d.labels.map((label,i)=>({
      label, data:[perc[i]], backgroundColor: palette[i%palette.length], borderWidth:1
    }));

    if (chart) chart.destroy();
    chart = new Chart(ctx, {
      type:'bar',
      data:{ labels:[pretty(key).toUpperCase()], datasets },
      options:{
        responsive:true, maintainAspectRatio:false, indexAxis:'y',
        scales:{ x:{stacked:true,min:0,max:100,ticks:{callback:v=>v+'%'}}, y:{stacked:true} },
        plugins:{
          legend:{position:'bottom'},
          tooltip:{callbacks:{
            label:(ct)=>{
              const i = ct.datasetIndex;
              const raw = d.values[i];
              const pct = ct.parsed.x || 0;
              return `${ct.dataset.label}: ${pct.toFixed(1)}% (${new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(raw)})`;
            },
            footer:()=>`Total: ${new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(total)}`
          }}
        }
      }
    });

    canvas.onclick = (evt)=>{
      const pts = chart.getElementsAtEventForMode(evt,'nearest',{intersect:true},true);
      if (!pts.length) return;
      const dsIdx = pts[0].datasetIndex;
      const segLabel   = chart.data.datasets?.[dsIdx]?.label;
      const groupLabel = chart.data.labels?.[0] || '';
      const path = resolvePath(groupLabel, segLabel);
      if (path) path.forEach(lbl=>openByLabel(lbl));
      else warn('sem caminho p/', groupLabel, segLabel);
    };
  }

  // ===== Inicializações =====
  buildHeadingIndex();
  showMode('pc'); // também ordena
  renderChart(initialKey);
  initializeToggleListeners();
  updateRankingUI(rankingSelect?.value || 'nacional'); // pinta os quadradinhos na carga
});
