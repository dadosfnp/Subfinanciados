// detail/static/detail/js/script_density.js
document.addEventListener("DOMContentLoaded", () => {
  let densityChart = null;
  let totalMunData = null; // Dados brutos (sempre a carga inicial)
  let AVAILABLE_KEYS = new Set(); // Lista de chaves que REALMENTE existem nos dados

  const categorySelect = document.getElementById('chart-category-select');
  const filtroPorte    = document.getElementById('filtro-porte');
  const filtroRm       = document.getElementById('filtro-rm');
  const filtroRegiao   = document.getElementById('filtro-regiao');
  const filtroUf       = document.getElementById('filtro-uf');
  const btnLimpar      = document.getElementById('btn-limpar-filtros');

  // Plugin de anotação
  const annotationPlugin = window['chartjs-plugin-annotation'];
  if (annotationPlugin && window.Chart) Chart.register(annotationPlugin);

  // --- Helpers Estatísticos ---
  const mean = arr => arr.length ? arr.reduce((a,b)=>a+b,0)/arr.length : 0;
  const gaussianKernel = u => Math.exp(-0.5*u*u)/Math.sqrt(2*Math.PI);
  const silvermanBandwidth = arr => {
    const n=arr.length; if(n<2) return 1e-6;
    const m=mean(arr); const s=Math.sqrt(arr.reduce((s,x)=>s+(x-m)**2,0)/(n-1));
    return s===0 ? 1e-6 : 1.06*s*Math.pow(n,-1/5);
  };
  const linspace = (a,b,n=300)=>Array.from({length:n},(_,i)=>a + i*(b-a)/(n-1));

  // --- Normalização de Texto ---
  const labelNorm = (s) => (s||'')
    .normalize('NFD').replace(/\p{Diacritic}/gu,'')
    .replace(/[^a-z0-9]+/gi,' ')
    .replace(/\s+/g,' ')
    .trim().toLowerCase();

  // --- Mapa: Rótulo do Select -> Sugestão de Chave ---
  // (Usado apenas quando o usuário muda pelo Select manualmente)
  const LABEL_TO_KEY = new Map([
    [labelNorm('IPTU'), 'iptu'],
    [labelNorm('ITBI'), 'itbi'],
    [labelNorm('ISS'),  'iss'],
    [labelNorm('Cota-Parte do FPM'), 'fpm'],
    [labelNorm('Cota-Parte do ICMS'), 'transferencia_estado_icms'],
    // É possível adicionar outros se o select falhar, mas a lógica Smart Match abaixo resolve 99%
  ]);

  // =========================================================================
  // SMART KEY RESOLVER (A Solução Definitiva)
  // Encontra a chave nos dados mesmo se houver divergência de singular/plural
  // =========================================================================
  function resolveKey(input) {
    if (!input) return null;
    
    // 1. Verifica se a chave exata já existe nos dados
    if (AVAILABLE_KEYS.has(input)) return input;

    // 2. Tenta mapear via LABEL_TO_KEY (para o Select)
    const normLabel = labelNorm(input);
    const mapped = LABEL_TO_KEY.get(normLabel);
    if (mapped && AVAILABLE_KEYS.has(mapped)) return mapped;

    // 3. BUSCA INTELIGENTE (Fuzzy Logic)
    // Isso resolve o problema de 'fpm' (input) vs 'transferencias_uniao_fpm' (dados)
    // ou 'transferencia_' (singular) vs 'transferencias_' (plural)
    
    const inputLower = input.toLowerCase();
    
    for (const realKey of AVAILABLE_KEYS) {
        const k = realKey.toLowerCase();

        // A. Match de Sufixo (Ex: input "fpm" casa com "transferencias_uniao_fpm")
        if (k.endsWith('_' + inputLower) || k.endsWith('.' + inputLower)) {
            console.log(`[Densidade] Match de Sufixo: "${input}" -> "${realKey}"`);
            return realKey;
        }

        // B. Match de Pluralização (Ex: "transferencia_..." casa com "transferencias_...")
        // Tenta transformar o input em plural e ver se bate
        const inputPlural = inputLower.replace('transferencia_', 'transferencias_');
        if (k === inputPlural) {
            console.log(`[Densidade] Match de Plural: "${input}" -> "${realKey}"`);
            return realKey;
        }
        
        // C. Match Reverso (Se o input for o longo e o dado for o curto)
        if (inputLower.endsWith('_' + k)) {
             return realKey;
        }
    }

    console.warn(`[Densidade] Chave "${input}" não encontrada nos dados disponíveis.`);
    return null;
  }

  // --- Função de Desenho ---
  function drawDensityPlot(dataKey, allData, filteredMean){
    try{
      if(!allData) return;

      // Usa o Resolver Inteligente
      const key = resolveKey(dataKey);
      
      if (!key) {
          if(densityChart) { densityChart.data.datasets[0].data = []; densityChart.update(); }
          return;
      }

      const raw = allData.map(d => Number(d[key])).filter(v => Number.isFinite(v));
      const values = raw.filter(v => v > 0); 

      const ctx = document.getElementById('densidadeReceita');
      if(!ctx) return;
      if(densityChart) densityChart.destroy();

      const fmtBRL = new Intl.NumberFormat('pt-BR', { style:'currency', currency:'BRL', maximumFractionDigits:0 });

      // Cálculo KDE
      let pontos;
      let poucosDados = false;

      if (values.length < 2) {
        poucosDados = true;
        const m = Number.isFinite(filteredMean) && filteredMean > 0 ? filteredMean : 1;
        const left  = Math.max(1, m * 0.6);
        const right = m * 1.4;
        pontos = [{x:left, y:0},{x:m, y:0},{x:right, y:0}];
      } else {
        const n = values.length;
        const meanVal = values.reduce((a,b)=>a+b,0)/n;
        
        // Log transform para melhor visualização de renda
        const logValues = values.map(Math.log);
        const xmin = Math.min(...logValues);
        const xmax = Math.max(...logValues);
        
        // Grid
        const xGrid = linspace(xmin, xmax, 400);
        const h = silvermanBandwidth(logValues);
        
        const dens = xGrid.map(x => logValues.reduce((s,xi)=>s+gaussianKernel((x-xi)/h),0)/(n*h));
        pontos = xGrid.map((x,i)=>({x: Math.exp(x), y: dens[i]}));
      }

      // Config Annotations
      const annotationConfig = annotationPlugin ? {
        annotations: {
          faixaAtual: {
            type:'line',
            xMin: filteredMean, xMax: filteredMean,
            borderColor: 'rgba(214,39,40,1)',
            borderWidth: 2,
            borderDash: [6,6],
            display: Number.isFinite(filteredMean)
          },
          avisoPoucosDados: {
            type:'label',
            xValue: pontos[Math.floor(pontos.length/3)].x,
            yValue: 0,
            content: poucosDados ? ['Dados insuficientes'] : '',
            display: poucosDados,
            backgroundColor:'rgba(0,0,0,.6)',
            color:'#fff',
            padding:6,
            borderRadius:4
          }
        }
      } : {};

      densityChart = new Chart(ctx, {
        type:'line',
        data:{
          datasets:[{
            label: 'Densidade',
            data: pontos,
            borderWidth: 2,
            tension: 0.35,
            fill: true,
            pointRadius: 0,
            borderColor: 'rgba(31,119,180,1)',
            backgroundColor: 'rgba(31,119,180,0.25)'
          }]
        },
        options:{
          parsing:false,
          maintainAspectRatio:false,
          scales:{
            x:{ type:'linear', title:{display:true,text:'Valor (R$)'}, ticks:{ callback:(v)=>fmtBRL.format(v)} },
            y:{ title:{display:true,text:'Densidade'}, beginAtZero:true }
          },
          plugins:{
            tooltip:{ callbacks:{
              title:(items)=> items.length ? fmtBRL.format(items[0].parsed.x) : '',
              label:(item)=> `Densidade: ${item.parsed.y.toFixed(4)}`
            }},
            legend:{
              position:'bottom',
              labels:{
                usePointStyle:false,
                generateLabels(chart){
                  const base = Chart.defaults.plugins.legend.labels.generateLabels(chart);
                  base.push({
                    text: 'Faixa Atual',
                    strokeStyle: 'rgba(214,39,40,1)',
                    lineWidth: 2,
                    lineDash: [6,6],
                    fillStyle: 'rgba(0,0,0,0)',
                    hidden: !Number.isFinite(filteredMean),
                    datasetIndex: -1
                  });
                  return base;
                }
              }
            },
            annotation: annotationConfig
          }
        }
      });
    } catch(err){ console.error('[densidade] erro render',err); }
  }

  // --- Atualização via Filtros ---
  async function updateFilteredDensity(){
    if(!totalMunData) return;
    const p = new URLSearchParams();
    p.set('porte',filtroPorte?.value||'todos');
    p.set('rm',filtroRm?.value||'todos');
    p.set('regiao',filtroRegiao?.value||'todos');
    p.set('uf',filtroUf?.value||'todos');

    try{
      // Busca dados filtrados da API
      const resp = await fetch(`/api/conjunto-data/?${p.toString()}`);
      if(!resp.ok) throw new Error('Falha API');
      const filteredMunData = await resp.json();

      // Pega a chave atual selecionada
      const rawKey = categorySelect?.value;
      
      // Resolve a chave usando a API response keys (se necessário) ou as chaves globais
      const key = resolveKey(rawKey);
      if(!key) return;

      // Calcula média da seleção atual
      // OBS: filteredMunData vem da API, que tem chaves CURTAS (singular).
      // totalMunData vem do load inicial, que tem chaves LONGAS (plural).
      // O resolveKey prioriza o que está em AVAILABLE_KEYS (Longas).
      
      // Tenta pegar o valor. Se falhar na chave longa, tenta a curta.
      let vals = filteredMunData.map(d => d[key]);
      
      // Se vier tudo undefined, tenta a chave "curta" equivalente
      if (vals.every(v => v === undefined)) {
          // hack reverso simples
          const shortKey = key.replace('transferencias_', 'transferencia_').replace('imposto_taxas_contribuicoes_', ''); 
          vals = filteredMunData.map(d => d[shortKey] || d[key] || 0);
      }
      
      const nums = vals.map(Number).filter(Number.isFinite);
      const filteredMean = mean(nums);

      drawDensityPlot(key, totalMunData, filteredMean);
    }catch(e){ console.error('[densidade] update error', e); }
  }

  // ===== Inicialização =====
  const rawData = document.getElementById("mun-data")?.textContent;
  if(rawData){
    try{
      totalMunData = JSON.parse(rawData);
      
      // Popula AVAILABLE_KEYS com as chaves que REALMENTE vieram do Django no load inicial
      AVAILABLE_KEYS = new Set();
      if (Array.isArray(totalMunData) && totalMunData.length > 0) {
        Object.keys(totalMunData[0]).forEach(k => AVAILABLE_KEYS.add(k));
      }
      console.log("[Densidade] Chaves carregadas:", AVAILABLE_KEYS.size);

    } catch(e){
      console.error('falha parse #mun-data', e);
    }
  }

  if(categorySelect && totalMunData){
    // 1. Desenho inicial
    const key0 = resolveKey(categorySelect.value);
    if(key0) {
        const initialValues = totalMunData.map(d => Number(d[key0])).filter(Number.isFinite);
        drawDensityPlot(key0, totalMunData, mean(initialValues));
    }

    // 2. Listener do Select manual
    categorySelect.addEventListener('change', updateFilteredDensity);

    // 3. Listener do Evento do Gráfico 
    categorySelect.addEventListener('composition-category-changed', (ev) => {
      const incoming = ev.detail?.key || categorySelect.value;
      console.log("[Densidade] Evento recebido:", incoming);
      
      const k = resolveKey(incoming);
      console.log("[Densidade] Chave resolvida:", k);

      if (k) {
          const vals = totalMunData.map(d => Number(d[k])).filter(Number.isFinite);
          drawDensityPlot(k, totalMunData, mean(vals));
          
          // Sincroniza o select visualmente
                if(categorySelect.querySelector(`option[value="${k}"]`)){
              categorySelect.value = k;
          }
      }
    });
  }

  [filtroPorte, filtroRm, filtroRegiao, filtroUf].forEach(el=>{
    if(el) el.addEventListener('change', updateFilteredDensity);
  });

  if(btnLimpar){
    btnLimpar.addEventListener('click', ()=> setTimeout(updateFilteredDensity, 100));
  }
});