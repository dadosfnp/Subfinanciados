// detail/static/detail/js/script_density_copy.js

document.addEventListener("DOMContentLoaded", () => {
    // --- Variáveis Globais para este script ---
    let densityChart = null;
    let totalMunData = null; // Guardará os dados de todos os municípios
    
    // --- Elementos do DOM ---
    const categorySelect = document.getElementById('chart-category-select');
    const filtroPorte = document.getElementById('filtro-porte');
    const filtroRm = document.getElementById('filtro-rm');
    const filtroRegiao = document.getElementById('filtro-regiao');
    const filtroUf = document.getElementById('filtro-uf');
    const btnLimpar = document.getElementById('btn-limpar-filtros');

    // --- Helpers Estatísticos (KDE) ---
    const gaussianKernel = u => Math.exp(-0.5 * u * u) / Math.sqrt(2 * Math.PI);
    const silvermanBandwidth = arr => {
        const n = arr.length;
        if (n < 2) return 1e-6;
        const mean = arr.reduce((a, b) => a + b, 0) / n;
        const std = Math.sqrt(arr.reduce((s, x) => s + (x - mean) ** 2, 0) / (n - 1));
        if (std === 0) return 1e-6;
        return 1.06 * std * Math.pow(n, -1 / 5);
    };
    const linspace = (a, b, n = 300) => {
        const step = (b - a) / (n - 1);
        return Array.from({ length: n }, (_, i) => a + i * step);
    };

    // --- Função para calcular os pontos da curva KDE ---
    function calculateKDE(data, dataKey) {
        if (!data || data.length === 0) return [];
        const values = data.map(d => Number(d[dataKey])).filter(v => Number.isFinite(v) && v > 0);
        if (values.length < 2) return [];

        const logValues = values.map(Math.log);
        const xmin = Math.min(...logValues);
        const xmax = Math.max(...logValues);
        const xGrid = linspace(xmin, xmax, 400);
        const h = silvermanBandwidth(logValues);
        const n = logValues.length;

        const dens = xGrid.map(x =>
            logValues.reduce((s, xi) => s + gaussianKernel((x - xi) / h), 0) / (n * h)
        );

        return xGrid.map((x, i) => ({ x: Math.exp(x), y: dens[i] }));
    }

    // --- Função principal para desenhar o gráfico com múltiplos datasets ---
    function drawDensityPlot(dataKey, allData, filteredData) {
        try {
            const totalPoints = calculateKDE(allData, dataKey);
            const filteredPoints = calculateKDE(filteredData, dataKey);

            const datasets = [];

            // Dataset da densidade total (fundo)
            if (totalPoints.length > 0) {
                datasets.push({
                    label: 'Densidade Total (Brasil)',
                    data: totalPoints,
                    borderColor: 'rgba(200, 200, 200, 0.8)',
                    backgroundColor: 'rgba(200, 200, 200, 0.2)',
                    borderWidth: 1.5,
                    fill: true,
                    pointRadius: 0,
                    tension: 0.35,
                });
            }

            // Dataset da densidade do filtro (destaque)
            if (filteredPoints.length > 0) {
                datasets.push({
                    label: 'Densidade do Filtro',
                    data: filteredPoints,
                    borderColor: 'rgba(31, 119, 180, 1)',
                    backgroundColor: 'rgba(31, 119, 180, 0.3)',
                    borderWidth: 2,
                    fill: true,
                    pointRadius: 0,
                    tension: 0.35,
                });
            }

            const ctx = document.getElementById('densidadeReceita');
            if (!ctx) return;
            if (densityChart) densityChart.destroy();
            
            const fmtBRL = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 });

            densityChart = new Chart(ctx, {
                type: 'line',
                data: { datasets },
                options: {
                    parsing: false,
                    maintainAspectRatio: false,
                    scales: {
                        x: { type: 'linear', title: { display: true, text: 'Valor (R$)' }, ticks: { callback: (val) => fmtBRL.format(val) } },
                        y: { title: { display: true, text: 'Densidade' }, beginAtZero: true }
                    },
                    plugins: {
                        tooltip: { callbacks: {
                            title: (items) => items.length ? fmtBRL.format(items[0].parsed.x) : '',
                            label: (item) => `${item.dataset.label}: ${item.parsed.y.toFixed(4)}`
                        }},
                        legend: { labels: { usePointStyle: true }, position: 'top' },
                    }
                }
            });
        } catch (err) {
            console.error("Falha ao desenhar o gráfico de densidade:", err);
        }
    }

    // --- Função para buscar dados filtrados e atualizar o gráfico ---
    async function updateFilteredDensity() {
        if (!totalMunData) return; // Garante que os dados totais foram carregados

        // Replica a lógica da função buildParams() do script.js
        const p = new URLSearchParams();
        p.set('porte', filtroPorte?.value || 'todos');
        p.set('rm', filtroRm?.value || 'todos');
        p.set('regiao', filtroRegiao?.value || 'todos');
        p.set('uf', filtroUf?.value || 'todos');
        
        try {
            const resp = await fetch(`/api/conjunto-data/?${p.toString()}`);
            if (!resp.ok) throw new Error('Falha ao buscar dados para o gráfico de densidade.');
            
            const filteredMunData = await resp.json();
            const currentCategory = categorySelect?.value;

            if (currentCategory) {
                drawDensityPlot(currentCategory, totalMunData, filteredMunData);
            }
        } catch (e) {
            console.error('[densidade] erro ao buscar dados filtrados:', e);
        }
    }

    // --- INICIALIZAÇÃO E EVENT LISTENERS ---
    
    // 1. Carrega os dados totais do HTML
    const rawData = document.getElementById("mun-data")?.textContent;
    if (rawData) {
        try {
            totalMunData = JSON.parse(rawData);
        } catch(e) {
            console.error("Falha ao parsear dados iniciais de #mun-data", e);
        }
    }

    // 2. Desenha o gráfico inicial (total + filtro inicial que é igual ao total)
    if (categorySelect && totalMunData) {
        drawDensityPlot(categorySelect.value, totalMunData, totalMunData);
    }
    
    // 3. Adiciona os listeners para os filtros
    [filtroPorte, filtroRm, filtroRegiao, filtroUf, categorySelect].forEach(el => {
        if (el) el.addEventListener('change', updateFilteredDensity);
    });

    if (btnLimpar) {
        btnLimpar.addEventListener('click', () => {
            // Atraso leve para garantir que os valores do select sejam resetados pelo script.js
            setTimeout(updateFilteredDensity, 100); 
        });
    }
});