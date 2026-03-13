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
    document.querySelectorAll('.valor-absoluto').forEach(el=>el.classList.toggle('hidden',isShowingPerCapita));
    document.querySelectorAll('.valor-per-capita').forEach(el=>el.classList.toggle('hidden',!isShowingPerCapita));
    sortAllRevenueSections(isShowingPerCapita);
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

  async function updateKPIs(){
    try{
      const r = await fetch(`/api/dados-detalhados/?${buildParams()}`);
      const d = await r.json();

      document.getElementById('kpi-populacao').textContent =
        (d.kpis?.populacao || 0).toLocaleString('pt-BR');

      document.getElementById('kpi-quantidade').textContent =
        (d.kpis?.quantidade || 0).toLocaleString('pt-BR');

      document.getElementById('kpi-receita-per-capita').textContent =
        (d.kpis?.receita_per_capita || 0)
          .toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

      const diff = Number(d.kpis?.diferenca_media ?? 0);
      const elDiff = document.getElementById('kpi-diferenca-media');
      elDiff.textContent = diff.toLocaleString('pt-BR', { style: 'percent', minimumFractionDigits: 2 });
      colorizeDiffKpi(diff);
    } catch(e) {
      console.error('[kpis] erro', e);
    }
  }

  const FNP_RANK_COLORS = { '1': '#A81C21', '2': '#E47326', '3': '#F4D01D', '4': '#6AC074', '5': '#1C9148' };
  const FNP_DECIL_COLORS = { '1': '#960E16', '2': '#CF3026', '3': '#EB6630', '4': '#F8A555', '5': '#FCE182', '6': '#DDEC88', '7': '#9DD57D', '8': '#60BA69', '9': '#2D964D', '10': '#076931' };

  let chartReceitaEvoInstance = null;
  let chartPopEvoInstance = null;
  let timelineMode = 'percentil';

  function renderTimelineRuler(mode, val00, val24) {
      const container = document.getElementById('timeline-ruler-container');
      if (!container) return;
      container.classList.remove('hidden');

      let trackHTML = ''; let pos00 = 0; let pos24 = 0; let color24 = '#103758';
      let txt00 = ''; let txt24 = ''; let scaleMarkers = '';

      if (mode === 'percentil') {
          trackHTML = `<div class="w-full h-2.5 rounded-full" style="background: linear-gradient(to right, #A81C21, #E47326, #F4D01D, #6AC074, #1C9148);"></div>`;
          pos00 = val00; pos24 = val24;
          txt00 = `${val00}% <span class="font-normal text-[11px] opacity-75">(2000)</span>`;
          txt24 = `${val24}% <span class="font-normal text-[11px] opacity-80">(2024)</span>`;
          scaleMarkers = `
            <span class="absolute -left-7 top-1/2 -translate-y-1/2 text-[10px] font-bold text-slate-300">0%</span>
            <span class="absolute -right-9 top-1/2 -translate-y-1/2 text-[10px] font-bold text-slate-300">100%</span>`;
          const decilIndex = Math.max(1, Math.ceil(val24 / 10));
          color24 = FNP_DECIL_COLORS[decilIndex] || '#1C9148';
      } else if (mode === 'quintil') {
          trackHTML = `<div class="w-full h-2.5 flex rounded-full overflow-hidden gap-0.5">
            ${[1, 2, 3, 4, 5].map(q => `<div class="flex-1" style="background-color: ${FNP_RANK_COLORS[q]}"></div>`).join('')}
          </div>`;
          pos00 = (val00 - 0.5) * 20; pos24 = (val24 - 0.5) * 20;
          txt00 = `${val00}º <span class="font-normal text-[11px] opacity-75">(2000)</span>`;
          txt24 = `${val24}º <span class="font-normal text-[11px] opacity-80">(2024)</span>`;
          color24 = FNP_RANK_COLORS[val24];
      } else if (mode === 'decil') {
          trackHTML = `<div class="w-full h-2.5 flex rounded-full overflow-hidden gap-[1px]">
            ${[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(d => `<div class="flex-1" style="background-color: ${FNP_DECIL_COLORS[d]}"></div>`).join('')}
          </div>`;
          pos00 = (val00 - 0.5) * 10; pos24 = (val24 - 0.5) * 10;
          txt00 = `${val00}º <span class="font-normal text-[11px] opacity-75">(2000)</span>`;
          txt24 = `${val24}º <span class="font-normal text-[11px] opacity-80">(2024)</span>`;
          color24 = FNP_DECIL_COLORS[val24];
      }

      container.innerHTML = `
        <div class="relative w-full flex items-center mt-6 mb-6">
            ${scaleMarkers}
            <div class="absolute flex flex-col items-center transition-all duration-500 ease-in-out whitespace-nowrap" style="left: ${pos00}%; bottom: 100%; transform: translateX(-50%);">
                <span class="text-[13px] font-bold text-slate-400 leading-none mb-1">${txt00}</span>
                <div class="w-0.5 h-2.5 bg-slate-300 rounded-full"></div>
            </div>
            ${trackHTML}
            <div class="absolute flex flex-col items-center transition-all duration-500 ease-in-out z-10 whitespace-nowrap" style="left: ${pos24}%; top: 100%; transform: translateX(-50%);">
                <div class="w-0.5 h-2.5 rounded-full" style="background-color: ${color24}"></div>
                <span class="text-[14px] font-black leading-none mt-1" style="color: ${color24}">${txt24}</span>
            </div>
        </div>`;
  }

  function updateTimelineColors(mode) {
      const timelineCircles = document.querySelectorAll('.timeline-circle-dynamic');
      const summaryContainer = document.getElementById('timeline-dynamic-summary');

      timelineCircles.forEach(circle => {
          const rawValue = circle.dataset[mode] || '-';
          const labelSpan = circle.querySelector('.dynamic-label');
          const valueSpan = circle.querySelector('.dynamic-value');
          const numMatch = rawValue.match(/\d+/);
          const num = numMatch ? numMatch[0] : null;

          let hex = null; let isLightBackground = false; let explanationText = '';
          if (num) {
              if (mode === 'percentil') {
                  if (labelSpan) labelSpan.textContent = 'Percentil';
                  if (valueSpan) valueSpan.textContent = num + '%';
                  const decilVal = Math.max(1, Math.ceil(parseInt(num) / 10));
                  hex = FNP_DECIL_COLORS[decilVal];
                  isLightBackground = (decilVal === 5 || decilVal === 6);
                  explanationText = `Maior que <strong class="text-slate-800">${num}%</strong> dos munícipios`;
              } else if (mode === 'quintil') {
                  if (labelSpan) labelSpan.textContent = 'Quintil';
                  if (valueSpan) valueSpan.textContent = num + 'º';
                  hex = FNP_RANK_COLORS[num];
                  isLightBackground = (num === '3');
                  const quintilWords = {'5': '20% mais ricos', '4': '40% a 20% mais ricos', '3': 'Intermediário', '2': 'Abaixo da Média', '1': '20% mais pobres'};
                  explanationText = `<strong class="text-slate-800">${quintilWords[num] || ''}</strong> do país`;
              } else if (mode === 'decil') {
                  if (labelSpan) labelSpan.textContent = 'Decil';
                  if (valueSpan) valueSpan.textContent = num + 'º';
                  hex = FNP_DECIL_COLORS[num];
                  isLightBackground = (num === '5' || num === '6');
                  explanationText = `Grupo <strong class="text-slate-800">${num}</strong> de 10 do país`;
              }
          } else {
              if (labelSpan) labelSpan.textContent = mode;
              if (valueSpan) valueSpan.textContent = '-';
              explanationText = 'Dado Indisponível';
          }

          if (hex) {
              circle.style.backgroundColor = hex;
              circle.style.color = isLightBackground ? '#103758' : '#ffffff';
          } else {
              circle.style.backgroundColor = '#f1f5f9';
              circle.style.color = '#94a3b8';
          }

          const explanationSpan = circle.nextElementSibling;
          if (explanationSpan && explanationSpan.classList.contains('dynamic-explanation')) {
              explanationSpan.innerHTML = explanationText;
          }
      });

      if (summaryContainer && timelineCircles.length >= 2) {
          const raw00 = timelineCircles[0].dataset[mode];
          const raw24 = timelineCircles[1].dataset[mode];
          const num00 = raw00 ? raw00.match(/\d+/) : null;
          const num24 = raw24 ? raw24.match(/\d+/) : null;
          if (num00 && num24) {
              const val00 = parseInt(num00[0]);
              const val24 = parseInt(num24[0]);
              if (val24 === val00) {
                  summaryContainer.innerHTML = `Entre 2000 e 2024, <strong class="text-slate-700">a posição relativa do conjunto no Brasil se manteve</strong>.`;
              } else if (mode === 'percentil') {
                  const statusAcao = val24 > val00 ? 'AVANÇOU' : 'RECUOU';
                  const statusColor = val24 > val00 ? 'text-emerald-600' : 'text-rose-600';
                  summaryContainer.innerHTML = `Nestas duas décadas, a receita por habitante do conjunto <span class="${statusColor} font-black">${statusAcao}</span> no ranking nacional, indo do percentil <span class="font-bold text-slate-400">${val00}%</span> para o <span class="${statusColor} font-black">${val24}%</span>.`;
              } else {
                  const isMelhor = val24 > val00;
                  const statusAcao = isMelhor ? 'SUBIU' : 'CAIU';
                  const corStatus = isMelhor ? 'text-emerald-600' : 'text-rose-600';
                  summaryContainer.innerHTML = `Entre 2000 e 2024, a posição relativa do conjunto <span class="${corStatus} font-black">${statusAcao}</span> do <span class="font-bold text-slate-400">${val00}º ${mode}</span> para o <span class="${corStatus} font-black">${val24}º ${mode}</span>.`;
              }
              renderTimelineRuler(mode, val00, val24);
          } else {
              summaryContainer.innerHTML = '';
              const r = document.getElementById('timeline-ruler-container');
              if (r) r.classList.add('hidden');
          }
      }
  }

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
                  const text = `${prefix}${val.toFixed(1).replace('.', ',')}%`;
                  ctx.save();
                  ctx.fillStyle = Array.isArray(dataset.backgroundColor) ? dataset.backgroundColor[index] : dataset.backgroundColor;
                  ctx.font = 'bolder 13px "Inter", sans-serif';
                  ctx.textAlign = 'center';
                  const yPos = val >= 0 ? bar.y - 8 : bar.y + 16;
                  ctx.fillText(text, bar.x, yPos);
                  ctx.restore();
              });
          });
      }
  };

  const commonEvoOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
          legend: { display: false },
          tooltip: {
              callbacks: {
                  label: function(ctx) {
                      let val = ctx.raw || 0;
                      let prefix = val > 0 ? '+' : '';
                      return ` ${prefix}${val.toFixed(1).replace('.', ',')}%`;
                  }
              }
          }
      },
      scales: {
          x: { grid: { display: false }, ticks: { font: { weight: 'bold' }, color: '#475569' } },
          y: { 
              beginAtZero: true,
              grace: '15%',
              grid: { color: (c) => c.tick && c.tick.value === 0 ? '#94a3b8' : '#f1f5f9', lineWidth: (c) => c.tick && c.tick.value === 0 ? 2 : 1 }, 
              ticks: { color: '#94a3b8', callback: (val) => val + '%' } 
          }
      }
  };

  function renderEvolutionCharts(hist) {
    const fmtPct = (v) => {
      const n = Number(v) || 0;
      const formatted = n.toFixed(2);
      return n >= 0
        ? `<span class="bg-emerald-50 text-emerald-700 font-bold px-1.5 py-0.5 rounded border border-emerald-100">+${formatted}%</span>`
        : `<span class="bg-rose-50 text-rose-700 font-bold px-1.5 py-0.5 rounded border border-rose-100">${formatted}%</span>`;
    };

    const elRc  = document.getElementById('text-delta-rc-pc');
    const elPop = document.getElementById('text-delta-pop');
    const deltaRc  = Number(hist.delta_rc_pc)  || 0;
    const deltaPop = Number(hist.delta_pop)     || 0;

    if (elRc)  elRc.innerHTML  = deltaRc  >= 0 ? `cresceu ${fmtPct(deltaRc)}`  : `caiu ${fmtPct(deltaRc)}`;
    if (elPop) elPop.innerHTML = deltaPop >= 0 ? `aumentou ${fmtPct(deltaPop)}` : `teve queda de ${fmtPct(deltaPop)}`;

    const elMedRc = document.getElementById('text-media-nacional-rc');
    const elMedPop = document.getElementById('text-media-nacional-pop');
    if (elMedRc && hist.media_nacional_rc_pc) elMedRc.textContent = Number(hist.media_nacional_rc_pc).toFixed(2) + '%';
    if (elMedPop && hist.media_nacional_pop) elMedPop.textContent = Number(hist.media_nacional_pop).toFixed(2) + '%';

    const filterText = getActiveFilterText();
    const filterLabel = getActiveFilterLabel();
    const txtFiltroRc = document.getElementById('text-filtro-nome-rc');
    const txtFiltroPop = document.getElementById('text-filtro-nome-pop');
    const txtLegendCjt = document.getElementById('text-legend-cjt');
    
    if (txtFiltroRc) txtFiltroRc.textContent = filterText;
    if (txtFiltroPop) txtFiltroPop.textContent = filterText;
    if (txtLegendCjt) txtLegendCjt.textContent = `${filterLabel.toUpperCase()} (EVOLUÇÃO)`;

    const p00 = hist.percentil00 || 0;
    const p24 = hist.percentil24 || 0;
    const d00 = Math.max(1, Math.ceil(p00 / 10));
    const d24 = Math.max(1, Math.ceil(p24 / 10));
    const q00 = Math.max(1, Math.ceil(p00 / 20));
    const q24 = Math.max(1, Math.ceil(p24 / 20));

    const c00 = document.getElementById('circle-2000');
    const c24 = document.getElementById('circle-2024');
    if (c00) {
        c00.dataset.percentil = p00;
        c00.dataset.decil = d00;
        c00.dataset.quintil = q00;
    }
    if (c24) {
        c24.dataset.percentil = p24;
        c24.dataset.decil = d24;
        c24.dataset.quintil = q24;
    }
    
    updateTimelineColors(timelineMode);
    
    document.querySelectorAll('#timeline-toggle .segmented-option').forEach(btn => {
        btn.onclick = function() {
            document.querySelectorAll('#timeline-toggle .segmented-option').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            timelineMode = this.dataset.mode;
            updateTimelineColors(timelineMode);
        }
    });

    const canvasRc = document.getElementById('chartReceitaEvo');
    if (canvasRc) {
      if (chartReceitaEvoInstance) chartReceitaEvoInstance.destroy();
      chartReceitaEvoInstance = new Chart(canvasRc.getContext('2d'), {
        type: 'bar',
        data: {
          labels: [filterLabel, 'Média Nacional'],
          datasets: [{
            data: [deltaRc, Number(hist.media_nacional_rc_pc) || 0],
            backgroundColor: ['#103758', '#cbd5e1'],
            borderRadius: 6,
            barPercentage: 0.5
          }]
        },
        options: commonEvoOptions,
        plugins: [topLabelsPlugin]
      });
    }

    const canvasPop = document.getElementById('chartPopEvo');
    if (canvasPop) {
      if (chartPopEvoInstance) chartPopEvoInstance.destroy();
      chartPopEvoInstance = new Chart(canvasPop.getContext('2d'), {
        type: 'bar',
        data: {
          labels: [filterLabel, 'Média Nacional'],
          datasets: [{
            data: [deltaPop, Number(hist.media_nacional_pop) || 0],
            backgroundColor: ['#EEAF19', '#cbd5e1'],
            borderRadius: 6,
            barPercentage: 0.5
          }]
        },
        options: commonEvoOptions,
        plugins: [topLabelsPlugin]
      });
    }
  }

  async function updateFiscalDetails(){
    try{
      const resp = await fetch(`/api/fiscal-details/?${buildParams()}`);
      if(!resp.ok) throw new Error('Falha ao buscar detalhes fiscais.');
      const data = await resp.json();
      
      const cont = document.getElementById('main-revenue-details-container');
      cont.innerHTML = data.html;
      
      initializeToggleListeners(cont);
      setValorMode(isShowingPerCapita ? 'percapita' : 'real');
      sortAllRevenueSections(isShowingPerCapita);
      buildHeadingIndex(document);

      // Síntese Fiscal
      const sinteseEl = document.getElementById('sintese-fiscal-container');
      const hist = data.hist_data;
      const hasData = hist && (hist.pop00 > 0 || hist.rc00 > 0);
      if (sinteseEl) {
        if (hasData) {
          sinteseEl.style.display = '';
          renderEvolutionCharts(hist);
        } else {
          sinteseEl.style.display = 'none';
        }
      }
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

  function getActiveFilterLabel() {
    const regiao = document.getElementById('filtro-regiao')?.value;
    const uf = document.getElementById('filtro-uf')?.value;
    const rm = document.getElementById('filtro-rm')?.value;
    const porte = document.getElementById('filtro-porte')?.value;
    
    if (rm && rm !== 'todos') {
      const sel = document.getElementById('filtro-rm');
      return `${sel.options[sel.selectedIndex].text}`;
    }
    if (uf && uf !== 'todos') return `UF: ${uf}`;
    if (regiao && regiao !== 'todos') return `Região ${regiao}`;
    if (porte && porte !== 'todos') return `Porte: ${porte}`;
    return 'Todos os Municípios';
  }

  function getActiveFilterText() {
    const regiao = document.getElementById('filtro-regiao')?.value;
    const uf = document.getElementById('filtro-uf')?.value;
    const rm = document.getElementById('filtro-rm')?.value;
    const porte = document.getElementById('filtro-porte')?.value;
    
    if (rm && rm !== 'todos') {
      const sel = document.getElementById('filtro-rm');
      return `da ${sel.options[sel.selectedIndex].text}`;
    }
    if (uf && uf !== 'todos') {
      return `de ${uf}`;
    }
    if (regiao && regiao !== 'todos') {
      return `da região ${regiao}`;
    }
    if (porte && porte !== 'todos') {
      return `dos municípios de porte ${porte}`;
    }
    return 'de todo o Brasil';
  }

  async function updateChart(){
    try{
      const r=await fetch(`/api/conjunto-chart-data/?${buildParams()}`);
      if(!r.ok) throw new Error('Falha ao buscar dados do gráfico.');
      currentChartData=await r.json();
      
      const chartSection = document.getElementById('chart-section');
      const emptyState = document.getElementById('chart-empty-state');
      
      if (Object.keys(currentChartData).length === 0) {
          if (chartSection) chartSection.style.display = 'none';
          if (emptyState) emptyState.style.display = 'block';
      } else {
          if (chartSection) chartSection.style.display = 'flex';
          if (emptyState) emptyState.style.display = 'none';
          renderChart(selectEl.value,currentChartData);
      }
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