// detail/static/detail/js/script_mun.js
document.addEventListener('DOMContentLoaded', function () {
    const DEBUG = false;
    const log  = (...a) => DEBUG && console.log('[detail-mun]', ...a);
    const warn = (...a) => DEBUG && console.warn('[detail-mun]', ...a);
  
    const $  = (sel, root=document) => root.querySelector(sel);
    const $$ = (sel, root=document) => Array.from(root.querySelectorAll(sel));
  
    // ------------ JSON helpers ------------
    function safeParseJSONById(id) {
      const el = document.getElementById(id);
      if (!el) return null;
      const txt = el.textContent?.trim();
      if (!txt) return null;
      try { let v = JSON.parse(txt); if (typeof v === 'string') v = JSON.parse(v); return v; }
      catch { return null; }
    }
    function getJsonText(id){ const el = document.getElementById(id); return (el && el.textContent) ? el.textContent.trim() : ''; }
    function parseRankingDataFromText(id){
      const txt = getJsonText(id); if (!txt) return null;
      const keys = ['rank_nacional','total_nacional','rank_estadual','total_estadual','rank_faixa','total_faixa'];
      const out = {};
      for (const k of keys){
        const re = new RegExp(`"${k}"\\s*:\\s*([^,}\\n\\r]+)`); const m = txt.match(re);
        if (!m){ out[k] = null; continue; }
        const raw = m[1].trim();
        if (/^null$/i.test(raw)) { out[k] = null; continue; }
        const unq = raw.replace(/^"(.*)"$/, '$1'); const digitsOnly = unq.replace(/\D+/g, '');
        out[k] = digitsOnly ? parseInt(digitsOnly, 10) : null;
      }
      return out;
    }
  
    // ------------ normalizers/formatters ------------
    const normalize = (str) => (str||'')
      .normalize('NFD').replace(/\p{Diacritic}/gu,'')
      .replace(/R\$\s?[\d\.,]+/g,' ')
      .replace(/[\d\.,]+/g,' ')
      .replace(/\s+/g,' ')
      .trim().toLowerCase();
  
    const fmtInt = (n) => (Number.isFinite(n) ? new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 }).format(n) : '—');
  
    const cleanText = (h) => {
      if (!h) return '';
      const c = h.cloneNode(true);
      c.querySelectorAll('.valor-absoluto,.valor-per-capita,.ranking-indicator-container').forEach(n=>n.remove());
      return (c.textContent || h.textContent || '').trim();
    };
  
    // ------------ Dados vindos do template ------------
    const allRevenueChartData = safeParseJSONById('chart-data');
    const percentileData      = safeParseJSONById('percentile-data');
    
    let municipioData = safeParseJSONById('municipio-data');
    if (!municipioData) {
        municipioData = parseRankingDataFromText('municipio-data');
    }
  
    // ------------ mapa “heading -> key” para percentis ------------
    const HEADING_TO_KEY = {
      'receita corrente':'rc',
      'transferencias correntes':'transferencias_correntes',
      'transferencias da uniao':'transferencias_uniao',
      'transferencias dos estados':'transferencias_estado',
      'outras transferencias':'outras_transferencias',
      'impostos, taxas e contribuicoes de melhoria':'imposto_taxas_contribuicoes',
      'impostos':'imposto',
      'taxas':'taxas',
      'contribuicoes de melhoria':'contribuicoes_melhoria',
      'outras receitas correntes':'outras_receitas',
      'contribuicoes':'contribuicoes'
    };
  
    // ------------ indicador (cores + tooltip da árvore) ------------
    function paintIndicator(container, percentile) {
      if (!container || percentile == null) return;
      const pct = parseFloat(percentile);
      if (isNaN(pct)) return;
  
      const ind = container.querySelector('.ranking-indicator') || container;
      const tip = container.querySelector('.ranking-tooltip');
  
      ind.classList.remove('quintil-1','quintil-2','quintil-3','quintil-4','quintil-5');
      if (pct <= 20) ind.classList.add('quintil-1');
      else if (pct <= 40) ind.classList.add('quintil-2');
      else if (pct <= 60) ind.classList.add('quintil-3');
      else if (pct <= 80) ind.classList.add('quintil-4');
      else ind.classList.add('quintil-5');
  
      if (tip) tip.textContent = `O município supera ${pct}% dos outros municípios`;
    }
  
    // ------------ FUNÇÃO DE RANKING UNIFICADA E BLINDADA ------------
    function updateRankingUI(selected) {
      if (percentileData) {
        $$('.revenue-item-wrapper').forEach(wrap => {
          let key = wrap.querySelector('[data-field-base]')?.dataset.fieldBase;
          if (!key) {
            const heading = wrap.querySelector('.toggle-heading');
            const txt = normalize(cleanText(heading));
            key = HEADING_TO_KEY[txt];
          }
          const pct = (key && percentileData[key]) ? percentileData[key][selected] : null;
          const container = wrap.querySelector('.ranking-indicator-container');
          
          if (pct != null && !isNaN(parseFloat(pct))) {
            paintIndicator(container, pct);
          } else if (container) {
            const ind = container.querySelector('.ranking-indicator');
            ind?.classList.remove('quintil-1','quintil-2','quintil-3','quintil-4','quintil-5');
            const tip = container.querySelector('.ranking-tooltip');
            if (tip) tip.textContent = 'Ranking não disponível';
          }
        });
      }
  
      const rankingValueEl = document.getElementById('ranking-value');
      if (rankingValueEl && municipioData) {
        const map = {
          nacional: ['rank_nacional','total_nacional'],
          estadual: ['rank_estadual','total_estadual'],
          faixa:    ['rank_faixa','total_faixa'],
        };
        const [rkKey, totKey] = map[selected] || map.nacional;
        
        const toSafeInt = (val) => {
            if (val == null) return NaN;
            return parseInt(String(val).replace(/\D+/g, ''), 10);
        };

        const rk  = toSafeInt(municipioData[rkKey]);
        const tot = toSafeInt(municipioData[totKey]);
        
        rankingValueEl.classList.remove(
            'text-quintil-1', 'text-quintil-2', 'text-quintil-3', 
            'text-quintil-4', 'text-quintil-5', 'text-[var(--fnp-dark-blue)]'
        );
        
        let rankColorClass = 'text-[var(--fnp-dark-blue)]';

        if (!isNaN(rk) && !isNaN(tot) && tot > 0) {
            const percentilReal = ((tot - rk) / tot) * 100;
            
            if (percentilReal <= 20) rankColorClass = 'text-[#A81C21]';
            else if (percentilReal <= 40) rankColorClass = 'text-[#E47326]';
            else if (percentilReal <= 60) rankColorClass = 'text-[#F4D01D]';
            else if (percentilReal <= 80) rankColorClass = 'text-[#6AC074]';
            else rankColorClass = 'text-[#1C9148]';

            rankingValueEl.innerHTML = `<span class="${rankColorClass}">${fmtInt(rk)}</span> <span class="text-slate-400 font-medium text-3xl">/</span> <span id="ranking-total" class="text-2xl text-slate-500 opacity-75">${fmtInt(tot)}</span>`;
        } else {
            rankingValueEl.innerHTML = `<span class="${rankColorClass}">—</span> <span class="text-slate-400 font-medium text-3xl">/</span> <span id="ranking-total" class="text-2xl text-slate-500 opacity-75">—</span>`;
        }
      }
    }
  
    // ------------ toggles da Árvore ------------
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
  
    // ------------ ordenação (VR/PC) ------------
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
  
    // ------------ Toggle PC/VR ------------
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
  
    // ------------ índice de headings (Gráfico -> Árvore) ------------
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
  
    // ==========================================
    // CONTROLE DO DROPDOWN CUSTOMIZADO DE RANKING
    // ==========================================
    const rankingSelect = document.getElementById('ranking-select');
    const triggerBtn = document.getElementById('custom-ranking-trigger');
    const menuDropdown = document.getElementById('custom-ranking-menu');
    const arrowIcon = document.getElementById('custom-ranking-arrow');
    const selectedText = document.getElementById('custom-ranking-text');
    const options = document.querySelectorAll('.ranking-option');
  
    if (triggerBtn && menuDropdown) {
        triggerBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const isClosed = menuDropdown.classList.contains('opacity-0');
            if (isClosed) {
                menuDropdown.classList.remove('opacity-0', 'scale-95', 'pointer-events-none');
                menuDropdown.classList.add('opacity-100', 'scale-100', 'pointer-events-auto');
                arrowIcon.style.transform = 'rotate(180deg)';
            } else {
                closeMenu();
            }
        });
  
        function closeMenu() {
            menuDropdown.classList.remove('opacity-100', 'scale-100', 'pointer-events-auto');
            menuDropdown.classList.add('opacity-0', 'scale-95', 'pointer-events-none');
            arrowIcon.style.transform = 'rotate(0deg)';
        }
  
        options.forEach(option => {
            option.addEventListener('click', (e) => {
                e.preventDefault();
                const value = option.getAttribute('data-value');
                const text = option.textContent;
                
                selectedText.textContent = text;
                
                if (rankingSelect) {
                    rankingSelect.value = value;
                    updateRankingUI(value); // Roda a função direto aqui!
                }
                closeMenu();
            });
        });
  
        document.addEventListener('click', (e) => {
            if (!triggerBtn.contains(e.target) && !menuDropdown.contains(e.target)) {
                closeMenu();
            }
        });
    }
  
    // ========== GRÁFICO (COMPOSIÇÃO) + SELECT DINÂMICO ==========
    const canvas = $('#myChart');
    let chart = null;
    let currentKey = 'main_categories';

    if (canvas && window.Chart) {
        canvas.style.cursor = 'pointer';
        const ctx = canvas.getContext('2d');
    
        const labelOf = (k) => ({
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
        }[k] || k);
    
        const CHILDREN = {
        imposto_taxas_contribuicoes: ['imposto', 'taxas', 'contribuicoes_melhoria'],
        transferencias_correntes: ['transferencias_uniao', 'transferencias_estado'],
        };
        const PARENT = {
        imposto: 'imposto_taxas_contribuicoes',
        taxas: 'imposto_taxas_contribuicoes',
        contribuicoes_melhoria: 'imposto_taxas_contribuicoes',
        transferencias_uniao: 'transferencias_correntes',
        transferencias_estado: 'transferencias_correntes',
        };
        
        const hasData = (key) => {
        const d = allRevenueChartData?.[key];
        return d && Array.isArray(d.labels) && d.labels.length && Array.isArray(d.values) && d.values.length;
        };
    
        const selectEl = document.getElementById('chart-category-select');
    
        function buildSelectFor(currentKey){
            if(!selectEl) return;
            let keys = ['main_categories'];
        
            if (currentKey === 'main_categories') {
                keys.push('imposto_taxas_contribuicoes','contribuicoes','transferencias_correntes','outras_receitas');
            } else {
                const parent = PARENT[currentKey] || null;
                if (parent) keys.push(parent);
                keys.push(currentKey);
                const kids = CHILDREN[currentKey] || CHILDREN[parent] || [];
                keys.push(...kids);
            }
        
            const seen = new Set();
            const finalKeys = keys.filter(k=>{
                if (seen.has(k)) return false;
                seen.add(k);
                return hasData(k) || k === 'main_categories';
            });
        
            selectEl.innerHTML = '';
            finalKeys.forEach(k=>{
                const opt = document.createElement('option');
                opt.value = k;
                opt.textContent = labelOf(k);
                selectEl.appendChild(opt);
            });
            selectEl.value = currentKey;
        }
    
        const COLOR_BY_LABEL = {
        'Impostos, Taxas e Contribuições': '#1f77b4',
        'Contribuições': '#ff7f0e',
        'Transf. Correntes': '#2ca02c',
        'Outras': '#d62728'
        };
        const palette = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd','#8c564b','#e377c2','#7f7f7f','#bcbd22','#17becf'];
    
        function notifyDensityKey(key){
            if (!selectEl || !key) return;
            selectEl.dispatchEvent(new CustomEvent('composition-category-changed', { bubbles: true, detail: { key } }));
        }
    
        function toSnakeKey(str){
            return String(str || '').normalize('NFD').replace(/\p{Diacritic}/gu,'').replace(/R\$\s?[\d\.,]+/g,' ').replace(/[\d\.,]+/g,' ').trim().toLowerCase().replace(/[^a-z0-9]+/g,'_').replace(/^_+|_+$/g,'');
        }
    
        const DENSITY_CHILD_KEYS = {
            imposto: new Map([[normalize('Imposto sobre Serviços'), 'iss'], [normalize("Imposto sobre a Transmissão 'Inter Vivos'"), 'itbi'], [normalize('Imposto sobre a Propriedade Predial e Territorial Urbana'), 'iptu'], [normalize('Imposto de Renda'), 'imposto_renda'], [normalize('Outros Impostos'), 'outros_impostos'], [normalize('Outros'), 'outros_impostos']]),
            taxas: new Map([[normalize('Taxas pelo Exercício do Poder de Polícia'), 'taxa_policia'], [normalize('Taxas pela Prestação de Serviços'), 'taxa_prestacao_servico'], [normalize('Outras Taxas'), 'outras_taxas'], [normalize('Outros'), 'outras_taxas']]),
            contribuicoes_melhoria: new Map([[normalize('Contribuição de Melhoria para Pavimentação e Obras'), 'contribuicao_melhoria_pavimento_obras'], [normalize('Contribuição de Melhoria para Rede de Água e Esgoto'), 'contribuicao_melhoria_agua_potavel'], [normalize('Contribuição de Melhoria para Iluminação Pública'), 'contribuicao_melhoria_iluminacao_publica'], [normalize('Outras Contribuições de Melhoria'), 'outras_contribuicoes_melhoria'], [normalize('Outros'), 'outras_contribuicoes_melhoria']]),
            contribuicoes: new Map([[normalize('Custeio do Serviço de Iluminação Pública'), 'contribuicoes_sociais'], [normalize('Outras Contribuições'), 'outras_contribuicoes'], [normalize('Outros'), 'outras_contribuicoes']]),
            transferencias_uniao: new Map([[normalize('Cota-Parte do FPM'), 'transferencias_uniao_fpm'], [normalize('Compensação Financeira (Recursos Naturais)'), 'transferencias_uniao_exploracao'], [normalize('Recursos do SUS'), 'transferencias_uniao_sus'], [normalize('Recursos do FNDE'), 'transferencias_uniao_fnde'], [normalize('Recursos do FUNDEB'), 'transferencias_uniao_fundeb'], [normalize('Recursos do FNAS'), 'transferencias_uniao_fnas'], [normalize('Recursos do Fundo Especial'), 'transferencias_uniao_fundo'], [normalize('Outras Transferências da União'), 'outras_transferencias_uniao'], [normalize('Outras'), 'outras_transferencias_uniao']]),
            transferencias_estado: new Map([[normalize('Cota-Parte do ICMS'), 'transferencias_estado_icms'], [normalize('Cota-Parte do IPVA'), 'transferencias_estado_ipva'], [normalize('Recursos do SUS'), 'transferencias_estado_sus'], [normalize('Assistência Social'), 'transferencias_estado_assistencia'], [normalize('Compensação Financeira (Recursos Naturais)'), 'transferencias_estado_exploracao'], [normalize('Outras Transferências dos Estados'), 'outras_transferencias_estado'], [normalize('Outras'), 'outras_transferencias_estado']]),
            outras_receitas: new Map([[normalize('Receita Patrimonial'), 'receita_patrimonial'], [normalize('Receita Agropecuária'), 'receita_agropecuaria'], [normalize('Receita Industrial'), 'receita_industrial'], [normalize('Receita de Serviços'), 'receita_servicos'], [normalize('Outras Receitas'), 'outras_receitas_outras'], [normalize('Outras'), 'outras_receitas_outras']])
        };
    
        const OUTROS_KEY_BY_GROUP = {
            imposto: 'outros_impostos', taxas: 'outras_taxas', contribuicoes_melhoria: 'outras_contribuicoes_melhoria', transferencias_uniao: 'outras_transferencias_uniao', transferencias_estado: 'outras_transferencias_estado', outras_receitas: 'outras_receitas_outras'
        };
    
        function resolveDensityChildKey(groupKey, clickedLabel){
            const n = normalize(clickedLabel);
            const table = DENSITY_CHILD_KEYS[groupKey];
            if (table?.has(n)) return table.get(n);
            if (table){ for (const [k,v] of table.entries()){ if (n.includes(k) || k.includes(n)) return v; } }
            if (n.includes('outro')) return OUTROS_KEY_BY_GROUP[groupKey] || toSnakeKey(clickedLabel);
            return toSnakeKey(clickedLabel);
        }
    
        function setCategoryAndSync(key){
            if (!selectEl) return;
            if (currentKey === key) {
                selectEl.dispatchEvent(new CustomEvent('composition-category-changed', { bubbles:true, detail:{ key } }));
                return;
            }
            currentKey = key;
            buildSelectFor(key);
            selectEl.value = key;
            renderChart(key);
            selectEl.dispatchEvent(new CustomEvent('composition-category-changed', { bubbles:true, detail:{ key } }));
        }
    
        if (selectEl){
            selectEl.addEventListener('change', () => setCategoryAndSync(selectEl.value));
        }
    
          function renderChart(key){
            const d = allRevenueChartData?.[key];
            if (!d){ return; }
            
            const total = d.values.reduce((a,b)=>a+b,0);
            const labels = d.labels.slice();
            const background = labels.map((lbl,i)=> COLOR_BY_LABEL[lbl] || palette[i%palette.length]);
        
            // PASSAGEM DE VALORES ABSOLUTOS PARA RENDERIZACAO CIRCULAR
            const dataset = {
                label: labelOf(key).toUpperCase(), 
                data: d.values, 
                backgroundColor: background, 
                borderWidth: 2,
                borderColor: '#ffffff',
                hoverOffset: 4
            };
        
            if (chart) chart.destroy();
            chart = new Chart(ctx, {
                type: 'doughnut',
                data: { labels, datasets: [dataset] },
                options: {
                    responsive: true, 
                    maintainAspectRatio: false,
                    // CONFIGURACAO DE ESTILO E POSICIONAMENTO DA LEGENDA
                    plugins: { 
                        legend: { 
                            display: true,
                            position: 'bottom',
                            labels: {
                                padding: 20,
                                usePointStyle: true,
                                pointStyle: 'circle',
                                font: {
                                    size: 11,
                                    family: "'Inter', sans-serif"
                                }
                            }
                        }, 
                        tooltip: { 
                            callbacks: { 
                                label: (ct) => { 
                                    const i = ct.dataIndex; 
                                    const raw = d.values[i]; 
                                    const pct = total ? (raw / total) * 100 : 0; 
                                    return `${labels[i]}: ${pct.toFixed(1)}% (${new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(raw)})`; 
                                }, 
                                footer: () => `Total: ${new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(total)}` 
                            } 
                        } 
                    },
                    cutout: '50%',
                    layout: {
                        padding: {
                            top: 0,
                            bottom: 0
                        }
                    }
                }
            });
        
            // CONTROLE DE EVENTOS DE CLIQUE MANTIDO INTACTO
            canvas.onclick = (evt) => {
                const pts = chart.getElementsAtEventForMode(evt,'nearest',{intersect:true},true);
                if (!pts.length) return;
                const idx = pts[0].index;
                const clickedLabel = labels[idx];
                const n = normalize(clickedLabel);
        
                if (key === 'main_categories') {
                    const dynMap = new Map();
                    for (const lbl of labels) {
                        const nl = normalize(lbl);
                        if (nl.includes('transf')) { dynMap.set(nl,'transferencias_correntes'); continue; }
                        if (nl === 'outras' || nl.includes('outras receitas')) { dynMap.set(nl,'outras_receitas'); continue; }
                        if (nl.includes('imposto') || nl.includes('taxa') || nl.includes('melhoria')) { dynMap.set(nl,'imposto_taxas_contribuicoes'); continue; }
                        if (nl.startsWith('contribu')) { dynMap.set(nl,'contribuicoes'); continue; }
                    }
                    const nxt = dynMap.get(n);
                    if (nxt) setCategoryAndSync(nxt);
                    return;
                }
        
                if (key === 'imposto_taxas_contribuicoes') {
                    if (n.includes('imposto'))  { setCategoryAndSync('imposto'); return; }
                    if (n.includes('taxa'))     { setCategoryAndSync('taxas'); return; }
                    if (n.includes('melhoria')) { setCategoryAndSync('contribuicoes_melhoria'); return; }
                    openByLabel(clickedLabel); return;
                }
        
                if (key === 'transferencias_correntes') {
                    if (n.includes('uniao'))  { setCategoryAndSync('transferencias_uniao');  return; }
                    if (n.includes('estado')) { setCategoryAndSync('transferencias_estado'); return; }
                    openByLabel(clickedLabel); return;
                }
        
                if (['imposto', 'taxas', 'contribuicoes_melhoria', 'transferencias_uniao', 'transferencias_estado', 'outras_receitas'].includes(key)) {
                    openByLabel(clickedLabel);
                    notifyDensityKey(resolveDensityChildKey(key, clickedLabel));
                    return;
                }
        
                openByLabel(clickedLabel);
            };
        }
    }
  
  // ========== LINHA DO TEMPO (QUINTIL/DECIL) ==========
  const timelineBtns = document.querySelectorAll('#timeline-toggle .segmented-option');
  // CORRECAO DO SELETOR PARA O ALVO DO DOM
  const timelineCircles = document.querySelectorAll('.timeline-circle-dynamic');

  const FNP_RANK_COLORS = {
      '1': '#A81C21',
      '2': '#E47326',
      '3': '#F4D01D',
      '4': '#6AC074',
      '5': '#1C9148'
  };

  const FNP_DECIL_COLORS = {
    '1': '#960E16',
    '2': '#CF3026',
    '3': '#EB6630',
    '4': '#F8A555',
    '5': '#FCE182',
    '6': '#DDEC88',
    '7': '#9DD57D',
    '8': '#60BA69',
    '9': '#2D964D',
    '10': '#076931'
};

  const DECIL_TO_QUINTIL = {
      '1': '1', '2': '1', '3': '2', '4': '2', '5': '3', 
      '6': '3', '7': '4', '8': '4', '9': '5', '10': '5'
  };

  function updateTimelineColors(mode) {
      timelineCircles.forEach(circle => {
          const rawValue = circle.getAttribute('data-' + mode) || '-';
          const spanText = circle.querySelector('span');
          
          // MANIPULACAO EXCLUSIVA DO NO DE TEXTO INTERNO
          if (spanText) {
              spanText.textContent = rawValue;
          }

          // EXTRACAO DE CARACTERES NUMERICOS DO ATRIBUTO DATA
          const numMatch = rawValue.match(/\d+/);
          const num = numMatch ? numMatch[0] : null;
          
          // RESOLUCAO DA PALETA DE CORES CONFORME MODO ATIVO
          const activePalette = mode === 'decil' ? FNP_DECIL_COLORS : FNP_RANK_COLORS;
          const hex = num ? activePalette[num] : null;

          // INJECAO DE ESTILOS CSS NOS ELEMENTOS DO DOM
          if (hex) {
              circle.style.backgroundColor = hex;
              circle.style.borderColor = hex;
              
              // CONTROLE DE CONTRASTE DA TIPOGRAFIA BASEADO NA LUMINOSIDADE DA COR
              if (spanText) {
                  const isLightBackground = (mode === 'quintil' && num === '3') || (mode === 'decil' && (num === '5' || num === '6'));
                  spanText.style.color = isLightBackground ? '#103758' : '#ffffff';
              }
          } else {
              // ESTADO DE FALLBACK PARA DADOS AUSENTES OU INVALIDOS
              circle.style.backgroundColor = '#ffffff';
              circle.style.borderColor = '#e2e8f0';
              
              if (spanText) {
                  spanText.style.color = '#94a3b8';
              }
          }
      });
  }

  timelineBtns.forEach(btn => {
    btn.addEventListener('click', function() {
      timelineBtns.forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      updateTimelineColors(this.getAttribute('data-mode'));
    });
  });
      
    // -------- INICIALIZAÇÕES FINAIS --------
    buildHeadingIndex();
    showMode('pc');
    if (typeof buildSelectFor === 'function') buildSelectFor(currentKey);
    if (typeof renderChart === 'function') renderChart(currentKey);
    initializeToggleListeners();
    updateRankingUI(rankingSelect?.value || 'nacional');
    
    // Dispara a cor inicial da linha do tempo
    updateTimelineColors('quintil');

    
    // -------- INICIALIZAÇÃO FINAL DA PÁGINA --------
    buildHeadingIndex();
    showMode('pc');
    if (typeof buildSelectFor === 'function') buildSelectFor(currentKey);
    if (typeof renderChart === 'function') renderChart(currentKey);
    initializeToggleListeners();
    updateRankingUI(rankingSelect?.value || 'nacional');

    // ==========================================
    // GRÁFICOS SEPARADOS DE EVOLUÇÃO (Receita e População)
    // ==========================================
    const canvasRec = document.getElementById('chartReceita');
    const canvasPop = document.getElementById('chartPop');
    const evoDataScript = document.getElementById('evolution-compare-data');

    if (canvasRec && canvasPop && evoDataScript) {
        try {
            const rawData = JSON.parse(evoDataScript.textContent);
            
            // Conversor à prova de balas (Entende 2.025,09 e transforma em 2025.09 pro JS)
            const parseSafe = (val) => {
                if (!val) return 0;
                let str = String(val).trim();
                if (str.includes('.') && str.includes(',')) {
                    str = str.replace(/\./g, '').replace(',', '.');
                } else if (str.includes(',')) {
                    str = str.replace(',', '.');
                }
                return parseFloat(str) || 0;
            };

            const commonOptions = {
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
                        grid: { color: '#f1f5f9' }, 
                        ticks: { color: '#94a3b8', callback: (val) => val + '%' } 
                    }
                }
            };

            // Gráfico 1: Receita (Azul)
            new Chart(canvasRec.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: [rawData.nome_muni || 'Município', 'Média do Estado', 'Média Nacional'],
                    datasets: [{
                        data: [parseSafe(rawData.receita.mun), parseSafe(rawData.receita.est), parseSafe(rawData.receita.nac)],
                        backgroundColor: ['#103758', '#cbd5e1', '#94a3b8'],
                        borderRadius: 6,
                        barPercentage: 0.5
                    }]
                },
                options: commonOptions
            });

            // Gráfico 2: População (Amarelo)
            new Chart(canvasPop.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: [rawData.nome_muni || 'Município', 'Média do Estado', 'Média Nacional'],
                    datasets: [{
                        data: [parseSafe(rawData.populacao.mun), parseSafe(rawData.populacao.est), parseSafe(rawData.populacao.nac)],
                        backgroundColor: ['#EEAF19', '#cbd5e1', '#94a3b8'],
                        borderRadius: 6,
                        barPercentage: 0.5
                    }]
                },
                options: commonOptions
            });

        } catch (e) {
            console.error("Erro ao gerar gráficos de evolução:", e);
        }
    }


}); //fechamento DOM