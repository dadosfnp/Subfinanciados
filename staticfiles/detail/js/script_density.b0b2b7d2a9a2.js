// detail/static/detail/js/script_density.js
document.addEventListener("DOMContentLoaded", () => {
  let densityChart = null;
  let totalMunData = null;

  const categorySelect = document.getElementById('chart-category-select');
  const filtroPorte   = document.getElementById('filtro-porte');
  const filtroRm      = document.getElementById('filtro-rm');
  const filtroRegiao  = document.getElementById('filtro-regiao');
  const filtroUf      = document.getElementById('filtro-uf');
  const btnLimpar     = document.getElementById('btn-limpar-filtros');

  // Plugin de anotação
  const annotationPlugin = window['chartjs-plugin-annotation'];
  if (annotationPlugin && window.Chart) Chart.register(annotationPlugin);

  // Helpers estatísticos
  const mean = arr => arr.length ? arr.reduce((a,b)=>a+b,0)/arr.length : 0;
  const gaussianKernel = u => Math.exp(-0.5*u*u)/Math.sqrt(2*Math.PI);
  const silvermanBandwidth = arr => {
    const n=arr.length; if(n<2) return 1e-6;
    const m=mean(arr); const s=Math.sqrt(arr.reduce((s,x)=>s+(x-m)**2,0)/(n-1));
    return s===0 ? 1e-6 : 1.06*s*Math.pow(n,-1/5);
  };
  const linspace = (a,b,n=300)=>Array.from({length:n},(_,i)=>a + i*(b-a)/(n-1));

  // --- Normalização e mapeamentos ---
  const labelNorm = (s) => (s||'')
    .normalize('NFD').replace(/\p{Diacritic}/gu,'')
    .replace(/[^a-z0-9]+/gi,' ')
    .replace(/\s+/g,' ')
    .trim().toLowerCase();

  // Mapa rótulo bonitinho → chave no dataset (#mun-data)
  const LABEL_TO_KEY = new Map([
    // IMPOSTOS
    [labelNorm('IPTU'), 'iptu'],
    [labelNorm('ITBI'), 'itbi'],
    [labelNorm('ISS'),  'iss'],
    [labelNorm('Outros Impostos'), 'outros_impostos'],

    // TAXAS
    [labelNorm('Taxas pelo Exercício do Poder de Polícia'), 'taxa_policia'],
    [labelNorm('Taxas pela Prestação de Serviços'),         'taxa_prestacao_servico'],
    [labelNorm('Outras Taxas'),                             'outras_taxas'],

    // CONTRIBUIÇÕES DE MELHORIA
    [labelNorm('Contribuição de Melhoria para Pavimentação e Obras'),  'contribuicao_melhoria_pavimento_obras'],
    [labelNorm('Contribuição de Melhoria para Rede de Água e Esgoto'), 'contribuicao_melhoria_agua_potavel'],
    [labelNorm('Contribuição de Melhoria para Iluminação Pública'),    'contribuicao_melhoria_iluminacao_publica'],
    [labelNorm('Outras Contribuições de Melhoria'),                    'outras_contribuicoes_melhoria'],

    // CONTRIBUIÇÕES (CORRENTES)
    [labelNorm('Custeio do Serviço de Iluminação Pública'), 'contribuicoes_iluminacao_publica'],
    [labelNorm('Contribuições Sociais'),                    'contribuicoes_sociais'],
    [labelNorm('Outras Contribuições'),                     'outras_contribuicoes'],

    // TRANSFERÊNCIAS DA UNIÃO
    [labelNorm('Cota-Parte do FPM'),                          'transferencias_uniao_fpm'],
    [labelNorm('Compensação Financeira (Recursos Naturais)'), 'transferencias_uniao_exploracao'],
    [labelNorm('Recursos do SUS'),                            'transferencias_uniao_sus'],
    [labelNorm('Recursos do FNDE'),                           'transferencias_uniao_fnde'],
    [labelNorm('Recursos do FNAS'),                           'transferencias_uniao_fnas'],
    [labelNorm('Outras Transferências da União'),             'outras_transferencias_uniao'],

    // TRANSFERÊNCIAS DOS ESTADOS
    [labelNorm('Cota-Parte do ICMS'),                         'transferencias_estado_icms'],
    [labelNorm('Cota-Parte do IPVA'),                         'transferencias_estado_ipva'],
    [labelNorm('Compensação Financeira (Recursos Naturais)'), 'transferencias_estado_exploracao'],
    [labelNorm('Recursos do SUS'),                            'transferencias_estado_sus'],
    [labelNorm('Assistência Social'),                         'transferencias_estado_assistencia'],
    [labelNorm('Outras Transferências dos Estados'),          'outras_transferencias_estado'],

    // OUTRAS RECEITAS CORRENTES
    [labelNorm('Receita Patrimonial'),  'receita_patrimonial'],
    [labelNorm('Receita Agropecuária'), 'receita_agropecuaria'],
    [labelNorm('Receita Industrial'),   'receita_industrial'],
    [labelNorm('Receita de Serviços'),  'receita_servicos'],
    [labelNorm('Outras Receitas'),      'outras_receitas_outras'],
  ]);

  // Conjunto dinâmico com TODAS as chaves presentes no array
  let AVAILABLE_KEYS = new Set();

  // Resolve entrada (rótulo amigável OU chave) → chave final
  function resolveKey(input){
    if(!input) return null;

    // Se já for chave exata (como vem do clique no gráfico), use
    if (AVAILABLE_KEYS.has(input)) return input;

    // Tenta mapear rótulo → chave
    const mapped = LABEL_TO_KEY.get(labelNorm(input));
    if (mapped) return mapped;

    // Último fallback: normaliza e retorna mesmo assim (não barre!)
    const norm = labelNorm(input);
    return norm || input;
  }

  function drawDensityPlot(dataKey, allData, filteredMean){
  try{
    if(!allData) return;

    const key = resolveKey(dataKey);
    const raw = allData.map(d => Number(d[key])).filter(v => Number.isFinite(v));
    const values = raw.filter(v => v > 0); // KDE em log precisa > 0

    const ctx = document.getElementById('densidadeReceita');
    if(!ctx) return;
    if(densityChart) densityChart.destroy();

    const fmtBRL = new Intl.NumberFormat('pt-BR', { style:'currency', currency:'BRL', maximumFractionDigits:0 });

    // --- Curva KDE (ou baseline quando faltar dado) ---
    let pontos;
    let poucosDados = false;

    if (values.length < 2) {
      poucosDados = true;
      const m = Number.isFinite(filteredMean) && filteredMean > 0 ? filteredMean : 1;
      const left  = Math.max(1, m * 0.6);
      const right = m * 1.4;
      pontos = [{x:left, y:0},{x:m, y:0},{x:right, y:0}];
    } else {
      const mean = arr => arr.reduce((a,b)=>a+b,0)/arr.length;
      const gaussianKernel = u => Math.exp(-0.5*u*u)/Math.sqrt(2*Math.PI);
      const silvermanBandwidth = arr => {
        const n=arr.length; if(n<2) return 1e-6;
        const m=mean(arr); const s=Math.sqrt(arr.reduce((s,x)=>s+(x-m)**2,0)/(n-1));
        return s===0 ? 1e-6 : 1.06*s*Math.pow(n,-1/5);
      };
      const linspace = (a,b,n=300)=>Array.from({length:n},(_,i)=>a + i*(b-a)/(n-1));
      const logValues = values.map(Math.log);
      const xmin = Math.min(...logValues);
      const xmax = Math.max(...logValues);
      const xGrid = linspace(xmin, xmax, 400);
      const h = silvermanBandwidth(logValues);
      const n = logValues.length;
      const dens = xGrid.map(x => logValues.reduce((s,xi)=>s+gaussianKernel((x-xi)/h),0)/(n*h));
      pontos = xGrid.map((x,i)=>({x: Math.exp(x), y: dens[i]}));
    }

    // --- Annotation: linha tracejada da Faixa Atual + aviso opcional ---
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
        datasets:[
          {
            label: 'Densidade',
            data: pontos,
            borderWidth: 2,
            tension: 0.35,
            fill: true,
            pointRadius: 0,
            borderColor: 'rgba(31,119,180,1)',
            backgroundColor: 'rgba(31,119,180,0.25)'
          }
          // NÃO há dataset para "Faixa Atual": a linha vem da annotation.
        ]
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
              // 🔧 Legenda customizada para exibir “Faixa Atual” como linha tracejada (sem retângulo)
              generateLabels(chart){
                // rótulos padrão (só “Densidade”)
                const base = Chart.defaults.plugins.legend.labels.generateLabels(chart);
                // adiciona o item “Faixa Atual” com traço
                base.push({
                  text: 'Faixa Atual',
                  // estilos usados pelo renderer da legenda para desenhar uma “amostra” de linha
                  strokeStyle: 'rgba(214,39,40,1)',
                  lineWidth: 2,
                  lineDash: [6,6],
                  // estes campos evitam o quadradinho de preenchimento
                  fillStyle: 'rgba(0,0,0,0)',
                  hidden: !Number.isFinite(filteredMean),
                  // índices fictícios, não clicáveis
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
  }catch(err){ console.error('[densidade] erro',err); }
}


  async function updateFilteredDensity(){
    if(!totalMunData) return;
    const p = new URLSearchParams();
    p.set('porte',filtroPorte?.value||'todos');
    p.set('rm',filtroRm?.value||'todos');
    p.set('regiao',filtroRegiao?.value||'todos');
    p.set('uf',filtroUf?.value||'todos');

    try{
      const resp = await fetch(`/api/conjunto-data/?${p.toString()}`);
      if(!resp.ok) throw new Error('Falha ao buscar dados do filtro.');
      const filteredMunData = await resp.json();

      const rawKey = categorySelect?.value;
      const key = resolveKey(rawKey);
      if(!key) return;

      const filteredValues = filteredMunData.map(d => Number(d[key])).filter(Number.isFinite);
      const filteredMean   = mean(filteredValues);
      drawDensityPlot(key, totalMunData, filteredMean);
    }catch(e){ console.error('[densidade] atualização', e); }
  }

  // ===== Init =====
  const rawData = document.getElementById("mun-data")?.textContent;
  if(rawData){
    try{
      totalMunData = JSON.parse(rawData);
      // União de chaves de TODO o array (não só do primeiro!)
      AVAILABLE_KEYS = new Set();
      if (Array.isArray(totalMunData)) {
        for (const row of totalMunData) {
          Object.keys(row||{}).forEach(k => AVAILABLE_KEYS.add(k));
        }
      }
    } catch(e){
      console.error('falha parse #mun-data', e);
    }
  }

  if(categorySelect && totalMunData){
    // desenha inicial (com média global da chave atual)
    const key0 = resolveKey(categorySelect.value);
    const initialValues = totalMunData.map(d => Number(d[key0])).filter(Number.isFinite);
    drawDensityPlot(key0, totalMunData, mean(initialValues));

    // 1) usuário muda manualmente
    categorySelect.addEventListener('change', updateFilteredDensity);

    // 2) mudança programática (clique no gráfico de composição)
    categorySelect.addEventListener('composition-category-changed', (ev) => {
      const incoming = ev.detail?.key || categorySelect.value;
      const k = resolveKey(incoming);
      const vals = totalMunData.map(d => Number(d[k])).filter(Number.isFinite);
      drawDensityPlot(k, totalMunData, mean(vals));
    });
  }

  [filtroPorte, filtroRm, filtroRegiao, filtroUf].forEach(el=>{
    if(el) el.addEventListener('change', updateFilteredDensity);
  });

  if(btnLimpar){
    btnLimpar.addEventListener('click', ()=> setTimeout(updateFilteredDensity, 100));
  }
});
