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

  // ------------ dados vindos do template ------------
  const allRevenueChartData = safeParseJSONById('chart-data');
  const percentileData      = safeParseJSONById('percentile-data');
  const municipioData       = parseRankingDataFromText('municipio-data');

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

  // ------------ indicador (cores + tooltip) ------------
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

  // ------------ toggles ------------
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

  // ------------ ordenação ------------
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

  // ------------ PC/VR ------------
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

  // ------------ índice de headings (abrir árvore) ------------
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

  // ------------ ranking (cores + texto) ------------
  function updateRankingUI(selected) {
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
      rankingValueEl.textContent = (Number.isFinite(rk) && Number.isFinite(tot)) ? `${fmtInt(rk)} / ${fmtInt(tot)}` : '—';
    }
  }

  const rankingSelect = $('#ranking-select');
  rankingSelect?.addEventListener('change', () => updateRankingUI(rankingSelect.value || 'nacional'));

  // ========== GRÁFICO (COMPOSIÇÃO) + SELECT DINÂMICO ==========
  const canvas = $('#myChart');
  if (!canvas){ console.error('Canvas #myChart não encontrado'); return; }
  if (!window.Chart){ console.error('Chart.js não carregado'); return; }
  canvas.style.cursor = 'pointer';
  const ctx = canvas.getContext('2d');

  // rótulos “bonitos” para o SELECT 
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

  // Hierarquia (pai -> filhos)
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
    // lista base
    let keys = ['main_categories'];

    // principal (4) quando está nas categorias principais
    if (currentKey === 'main_categories') {
      keys.push('imposto_taxas_contribuicoes','contribuicoes','transferencias_correntes','outras_receitas');
    } else {
      // pai (se existir)
      const parent = PARENT[currentKey] || null;
      if (parent) keys.push(parent);
      // selecionado
      keys.push(currentKey);
      // filhos (se existir)
      const kids = CHILDREN[currentKey] || CHILDREN[parent] || [];
      keys.push(...kids);
    }

    // filtra duplicados e só com dados
    const seen = new Set();
    const finalKeys = keys.filter(k=>{
      if (seen.has(k)) return false;
      seen.add(k);
      return hasData(k) || k === 'main_categories'; // main_categories sempre presente
    });

    // render
    selectEl.innerHTML = '';
    finalKeys.forEach(k=>{
      const opt = document.createElement('option');
      opt.value = k;
      opt.textContent = labelOf(k);
      selectEl.appendChild(opt);
    });
    selectEl.value = currentKey;  // mantém o selecionado
  }

  // Paleta fixa das 4 principais para o gráfico (barras)
  const COLOR_BY_LABEL = {
    'Impostos, Taxas e Contribuições': '#1f77b4',
    'Contribuições': '#ff7f0e',
    'Transf. Correntes': '#2ca02c',
    'Outras': '#d62728'
  };
  const palette = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd','#8c564b','#e377c2','#7f7f7f','#bcbd22','#17becf'];

  // --- helper para notificar o gráfico de densidade sem trocar o <select> 
  function notifyDensityKey(key){
    const sel = document.getElementById('chart-category-select');
    if (!sel || !key) return;
    sel.dispatchEvent(new CustomEvent('composition-category-changed', {
      bubbles: true,
      detail: { key }
    }));
  }

  // --- normalizador simples para chaves (fallback snake_case) ---
  function toSnakeKey(str){
    return String(str || '')
      .normalize('NFD').replace(/\p{Diacritic}/gu,'')
      .replace(/R\$\s?[\d\.,]+/g,' ')
      .replace(/[\d\.,]+/g,' ')
      .trim().toLowerCase()
      .replace(/[^a-z0-9]+/g,'_')
      .replace(/^_+|_+$/g,'');
  }

  

  // --- resolver tolerante: tenta match exato, depois fuzzy, depois snake_case ---
  function resolveDensityChildKey(groupKey, clickedLabel){
    const n = normalize(clickedLabel);
    const table = DENSITY_CHILD_KEYS[groupKey];
    if (!table) return null;

    // 1) exato
    if (table.has(n)) return table.get(n);

    // 2) fuzzy "contém"
    for (const [k,v] of table.entries()){
      if (n.includes(k) || k.includes(n)) return v;
    }

    // 3) fallback: gera snake_case do label
    return toSnakeKey(clickedLabel);
  }


  let chart = null;

    // Texto normalizado (categorias principais -> chave interna)
const MAIN_CLICK_TO_KEY = new Map([
  [normalize('Impostos, Taxas e Contribuições'), 'imposto_taxas_contribuicoes'],
  [normalize('Contribuições'),                   'contribuicoes'],
  [normalize('Transf. Correntes'),               'transferencias_correntes'],
  [normalize('Outras'),                          'outras_receitas'],
]);

