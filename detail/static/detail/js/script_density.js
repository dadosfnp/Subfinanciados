// detail/static/detail/js/script_density.js
document.addEventListener("DOMContentLoaded", () => {
  let densityChart = null;
  let totalMunData = null;

  const categorySelect = document.getElementById('chart-category-select');
  const filtroPorte = document.getElementById('filtro-porte');
  const filtroRm = document.getElementById('filtro-rm');
  const filtroRegiao = document.getElementById('filtro-regiao');
  const filtroUf = document.getElementById('filtro-uf');
  const btnLimpar = document.getElementById('btn-limpar-filtros');

  // Plugin de anotação
  const annotationPlugin = window['chartjs-plugin-annotation'];
  if (annotationPlugin) Chart.register(annotationPlugin);

  // Helpers estatísticos
  const mean = arr => arr.length ? arr.reduce((a,b)=>a+b,0)/arr.length : 0;
  const gaussianKernel = u => Math.exp(-0.5*u*u)/Math.sqrt(2*Math.PI);
  const silvermanBandwidth = arr => {
    const n=arr.length; if(n<2) return 1e-6;
    const m=mean(arr); const s=Math.sqrt(arr.reduce((s,x)=>s+(x-m)**2,0)/(n-1));
    return s===0 ? 1e-6 : 1.06*s*Math.pow(n,-1/5);
  };
  const linspace = (a,b,n=300)=>Array.from({length:n},(_,i)=>a + i*(b-a)/(n-1));

  function drawDensityPlot(dataKey, allData, filteredMean){
    try{
      if(!allData) return;
      const values = allData.map(d => Number(d[dataKey])).filter(v => Number.isFinite(v) && v>0);
      if(values.length < 2){ if(densityChart) densityChart.destroy(); return; }

      const logValues = values.map(Math.log);
      const xmin = Math.min(...logValues);
      const xmax = Math.max(...logValues);
      const xGrid = linspace(xmin, xmax, 400);
      const h = silvermanBandwidth(logValues);
      const n = logValues.length;
      const dens = xGrid.map(x => logValues.reduce((s,xi)=>s+gaussianKernel((x-xi)/h),0)/(n*h));
      const pontos = xGrid.map((x,i)=>({x: Math.exp(x), y: dens[i]}));

      const ctx = document.getElementById('densidadeReceita');
      if(!ctx) return;
      if(densityChart) densityChart.destroy();

      const fmtBRL = new Intl.NumberFormat('pt-BR', { style:'currency', currency:'BRL', maximumFractionDigits:0 });

      // annotation (linha da faixa atual)
      const annotationConfig = annotationPlugin ? {
        annotations: {
          faixaAtual: {
            type:'line',
            xMin: filteredMean, xMax: filteredMean,
            borderColor: 'rgba(214,39,40,1)',
            borderWidth: 2,
            borderDash: [6,6],
            display: Number.isFinite(filteredMean),
            label: {
              enabled: true,
              content: `Receita Per Capita: ${fmtBRL.format(filteredMean||0)}`,
              position: 'start',
              backgroundColor: 'rgba(0,0,0,.75)',
              color:'#fff',
              padding:6,
              borderRadius:4
            }
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
            },
            // dataset vazio apenas para exibir "Faixa Atual" na legenda
            {
              label: 'Faixa Atual',
              data: [],
              borderColor: 'rgba(214,39,40,1)',
              borderDash: [6,6],
              borderWidth: 2,
              pointRadius: 0,
              fill: false,
              type: 'line'
            }
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
            legend:{ position:'bottom', labels:{ usePointStyle:false } },
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
      const key = categorySelect?.value;
      if(!key) return;

      const filteredValues = filteredMunData.map(d => Number(d[key])).filter(Number.isFinite);
      const filteredMean = mean(filteredValues);
      drawDensityPlot(key, totalMunData, filteredMean);
    }catch(e){ console.error('[densidade] atualização', e); }
  }

  // ===== Init =====
  const rawData = document.getElementById("mun-data")?.textContent;
  if(rawData){
    try{ totalMunData = JSON.parse(rawData); } catch(e){ console.error('falha parse #mun-data', e); }
  }

  if(categorySelect && totalMunData){
    const key = categorySelect.value;
    const initialValues = totalMunData.map(d => Number(d[key])).filter(Number.isFinite);
    drawDensityPlot(key, totalMunData, mean(initialValues));
  }

  [filtroPorte, filtroRm, filtroRegiao, filtroUf, categorySelect].forEach(el=>{
    if(el) el.addEventListener('change', updateFilteredDensity);
  });
  if(btnLimpar){
    btnLimpar.addEventListener('click', ()=> setTimeout(updateFilteredDensity, 100));
  }
});
