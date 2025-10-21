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
    els.forEach(el=>{ el.removeEventListener('click',handleToggleClick); el.addEventListener('click',handleToggleClick); });
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
  try{ initialChartData = parsePossiblyMultiSerialized(dataEl.textContent); }catch(e){ console.error('[chart] Falha JSON inicial',e); return; }

  // =============== Toggle PC/Real ===============
  let isShowingPerCapita = true;
  const perCapitaBtn = document.getElementById('btn-per-capita');
  const reaisBtn     = document.getElementById('btn-valores-reais');
  function setValorMode(mode){
    isShowingPerCapita = (mode==='percapita');
    perCapitaBtn?.classList.toggle('active',isShowingPerCapita);
    reaisBtn?.classList.toggle('active',!isShowingPerCapita);
    document.querySelectorAll('.valor-absoluto').forEach(el=>el.classList.toggle('hidden',isShowingPerCapita));
    document.querySelectorAll('.valor-per-capita').forEach(el=>el.classList.toggle('hidden',!isShowingPerCapita));
    sortAllRevenueSections(isShowingPerCapita);
  }
  perCapitaBtn?.addEventListener('click',()=>setValorMode('percapita'));
  reaisBtn?.addEventListener('click',()=>setValorMode('real'));
  setValorMode('percapita');

  // =============== Filtros / KPIs / Detalhes (inalterado) ===============
  function restoreSelectValue(sel, val){ const has=[...sel.options].some(o=>o.value===val); sel.value = has?val:'todos'; }
  async function updateDependentFilters(){
    if(!filtroRegiao || !filtroUf || !filtroRm) return;
    const r=filtroRegiao.value,u=filtroUf.value,m=filtroRm.value;
    try{
      const resp=await fetch('/api/get-dependent-filters/?regiao=todos&uf=todos&rm=todos');
      if(!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data=await resp.json();
      filtroRegiao.innerHTML='<option value="todos">Todas</option>'; (data.regioes||[]).forEach(x=>filtroRegiao.add(new Option(x,x))); restoreSelectValue(filtroRegiao,r);
      filtroRm.innerHTML   ='<option value="todos">Todos</option>';   (data.rms||[]).forEach(x=>filtroRm.add(new Option(x,x)));        restoreSelectValue(filtroRm,m);
      filtroUf.innerHTML   ='<option value="todos">Todas</option>';   (data.ufs||[]).forEach(x=>filtroUf.add(new Option(x,x)));        restoreSelectValue(filtroUf,u);
    }catch(e){ console.error('[filtros] erro',e); }
  }
  const buildParams = () => {
    const p=new URLSearchParams();
    p.set('porte',filtroPorte?.value||'todos');
    p.set('rm',filtroRm?.value||'todos');
    p.set('regiao',filtroRegiao?.value||'todos');
    p.set('uf',filtroUf?.value||'todos');
    return p;
  };
  async function updateKPIs(){
    try{
      const r=await fetch(`/api/dados-detalhados/?${buildParams()}`); const d=await r.json();
      document.getElementById('kpi-populacao').textContent=(d.kpis?.populacao||0).toLocaleString('pt-BR');
      document.getElementById('kpi-quantidade').textContent=(d.kpis?.quantidade||0).toLocaleString('pt-BR');
      document.getElementById('kpi-receita-per-capita').textContent=(d.kpis?.receita_per_capita||0).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});
      document.getElementById('kpi-diferenca-media').textContent=(d.kpis?.diferenca_media||0).toLocaleString('pt-BR',{style:'percent',minimumFractionDigits:2});
    }catch(e){ console.error('[kpis] erro',e); }
  }
  async function updateFiscalDetails(){
    try{
      const resp=await fetch(`/api/fiscal-details/?${buildParams()}`);
      if(!resp.ok) throw new Error('Falha ao buscar detalhes fiscais.');
      const data=await resp.json();
      const cont=document.getElementById('main-revenue-details-container');
      cont.innerHTML=data.html;
      initializeToggleListeners(cont);
      sortAllRevenueSections(isShowingPerCapita);
      buildHeadingIndex(document);
    }catch(e){
      console.error('[detalhes] erro',e);
      const c=document.getElementById('main-revenue-details-container');
      if(c) c.innerHTML='<p class="text-red-500 text-center py-4">Erro ao carregar os dados.</p>';
    }
  }

  // =============== GRÁFICO COMPOSIÇÃO ===============
  const canvas = document.getElementById('myChart');
  if(!canvas){ console.warn('[chart] canvas não encontrado'); return; }
  const ctx = canvas.getContext('2d');
  const selectEl = document.getElementById('chart-category-select');

  // Remove “Impostos, Taxas e Contribuições de Melhoria” do select (não usamos mais)
  (function removeITCGroup(){
    const opt = selectEl?.querySelector('option[value="imposto_taxas_contribuicoes"]');
    if (opt) opt.remove();
  })();

  // Cores fixas p/ categorias principais
  const COLOR_BY_LABEL = {
    'ITC': '#1f77b4',
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
      'ITC':               ['Impostos, Taxas e Contribuições de Melhoria'],
      'Contribuições':     ['Contribuições'],
      'Transf. Correntes': ['Transferências Correntes'],
      'Outras':            ['Outras Receitas Correntes'],
    },
    imposto: {
      'IPTU': ['Impostos, Taxas e Contribuições de Melhoria','Impostos','IPTU'],
      'ITBI': ['Impostos, Taxas e Contribuições de Melhoria','Impostos','ITBI'],
      'ISS':  ['Impostos, Taxas e Contribuições de Melhoria','Impostos','ISS'],
      'Outros': ['Impostos, Taxas e Contribuições de Melhoria','Impostos','Outros Impostos'],
    },
    taxas: {
      'Taxas pela Prestação de Serviços': ['Impostos, Taxas e Contribuições de Melhoria','Taxas','Taxas pela Prestação de Serviços'],
      'Taxas pelo Exercício do Poder de Polícia': ['Impostos, Taxas e Contribuições de Melhoria','Taxas','Taxas pelo Exercício do Poder de Polícia'],
      'Outras': ['Impostos, Taxas e Contribuições de Melhoria','Taxas','Outras Taxas'],
    },
    contribuicoes_melhoria: {
      'Pavimentação': ['Impostos, Taxas e Contribuições de Melhoria','Contribuições de Melhoria', 'Contribuição de Melhoria para Pavimentação e Obras'],
      'Água/Esgoto': ['Impostos, Taxas e Contribuições de Melhoria','Contribuições de Melhoria', 'Contribuição de Melhoria para Rede de Água e Esgoto'],
      'Iluminação': ['Impostos, Taxas e Contribuições de Melhoria','Contribuições de Melhoria', 'Contribuição de Melhoria para Iluminação Pública'],
      'Outras': ['Impostos, Taxas e Contribuições de Melhoria','Contribuições de Melhoria', 'Outras Contribuições de Melhoria'],
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
      'FPM': ['Transferências Correntes','Transferências da União', 'Cota-Parte do FPM'],
      'Rec. Naturais': ['Transferências Correntes','Transferências da União', 'Compensação Financeira (Recursos Naturais)'],
      'SUS': ['Transferências Correntes','Transferências da União', 'Recursos do SUS'],
      'FNDE': ['Transferências Correntes','Transferências da União', 'Recursos do FNDE'],
      'FNAS': ['Transferências Correntes','Transferências da União', 'Recursos do FNAS'],
      'Outras': ['Transferências Correntes','Transferências da União', 'Outras Transferências da União'],
    },
    transferencias_estado: {
      'ICMS': ['Transferências Correntes','Transferências dos Estados', 'Cota-Parte do ICMS'],
      'IPVA': ['Transferências Correntes','Transferências dos Estados', 'Cota-Parte do IPVA'],
      'Rec. Naturais': ['Transferências Correntes','Transferências dos Estados', 'Compensação Financeira (Recursos Naturais)'],
      'SUS': ['Transferências Correntes','Transferências dos Estados', 'Recursos do SUS'],
      'Assistência': ['Transferências Correntes','Transferências dos Estados', 'Assistência Social'],
      'Outras': ['Transferências Correntes','Transferências dos Estados', 'Outras Transferências dos Estados'],
    },
    outras_receitas: {
      'Patrimonial': ['Outras Receitas Correntes', 'Receita Patrimonial'],
      'Agropecuária': ['Outras Receitas Correntes', 'Receita Agropecuária'],
      'Industrial': ['Outras Receitas Correntes', 'Receita Industrial'],
      'Serviços': ['Outras Receitas Correntes', 'Receita de Serviços'],
      'Outras': ['Outras Receitas Correntes', 'Outras Receitas'],
    },
  };

  const MAIN_TO_KEY = {
    'ITC':'imposto',
    'Contribuições':'contribuicoes',
    'Transf. Correntes':'transferencias_correntes',
    'Outras':'outras_receitas'
  };

  // helper para sincronizar com densidade
  function setCategoryAndSync(key){
    if (!selectEl) return;
    selectEl.value = key;
    renderChart(key, currentChartData);
    selectEl.dispatchEvent(new Event('change', { bubbles:true })); // avisa o script de densidade
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

    // prepara dados
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
      data:{ labels, datasets:[{ label:(selectEl?.selectedOptions?.[0]?.text || 'Categoria').toUpperCase(), data: perc, backgroundColor: bcolors, borderWidth:1 }] },
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

      if (categoryKey === 'main_categories') {
        const nextKey = MAIN_TO_KEY[clicked];
        if (nextKey) { setCategoryAndSync(nextKey); }
        else { const path = resolvePath(categoryKey, clicked); path? openByPath(path): openSectionByLabel(clicked); }
        return;
      }

      if (categoryKey === 'transferencias_correntes') {
        const l = normalizeLabel(clicked);
        if (l.includes('uniao'))  { setCategoryAndSync('transferencias_uniao');  return; }
        if (l.includes('estado')) { setCategoryAndSync('transferencias_estado'); return; }
        const path = resolvePath(categoryKey, clicked); path? openByPath(path): openSectionByLabel(clicked);
        return;
      }

      const path = resolvePath(categoryKey, clicked);
      path ? openByPath(path) : openSectionByLabel(clicked);
    };
  }

  if(selectEl){ selectEl.addEventListener('change', ()=>renderChart(selectEl.value, currentChartData)); }

  // Render inicial
  renderChart(selectEl?.value || 'main_categories', initialChartData);

  // =============== APLICAÇÃO / EVENTOS ===============
  async function applyFilters(){ await Promise.all([updateKPIs(), updateFiscalDetails(), updateChart()]); }
  if(filtroRegiao) filtroRegiao.addEventListener('change', applyFilters);
  if(filtroUf)     filtroUf.addEventListener('change',     applyFilters);
  if(filtroRm)     filtroRm.addEventListener('change',     applyFilters);
  if(filtroPorte)  filtroPorte.addEventListener('change',  applyFilters);

  const btnLimpar=document.getElementById('btn-limpar-filtros');
  if(btnLimpar){
    btnLimpar.addEventListener('click',()=>{
      if(filtroRegiao) filtroRegiao.value='todos';
      if(filtroRm)     filtroRm.value='todos';
      if(filtroUf)     filtroUf.value='todos';
      if(filtroPorte)  filtroPorte.value='todos';
      updateDependentFilters();
      applyFilters();
    });
  }

  updateDependentFilters();
  applyFilters();
  buildHeadingIndex(document);
});
