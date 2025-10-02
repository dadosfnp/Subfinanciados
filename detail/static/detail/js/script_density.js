// script_density.js

// 1) Registrar o plugin de anotação (precisa estar após carregar chart.js e chartjs-plugin-annotation)
const annotationPlugin = window['chartjs-plugin-annotation'];
if (annotationPlugin) {
  Chart.register(annotationPlugin);
}

// 2) Helpers estatísticos
const mean = arr => arr.reduce((a,b)=>a+b,0)/arr.length;
const variance = arr => {
  const m = mean(arr);
  return arr.reduce((s,x)=>s+(x-m)*(x-m),0)/(arr.length-1);
};
const std = arr => Math.sqrt(Math.max(variance(arr), 0));
const silvermanBandwidth = arr => {
  const s = std(arr);
  const n = arr.length;
  if (n < 2 || s === 0) return 1e-6;
  return 1.06 * s * Math.pow(n, -1/5);
};
const gaussianKernel = u => Math.exp(-0.5 * u * u) / Math.sqrt(2 * Math.PI);
const linspace = (a, b, n=300) => {
  if (n < 2) return [a];
  const step = (b - a) / (n - 1);
  return Array.from({length: n}, (_,i) => a + i*step);
};

// 3) Loader principal
(async function loadAndDraw() {
  try {
    // a) Buscar dados da API
    const res = await fetch("http://127.0.0.1:8000/api/dados-municipios/");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    // b) Extrair vetor de receitas (só números finitos)
    const receitas = (data?.features ?? [])
      .map(f => f?.properties?.rc_23_pc)
      .filter(v => Number.isFinite(v));

    if (!receitas.length) {
      console.warn("Sem valores numéricos em rc_23_pc.");
      return;
    }

    // c) Preparar KDE (usar log por assimetria)
    const useLog = true;
    const dataTransf = useLog ? receitas.filter(v => v > 0).map(Math.log) : receitas.slice();
    if (!dataTransf.length) {
      console.warn("Sem dados válidos após log.");
      return;
    }

    const xmin = Math.min(...dataTransf);
    const xmax = Math.max(...dataTransf);
    const xGrid = linspace(xmin, xmax, 400);
    const h = silvermanBandwidth(dataTransf);
    const n = dataTransf.length;

    const dens = xGrid.map(x =>
      dataTransf.reduce((s, xi) => s + gaussianKernel((x - xi) / h), 0) / (n * h)
    );

    const pontos = xGrid.map((x, i) => ({
      x: useLog ? Math.exp(x) : x,
      y: dens[i]
    }));

    // d) Formatador BRL e densidade no x de referência (se quiser a linha)
    const fmtBRL = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 });
    const xRef = 4884.60818016387;
    const densityAtX = (pts, x) => {
      let i = 0;
      while (i < pts.length && pts[i].x < x) i++;
      if (i === 0) return pts[0].y;
      if (i === pts.length) return pts[pts.length - 1].y;
      const p0 = pts[i-1], p1 = pts[i];
      const t = (x - p0.x) / (p1.x - p0.x);
      return p0.y + t * (p1.y - p0.y);
    };

    // e) Montar o chart
    const ctx = document.getElementById('densidadeReceita');
    if (!ctx) {
      console.warn("#densidadeReceita não encontrado no DOM.");
      return;
    }

    new Chart(ctx, {
      type: 'line',
      data: {
        datasets: [{
          label: 'Densidade',
          data: pontos,
          borderWidth: 2,
          tension: 0.35,
          fill: true,
          pointRadius: 0
        }]
      },
      options: {
        parsing: false,
        animation: false,
        maintainAspectRatio: false,
        scales: {
          x: {
            type: 'linear',
            title: {
              display: true,
              text: useLog ? 'Receita' : 'Receita'
            },
            ticks: { callback: (val) => fmtBRL.format(val) }
          },
          y: {
            title: { display: true, text: 'Densidade' },
            beginAtZero: true
          }
        },
        plugins: {
          tooltip: {
            callbacks: {
              title: (items) => items.length ? fmtBRL.format(items[0].parsed.x) : '',
              label: (item) => `Densidade: ${item.parsed.y.toFixed(4)}`
            }
          },
          legend: { labels: { usePointStyle: true } },
          annotation: {
            annotations: {
              linhaRef: {
                type: 'line',
                xMin: xRef,
                xMax: xRef,
                borderColor: 'red',
                borderWidth: 2,
                borderDash: [6, 6],
                label: {
                  enabled: true,
                  position: 'end',
                  backgroundColor: 'rgba(0,0,0,0.75)',
                  color: '#fff',
                  padding: 6,
                  content: () => `${fmtBRL.format(xRef)} • dens=${densityAtX(pontos, xRef).toFixed(4)}`
                }
              }
            }
          }
        }
      }
    });
  } catch (err) {
    console.error("Falha ao carregar/desenhar densidade:", err);
  }
})();
