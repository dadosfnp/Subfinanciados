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
  
      ind.classList.remove('quintil-0','quintil-1','quintil-2','quintil-3','quintil-4','quintil-5');
      
      if (pct < 0) ind.classList.add('quintil-1');
      else if (pct <= 20) ind.classList.add('quintil-1');
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
      
      $$('.lbl-tipo-valor').forEach(el => {
          el.textContent = pc ? 'Valor por Habitante' : 'Valor Real';
      });

      $$('.media-block-wrapper').forEach(el => el.classList.toggle('hidden', !pc));

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
  
    
// ==========================================================================
    // CONTROLE DOS RANKINGS INDEPENDENTES (POPULAÇÃO E RECEITA)
    // ==========================================================================
    const kpiRankingTriggers = document.querySelectorAll('.kpi-ranking-trigger');
    const kpiRankOptions = document.querySelectorAll('.rank-opt');

    // 1. Função para abrir/fechar menu
    kpiRankingTriggers.forEach(trigger => {
        trigger.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const menu = this.nextElementSibling;
            const arrow = this.querySelector('svg');
            const isOpen = !menu.classList.contains('opacity-0');

            // Fecha outros menus antes de abrir o atual
            document.querySelectorAll('.kpi-ranking-menu').forEach(m => {
                m.classList.add('opacity-0', 'scale-95', 'pointer-events-none');
                m.previousElementSibling.querySelector('svg').style.transform = 'rotate(0deg)';
            });

            if (!isOpen) {
                menu.classList.remove('opacity-0', 'scale-95', 'pointer-events-none');
                menu.classList.add('opacity-100', 'scale-100', 'pointer-events-auto');
                arrow.style.transform = 'rotate(180deg)';
            }
        });
    });

    // 2. Lógica de Troca de Valores
    kpiRankOptions.forEach(option => {
        option.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const type = this.getAttribute('data-type');
            const value = this.getAttribute('data-value');
            const card = this.closest('article');
            const textSelected = this.textContent;

            const label = card.querySelector('.ranking-label');
            if (label) label.textContent = textSelected;

            const displayEl = card.querySelector('.rank-display-value');
            const dataKey = `data-${type}-${value}`;
            const rawVal = displayEl.getAttribute(dataKey);

            if (rawVal) {
                const parts = rawVal.split('/');
                if (parts.length === 2) {
                    displayEl.innerHTML = `${parts[0].trim()}<span class="text-xs font-bold opacity-30 ml-1">/ ${parts[1].trim()}</span>`;
                } else {
                    displayEl.textContent = rawVal;
                }
            }

            if (type === 'rev' && typeof updateRankingUI === 'function') {
                updateRankingUI(value);
            }

            const menu = this.closest('.kpi-ranking-menu');
            if (menu) {
                menu.classList.add('opacity-0', 'scale-95', 'pointer-events-none');
                menu.classList.remove('opacity-100', 'scale-100', 'pointer-events-auto');
            }
            
            const triggerSvg = card.querySelector('.kpi-ranking-trigger svg');
            if (triggerSvg) triggerSvg.style.transform = 'rotate(0deg)';
        });
    });

    // Fecha ao clicar fora
    document.addEventListener('click', function() {
        document.querySelectorAll('.kpi-ranking-menu').forEach(menu => {
            menu.classList.add('opacity-0', 'scale-95', 'pointer-events-none');
            menu.classList.remove('opacity-100', 'scale-100', 'pointer-events-auto');
            
            const trigger = menu.previousElementSibling;
            if (trigger && trigger.querySelector('svg')) {
                trigger.querySelector('svg').style.transform = 'rotate(0deg)';
            }
        });
    });


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
            imposto: new Map([[normalize('Imposto sobre Serviços'), 'iss'], [normalize("Imposto sobre a Transmissão 'Inter Vivos'"), 'itbi'], [normalize('Imposto sobre a Propriedade Predial e Territorial Urbana'), 'iptu'], [normalize('Imposto de Renda'), 'imposto_renda'], [normalize('Imposto sobre o ICMS'), 'imposto_icms'], [normalize('Imposto sobre o IPVA'), 'imposto_ipva'], [normalize('Outros Impostos'), 'outros_impostos'], [normalize('Outros'), 'outros_impostos']]),
            taxas: new Map([[normalize('Taxas pelo Exercício do Poder de Polícia'), 'taxa_policia'], [normalize('Taxas pela Prestação de Serviços'), 'taxa_prestacao_servico'], [normalize('Outras Taxas'), 'outras_taxas'], [normalize('Outros'), 'outras_taxas']]),
            contribuicoes_melhoria: new Map([[normalize('Contribuição de Melhoria para Pavimentação e Obras'), 'contribuicao_melhoria_pavimento_obras'], [normalize('Contribuição de Melhoria para Rede de Água e Esgoto'), 'contribuicao_melhoria_agua_potavel'], [normalize('Contribuição de Melhoria para Iluminação Pública'), 'contribuicao_melhoria_iluminacao_publica'], [normalize('Outras Contribuições de Melhoria'), 'outras_contribuicoes_melhoria'], [normalize('Outros'), 'outras_contribuicoes_melhoria']]),
            contribuicoes: new Map([[normalize('Custeio do Serviço de Iluminação Pública'), 'contribuicoes_sociais'], [normalize('Outras Contribuições'), 'outras_contribuicoes'], [normalize('Outros'), 'outras_contribuicoes']]),
            transferencias_uniao: new Map([[normalize('Cota-Parte do FPM'), 'transferencias_uniao_fpm'], [normalize('Cota-Parte do FPE'), 'transferencias_uniao_fpe'], [normalize('Compensação Financeira (Recursos Naturais)'), 'transferencias_uniao_exploracao'], [normalize('Recursos do SUS'), 'transferencias_uniao_sus'], [normalize('Recursos do FNDE'), 'transferencias_uniao_fnde'], [normalize('Recursos do FUNDEB'), 'transferencias_uniao_fundeb'], [normalize('Recursos do FNAS'), 'transferencias_uniao_fnas'], [normalize('Recursos do Fundo Especial'), 'transferencias_uniao_fundo'], [normalize('Outras Transferências da União'), 'outras_transferencias_uniao'], [normalize('Outras'), 'outras_transferencias_uniao']]),
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
            // DETECTA SE É MOBILE PARA AJUSTAR A FONTE E A QUEBRA DA LEGENDA
            const isMobile = window.innerWidth < 768;

            chart = new Chart(ctx, {
                type: 'doughnut',
                data: { labels, datasets: [dataset] },
                options: {
                    responsive: true, 
                    maintainAspectRatio: false,
                    plugins: { 
                        legend: { 
                            display: true,
                            position: 'bottom',
                            align: 'center',
                            labels: {
                                padding: isMobile ? 12 : 20, 
                                usePointStyle: true,
                                pointStyle: 'circle',
                                boxWidth: isMobile ? 8 : 12,
                                font: {
                                    // 10px é o tamanho exato para caber frases muito longas no mobile sem cortar
                                    size: isMobile ? 10 : 14, 
                                    family: "'Inter', sans-serif",
                                    weight: '600'
                                },
                                color: '#475569',
                                generateLabels: function(chart) {
                                    const data = chart.data;
                                    if (data.labels.length && data.datasets.length) {
                                        return data.labels.map((label, i) => {
                                            const meta = chart.getDatasetMeta(0);
                                            const style = meta.controller.getStyle(i);

                                            return {
                                                text: label, // <-- TEXTO PURO E INTEIRO (Removemos o Array que causava a quebra)
                                                fillStyle: style.backgroundColor,
                                                strokeStyle: style.borderColor,
                                                lineWidth: style.borderWidth,
                                                hidden: isNaN(dataset.data[i]) || meta.data[i].hidden,
                                                index: i
                                            };
                                        });
                                    }
                                    return [];
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
  
/* ========== LINHA DO TEMPO (QUINTIL/DECIL/PERCENTIL) ========== */
const timelineBtns = document.querySelectorAll('#timeline-toggle .segmented-option');
const timelineCircles = document.querySelectorAll('.timeline-circle-dynamic');

const FNP_RANK_COLORS = {
    '1': '#A81C21', '2': '#E47326', '3': '#F4D01D', '4': '#6AC074', '5': '#1C9148'
};

const FNP_DECIL_COLORS = {
    '1': '#960E16', '2': '#CF3026', '3': '#EB6630', '4': '#F8A555', '5': '#FCE182',
    '6': '#DDEC88', '7': '#9DD57D', '8': '#60BA69', '9': '#2D964D', '10': '#076931'
};

function updateTimelineColors(mode) {
    const timelineCircles = document.querySelectorAll('.timeline-circle-dynamic');
    const summaryContainer = document.getElementById('timeline-dynamic-summary');
    
    // 1. Atualiza as cores e rótulos de cada círculo individualmente
    timelineCircles.forEach(circle => {
        const rawValue = circle.getAttribute('data-' + mode) || '-';
        const labelSpan = circle.querySelector('.dynamic-label');
        const valueSpan = circle.querySelector('.dynamic-value');
        const numMatch = rawValue.match(/\d+/);
        const num = numMatch ? numMatch[0] : null;

        let hex = null;
        let isLightBackground = false;

        if (num) {
            if (mode === 'percentil') {
                if (labelSpan) labelSpan.textContent = 'Percentil';
                if (valueSpan) valueSpan.textContent = num + '%';
                const decilVal = Math.max(1, Math.ceil(parseInt(num) / 10));
                hex = FNP_DECIL_COLORS[decilVal];
                isLightBackground = (decilVal === 5 || decilVal === 6);
            } 
            else if (mode === 'quintil') {
                if (labelSpan) labelSpan.textContent = 'Quintil';
                if (valueSpan) valueSpan.textContent = num + 'º';
                hex = FNP_RANK_COLORS[num];
                isLightBackground = (num === '3');
            } 
            else if (mode === 'decil') {
                if (labelSpan) labelSpan.textContent = 'Decil';
                if (valueSpan) valueSpan.textContent = num + 'º';
                hex = FNP_DECIL_COLORS[num];
                isLightBackground = (num === '5' || num === '6');
            }
        } else {
            if (labelSpan) labelSpan.textContent = mode;
            if (valueSpan) valueSpan.textContent = '-';
        }

        if (hex) {
            circle.style.backgroundColor = hex;
            circle.style.color = isLightBackground ? '#103758' : '#ffffff';
        } else {
            circle.style.backgroundColor = '#f1f5f9';
            circle.style.color = '#94a3b8';
        }
    }); // Fim do loop dos círculos

    // 2. Lógica de síntese (executa apenas UMA VEZ após o loop)
    if (summaryContainer && timelineCircles.length >= 2) {
        const muniName = summaryContainer.getAttribute('data-muni-name');
        const raw00 = timelineCircles[0].getAttribute('data-' + mode);
        const raw24 = timelineCircles[1].getAttribute('data-' + mode);
        
        const num00 = raw00 ? raw00.match(/\d+/) : null;
        const num24 = raw24 ? raw24.match(/\d+/) : null;
        
        if (num00 && num24) {
            const val00 = parseInt(num00[0]);
            const val24 = parseInt(num24[0]);
            
        if (val24 === val00) {
            /* Tratamento de estabilidade unificado para todos os modos */
            summaryContainer.innerHTML = `Entre 2000 e 2024, <strong class="text-slate-700">a posição se manteve</strong>.`;
        } 
        else if (mode === 'percentil') {
            /* Helper para narrativa de percentil com inversao de lógica < 50% */
            const formatPercentilNarrativa = (v, isFull) => {
                const isInf = v < 50;
                const displayVal = isInf ? (100 - v) : v;
                const textoStatus = isInf ? 'inferior a' : 'superior a';
                const corStatus = isInf ? 'text-rose-600' : 'text-emerald-600';
                const sufixoGeo = isFull ? ' dos municípios do país' : ' dos municípios do país';
                return `<span class="${corStatus} font-black">${textoStatus} ${displayVal}%</span>${sufixoGeo}`;
            };

            const statusAcao = val24 > val00 ? 'MELHOROU' : 'PIOROU';
            const statusColor = val24 > val00 ? 'text-emerald-600' : 'text-rose-600';

            summaryContainer.innerHTML = `A  receita per capita de <strong class="text-slate-700">${muniName}</strong>, em 2000, era ${formatPercentilNarrativa(val00, false)}. <br>Em 2024 a receita relativa por habitante <span class="${statusColor} font-black">${statusAcao}</span>. Atualmente é ${formatPercentilNarrativa(val24, true)}.`;
        } 
        else {
            /* Padrao Premium para Quintil e Decil com destaque no resultado */
            const isMelhor = val24 > val00;
            const statusAcao = isMelhor ? 'SUBIU' : 'CAIU';
            const corStatus = isMelhor ? 'text-emerald-600' : 'text-rose-600';
            
            const text00 = `${val00}º ${mode}`;
            const text24 = `${val24}º ${mode}`;

            summaryContainer.innerHTML = `Entre 2000 e 2024, a posição da receita per capita de <strong class="text-slate-700">${muniName}</strong> <span class="${corStatus} font-black">${statusAcao}</span> do <span class="font-bold text-slate-400">${text00}</span> para o <span class="${corStatus} font-black">${text24}</span>.`;
        }
        } else {
            summaryContainer.innerHTML = '';
        }
    }
}

timelineBtns.forEach(btn => {
    btn.addEventListener('click', function() {
        timelineBtns.forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        updateTimelineColors(this.getAttribute('data-mode'));
    });
});
      
    // ==========================================
    // CONTROLE GLOBAL DE BASE E GRÁFICOS DE EVOLUÇÃO
    // ==========================================
    const globalBaseBtns = document.querySelectorAll('#global-base-toggle .segmented-option');
    const lblMediaBase = document.querySelectorAll('.lbl-media-base');
    const lblMediaBaseChart = document.querySelector('.lbl-media-base-chart');
    const valMediaRc = document.getElementById('val-media-rc');
    const valMediaPop = document.getElementById('val-media-pop');

    const canvasRec = document.getElementById('chartReceita');
    const canvasPop = document.getElementById('chartPop');
    const evoDataScript = document.getElementById('evolution-compare-data');

    let chartReceitaInstance = null;
    let chartPopInstance = null;
    let evolutionData = null;

    if (evoDataScript) {
        try { evolutionData = JSON.parse(evoDataScript.textContent); } 
        catch (e) { console.error(e); }
    }

    const parseSafe = (val) => {
        if (!val) return 0;
        let str = String(val).trim();
        if (str.includes('.') && str.includes(',')) str = str.replace(/\./g, '').replace(',', '.');
        else if (str.includes(',')) str = str.replace(',', '.');
        return parseFloat(str) || 0;
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
            x: { 
                grid: { display: false }, 
                ticks: { font: { weight: 'bold' }, color: '#475569' } 
            },
            y: { 
                beginAtZero: true,
                grace: '15%',
                grid: { 
                    color: (context) => context.tick && context.tick.value === 0 ? '#94a3b8' : '#f1f5f9',
                    lineWidth: (context) => context.tick && context.tick.value === 0 ? 2 : 1
                }, 
                ticks: { 
                    color: '#94a3b8', 
                    callback: (val) => val + '%' 
                } 
            }
        }
    };

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

    function updateGlobalBase(base) {
        globalBaseBtns.forEach(b => b.classList.toggle('active', b.dataset.base === base));

        const baseNomes = { 'nacional': 'média nacional', 'estadual': 'média estadual', 'faixa': 'média da faixa' };
        const labelNome = baseNomes[base] || 'média';
        
        lblMediaBase.forEach(el => el.textContent = labelNome);
        if (lblMediaBaseChart) lblMediaBaseChart.textContent = labelNome.charAt(0).toUpperCase() + labelNome.slice(1);

        const evoKeys = {
            'nacional': 'nac',
            'estadual': 'est',
            'faixa': 'faixa'
        };
        const evoKey = evoKeys[base];

        if (evolutionData && valMediaRc && valMediaPop) {
            valMediaRc.textContent = `${evolutionData.receita[evoKey] || 0}%`;
            valMediaPop.textContent = `${evolutionData.populacao[evoKey] || 0}%`;
        }

        if (evolutionData && canvasRec && canvasPop) {
            const labelChart = labelNome.charAt(0).toUpperCase() + labelNome.slice(1);
            
            const dataRec = [parseSafe(evolutionData.receita.mun), parseSafe(evolutionData.receita[evoKey])];
            const dataPop = [parseSafe(evolutionData.populacao.mun), parseSafe(evolutionData.populacao[evoKey])];

            if (chartReceitaInstance) chartReceitaInstance.destroy();
            chartReceitaInstance = new Chart(canvasRec.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: [evolutionData.nome_muni || 'Município', labelChart],
                    datasets: [{
                        data: dataRec,
                        backgroundColor: ['#103758', '#647080'],
                        borderRadius: 6,
                        barPercentage: 0.5
                    }]
                },
                options: commonEvoOptions,
                plugins: [topLabelsPlugin]
            });

            if (chartPopInstance) chartPopInstance.destroy();
            chartPopInstance = new Chart(canvasPop.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: [evolutionData.nome_muni || 'Município', labelChart],
                    datasets: [{
                        data: dataPop,
                        backgroundColor: ['#EEAF19', '#647080'],
                        borderRadius: 6,
                        barPercentage: 0.5
                    }]
                },
                options: commonEvoOptions,
                plugins: [topLabelsPlugin]
            });
        }

        if (typeof updateRankingUI === 'function') updateRankingUI(base);

        // ATUALIZAÇÃO DAS CORES DA ESTRUTURA DE RECEITAS
        const colorIndicators = document.querySelectorAll('.revenue-color-indicator');

        const REVENUE_COLORS = {
            '0': '#808080',
            '1': '#A81C21',
            '2': '#E47326',
            '3': '#F4D01D',
            '4': '#6AC074',
            '5': '#1C9148'
        };

        colorIndicators.forEach(indicator => {
            const quintil = indicator.getAttribute(`data-q-${base}`);
            indicator.classList.remove('bg-slate-200');
            
            if (quintil && REVENUE_COLORS[quintil]) {
                indicator.style.backgroundColor = REVENUE_COLORS[quintil];
            } else {
                indicator.style.backgroundColor = ''; 
                indicator.classList.add('bg-slate-200');
            }
        });

        // DICIONÁRIO DE RÓTULOS E SUFIXOS PARA AS FRASES DINÂMICAS
        const baseLabels = {
            'nacional': { media: 'Média Nacional', mediana: "Mediana Nacional", sufixo: 'dos municípios do país', kpi: 'Ranking Nacional' },
            'estadual': { media: 'Média Estadual', mediana: "Mediana Estadual", sufixo: 'dos municípios do estado', kpi: 'Ranking Estadual' },
            'faixa': { media: 'Média da Faixa', mediana: "Mediana da Faixa", sufixo: 'dos municípios da mesma faixa populacional', kpi: 'Ranking por Faixa' }
        };

        const config = baseLabels[base];

        // 1. ATUALIZA OS RÓTULOS DA MÉDIA (Ex: Média Nacional -> Média Estadual)
        document.querySelectorAll('.revenue-dynamic-media-label').forEach(el => {
            el.textContent = config.media;
        });

        document.querySelectorAll('.revenue-dynamic-mediana-label').forEach(el => {
            el.textContent = config.mediana;
        });

        // 2. ATUALIZA OS VALORES DA MÉDIA (Ex: R$ 6.000 -> R$ 5.000)
        document.querySelectorAll('.revenue-dynamic-media-value').forEach(el => {
            const val = el.getAttribute(`data-val-${base}`);
            el.textContent = (val && val.trim() !== '') ? val : 'R$ --,--';
        });

        document.querySelectorAll('.revenue-dynamic-mediana-value').forEach(el => {
            // Atenção ao nome do atributo no seu HTML. Aqui usei data-mediana-${base}
            const val = el.getAttribute(`data-val-${base}`);
            el.textContent = (val && val.trim() !== '') ? val : 'R$ --,--';
        });

        // 3. CONSTRÓI A FRASE DE IMPACTO DO PERCENTIL
        document.querySelectorAll('.revenue-dynamic-phrase').forEach(el => {
            const pct = el.getAttribute(`data-pct-${base}`);
            const muniName = el.getAttribute('data-muni-name');

            /* Captura o elemento do indicador de cor no mesmo nivel hierarquico para uso como referencia de estilo */
            const indicator = el.closest('.tree-row').querySelector('.revenue-color-indicator');
            const indicatorColor = indicator ? indicator.style.backgroundColor : 'inherit';

            if (pct && pct.trim() !== '' && pct !== 'None') {
                const numPct = parseFloat(pct.replace(',', '.'));

                if (numPct < 0) {
                    el.innerHTML = '';
                } else {
                    const adv = numPct > 50 ? '' : 'apenas ';
                    /* Engloba o texto de acao e o valor numerico do percentil na mesma estilizacao de cor do indicador */
                    el.innerHTML = `<strong class="font-semibold text-slate-700">${muniName}</strong> <span style="color: ${indicatorColor}; font-weight: 600;">supera ${adv}${pct}%</span> ${config.sufixo}`;
                }

            } else {
                el.innerHTML = 'Sem dados comparativos';
            }
        });

        // ====================================================================
        // ATUALIZAÇÃO DOS CARDS PRINCIPAIS (POPULAÇÃO E RECEITA)
        // ====================================================================
        /* Define o componente visual do icone de informacao com propriedades de transicao para feedback visual ao hover */
        const INFO_ICON_SVG = `
            <svg class="w-3.5 h-3.5 ml-1.5 opacity-50 group-hover:opacity-100 transition-opacity shrink-0" 
                fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" 
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z">
                </path>
            </svg>`;
        // Atualiza os labels "Ranking Nacional", "Ranking Estadual", etc.
        document.querySelectorAll('.global-ranking-label').forEach(el => {
            el.textContent = config.kpi;
        });

        // Função auxiliar para atualizar o número no card 
        const updateKpiRank = (selector, dataPrefix) => {
            const kpiEl = document.querySelector(selector);
            if (kpiEl) {
                // Adicionamos 'group' para controlar a opacidade do icone via CSS do pai
                kpiEl.className = 'flex items-baseline ifem-tooltip-container group cursor-help';
                
                const dataStr = kpiEl.getAttribute(`data-${dataPrefix}-${base}`);
                const totalBaseFixa = "5.479";
                
                if (dataStr && dataStr.includes('/')) {
                    const parts = dataStr.split('/');
                    const rank = parts[0].trim();

                    kpiEl.innerHTML = `
                        <span class="kpi-hero-value">${rank}º</span> 
                        <span class="text-lg md:text-xl font-bold text-slate-500 ml-2">de ${totalBaseFixa}</span>
                        ${INFO_ICON_SVG}
                        <div class="ifem-tooltip-box">
                            O município ocupa a ${rank}ª posição entre os ${totalBaseFixa} municípios do Brasil com dados disponíveis.
                        </div>
                    `;
                }
            }
        };

        // Aplica a atualização nos dois cards
        updateKpiRank('.kpi-pop-rank', 'pop');
        updateKpiRank('.kpi-rev-rank', 'rev');



        // CÁLCULO DE BENCHMARK E RENDERIZAÇÃO DE TOOLTIP CUSTOMIZADO
    const updateBenchmarkTrend = (containerId, munValue, compValue, labelBase) => {
    const container = document.getElementById(containerId);
    if (!container) return;

    const isPop = containerId.includes('pop');
    let state = 'neutral';
    let arrow = '•';
    let statusClass = 'text-slate-500';
    let tooltipMsg = "";

    /* Logica de comparacao baseada no tipo de indicador (percentual absoluto ou relativo a media) */
    if (isPop) {
        const isPos = munValue >= 0;
        state = isPos ? 'positive' : 'negative';
        arrow = isPos ? '▲' : '▼';
        statusClass = isPos ? 'positive' : 'negative';
        const verb = isPos ? 'aumentou' : 'diminuiu';
        tooltipMsg = `A população ${verb} ${Math.abs(munValue)}% no período de 2000 a 2024.`;
    } else {
        if (compValue !== 0 && !isNaN(compValue)) {
            const fPct = Math.round((munValue / compValue - 1) * 100);
            const isPositive = fPct >= 0;
            const direcao = isPositive ? "acima" : "abaixo";
            state = isPositive ? 'positive' : 'negative';
            arrow = isPositive ? '▲' : '▼';
            statusClass = isPositive ? 'positive' : 'negative';
            const suffix = isPositive ? 'acima' : 'abaixo';
            tooltipMsg = `A receita do município cresceu ${Math.abs(fPct)}% ${suffix} ${direcao} da receita da ${labelBase} no período de 2000 a 2024.`;        }
    }

    if ((isPop && munValue === 0) || (!isPop && munValue === compValue)) {
        arrow = '•';
        statusClass = 'text-slate-500 font-bold';
        tooltipMsg = "O indicador permaneceu estável em relação ao período ou benchmark anterior.";
    }

    /* Renderiza o container com suporte a tooltip-box para feedback visual ao hover */
    container.className = `kpi-hero-trend ${statusClass} mt-1 transition-all ifem-tooltip-container group cursor-help flex items-center`;
        
        const valDisplay = containerId.includes('pop') ? Math.abs(munValue) : (compValue !== 0 ? Math.round((munValue / compValue - 1) * 100) : 0);
        
        container.innerHTML = `
            <span class="font-black">${arrow} ${valDisplay}%</span> 
            <span class="text-slate-600 font-medium ml-1">no período</span>
            ${INFO_ICON_SVG}
            <div class="ifem-tooltip-box">${tooltipMsg}</div>
        `;
    };

        if (evolutionData) {
            const evoKeys = { 'nacional': 'nac', 'estadual': 'est', 'faixa': 'faixa' };
            const evoKey = evoKeys[base];
            
            const munRc = parseSafe(evolutionData.receita.mun);
            const compRc = parseSafe(evolutionData.receita[evoKey]);
            const munPop = parseSafe(evolutionData.populacao.mun);
            const compPop = parseSafe(evolutionData.populacao[evoKey]);

            updateBenchmarkTrend('trend-comparativo-rc', munRc, compRc, labelNome);
            updateBenchmarkTrend('trend-comparativo-pop', munPop, compPop, labelNome);
        }

        // ------------ Toggle Interno do Card de Receita (Per Capita / Absolut) ------------
        const kpiRcToggles = document.querySelectorAll('.kpi-rc-toggle');
        const kpiRcLabel = document.getElementById('kpi-rc-label');
        const kpiRcValue = document.getElementById('kpi-rc-value');

        if (kpiRcToggles.length > 0) {
            kpiRcToggles.forEach(btn => {
                btn.addEventListener('click', () => {
                    // Alterna o estilo visual dos botões
                    kpiRcToggles.forEach(b => {
                        b.classList.remove('active', 'bg-white', 'text-[#103758]', 'shadow-sm');
                        b.classList.add('text-slate-400');
                    });
                    btn.classList.add('active', 'bg-white', 'text-[#103758]', 'shadow-sm');
                    btn.classList.remove('text-slate-400');

                    // Alterna os textos e valores
                    const mode = btn.dataset.mode;
                    if (mode === 'pc') {
                        kpiRcLabel.textContent = 'Valor por Habitante';
                        kpiRcValue.textContent = kpiRcValue.getAttribute('data-val-pc');
                    } else {
                        kpiRcLabel.textContent = 'Total Absoluto';
                        kpiRcValue.textContent = kpiRcValue.getAttribute('data-val-tot');
                    }
                });
            });
        }
    }

    globalBaseBtns.forEach(btn => btn.addEventListener('click', function() { updateGlobalBase(this.dataset.base); }));

    // -------- INICIALIZAÇÕES FINAIS --------
    buildHeadingIndex();
    showMode('pc');
    if (typeof buildSelectFor === 'function') buildSelectFor(currentKey);
    if (typeof renderChart === 'function') renderChart(currentKey);
    initializeToggleListeners();
    // Detecta qual modo esta ativo no HTML e inicializa a timeline com ele */
    const activeTimelineMode = document.querySelector('#timeline-toggle .segmented-option.active')?.dataset.mode || 'percentil';
    updateTimelineColors(activeTimelineMode);    
    // Dispara a visualização global padrão
    updateGlobalBase('nacional');


}); //fechamento DOM