// ===== Helpers para densidade por filho =====
function notifyDensityKey(key){
  const sel = document.getElementById('chart-category-select');
  if (!sel || !key) return;
  sel.dispatchEvent(new CustomEvent('composition-category-changed', {
    bubbles: true,
    detail: { key }
  }));
}
function toSnakeKey(str){
  return String(str||'')
    .normalize('NFD').replace(/\p{Diacritic}/gu,'')
    .replace(/R\$\s?[\d\.,]+/g,' ')
    .replace(/[\d\.,]+/g,' ')
    .trim().toLowerCase()
    .replace(/[^a-z0-9]+/g,'_')
    .replace(/^_+|_+$/g,'');
}

// “Outros” por grupo (bate com #mun-data)
const OUTROS_KEY_BY_GROUP = {
  imposto: 'outros_impostos',
  taxas: 'outras_taxas',
  contribuicoes_melhoria: 'outras_contribuicoes_melhoria',
  transferencias_uniao: 'outras_transferencias_uniao',
  transferencias_estado: 'outras_transferencias_estado',
  outras_receitas: 'outras_receitas_outras',
};

// Mapa rótulo->campo (#mun-data) para TODOS os filhos (pelos labels do seu print)
const DENSITY_CHILD_KEYS = {
  // IMPOSTOS
  imposto: new Map([
    [normalize('Imposto sobre Serviços'), 'iss'],
    [normalize("Imposto sobre a Transmissão 'Inter Vivos'"), 'itbi'],
    [normalize('Imposto sobre a Propriedade Predial e Territorial Urbana'), 'iptu'],
    [normalize('Imposto de Renda'), 'imposto_renda'],
    [normalize('Outros Impostos'), 'outros_impostos'],
    [normalize('Outros'), 'outros_impostos'],
  ]),
  // TAXAS
  taxas: new Map([
    [normalize('Taxas pelo Exercício do Poder de Polícia'), 'taxa_policia'],
    [normalize('Taxas pela Prestação de Serviços'),         'taxa_prestacao_servico'],
    [normalize('Outras Taxas'),                             'outras_taxas'],
    [normalize('Outros'),                                   'outras_taxas'],
  ]),
  // CONTRIBUIÇÕES DE MELHORIA
  contribuicoes_melhoria: new Map([
    [normalize('Contribuição de Melhoria para Pavimentação e Obras'), 'contribuicao_melhoria_pavimento_obras'],
    [normalize('Contribuição de Melhoria para Rede de Água e Esgoto'), 'contribuicao_melhoria_agua_potavel'],
    [normalize('Contribuição de Melhoria para Iluminação Pública'),     'contribuicao_melhoria_iluminacao_publica'],
    [normalize('Outras Contribuições de Melhoria'),                      'outras_contribuicoes_melhoria'],
    [normalize('Outros'),                                                'outras_contribuicoes_melhoria'],
  ]),
  // CONTRIBUIÇÕES
  contribuicoes: new Map([
    [normalize('Custeio do Serviço de Iluminação Pública'), 'contribuicoes_sociais'],
    [normalize('Outras Contribuições'),                     'outras_contribuicoes'],
    [normalize('Outros'),                                   'outras_contribuicoes'],
  ]),
  // TRANSF. UNIÃO (todos os filhos existentes no #mun-data)
  transferencias_uniao: new Map([
    [normalize('Cota-Parte do FPM'),                                   'transferencias_uniao_fpm'],
    [normalize('Compensação Financeira (Recursos Naturais)'),          'transferencias_uniao_exploracao'],
    [normalize('Recursos do SUS'),                                     'transferencias_uniao_sus'],
    [normalize('Recursos do FNDE'),                                    'transferencias_uniao_fnde'],
    [normalize('Recursos do FUNDEB'),                                    'transferencias_uniao_fundeb'],
    [normalize('Recursos do FNAS'),                                    'transferencias_uniao_fnas'],
    [normalize('Recursos do Fundo Especial'),                           'transferencias_uniao_fundo'],   // <== novo
    [normalize('Outras Transferências da União'),                       'outras_transferencias_uniao'],
    [normalize('Outras'),                                               'outras_transferencias_uniao'],
  ]),

  // TRANSF. ESTADOS (todos os filhos existentes no #mun-data)
  transferencias_estado: new Map([
    [normalize('Cota-Parte do ICMS'),                                   'transferencias_estado_icms'],
    [normalize('Cota-Parte do IPVA'),                                   'transferencias_estado_ipva'],
    [normalize('Recursos do SUS'),                                      'transferencias_estado_sus'],
    [normalize('Assistência Social'),                                   'transferencias_estado_assistencia'], // <== novo
    [normalize('Compensação Financeira (Recursos Naturais)'),           'transferencias_estado_exploracao'],  // <== novo
    [normalize('Outras Transferências dos Estados'),                    'outras_transferencias_estado'],
    [normalize('Outras'),                                               'outras_transferencias_estado'],
  ]),

  // OUTRAS RECEITAS
  outras_receitas: new Map([
    [normalize('Receita Patrimonial'),  'receita_patrimonial'],
    [normalize('Receita Agropecuária'), 'receita_agropecuaria'],
    [normalize('Receita Industrial'),   'receita_industrial'],
    [normalize('Receita de Serviços'),  'receita_servicos'],
    [normalize('Outras Receitas'),      'outras_receitas_outras'],
    [normalize('Outras'),               'outras_receitas_outras'],
  ]),
};

