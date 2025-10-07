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

    // 1) Registrar o plugin de anotação, se ele existir
    const annotationPlugin = window['chartjs-plugin-annotation'];
    if (annotationPlugin) {
        Chart.register(annotationPlugin);
    } else {
        console.warn('Chart.js Annotation plugin não foi encontrado. A linha de média não será exibida.');
    }

    // --- Helpers Estatísticos ---
    const mean = arr => arr.length > 0 ? arr.reduce((a, b) => a + b, 0) / arr.length : null;
    const gaussianKernel = u => Math.exp(-0.5 * u * u) / Math.sqrt(2 * Math.PI);
    const silvermanBandwidth = arr => {
        const n = arr.length;
        if (n < 2) return 1e-6;
        const m = mean(arr);
        const std = Math.sqrt(arr.reduce((s, x) => s + (x - m) ** 2, 0) / (n - 1));
        if (std === 0) return 1e-6;
        return 1.06 * std * Math.pow(n, -1 / 5);
    };
    const linspace = (a, b, n = 300) => {
        const step = (b - a) / (n - 1);
        return Array.from({ length: n }, (_, i) => a + i * step);
    };

    // --- Função principal para desenhar o gráfico ---
    function drawDensityPlot(dataKey, allData, filteredMean) {
        try {
            if (!allData) return;

            const values = allData.map(d => Number(d[dataKey])).filter(v => Number.isFinite(v) && v > 0);
            if (values.length < 2) {
                if(densityChart) densityChart.destroy();
                return;
            }

            const logValues = values.map(Math.log);
            const xmin = Math.min(...logValues);
            const xmax = Math.max(...logValues);
            const xGrid = linspace(xmin, xmax, 400);
            const h = silvermanBandwidth(logValues);
            const n = logValues.length;

            const dens = xGrid.map(x =>
                logValues.reduce((s, xi) => s + gaussianKernel((x - xi) / h), 0) / (n * h)
            );
            
            const pontos = xGrid.map((x, i) => ({ x: Math.exp(x), y: dens[i] }));
            
            const ctx = document.getElementById('densidadeReceita');
            if (!ctx) return;
            if (densityChart) densityChart.destroy();

            const fmtBRL = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 });

            // Define o texto da etiqueta da linha de média
            const labelContent = filteredMean === mean(values) 
                ? `Média (Brasil): ${fmtBRL.format(filteredMean || 0)}`
                : `Média do Filtro: ${fmtBRL.format(filteredMean || 0)}`;

            // Configuração da anotação (linha da média)
            const annotationConfig = {
                annotations: {
                    linhaMediaFiltro: {
                        type: 'line',
                        xMin: filteredMean,
                        xMax: filteredMean,
                        borderColor: '#dc3545', // Vermelho
                        borderWidth: 2,
                        borderDash: [6, 6], // Linha pontilhada
                        display: Number.isFinite(filteredMean), // Só exibe se a média for um número válido
                        label: {
                            enabled: true,
                            content: labelContent,
                            position: 'start',
                            backgroundColor: 'rgba(220, 53, 69, 0.8)',
                            color: '#fff',
                            padding: 6,
                            borderRadius: 4,
                        }
                    }
                }
            };
            
            densityChart = new Chart(ctx, {
                type: 'line',
                data: {
                    datasets: [{
                        label: 'Densidade (Brasil)',
                        data: pontos,
                        borderWidth: 2,
                        fill: true,
                        pointRadius: 0,
                        tension: 0.35,
                    }]
                },
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
                            label: (item) => `Densidade: ${item.parsed.y.toFixed(4)}`
                        }},
                        legend: { display: false },
                        annotation: annotationPlugin ? annotationConfig : {}
                    }
                }
            });

        } catch (err) {
            console.error("Falha ao desenhar o gráfico de densidade:", err);
        }
    }

    // --- Função para buscar dados, calcular média e atualizar o gráfico ---
    async function updateFilteredDensity() {
        if (!totalMunData) return;

        const p = new URLSearchParams();
        p.set('porte', filtroPorte?.value || 'todos');
        p.set('rm', filtroRm?.value || 'todos');
        p.set('regiao', filtroRegiao?.value || 'todos');
        p.set('uf', filtroUf?.value || 'todos');
        
        try {
            const resp = await fetch(`/api/conjunto-data/?${p.toString()}`);
            if (!resp.ok) throw new Error('Falha ao buscar dados do filtro.');
            
            const filteredMunData = await resp.json();
            const currentCategory = categorySelect?.value;

            if (currentCategory) {
                const filteredValues = filteredMunData.map(d => Number(d[currentCategory])).filter(Number.isFinite);
                const filteredMean = mean(filteredValues);
                
                drawDensityPlot(currentCategory, totalMunData, filteredMean);
            }
        } catch (e) {
            console.error('[densidade] erro na atualização:', e);
        }
    }

    // --- INICIALIZAÇÃO E EVENT LISTENERS ---
    
    // 1. Carrega os dados totais do Brasil a partir do HTML
    const rawData = document.getElementById("mun-data")?.textContent;
    if (rawData) {
        try {
            totalMunData = JSON.parse(rawData);
        } catch(e) {
            console.error("Falha ao parsear dados de #mun-data", e);
        }
    }

    // 2. Desenha o gráfico inicial
    if (categorySelect && totalMunData) {
        // CORREÇÃO AQUI: Calcula a média do total para a primeira visualização
        const currentCategory = categorySelect.value;
        const initialValues = totalMunData.map(d => Number(d[currentCategory])).filter(Number.isFinite);
        const initialMean = mean(initialValues);
        drawDensityPlot(currentCategory, totalMunData, initialMean);
    }
    
    // 3. Adiciona os listeners para os filtros
    [filtroPorte, filtroRm, filtroRegiao, filtroUf, categorySelect].forEach(el => {
        if (el) el.addEventListener('change', updateFilteredDensity);
    });

    if (btnLimpar) {
        btnLimpar.addEventListener('click', () => {
            setTimeout(updateFilteredDensity, 100);
        });
    }
});