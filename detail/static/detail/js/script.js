// detail/static/detail/js/script.js  (CONJUNTO)
document.addEventListener('DOMContentLoaded', function () {
  // --- Debug helpers ---
  const DEBUG = false;
  const log  = (...a) => { if (DEBUG) console.log('[detail-conjunto]', ...a); };
  const warn = (...a) => { if (DEBUG) console.warn('[detail-conjunto]', ...a); };

  // =============== UTILS =================
  const parsePossiblyMultiSerialized = (text) => {
    let out = text;
    try { out = JSON.parse(out); } catch { return text; }
    while (typeof out === 'string') {
      try { out = JSON.parse(out); } catch { break; }
    }
    return out;
  };
  const normalizeLabel = (str) => (str||'')
    .normalize('NFD').replace(/[\u0300-\u036f]/g,'')
    .replace(/[^a-z0-9]+/gi,' ')
    .replace(/\s+/g,' ')
    .trim().toLowerCase();

  // Índice para abrir seções
  let headingIndex = new Map();
  function buildHeadingIndex(scope=document){
    headingIndex.clear();
    const headers = scope.querySelectorAll(
      '#main-revenue-details-container .toggle-heading, '+
      '#main-revenue-details-container .toggle-subheading'
    );
    headers.forEach(h=>{
      const clone = h.cloneNode(true);
      clone.querySelectorAll('.valor-absoluto,.valor-per-capita').forEach(n=>n.remove());
      const key = normalizeLabel(clone.textContent);
      const targetId = h.dataset.target;
      const content  = targetId ? document.getElementById(targetId) : null;
      if (key) headingIndex.set(key,{header:h,content,targetId});
    });
  }
  function openSectionByLabel(label, opts={scroll:true, highlight:false}){
    if(!label) return null;
    const needle = normalizeLabel(label);
    let entry = headingIndex.get(needle);
    if(entry){
      if(entry.content) entry.content.classList.remove('hidden');
      entry.header.classList.add('open');
      const parentToggle = entry.header.closest('.revenue-section')?.querySelector?.('.toggle-heading');
      if(parentToggle && parentToggle!==entry.header){
        const pid = parentToggle.dataset.target;
        if(pid){ document.getElementById(pid)?.classList.remove('hidden'); parentToggle.classList.add('open'); }
      }
      if(opts.scroll) entry.header.scrollIntoView({behavior:'smooth', block:'center'});
      return entry.header;
    }
    for(const [k,v] of headingIndex){
      if(k.includes(needle) || needle.includes(k)){
        if(v.content) v.content.classList.remove('hidden');
        v.header.classList.add('open');
        const parentToggle = v.header.closest('.revenue-section')?.querySelector?.('.toggle-heading');
        if(parentToggle && parentToggle!==v.header){
          const pid = parentToggle.dataset.target;
          if(pid){ document.getElementById(pid)?.classList.remove('hidden'); parentToggle.classList.add('open'); }
        }
        if(opts.scroll) v.header.scrollIntoView({behavior:'smooth', block:'center'});
        return v.header;
      }
    }
    return null;
  }
  function openByPath(path){
    if(!Array.isArray(path) || !path.length) return;
    for(let i=0;i<path.length-1;i++) openSectionByLabel(path[i], {scroll:false});
    openSectionByLabel(path[path.length-1], {scroll:true, highlight:true});
  }

  // =============== TOGGLES / ORDEM ===============
  function handleToggleClick(e){
    e.stopPropagation();
    const targetId = this.dataset.target;
    if(!targetId) return;
    const el = document.getElementById(targetId);
    if(el){ this.classList.toggle('open'); el.classList.toggle('hidden'); }
  }
  function initializeToggleListeners(scope=document){
    const els = scope.querySelectorAll('.toggle-heading, .toggle-subheading');
    els.forEach(el=>{
      el.removeEventListener('click',handleToggleClick);
      el.addEventListener('click',handleToggleClick);
    });
  }
  const parseCurrencyValue = (str) => !str ? 0 : parseFloat(String(str).replace('R$','').replace(/\./g,'').replace(',','.').trim());
  function sortChildrenByValue(container,isPC){
    const kids=[...container.children];
    kids.sort((a,b)=>{
      const sel=isPC?'.valor-per-capita':'.valor-absoluto';
      return parseCurrencyValue(b.querySelector(sel)?.textContent) - parseCurrencyValue(a.querySelector(sel)?.textContent);
    });
    kids.forEach(k=>container.appendChild(k));
  }
  function sortAllRevenueSections(isPC){
    document.querySelectorAll('#main-revenue-details-container, [id^="detalhe-"]').forEach(c=>sortChildrenByValue(c,isPC));
    initializeToggleListeners();
    buildHeadingIndex(document);
  }

  // =============== ELEMENTOS / DADOS INICIAIS ===============
  const dataEl = document.getElementById('chart-data');
  if(!dataEl){ console.error('[chart] #chart-data não encontrado'); return; }

  const filtroRegiao = document.getElementById('filtro-regiao');
  const filtroUf     = document.getElementById('filtro-uf');
  const filtroPorte  = document.getElementById('filtro-porte');
  const filtroRm     = document.getElementById('filtro-rm');

  let initialChartData=null;
  try{
    initialChartData = parsePossiblyMultiSerialized(dataEl.textContent);
  }catch(e){
    console.error('[chart] Falha JSON inicial',e); return;
  }

  // =============== Toggle PC/Real ===============
  let isShowingPerCapita = true;
  const perCapitaBtn = document.getElementById('btn-per-capita');
  const reaisBtn     = document.getElementById('btn-valores-reais');
  function setValorMode(mode){
    isShowingPerCapita = (mode==='percapita');
    perCapitaBtn?.classList.toggle('active',isShowingPerCapita);
    reaisBtn?.classList.toggle('active',!isShowingPerCapita);
    
    // Aplica visibilidade aos itens atuais (árvore)
    applyVisibilityToTree();
    sortAllRevenueSections(isShowingPerCapita);
  }

  function applyVisibilityToTree() {
    document.querySelectorAll('.valor-absoluto').forEach(el=>el.classList.toggle('hidden',isShowingPerCapita));
    document.querySelectorAll('.valor-per-capita').forEach(el=>el.classList.toggle('hidden',!isShowingPerCapita));
    
    document.querySelectorAll('.lbl-tipo-valor').forEach(el => {
      el.textContent = isShowingPerCapita ? 'Valor por Habitante' : 'Valor Real';
    });
    document.querySelectorAll('.media-block-wrapper').forEach(el => {
      el.classList.toggle('hidden', !isShowingPerCapita);
    });
  }

  perCapitaBtn?.addEventListener('click',()=>setValorMode('percapita'));
  reaisBtn?.addEventListener('click',()=>setValorMode('real'));
  setValorMode('percapita');

  // =============== Filtros / KPIs / Detalhes ===============
  function restoreSelectValue(sel, val){ const has=[...sel.options].some(o=>o.value===val); sel.value = has?val:'todos'; }

  const buildParams = () => {
    const p = new URLSearchParams();
    p.set('porte', filtroPorte?.value || 'todos');
    p.set('rm', filtroRm?.value || 'todos');
    p.set('regiao', filtroRegiao?.value || 'todos');
    p.set('uf', filtroUf?.value || 'todos');
    return p;
  };

  async function updateDependentFilters(){
    if(!filtroRegiao || !filtroUf || !filtroRm) return;
    
    const r = filtroRegiao.value;
    const u = filtroUf.value;
    const m = filtroRm.value;
    
    try{
      const resp = await fetch(`/api/get-dependent-filters/?${buildParams().toString()}`);
      if(!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      
      filtroRegiao.innerHTML='<option value="todos">Todas</option>';
      (data.regioes||[]).forEach(x=>filtroRegiao.add(new Option(x,x))); 
      restoreSelectValue(filtroRegiao,r);
      
      filtroRm.innerHTML ='<option value="todos">Todos</option>';
      (data.rms||[]).forEach(x=>filtroRm.add(new Option(x,x)));        
      restoreSelectValue(filtroRm,m);
      
      filtroUf.innerHTML ='<option value="todos">Todas</option>';
      (data.ufs||[]).forEach(x=>filtroUf.add(new Option(x,x)));        
      restoreSelectValue(filtroUf,u);
    } catch(e) { 
      console.error('[filtros] erro', e); 
    }
  }

  // =============== Toggle KPI Receita Corrente ===============
  let isKpiPc = true;
  const kpiRcLabel = document.getElementById('kpi-rc-label');
  const kpiRcValue = document.getElementById('kpi-receita-per-capita');
  const kpiBtns = document.querySelectorAll('.kpi-segmented button');

  function formatAbrevBR(value) {
      if (!value) return "R$ 0";
      if (value >= 1e9) {
          return "R$ " + (value / 1e9).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 2 }) + " Bi";
      } else if (value >= 1e6) {
          return "R$ " + (value / 1e6).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 2 }) + " Mi";
      } else {
          return "R$ " + value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      }
  }

  function updateKpiReceitaDisplay() {
    if(!kpiRcValue) return;
    const pc = Number(kpiRcValue.dataset.valPc || 0);
    const tot = Number(kpiRcValue.dataset.valTot || 0);
    
    if (isKpiPc) {
      if(kpiRcLabel) kpiRcLabel.textContent = 'Receita por Habitante';
      kpiRcValue.textContent = pc.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    } else {
      if(kpiRcLabel) kpiRcLabel.textContent = 'Receita Total';
      kpiRcValue.textContent = formatAbrevBR(tot);
    }
  }

  kpiBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      kpiBtns.forEach(b => b.classList.remove('active'));
      const target = e.currentTarget;
      target.classList.add('active');
      isKpiPc = target.dataset.mode === 'pc';
      updateKpiReceitaDisplay();
    });
  });

  async function updateKPIs(){
    try{
      const r = await fetch(`/api/dados-detalhados/?${buildParams()}`);
      const d = await r.json();

      document.getElementById('kpi-populacao').textContent =
        (d.kpis?.populacao || 0).toLocaleString('pt-BR');

      document.getElementById('kpi-quantidade').textContent =
        (d.kpis?.quantidade || 0).toLocaleString('pt-BR');

      if (kpiRcValue) {
        kpiRcValue.dataset.valPc = (d.kpis?.receita_per_capita || 0);
        kpiRcValue.dataset.valTot = (d.kpis?.receita_corrente || 0);
        updateKpiReceitaDisplay();
      }

      const diff = Number(d.kpis?.diferenca_media ?? 0);
      const elDiff = document.getElementById('kpi-diferenca-media');
      elDiff.textContent = diff.toLocaleString('pt-BR', { style: 'percent', minimumFractionDigits: 2 });
      colorizeDiffKpi(diff);

      // Nova lógica: Síntese Histórica
      updateHistoricalSynthesis(d.kpis);

    } catch(e) {
      console.error('[kpis] erro', e);
    }
  }

  // =============== EVOLUÇÃO HISTÓRICA (SÍNTESE) ===============
  let chartReceitaEvo = null;
  let chartPopEvo = null;

  const topLabelsPlugin = {
    id: 'topLabels',
    afterDatasetsDraw(chart) {
      const { ctx } = chart;
      chart.data.datasets.forEach((dataset, i) => {
        const meta = chart.getDatasetMeta(i);
        meta.data.forEach((bar, index) => {
          const val = dataset.data[index];
          if (val === undefined || val === null) return;
          const prefix = val > 0 ? '+' : '';
          const text = `${prefix}${Number(val).toFixed(1).replace('.', ',')}%`;
          ctx.save();
          ctx.fillStyle = Array.isArray(dataset.backgroundColor) ? dataset.backgroundColor[index] : dataset.backgroundColor;
          ctx.font = 'bold 12px "Inter", sans-serif';
          ctx.textAlign = 'center';
          const yPos = val >= 0 ? bar.y - 8 : bar.y + 16;
          ctx.fillText(text, bar.x, yPos);
          ctx.restore();
        });
      });
    }
  };

  function renderEvolutionCharts(evoData) {
    if (!evoData) return;

    const canvasRec = document.getElementById('chartReceitaEvo');
    const canvasPop = document.getElementById('chartPopEvo');

    if (canvasRec) {
      const ctxRec = canvasRec.getContext('2d');
      if (chartReceitaEvo) chartReceitaEvo.destroy();
      chartReceitaEvo = new Chart(ctxRec, {
        type: 'bar',
        data: {
          labels: ['Este Conjunto', 'Média Nacional'],
          datasets: [{
            data: [parsePossiblyMultiSerialized(evoData.receita.group), parsePossiblyMultiSerialized(evoData.receita.nac)],
            backgroundColor: ['#103758', '#cbd5e1'],
            borderRadius: 6,
            barPercentage: 0.5
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { display: false } },
            y: {
              beginAtZero: true,
              grace: '15%',
              ticks: { callback: v => v + '%' }
            }
          }
        },
        plugins: [topLabelsPlugin]
      });
    }

    if (canvasPop) {
      const ctxPop = canvasPop.getContext('2d');
      if (chartPopEvo) chartPopEvo.destroy();
      chartPopEvo = new Chart(ctxPop, {
        type: 'bar',
        data: {
          labels: ['Este Conjunto', 'Média Nacional'],
          datasets: [{
            data: [parsePossiblyMultiSerialized(evoData.populacao.group), parsePossiblyMultiSerialized(evoData.populacao.nac)],
            backgroundColor: ['#EEAF19', '#cbd5e1'],
            borderRadius: 6,
            barPercentage: 0.5
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { display: false } },
            y: {
              beginAtZero: true,
              grace: '15%',
              ticks: { callback: v => v + '%' }
            }
          }
        },
        plugins: [topLabelsPlugin]
      });
    }
  function updateHistoricalSynthesis(kpis) {
    if (!kpis) return;
    log('[evo] atualizando síntese', kpis);
    
    // Suporta tanto kpis (da API de detalhes) quanto hist_data (da API fiscal)
    const deltaRc = Number(kpis.delta_rc_pc ?? 0);
    const deltaPop = Number(kpis.delta_pop ?? 0);

    const txtRc = document.getElementById('text-delta-rc-pc');
    const txtPop = document.getElementById('text-delta-pop');

    if (txtRc) {
      const isPos = deltaRc >= 0;
      txtRc.innerHTML = isPos 
        ? `cresceu <span class="bg-emerald-50 text-emerald-700 font-bold px-1.5 py-0.5 rounded border border-emerald-100">+${deltaRc.toFixed(2)}%</span>`
        : `caiu <span class="bg-rose-50 text-rose-700 font-bold px-1.5 py-0.5 rounded border border-rose-100">${deltaRc.toFixed(2)}%</span>`;
    }

    if (txtPop) {
      const isPos = deltaPop >= 0;
      txtPop.innerHTML = isPos
        ? `aumentou <span class="bg-blue-50 text-blue-700 font-bold px-1.5 py-0.5 rounded border border-blue-100">+${deltaPop.toFixed(2)}%</span>`
        : `teve queda de <span class="bg-rose-50 text-rose-700 font-bold px-1.5 py-0.5 rounded border border-rose-100">${deltaPop.toFixed(2)}%</span>`;
    }

    // Mesmo sem o container de data inicial, podemos renderizar se os canvas existirem
    const currentEvo = {
      receita: { group: deltaRc, nac: kpis.media_nacional_rc_pc || 316.74 },
      populacao: { group: deltaPop, nac: kpis.media_nacional_pop || 16.04 }
    };
    renderEvolutionCharts(currentEvo);
  }

  async function updateFiscalDetails(){
    try{
      const resp = await fetch(`/api/fiscal-details/?${buildParams()}`);
      if(!resp.ok) throw new Error('Falha ao buscar detalhes fiscais.');
      const data = await resp.json();
      
      const cont = document.getElementById('main-revenue-details-container');
      cont.innerHTML = data.html;

      // Sincroniza Síntese Histórica (pela chave hist_data que vem dessa API)
      if(data.hist_data) updateHistoricalSynthesis(data.hist_data);
      
      initializeToggleListeners(cont);
      applyVisibilityToTree();
      sortAllRevenueSections(isShowingPerCapita);
      buildHeadingIndex(document);
    } catch(e) {
      console.error('[detalhes] erro', e);
      const c = document.getElementById('main-revenue-details-container');
      if(c) c.innerHTML = '<p class="text-red-500 text-center py-4">Erro ao carregar os dados.</p>';
    }
  }

  // =============== GRÁFICO COMPOSIÇÃO / SELECT HIERÁRQUICO ===============
  const canvas = document.getElementById('myChart');
  if(!canvas){ console.warn('[chart] canvas não encontrado'); return; }
  const ctx = canvas.getContext('2d');
  const selectEl = document.getElementById('chart-category-select');

  // Rótulos bonitos do select
  const PRETTY = {
    main_categories: 'Categorias Principais',
    imposto_taxas_contribuicoes: 'Impostos, Taxas e Contribuições',
    imposto: 'Impostos',
    taxas: 'Taxas',
    contribuicoes_melhoria: 'Contribuições de Melhoria',
    contribuicoes: 'Contribuições',
    transferencias_correntes: 'Transferências Correntes',
    transferencias_uniao: 'Transferências da União',
    transferencias_estado: 'Transferências dos Estados',
    outras_receitas: 'Outras Receitas'
  };

  // Hierarquia do select
  const HIERARCHY = {
    main_categories: { parent: null, children: ['imposto_taxas_contribuicoes','contribuicoes','transferencias_correntes','outras_receitas'] },
    imposto_taxas_contribuicoes: { parent: 'main_categories', children: ['imposto','taxas','contribuicoes_melhoria'] },
    imposto: { parent: 'imposto_taxas_contribuicoes', children: [] },
    taxas: { parent: 'imposto_taxas_contribuicoes', children: [] },
    contribuicoes_melhoria: { parent: 'imposto_taxas_contribuicoes', children: [] },
    contribuicoes: { parent: 'main_categories', children: [] },
    transferencias_correntes: { parent: 'main_categories', children: ['transferencias_uniao','transferencias_estado'] },
    transferencias_uniao: { parent: 'transferencias_correntes', children: [] },
    transferencias_estado: { parent: 'transferencias_correntes', children: [] },
    outras_receitas: { parent: 'main_categories', children: [] }
  };

  // ---- Notificações de densidade (apenas quando muda a CATEGORIA) ----
  function notifyDensity(key){
    if(!selectEl) return;
    const ev = new CustomEvent('composition-category-changed', { detail:{ key } });
    selectEl.dispatchEvent(ev);
  }

  // Troca categoria (por select ou clique) + renderiza + notifica densidade
  function setCategory(key){
    if(!selectEl) return;
    rebuildSelectOptions(key);
    renderChart(key, currentChartData);
    // >>> Mantemos a densidade sincronizada SOMENTE quando a categoria muda
    notifyDensity(key);
  }

  // Mapa de cliques das barras principais -> chave do select
  const MAIN_CLICK_TO_KEY = {
    'Impostos, Taxas e Contribuições': 'imposto_taxas_contribuicoes',
    'Contribuições': 'contribuicoes',
    'Transf. Correntes': 'transferencias_correntes',
    'Outras': 'outras_receitas'
  };

  // Cores das barras
  const COLOR_BY_LABEL = {
    'Impostos, Taxas e Contribuições': '#1f77b4',
    'Contribuições': '#ff7f0e',
    'Transf. Correntes': '#2ca02c',
    'Outras': '#d62728'
  };
  const palette  = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd','#8c564b','#e377c2','#7f7f7f','#bcbd22','#17becf'];

  let chartInstance=null;
  let currentChartData = initialChartData;

  async function updateChart(){
    try{
      const r=await fetch(`/api/conjunto-chart-data/?${buildParams()}`);
      if(!r.ok) throw new Error('Falha ao buscar dados do gráfico.');
      currentChartData=await r.json();
      renderChart(selectEl.value,currentChartData);
    }catch(e){ console.error('[chart] erro',e); }
  }

  // Caminhos para abrir linhas na árvore
  const PATH_HINTS = {
    main_categories: {
      'imposto_taxas_contribuicoes': ['Impostos, Taxas e Contribuições de Melhoria'],
      'Contribuições': ['Contribuições'],
      'Transf. Correntes': ['Transferências Correntes'],
      'Outras': ['Outras Receitas Correntes'],
    },
    imposto: {
      'IPTU': ['Impostos, Taxas e Contribuições de Melhoria','Impostos','IPTU'],
      'ITBI': ['Impostos, Taxas e Contribuições de Melhoria','Impostos','ITBI'],
      'ISS':  ['Impostos, Taxas e Contribuições de Melhoria','Impostos','ISS'],
      'Imposto de Renda': ['Impostos, Taxas e Contribuições de Melhoria','Impostos','Imposto de Renda'],
      'Outros': ['Impostos, Taxas e Contribuições de Melhoria','Impostos','Outros Impostos'],
    },
    taxas: {
      'Taxas pela Prestação de Serviços': ['Impostos, Taxas e Contribuições de Melhoria','Taxas','Taxas pela Prestação de Serviços'],
      'Taxas pelo Exercício do Poder de Polícia': ['Impostos, Taxas e Contribuições de Melhoria','Taxas','Taxas pelo Exercício do Poder de Polícia'],
      'Outras': ['Impostos, Taxas e Contribuições de Melhoria','Taxas','Outras Taxas'],
    },
    contribuicoes_melhoria: {
      'Pavimentação': ['Impostos, Taxas e Contribuições de Melhoria','Contribuições de Melhoria','Contribuição de Melhoria para Pavimentação e Obras'],
      'Água/Esgoto':  ['Impostos, Taxas e Contribuições de Melhoria','Contribuições de Melhoria','Contribuição de Melhoria para Rede de Água e Esgoto'],
      'Iluminação':   ['Impostos, Taxas e Contribuições de Melhoria','Contribuições de Melhoria','Contribuição de Melhoria para Iluminação Pública'],
      'Outras': ['Impostos, Taxas e Contribuições de Melhoria','Contribuições de Melhoria','Outras Contribuições de Melhoria'],
    },
    contribuicoes: {
      'Sociais': ['Contribuições','Contribuições Sociais'],
      'Iluminação Pública': ['Contribuições','Custeio do Serviço de Iluminação Pública'],
      'Outras': ['Contribuições','Outras Contribuições'],
    },
    transferencias_correntes: {
      'União':   ['Transferências Correntes','Transferências da União'],
      'Estados': ['Transferências Correntes','Transferências dos Estados'],
      'Outras':  ['Transferências Correntes','Outras Transferências'],
    },
    transferencias_uniao: {
      'FPM': ['Transferências Correntes','Transferências da União','Cota-Parte do FPM'],
      'Rec. Naturais': ['Transferências Correntes','Transferências da União','Compensação Financeira (Recursos Naturais)'],
      'SUS': ['Transferências Correntes','Transferências da União','Recursos do SUS'],
      'FNDE': ['Transferências Correntes','Transferências da União','Recursos do FNDE'],
      'FUNDEB': ['Transferências Correntes','Transferências da União','Recursos do FUNDEB'],
      'FNAS': ['Transferências Correntes','Transferências da União','Recursos do FNAS'],
      'Outras': ['Transferências Correntes','Transferências da União','Outras Transferências da União'],
    },
    transferencias_estado: {
      'ICMS': ['Transferências Correntes','Transferências dos Estados','Cota-Parte do ICMS'],
      'IPVA': ['Transferências Correntes','Transferências dos Estados','Cota-Parte do IPVA'],
      'Rec. Naturais': ['Transferências Correntes','Transferências dos Estados','Compensação Financeira (Recursos Naturais)'],
      'SUS': ['Transferências Correntes','Transferências dos Estados','Recursos do SUS'],
      'Assistência': ['Transferências Correntes','Transferências dos Estados','Assistência Social'],
      'Outras': ['Transferências Correntes','Transferências dos Estados','Outras Transferências dos Estados'],
    },
    outras_receitas: {
      'Patrimonial':  ['Outras Receitas Correntes','Receita Patrimonial'],
      'Agropecuária': ['Outras Receitas Correntes','Receita Agropecuária'],
      'Industrial':   ['Outras Receitas Correntes','Receita Industrial'],
      'Serviços':     ['Outras Receitas Correntes','Receita de Serviços'],
      'Outras':       ['Outras Receitas Correntes','Outras Receitas'],
    },
  };

  // ------ Select Hierárquico ------
  function rebuildSelectOptions(currentKey){
    if(!selectEl) return;
    selectEl.innerHTML = '';

    const push = (k)=>{
      const opt = document.createElement('option');
      opt.value = k;
      opt.textContent = PRETTY[k] || k;
      selectEl.appendChild(opt);
    };

    // Sempre começa com "Categorias Principais"
    push('main_categories');

    if (currentKey === 'main_categories'){
      HIERARCHY.main_categories.children.forEach(push);
    } else {
      const parent = HIERARCHY[currentKey]?.parent;
      if (parent) push(parent);
      push(currentKey);
      const children = HIERARCHY[currentKey]?.children || [];
      children.forEach(push);
    }
    selectEl.value = currentKey;
  }

  // Troca categoria (select)
  if(selectEl){
    selectEl.addEventListener('change', (e)=> setCategory(e.target.value));
  }

  function resolvePath(categoryKey, datasetLabel){
    const table = PATH_HINTS[categoryKey] || {};
    const n = normalizeLabel(datasetLabel);
    for(const [k, path] of Object.entries(table)){
      const nk = normalizeLabel(k);
      if(nk===n || nk.includes(n) || n.includes(nk)) return path;
    }
    return null;
  }

  function renderChart(categoryKey, allData){
    if(!allData){ console.error('[chart] sem dados'); return; }
    const d = allData[categoryKey];
    if(!d || !Array.isArray(d.labels) || !Array.isArray(d.values)){
      console.error('[chart] estrutura inesperada em', categoryKey, d);
      if(chartInstance) chartInstance.destroy();
      return;
    }

    const raw = d.values.map(v=>Number(v)||0);
    const total = raw.reduce((a,b)=>a+b,0);
    const items = d.labels.map((label,i)=>({label, value:raw[i]})).filter(x=>x.value>0);
    const labels = items.map(x=>x.label);
    const values = items.map(x=>x.value);
    const perc   = values.map(v=> total? (v/total)*100 : 0);

    const bcolors = labels.map((lbl,i)=> COLOR_BY_LABEL[lbl] || palette[i % palette.length]);

    if(chartInstance) chartInstance.destroy();
    chartInstance = new Chart(ctx,{
      type:'bar',
      data:{
        labels,
        datasets:[{
          label:(PRETTY[categoryKey] || 'Categoria').toUpperCase(),
          data: perc,
          backgroundColor: bcolors,
          borderWidth:1
        }]
      },
      options:{
        responsive:true, maintainAspectRatio:false, indexAxis:'y',
        scales:{ x:{min:0,max:100,ticks:{callback:v=>v+'%'}}, y:{ticks:{autoSkip:false}} },
        plugins:{ legend:{ display:false }, tooltip:{ callbacks:{
          label:(ct)=>{
            const i=ct.dataIndex; const pct=ct.parsed.x || 0; const rawVal = values[i];
            const fmt = new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'});
            return `${labels[i]}: ${pct.toFixed(1)}% (${fmt.format(rawVal)})`;
          },
          footer:()=>`Total: ${new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(total)}`
        } } }
      }
    });

    // clique
    canvas.style.cursor='pointer';
    canvas.onclick = (evt)=>{
      const pts = chartInstance.getElementsAtEventForMode(evt,'nearest',{intersect:true},true);
      if (!pts.length) return;
      const idx = pts[0].index;
      const clicked = labels[idx];

      // 1) Categorias Principais → descer um nível 
      if (categoryKey === 'main_categories') {
        const nxt = MAIN_CLICK_TO_KEY[clicked] || null;
        if (nxt){ setCategory(nxt); }
        return;
      }

      // 2) Grupo intermediário ITC → filhos 
      if (categoryKey === 'imposto_taxas_contribuicoes') {
        const n = normalizeLabel(clicked);
        if (n.includes('imposto'))  { rebuildSelectOptions('imposto'); renderChart('imposto', currentChartData); return; }
        if (n.includes('taxa'))     { rebuildSelectOptions('taxas'); renderChart('taxas', currentChartData); return; }
        if (n.includes('melhoria')) { rebuildSelectOptions('contribuicoes_melhoria'); renderChart('contribuicoes_melhoria', currentChartData); return; }
      }

      // 3) Transferências Correntes → União/Estados 
      if (categoryKey === 'transferencias_correntes') {
        const l = normalizeLabel(clicked);
        if (l.includes('uniao'))  { rebuildSelectOptions('transferencias_uniao');  renderChart('transferencias_uniao', currentChartData);  return; }
        if (l.includes('estado')) { rebuildSelectOptions('transferencias_estado'); renderChart('transferencias_estado', currentChartData); return; }
        const pathTC = resolvePath(categoryKey, clicked);
        pathTC ? openByPath(pathTC) : openSectionByLabel(clicked);
        return;
      }

      // 4) Filhos (qualquer categoria): apenas abre a árvore visual 
      const path = resolvePath(categoryKey, clicked);
      path ? openByPath(path) : openSectionByLabel(clicked);
    };
  }

  // Render/Select inicial
  const initialKey = 'main_categories';
  rebuildSelectOptions(initialKey);
  renderChart(initialKey, initialChartData);
  notifyDensity(initialKey); // sincroniza densidade com a categoria inicial

  // =============== APLICAÇÃO / EVENTOS ===============
  async function applyFiltersAndData(){ 
    await updateDependentFilters();
    await Promise.all([updateKPIs(), updateFiscalDetails(), updateChart()]); 
  }

  if(filtroRegiao) filtroRegiao.addEventListener('change', applyFiltersAndData);
  if(filtroUf)     filtroUf.addEventListener('change',     applyFiltersAndData);
  if(filtroRm)     filtroRm.addEventListener('change',     applyFiltersAndData);
  if(filtroPorte)  filtroPorte.addEventListener('change',  applyFiltersAndData);

  const btnLimpar=document.getElementById('btn-limpar-filtros');
  if(btnLimpar){
    btnLimpar.addEventListener('click',()=>{
      if(filtroRegiao) filtroRegiao.value='todos';
      if(filtroRm)     filtroRm.value='todos';
      if(filtroUf)     filtroUf.value='todos';
      if(filtroPorte)  filtroPorte.value='todos';
      applyFiltersAndData();
    });
  }

  // Inicialização Gráficos Evolução
  const initialEvoEl = document.getElementById('evolution-compare-data');
  if (initialEvoEl) {
    try {
      const initialEvo = JSON.parse(initialEvoEl.textContent);
      renderEvolutionCharts(initialEvo);
    } catch(e) { console.error('[evo] falha json inicial', e); }
  }

  applyFiltersAndData();
  buildHeadingIndex(document);
});

// Helper para colorir o KPI da diferença
function colorizeDiffKpi(value){
  const el = document.getElementById('kpi-diferenca-media');
  if(!el) return;
  el.classList.remove('neg','pos','neu');
  el.classList.add(value < 0 ? 'neg' : value > 0 ? 'pos' : 'neu');
}