// Resolver: exato → fuzzy → “Outros” por grupo → fallback snake_case
function resolveDensityChildKey(groupKey, clickedLabel){
  const n = normalize(clickedLabel);
  const table = DENSITY_CHILD_KEYS[groupKey];

  if (table?.has(n)) return table.get(n);

  if (table){
    for (const [k,v] of table.entries()){
      if (n.includes(k) || k.includes(n)) return v;
    }
  }

  if (n.includes('outro')) return OUTROS_KEY_BY_GROUP[groupKey] || toSnakeKey(clickedLabel);

  return toSnakeKey(clickedLabel);
}

// guarda a categoria atual para evitar renders desnecessários
let currentKey = 'main_categories';

function setCategoryAndSync(key){
  if (!selectEl) return;
  if (currentKey === key) {
    // ainda assim notifica densidade (pode vir de clique)
    selectEl.dispatchEvent(new CustomEvent('composition-category-changed', { bubbles:true, detail:{ key } }));
    return;
  }
  currentKey = key;

  buildSelectFor(key);            // reconstrói a lista conforme Pai/Filhos
  selectEl.value = key;
  renderChart(key);               // composição

  // avisa a densidade sem disparar 'change'
  selectEl.dispatchEvent(new CustomEvent('composition-category-changed', { bubbles:true, detail:{ key } }));
}

// select → usuário trocou manualmente
if (selectEl){
  selectEl.addEventListener('change', () => setCategoryAndSync(selectEl.value));
}

function renderChart(key){
  const d = allRevenueChartData?.[key];
  if (!d){ warn('chave não encontrada no chart-data:', key); return; }
  if (!Array.isArray(d.labels) || !Array.isArray(d.values)){ warn('estrutura inesperada:', d); return; }

  const total = d.values.reduce((a,b)=>a+b,0);
  const perc  = d.values.map(v=> total ? (v/total)*100 : 0);

  const labels = d.labels.slice();
  const background = labels.map((lbl,i)=> COLOR_BY_LABEL[lbl] || palette[i%palette.length]);

  const dataset = {
    label: labelOf(key).toUpperCase(),
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
      scales:{ x:{ min:0, max:100, ticks:{ callback:v=>v+'%'} }, y:{ ticks:{ autoSkip:false } } },
      plugins:{ legend:{ display:false }, tooltip:{ callbacks:{
        label:(ct)=>{
          const i = ct.dataIndex;
          const raw = d.values[i];
          const pct = ct.parsed.x || 0;
          return `${labels[i]}: ${pct.toFixed(1)}% (${new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(raw)})`;
        },
        footer:()=>`Total: ${new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(total)}`
      } } }
    }
  });

  // clique → muda chave / abre árvore / dispara densidade
  canvas.onclick = (evt) => {
    const pts = chart.getElementsAtEventForMode(evt,'nearest',{intersect:true},true);
    if (!pts.length) return;
    const idx = pts[0].index;
    const clickedLabel = labels[idx];
    const n = normalize(clickedLabel);

    // 1) Categorias Principais → descer 1 nível (tolerante a renomes)
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

    // 2) ITC → filhos maiores
    if (key === 'imposto_taxas_contribuicoes') {
      if (n.includes('imposto'))  { setCategoryAndSync('imposto'); return; }
      if (n.includes('taxa'))     { setCategoryAndSync('taxas'); return; }
      if (n.includes('melhoria')) { setCategoryAndSync('contribuicoes_melhoria'); return; }
      openByLabel(clickedLabel); return;
    }

    // 3) Transferências Correntes → União/Estados
    if (key === 'transferencias_correntes') {
      if (n.includes('uniao'))  { setCategoryAndSync('transferencias_uniao');  return; }
      if (n.includes('estado')) { setCategoryAndSync('transferencias_estado'); return; }
      openByLabel(clickedLabel); return;
    }

    // 3.1) Filhos: Impostos / Taxas / Contribuições de Melhoria
    if (key === 'imposto' || key === 'taxas' || key === 'contribuicoes_melhoria') {
      openByLabel(clickedLabel);
      notifyDensityKey(resolveDensityChildKey(key, clickedLabel));
      return;
    }

    // 3.2) Filhos: Transferências da União / dos Estados
    if (key === 'transferencias_uniao' || key === 'transferencias_estado') {
      openByLabel(clickedLabel);
      notifyDensityKey(resolveDensityChildKey(key, clickedLabel));
      return;
    }

    // 3.3) Filhos: Outras Receitas
    if (key === 'outras_receitas') {
      openByLabel(clickedLabel);
      notifyDensityKey(resolveDensityChildKey(key, clickedLabel));
      return;
    }

    // 4) Demais → abre na árvore
    openByLabel(clickedLabel);
  };
}


  // -------- Inicializações --------
  buildHeadingIndex();
  showMode('pc');
  currentKey = 'main_categories';
  buildSelectFor(currentKey);
  renderChart(currentKey);
  initializeToggleListeners();
  updateRankingUI(rankingSelect?.value || 'nacional');

});
