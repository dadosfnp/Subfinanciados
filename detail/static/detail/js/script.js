document.addEventListener('DOMContentLoaded', function () {

  // --- Debug helpers seguros (no-ops quando DEBUG=false) ---
  const DEBUG = false;
  const log  = (...a) => { if (DEBUG) console.log('[detail]', ...a); };
  const warn = (...a) => { if (DEBUG) console.warn('[detail]', ...a); };

  // =============== UTILS =================
  function parsePossiblyMultiSerialized(text) {
    let out = text;
    try { out = JSON.parse(out); } catch { return text; }
    while (typeof out === 'string') {
      try { out = JSON.parse(out); } catch { break; }
    }
    return out;
  }
  function normalizeLabel(str) {
    return (str||'')
      .normalize('NFD').replace(/[\u0300-\u036f]/g,'')
      .replace(/[^a-z0-9]+/gi,' ')
      .replace(/\s+/g,' ')
      .trim().toLowerCase();
  }

  // Apelidos simples
  const HEADING_ALIAS = new Map([
    ['itc', 'Impostos, Taxas e Contribuições de Melhoria'],
    ['transf correntes', 'Transferências Correntes'],
    ['outras', 'Outras Receitas Correntes'],
  ]);

  function aliasToHeading(label){
    const k = normalizeLabel(label);
    return HEADING_ALIAS.get(k) || label;
  }

  // ---------- Índice de headings ----------
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
    log('headings indexados (limpos):', Array.from(headingIndex.keys()));
  }

  // ---------- Localiza linha por texto ----------
  function findRowByLabel(label){
    const needle = normalizeLabel(label);
    const scope  = document.getElementById('main-revenue-details-container');
    if(!scope) return null;

    const candidates = scope.querySelectorAll(
      '.toggle-heading, .toggle-subheading, .revenue-item, .revenue-row, li, .item-row, .row'
    );

    let best = null; // {el, score, dist}
    const pick = (el, score, dist)=>{
      if(!best || score>best.score || (score===best.score && dist<best.dist)){
        best = {el, score, dist};
      }
    };

    for(const el of candidates){
      const clone = el.cloneNode(true);
      clone.querySelectorAll('.valor-absoluto,.valor-per-capita').forEach(n=>n.remove());
      const txt = normalizeLabel(clone.textContent);
      if(!txt) continue;

      if (txt === needle) { pick(el, 2, 0); break; }
      if (txt.includes(needle) || needle.includes(txt)){
        pick(el, 1, Math.abs(txt.length-needle.length));
      }
    }
    return best?.el || null;
  }

  // ---------- Expande pais ----------
  function expandAncestorsFor(el){
    if(!el) return;
    const root = document.getElementById('main-revenue-details-container');
    let node = el;
    while(node && node!==root){
      const container = node.closest('div[id^="detalhe-"]');
      if(container){
        const id = container.id;
        const heading = document.querySelector(`.toggle-heading[data-target="${id}"]`);
        if(heading){
          container.classList.remove('hidden');
          heading.classList.add('open');
        }
        node = container.parentElement;
      }else{
        node = node.parentElement;
      }
    }
  }

  // ---------- Abre por rótulo (heading/linha) ----------
  function openSectionByLabel(label, opts={scroll:true, highlight:false}){
    if(!label) return;
    label = aliasToHeading(label);
    const needle = normalizeLabel(label);

    // 1) HEADING exato
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

    // 2) LINHA (folha) – abre pais e, se ela for toggle, abre filhos
    let row = findRowByLabel(label);
    if(row){
      expandAncestorsFor(row);
      if((row.classList.contains('toggle-heading') || row.classList.contains('toggle-subheading')) && row.dataset?.target){
        const tgt = document.getElementById(row.dataset.target);
        if(tgt) tgt.classList.remove('hidden');
        row.classList.add('open');
      }
      if(opts.scroll){
        row.scrollIntoView({behavior:'smooth', block:'center'});
        if(opts.highlight){ row.classList.add('ring-2','ring-yellow-400'); setTimeout(()=>row.classList.remove('ring-2','ring-yellow-400'), 900); }
      }
      return row;
    }

    // 3) HEADING por substring
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

    warn('heading/linha não encontrada p/ label:', label, 'needle:', needle);
    return null;
  }

  // ---------- Abre por trilha ----------
  function openByPath(path){
    if(!Array.isArray(path) || !path.length) return;
    // abre pais sem scroll
    for(let i=0;i<path.length-1;i++){
      openSectionByLabel(path[i], {scroll:false});
    }
    // foco no último
    openSectionByLabel(path[path.length-1], {scroll:true, highlight:true});
  }

  // =============== TOGGLES / ORDEM (mesmo de antes) ===============
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
  function parseCurrencyValue(str){ if(!str) return 0; return parseFloat(String(str).replace('R$','').replace(/\./g,'').replace(',','.').trim()); }
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
  }
  function restoreSelectValue(sel, val){ const has=[...sel.options].some(o=>o.value===val); sel.value = has?val:'todos'; }

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

  // =============== Filtros / KPIs / Detalhes ===============
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
  function buildParams(){
    const p=new URLSearchParams();
    p.set('porte',filtroPorte?.value||'todos');
    p.set('rm',filtroRm?.value||'todos');
    p.set('regiao',filtroRegiao?.value||'todos');
    p.set('uf',filtroUf?.value||'todos');
    return p;
  }
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

  // =============== GRÁFICO ===============
  const canvas = document.getElementById('myChart');
  if(!canvas){ console.warn('[chart] canvas não encontrado'); return; }
  const ctx = canvas.getContext('2d');
  const selectEl = document.getElementById('chart-category-select');
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

  // ---- Tabela de trilhas por categoria ----
  PATH_HINTS = {
    //Gráfico "Categorias Principais"
    main_categories: {
      'ITC':                ['Impostos, Taxas e Contribuições de Melhoria'],
      'Transf. Correntes':  ['Transferências Correntes'],
      'Contribuições':      ['Contribuições'],
      'Outras':             ['Outras Receitas Correntes'],
    },

    // (NOVO) Adicione esta seção
    imposto_taxas_contribuicoes: {
        'Impostos':    ['Impostos, Taxas e Contribuições de Melhoria', 'Impostos'],
        'Taxas':       ['Impostos, Taxas e Contribuições de Melhoria', 'Taxas'],
        'Contribuições de Melhoria': ['Impostos, Taxas e Contribuições de Melhoria', 'Contribuições de Melhoria'],
    },
    // Gráfico "Impostos"
    imposto: {
      'IPTU':   ['Impostos, Taxas e Contribuições de Melhoria','Impostos','IPTU'],
      'ITBI':   ['Impostos, Taxas e Contribuições de Melhoria','Impostos','ITBI'],
      'ISS':    ['Impostos, Taxas e Contribuições de Melhoria','Impostos','ISS'],
      'Outros': ['Impostos, Taxas e Contribuições de Melhoria','Impostos','Outros Impostos'],
    },
    // Gráfico "Taxas"
    taxas: {
      'Taxas pela Prestação de Serviços': ['Impostos, Taxas e Contribuições de Melhoria','Taxas','Taxas pela Prestação de Serviços'],
      'Taxas pelo Exercício do Poder de Polícia': ['Impostos, Taxas e Contribuições de Melhoria','Taxas','Taxas pelo Exercício do Poder de Polícia'],
      'Outras': ['Impostos, Taxas e Contribuições de Melhoria','Taxas','Outras Taxas'],
    },
    // Gráfico "Contribuições de Melhoria"
    contribuicoes_melhoria: {
      'Pavimentação': ['Impostos, Taxas e Contribuições de Melhoria','Contribuições de Melhoria', 'Contribuição de Melhoria para Pavimentação e Obras'],
      'Água/Esgoto': ['Impostos, Taxas e Contribuições de Melhoria','Contribuições de Melhoria', 'Contribuição de Melhoria para Rede de Água e Esgoto'],
      'Iluminação': ['Impostos, Taxas e Contribuições de Melhoria','Contribuições de Melhoria', 'Contribuição de Melhoria para Iluminação Pública'],
      'Outras': ['Impostos, Taxas e Contribuições de Melhoria','Contribuições de Melhoria', 'Outras Contribuições de Melhoria'],
    },
    // Gráfico "Contribuições" (nível detalhado)
    contribuicoes: {
      'Sociais': ['Contribuições', 'Contribuições Sociais'],
      'Iluminação Pública': ['Contribuições', 'Custeio do Serviço de Iluminação Pública'],
      'Outras': ['Contribuições', 'Outras Contribuições'],
    },
    // Gráfico "Transferências Correntes"
    transferencias_correntes: {
      'Transferências da União':   ['Transferências Correntes','Transferências da União'],
      'Transferências dos Estados':['Transferências Correntes','Transferências dos Estados'],
      'Outras':                    ['Transferências Correntes','Outras Transferências'],
    },
    // Gráfico "Transferências da União" (detalhe)
    transferencias_uniao: {
      'FPM': ['Transferências Correntes','Transferências da União', 'Cota-Parte do FPM'],
      'Rec. Naturais': ['Transferências Correntes','Transferências da União', 'Compensação Financeira (Recursos Naturais)'],
      'SUS': ['Transferências Correntes','Transferências da União', 'Recursos do SUS'],
      'FNDE': ['Transferências Correntes','Transferências da União', 'Recursos do FNDE'],
      'FNAS': ['Transferências Correntes','Transferências da União', 'Recursos do FNAS'],
      'Outras': ['Transferências Correntes','Transferências da União', 'Outras Transferências da União'],
    },
    // Gráfico "Transferências dos Estados" (detalhe)
    transferencias_estado: {
      'ICMS': ['Transferências Correntes','Transferências dos Estados', 'Cota-Parte do ICMS'],
      'IPVA': ['Transferências Correntes','Transferências dos Estados', 'Cota-Parte do IPVA'],
      'Rec. Naturais': ['Transferências Correntes','Transferências dos Estados', 'Compensação Financeira (Recursos Naturais)'],
      'SUS': ['Transferências Correntes','Transferências dos Estados', 'Recursos do SUS'],
      'Assistência': ['Transferências Correntes','Transferências dos Estados', 'Assistência Social'],
      'Outras': ['Transferências Correntes','Transferências dos Estados', 'Outras Transferências dos Estados'],
    },
    // Gráfico "Outras Receitas Correntes"
    outras_receitas_correntes: { // Renomeado para evitar conflito com "outras_receitas" do aggregated_data
      'Patrimonial': ['Outras Receitas Correntes', 'Receita Patrimonial'],
      'Agropecuária': ['Outras Receitas Correntes', 'Receita Agropecuária'],
      'Industrial': ['Outras Receitas Correntes', 'Receita Industrial'],
      'Serviços': ['Outras Receitas Correntes', 'Receita de Serviços'],
      'Outras': ['Outras Receitas Correntes', 'Outras Receitas'],
    },
  };

  function resolvePath(categoryKey, datasetLabel){
    const table = PATH_HINTS[categoryKey] || {};
    const n = normalizeLabel(datasetLabel);
    for(const [k, path] of Object.entries(table)){
      const nk = normalizeLabel(k);
      if(nk===n || nk.includes(n) || n.includes(nk)) return path;
    }
    return null; // sem trilha conhecida
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
    const finalLabels = items.map(x=>x.label);
    const finalValues = items.map(x=>x.value);
    const perc = finalValues.map(v=> total? (v/total)*100 : 0);

    const datasets = finalLabels.map((label,i)=>({
      label, data:[perc[i]], backgroundColor: palette[i % palette.length], borderWidth:1
    }));

    if(chartInstance) chartInstance.destroy();

    chartInstance = new Chart(ctx,{
      type:'bar',
      data:{ labels:[(selectEl?.options[selectEl.selectedIndex]?.text||'Categoria').toUpperCase()], datasets },
      options:{
        responsive:true, maintainAspectRatio:false, indexAxis:'y',
        scales:{ x:{ stacked:true, min:0, max:100, ticks:{ callback:v=>v+'%'} }, y:{ stacked:true } },
        plugins:{
          legend:{ position:'bottom' },
          tooltip:{ callbacks:{
            label:(ctx)=>{
              const i=ctx.datasetIndex, pct=ctx.parsed.x ?? 0, raw=finalValues[i];
              const fmt = new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'});
              return `${ctx.dataset.label}: ${pct.toFixed(1)}% (${fmt.format(raw)})`;
            },
            footer:()=>{
              const fmt = new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'});
              return `Total: ${fmt.format(total)}`;
            }
          } }
        }
      }
    });

    // Clique -> abre trilha
    canvas.style.cursor='pointer';
    canvas.onclick = (evt)=>{
      if(!chartInstance) return;
      const pts = chartInstance.getElementsAtEventForMode(evt,'nearest',{intersect:false},false);
      if(!pts.length) return;
      const {datasetIndex} = pts[0];
      const ds = chartInstance.data.datasets?.[datasetIndex];
      const labelClicado = ds?.label || '';
      log('click label:', labelClicado);

      // tenta trilha conhecida primeiro
      const path = resolvePath(categoryKey, labelClicado);
      if(path){ openByPath(path); return; }

      // fallback: tenta abrir pelo rótulo direto
      openSectionByLabel(labelClicado, {scroll:true, highlight:true});
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
