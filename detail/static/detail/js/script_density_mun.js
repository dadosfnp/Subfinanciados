// script_density.js

// Variável para guardar a instância do gráfico e poder destruí-la depois
let densityChart = null;

// 1) Registrar o plugin de anotação
const annotationPlugin = window['chartjs-plugin-annotation'];
if (annotationPlugin) {
  Chart.register(annotationPlugin);
}

// 2) Helpers estatísticos (sem alterações aqui)
const mean = arr => arr.reduce((a, b) => a + b, 0) / arr.length;
const variance = arr => {
    const m = mean(arr);
    return arr.reduce((s, x) => s + (x - m) * (x - m), 0) / (arr.length - 1);
};
const std = arr => Math.sqrt(Math.max(variance(arr), 0));
const silvermanBandwidth = arr => {
    const s = std(arr);
    const n = arr.length;
    if (n < 2 || s === 0) return 1e-6;
    return 1.06 * s * Math.pow(n, -1 / 5);
};
const gaussianKernel = u => Math.exp(-0.5 * u * u) / Math.sqrt(2 * Math.PI);
const linspace = (a, b, n = 300) => {
    if (n < 2) return [a];
    const step = (b - a) / (n - 1);
    return Array.from({ length: n }, (_, i) => a + i * step);
};
const densityAtX = (pts, x) => {
    let i = 0;
    while (i < pts.length && pts[i].x < x) i++;
    if (i === 0) return pts[0].y;
    if (i === pts.length) return pts[pts.length - 1].y;
    const p0 = pts[i - 1], p1 = pts[i];
    const t = (x - p0.x) / (p1.x - p0.x);
    return p0.y + t * (p1.y - p0.y);
};

// 3) Função principal para desenhar o gráfico, agora parametrizada
async function drawDensityPlot(dataKey) {
    try {
        // a) Obter os dados brutos do HTML
        const raw = document.getElementById("mun-data").textContent;
        const dados = JSON.parse(raw);

        // b) Extrair o vetor de dados usando a CHAVE DINÂMICA (dataKey)
        const receitas = dados
            .map(d => Number(d[dataKey])) // <-- MUDANÇA PRINCIPAL AQUI
            .filter(v => Number.isFinite(v));

        if (!receitas.length) {
            console.warn(`Sem valores numéricos em '${dataKey}'.`);
            return;
        }

        // c) Obter o valor de referência para o município em foco
        const pathParts = window.location.pathname.split("/");
        const cod_ibge = pathParts.find(p => /^\d{7}$/.test(p));
        const municipio = dados.find(d => String(d.cod_ibge) === String(cod_ibge));
        
        if (!municipio) {
            console.warn("Município não encontrado:", cod_ibge);
            return;
        }
        
        // Extrai o valor de referência usando a CHAVE DINÂMICA
        const xRef = Number(municipio[dataKey]); // <-- MUDANÇA PRINCIPAL AQUI
        if (!Number.isFinite(xRef)) {
            console.warn(`Valor de referência inválido para '${dataKey}' no município ${cod_ibge}.`);
            // Você pode optar por desenhar o gráfico sem a linha de referência ou não desenhar nada
        }


        // d) Preparar KDE (Kernel Density Estimation)
        const useLog = true;
        const dataTransf = useLog ? receitas.filter(v => v > 0).map(Math.log) : receitas.slice();
        if (!dataTransf.length) {
            console.warn("Sem dados válidos após transformação logarítmica.");
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

        // e) Montar o chart
        const ctx = document.getElementById('densidadeReceita');
        if (!ctx) {
            console.warn("#densidadeReceita não encontrado no DOM.");
            return;
        }
        
        // Destruir o gráfico antigo antes de criar um novo
        if (densityChart) {
            densityChart.destroy();
        }

        const fmtBRL = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 });
        
        // Guardar a nova instância do gráfico na variável global
        densityChart = new Chart(ctx, {
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
                animation: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'linear',
                        title: { display: true, text: 'Valor (R$)' },
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
                                display: Number.isFinite(xRef), // Só mostra a linha se o valor for válido
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
}

// 4) Gatilho: Adicionar o event listener e fazer a chamada inicial
document.addEventListener("DOMContentLoaded", () => {
    const categorySelect = document.getElementById('chart-category-select');

    if (categorySelect) {
        // Desenha o gráfico inicial com o valor padrão do select
        drawDensityPlot(categorySelect.value);

        // Adiciona o listener para redesenhar quando o valor mudar
        categorySelect.addEventListener('change', (event) => {
            drawDensityPlot(event.target.value);
        });
    }
});