// >>> HOME filters: lista em cascata e atualização de dados <<<

// Variáveis globais para elementos DOM e instância do gráfico
let filtroRegiao;
let filtroUf;
let filtroRm;
let filtroConsorcio;
let filtroPorte;
let btnLimpar;

let quantilQuintilRadio;
let quantilDecilRadio;

let formatNumeroRadio;
let formatPorcentagemRadio;

let calcModeTotalRadio;
let calcModeFilteredRadio;

let toggle2025;
let toggle2000e2025;

let populacaoQuintilCtx;
let populacaoQuintilChart;

// Variáveis das tabelas
let tableCard2025;
let table2025Head;
let table2025Body;

let tableCard2000;
let table2000Head;
let table2000Body;

/**
 * Restaura o valor de um <select> se existir entre as opções; senão, cai para 'todos'.
 */
function restoreSelectValue(selectEl, value) {
    const has = Array.from(selectEl.options).some(o => o.value === value);
    selectEl.value = has ? value : 'todos';
}

/**
 * Pinta o número da Diferença % (verde/verm.) conforme sinal.
 * Espera valor EM PORCENTO (ex.: 24.1, -3.5).
 */
function applyDiffColor(percentValue) {
    const el = document.getElementById('summary-diff-nacional');
    if (!el) return;
    const EPS = 0.0001;
    el.classList.remove('positive', 'negative', 'neutral');
    if (percentValue > EPS) el.classList.add('positive');
    else if (percentValue < -EPS) el.classList.add('negative');
    else el.classList.add('neutral');
}

/**
 * Constrói os parâmetros de URL com base nos selects atuais da Home.
 */
function buildHomeParams() {
    const p = new URLSearchParams();
    p.set('porte', filtroPorte?.value || 'todos');
    p.set('rm', filtroRm?.value || 'todos');
    p.set('consorcio', filtroConsorcio?.value || 'todos');
    p.set('regiao', filtroRegiao?.value || 'todos');
    p.set('uf', filtroUf?.value || 'todos');
    return p;
}

/**
 * Atualiza os filtros DEPENDENTES (em cascata) enviando o estado atual para a API.
 */
async function updateDependentFilters(initial = false) {
    if (!filtroRegiao || !filtroUf || !filtroRm) return;

    const regiaoAtual = filtroRegiao.value;
    const ufAtual     = filtroUf.value;
    const rmAtual     = filtroRm.value;
    const consorcioAtual = filtroConsorcio ? filtroConsorcio.value : 'todos';

    try {
        const resp = await fetch(`/api/get-dependent-filters/?${buildHomeParams().toString()}`);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();

        filtroRegiao.innerHTML = '<option value="todos">Todas</option>';
        (data.regioes || []).forEach(v => filtroRegiao.add(new Option(v, v)));
        restoreSelectValue(filtroRegiao, regiaoAtual);

        filtroRm.innerHTML = '<option value="todos">Todos</option>';
        (data.rms || []).forEach(v => filtroRm.add(new Option(v, v)));
        restoreSelectValue(filtroRm, rmAtual);

        if (filtroConsorcio) {
            filtroConsorcio.innerHTML = '<option value="todos">Todos</option>';
            (data.consorcios || []).forEach(v => filtroConsorcio.add(new Option(v, v)));
            restoreSelectValue(filtroConsorcio, consorcioAtual);
        }

        filtroUf.innerHTML = '<option value="todos">Todas</option>';
        (data.ufs || []).forEach(v => filtroUf.add(new Option(v, v)));
        restoreSelectValue(filtroUf, ufAtual);

    } catch (error) {
        console.error('Erro ao atualizar filtros dependentes na Home:', error);
    }

    if (!initial) await atualizarFiltros();
}

/**
 * Renderiza tabela genérica
 */
function renderTable(tableHeadElement, tableBodyElement, headers, data) {
    tableHeadElement.innerHTML = '';
    tableBodyElement.innerHTML = '';

    const headerRow = tableHeadElement.insertRow();
    headers.forEach(headerText => {
        const th = document.createElement('th');
        th.textContent = headerText;
        if (headerText === 'Faixas' || headerText === 'Total') th.style.fontWeight = 'bold';
        headerRow.appendChild(th);
    });

    data.forEach(rowData => {
        const row = tableBodyElement.insertRow();
        headers.forEach(headerKey => {
            const cell = row.insertCell();
            const cellValue = rowData[headerKey];
            cell.textContent = cellValue;
            if (headerKey === 'Faixas' || headerKey === 'Total') cell.style.fontWeight = 'bold';
        });
    });
}

/**
 * Busca e atualiza cards, gráfico e tabelas com base nos filtros atuais.
 */
async function atualizarFiltros() {
    const selectedRegiao = filtroRegiao.value;
    const selectedUf = filtroUf.value;
    const selectedRm = filtroRm.value;
    const selectedConsorcio = filtroConsorcio ? filtroConsorcio.value : 'todos';
    const selectedPorte = filtroPorte ? filtroPorte.value : 'todos';

    const classificationFilter = quantilDecilRadio?.checked ? 'decil' : 'quintil';
    const displayFormat = formatPorcentagemRadio?.checked ? 'porcentagem' : 'numero';
    const calculationMode = calcModeFilteredRadio.checked ? 'por_filtro' : 'total';
    const variavelAnalisadaSelect = document.getElementById('variavelAnalisadaSelect');
    const variavelAnalisada = variavelAnalisadaSelect ? variavelAnalisadaSelect.value : 'populacao';

    const selectedYearOptionElement = document.querySelector('.toggle-option.active');
    const selectedYearOption = selectedYearOptionElement ? selectedYearOptionElement.dataset.option : '2025';
    const include2000Data = (selectedYearOption === '2000 e 2025');

    const capagTipoSelect = document.getElementById('capagTipoSelect');
    const capagNotaSelect = document.getElementById('capagNotaSelect');

    const riscoTipoSelect = document.getElementById('riscoTipoSelect');
    const riscoNivelSelect = document.getElementById('riscoNivelSelect');

    const apiUrl =
        `/api/dashboard-data/?regiao=${selectedRegiao}` +
        `&uf=${selectedUf}` +
        `&rm=${selectedRm}` +
        `&consorcio=${encodeURIComponent(selectedConsorcio)}` +
        `&porte=${selectedPorte}` +
        `&classification=${classificationFilter}` +
        `&display_format=${displayFormat}` +
        `&calculation_mode=${calculationMode}` +
        `&include_2000_data=${include2000Data}` +
        `&variavel_analisada=${variavelAnalisada}` +
        `&capag_campo=${encodeURIComponent(capagTipoSelect ? capagTipoSelect.value : 'geral')}` +
        `&capag_nota=${encodeURIComponent(capagNotaSelect ? capagNotaSelect.value : 'todos')}` +
        `&risco_campo=${encodeURIComponent(riscoTipoSelect ? riscoTipoSelect.value : 'media_ponderada')}` +
        `&risco_nivel=${encodeURIComponent(riscoNivelSelect ? riscoNivelSelect.value : 'todos')}`;

    try {
        const response = await fetch(apiUrl);
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Erro HTTP! Status: ${response.status}, Mensagem: ${errorText}`);
        }
        const data = await response.json();

        // ==== Cards de resumo ====
        document.getElementById('summary-total-municipios').textContent =
            `${data.summaryCards.totalMunicipios.toLocaleString('pt-BR')} (${data.summaryCards.percTotalMunicipios.toFixed(1)}%)`;

        document.getElementById('summary-media-receita').textContent =
            data.summaryCards.mediaReceitaPerCapita.toLocaleString(
                'pt-BR',
                { style: 'currency', currency: 'BRL' }
            );

        const diffNational = data.summaryCards.diffMediaNacional; 
        const diffValueEl = document.getElementById('summary-diff-nacional');
        diffValueEl.textContent = `${diffNational.toFixed(1)}%`;

        const diffTrendElement = document.getElementById('summary-diff-nacional-trend');
        diffTrendElement.textContent = diffNational > 0
            ? 'Acima da média nacional'
            : (diffNational < 0 ? 'Abaixo da média nacional' : 'Na média nacional');
        diffTrendElement.className =
            `sub-value ${diffNational < 0 ? 'negative' : ''} ${diffNational > 0 ? 'positive' : ''}`;

        applyDiffColor(diffNational);
        document.getElementById('summary-gini').textContent = data.summaryCards.giniIndex;

        // Atualizar Títulos Dinâmicos (exceto o gráfico principal que agora tem o select)
        if (data.tableTitle24) {
            const tTitle24 = document.getElementById('table-2025-title');
            if (tTitle24) tTitle24.textContent = data.tableTitle24;
        }
        if (data.tableTitle00) {
            const tTitle00 = document.getElementById('table-2000-title');
            if (tTitle00) tTitle00.textContent = data.tableTitle00;
        }

        // ==== Gráfico ====
        populacaoQuintilChart.data.labels = data.chartData.labels;
        populacaoQuintilChart.data.datasets = [];

        // =====================================================
        // PALETA E RENDERIZAÇÃO DE DADOS NO GRÁFICO
        // =====================================================
        const QUINTIL_PALETTE = [
            '#A33242', '#D97636', '#E8C83E', '#72BA6A', '#2D8A4E'
        ];

        const DECIL_PALETTE = [
            '#a50026', '#d73027', '#f46d43', '#fdae61', '#fee08b',
            '#d9ef8b', '#a6d96a', '#66bd63', '#1a9850', '#006837'
        ];

        // Nota geral: gradiente do verde ao vermelho
        const CAPAG_PALETTE = {
            'A': '#2D8A4E',
            'B': '#72BA6A',
            'C': '#E8C83E',
            'D e outros': '#A33242'
        };

        // Indicadores I, II e III: semáforo, com cinza para a faixa sem nota
        const CAPAG_INDICADOR_PALETTE = {
            'A': '#2D8A4E',            // verde
            'B': '#E8C83E',            // amarelo
            'C': '#A33242',            // vermelho
            'n.d. ou n.e.': '#9E9E9E'  // cinza
        };

        const RISCO_PALETTE = {
            'Muito baixo': '#2D8A4E',
            'Baixo': '#72BA6A',
            'Médio': '#E8C83E',
            'Alto': '#D97636',
            'Muito alto': '#A33242'
        };

        /* Retorna a paleta correta baseada no número de grupos (5 para Quintil, 10 para Decil) */
        const getColors = (count) => {
            if (count > 5) return DECIL_PALETTE; 
            return QUINTIL_PALETTE;
        };

        // A nota geral e os indicadores da CAPAG têm paleta e ordem de legenda próprias
        const capagEhIndicador = variavelAnalisada === 'capag' && capagTipoSelect && capagTipoSelect.value !== 'geral';

        if (data.chartData.datasets?.length > 0) {
            const createDiagonalPattern = (color) => {
                const shape = document.createElement('canvas');
                shape.width = 10;
                shape.height = 10;
                const c = shape.getContext('2d');
                c.fillStyle = color;
                c.fillRect(0, 0, 10, 10);
                c.strokeStyle = '#ffffff';
                c.lineWidth = 2; 
                c.beginPath();
                c.moveTo(0, 10);
                c.lineTo(10, 0);
                c.stroke();
                return populacaoQuintilChart.ctx.createPattern(shape, 'repeat');
            };

            if (data.chartData.datasets.length === 2 && variavelAnalisada === 'populacao') {
                data.chartData.datasets.sort((a, b) => {
                    if (a.label.includes('2000')) return -1;
                    if (b.label.includes('2000')) return 1;
                    return 0;
                });
            }

            data.chartData.datasets.forEach((dataset) => {
                let barColors;
                if (variavelAnalisada === 'populacao') {
                    // Cada barra recebe uma cor dependendo do seu índice (Quintil/Decil)
                    barColors = getColors(dataset.data.length);
                } else {
                    // Uma cor por dataset
                    const labelBase = dataset.label.replace(' (2025)', '').replace(' (2000)', '');
                    let singleColor = '#cccccc';
                    if (variavelAnalisada === 'capag') {
                        singleColor = (capagEhIndicador ? CAPAG_INDICADOR_PALETTE : CAPAG_PALETTE)[labelBase] || '#9E9E9E';
                    } else if (variavelAnalisada === 'risco_climatico') {
                        singleColor = RISCO_PALETTE[labelBase] || '#9E9E9E';
                    }
                    barColors = Array(dataset.data.length).fill(singleColor);
                }

                const is2025 = dataset.label.toString().includes('2025');

                const backgroundColors = barColors.map(color => 
                    is2025 ? color : createDiagonalPattern(color) 
                );

                populacaoQuintilChart.data.datasets.push({
                    // Só o modo população compara anos; nos demais a legenda dispensa o ano (o tooltip mantém)
                    label: variavelAnalisada !== 'populacao'
                        ? dataset.label.replace(/ \((?:2000|2025)\)$/, '')
                        : dataset.label,
                    tooltipLabel: dataset.label, // label completo (com ano) usado só no tooltip
                    data: dataset.data,
                    backgroundColor: backgroundColors,
                    borderColor: barColors, 
                    borderWidth: 2,
                    fill: true,
                    barPercentage: 0.6,      
                    categoryPercentage: 0.6, 
                    grouped: variavelAnalisada === 'populacao'
                });
            });

        } else {
            console.warn('A API não retornou dados para o gráfico.');
        }

        populacaoQuintilChart.options.scales.x.stacked = variavelAnalisada !== 'populacao';
        populacaoQuintilChart.options.scales.y.stacked = variavelAnalisada !== 'populacao';
        populacaoQuintilChart.options.scales.y.title.text = data.chartData.yAxisTitle;
        populacaoQuintilChart.options.scales.y.ticks.callback = function (value) {
            if (formatPorcentagemRadio.checked) return value.toFixed(0) + '%';
            return variavelAnalisada === 'populacao' 
                ? value.toLocaleString('pt-BR') + 'M' 
                : value.toLocaleString('pt-BR');
        };

        // Arrumando formatter dos tooltips (Datalabels plugin config in default init can't be changed here without replacing the whole formatter, but wait - there is datalabels plugin!)
        populacaoQuintilChart.options.plugins.datalabels.formatter = function (value) {
            if (value === 0) return ''; // Hide 0 values for cleaner stacked charts
            if (formatPorcentagemRadio.checked) return value.toFixed(1) + '%';
            return variavelAnalisada === 'populacao' 
                ? value.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + 'M'
                : value.toLocaleString('pt-BR');
        };

        // Arrumando posição do datalabel para gráficos empilhados
        populacaoQuintilChart.options.plugins.datalabels.align = variavelAnalisada === 'populacao' ? 'top' : 'center';
        populacaoQuintilChart.options.plugins.datalabels.anchor = variavelAnalisada === 'populacao' ? 'end' : 'center';

        populacaoQuintilChart.update();

        // ==== Tabelas ====
        if (data.tableData24 && tableCard2025) {
            tableCard2025.classList.remove('d-none');
            renderTable(table2025Head, table2025Body, data.tableHeaders24, data.tableData24);
        } else if (tableCard2025) {
            tableCard2025.classList.add('d-none');
        }

        if (include2000Data && data.tableData00 && data.tableHeaders00 && tableCard2000) {
            tableCard2000.classList.remove('d-none');
            renderTable(table2000Head, table2000Body, data.tableHeaders00, data.tableData00);
        } else if (tableCard2000) {
            tableCard2000.classList.add('d-none');
        }

        enableSynchronizedHover('#table-2025', '#table-2000');

    } catch (error) {
        console.error('Erro ao atualizar filtros:', error);
        alert('Ocorreu um erro ao carregar os dados do dashboard. Por favor, tente novamente.');
    }
}

// ==== Eventos e inicialização ====
/**
 * Reconstrói o select de notas CAPAG conforme o tipo escolhido:
 * a nota geral chega até D, enquanto os indicadores vão de A a C.
 */
function atualizarOpcoesNotaCapag() {
    const tipo = document.getElementById('capagTipoSelect');
    const nota = document.getElementById('capagNotaSelect');
    if (!tipo || !nota) return;

    const outros = tipo.value === 'geral' ? 'D e outros' : 'n.d. ou n.e.';
    const selecaoAnterior = nota.value;

    nota.innerHTML = `
        <option value="todos">Todas as Notas</option>
        <option value="A">A</option>
        <option value="B">B</option>
        <option value="C">C</option>
        <option value="${outros}">${outros}</option>
    `;

    // Mantém a nota selecionada quando ela ainda existir na nova lista
    const aindaExiste = Array.from(nota.options).some(opt => opt.value === selecaoAnterior);
    nota.value = aindaExiste ? selecaoAnterior : 'todos';
}

document.addEventListener('DOMContentLoaded', () => {
    filtroRegiao = document.getElementById('filtro-regiao');
    filtroUf = document.getElementById('filtro-uf');
    filtroRm = document.getElementById('filtro-rm');
    filtroConsorcio = document.getElementById('filtro-consorcio');
    filtroPorte = document.getElementById('filtro-porte');
    btnLimpar = document.getElementById('btn-limpar-filtros');

    quantilQuintilRadio = document.getElementById('quantilQuintil');
    quantilDecilRadio = document.getElementById('quantilDecil');

    formatNumeroRadio = document.getElementById('formatNumero');
    formatPorcentagemRadio = document.getElementById('formatPorcentagem');

    calcModeTotalRadio = document.getElementById('calcModeTotal');
    calcModeFilteredRadio = document.getElementById('calcModeFiltered');

    toggle2025 = document.querySelector('.toggle-option[data-option="2025"]');
    toggle2000e2025 = document.querySelector('.toggle-option[data-option="2000 e 2025"]');

    tableCard2025 = document.getElementById('table-card-2025');
    table2025Head = document.querySelector('#table-2025 thead');
    table2025Body = document.querySelector('#table-2025 tbody');

    tableCard2000 = document.getElementById('table-card-2000');
    table2000Head = document.querySelector('#table-2000 thead');
    table2000Body = document.querySelector('#table-2000 tbody');

    populacaoQuintilCtx = document.getElementById('populacaoQuintilChart').getContext('2d');

    // Inicialização da instância base do Chart.js
    populacaoQuintilChart = new Chart(populacaoQuintilCtx, {
        type: 'bar',
        data: { labels: [], datasets: [] },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { 
                    display: true, 
                    position: 'top',
                    labels: {
                        usePointStyle: false, 
                        boxWidth: 40,
                        padding: 20,
                        generateLabels: function(chart) {
                            const original = Chart.defaults.plugins.legend.labels.generateLabels(chart);
                            const varSelect = document.getElementById('variavelAnalisadaSelect');
                            const currentVar = varSelect ? varSelect.value : 'populacao';

                            original.forEach(label => {
                                label.strokeStyle = '#000000';
                                label.lineWidth = 1;

                                const dsBackgroundColor = chart.data.datasets[label.datasetIndex]?.backgroundColor;
                                const baseColor = Array.isArray(dsBackgroundColor) ? dsBackgroundColor[0] : dsBackgroundColor;

                                const finalColor = (currentVar === 'populacao') ? '#000000' : (baseColor || '#000000');

                                if (label.text.includes('2000')) {
                                    const patternCanvas = document.createElement('canvas');
                                    patternCanvas.width = 10;
                                    patternCanvas.height = 10;
                                    const ctx = patternCanvas.getContext('2d');
                                    ctx.fillStyle = finalColor;
                                    ctx.fillRect(0, 0, 10, 10);
                                    ctx.strokeStyle = '#ffffff';
                                    ctx.lineWidth = 2;
                                    ctx.beginPath();
                                    ctx.moveTo(0, 10);
                                    ctx.lineTo(10, 0);
                                    ctx.stroke();
                                    const pattern = chart.ctx.createPattern(patternCanvas, 'repeat');
                                    label.fillStyle = pattern;
                                } else {
                                    label.fillStyle = finalColor; 
                                }
                            });

                            // Nos indicadores da CAPAG os datasets chegam invertidos (a melhor nota
                            // é empilhada por último, no topo); a legenda segue a leitura visual do
                            // topo para a base: A, B, C e n.d. ou n.e.
                            const capagTipo = document.getElementById('capagTipoSelect');
                            const ehIndicador = currentVar === 'capag' && capagTipo && capagTipo.value !== 'geral';
                            return ehIndicador ? original.reverse() : original;
                        }
                    }
                },
                datalabels: {
                    anchor: 'end',
                    align: 'top',
                    color: '#000000',
                    font: { size: 12, weight: 'bold' },
                    formatter: function (value) {
                        const isPercentage = document.getElementById('formatPorcentagem').checked;
                        return isPercentage
                            ? value.toFixed(1) + '%'
                            : value.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + 'M';
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            // Usa tooltipLabel (com ano) se disponível, senão usa label normal
                            const fullLabel = context.dataset.tooltipLabel || context.dataset.label;
                            const value = context.formattedValue;
                            return `${fullLabel}: ${value}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'População (milhões)' },
                    ticks: {
                        callback: function (value) {
                            return document.getElementById('formatPorcentagem').checked
                                ? value.toFixed(0) + '%'
                                : value.toLocaleString('pt-BR') + 'M';
                        }
                    }
                },
                x: {
                    title: { display: false, text: '' },
                    categoryPercentage: 0.6, 
                    barPercentage: 0.8,      
                    ticks: {
                        color: '#333', 
                        font: { size: 12, weight: 'bold' } 
                    }
                }
            }
        },
        plugins: [ChartDataLabels]
    });

    // Orquestrador de eventos para garantir a cascata na Home
    async function handleHomeFilterChange() {
        await updateDependentFilters(false);
    }

    // Apenas os selects estruturais disparam a cascata inteira
    [filtroRegiao, filtroUf, filtroRm, filtroConsorcio, filtroPorte].forEach(select => {
        if (select) select.addEventListener('change', handleHomeFilterChange);
    });

    // Filtros visuais/cálculo afetam apenas os dados (não a estrutura dos selects)
    [quantilQuintilRadio, quantilDecilRadio, formatNumeroRadio, formatPorcentagemRadio, calcModeTotalRadio, calcModeFilteredRadio].forEach(radio => {
        if (radio) radio.addEventListener('change', atualizarFiltros);
    });

    const variavelAnalisadaSelect = document.getElementById('variavelAnalisadaSelect');

    if (variavelAnalisadaSelect) {
        variavelAnalisadaSelect.addEventListener('change', (e) => {
            if (e.target.value !== 'populacao') {
                if (toggle2000e2025) {
                    toggle2000e2025.classList.add('d-none');
                }
                if (toggle2025) {
                    document.querySelectorAll('.toggle-option').forEach(opt => opt.classList.remove('active'));
                    toggle2025.classList.add('active');
                }
            } else {
                if (toggle2000e2025) {
                    toggle2000e2025.classList.remove('d-none');
                }
            }

            // Cada modo exibe apenas o seu próprio par de filtros (tipo + nota/nível)
            const mostraCapag = e.target.value === 'capag';
            const mostraRisco = e.target.value === 'risco_climatico';

            const ct = document.getElementById('capagTipoSelect');
            const cn = document.getElementById('capagNotaSelect');
            const rt = document.getElementById('riscoTipoSelect');
            const rn = document.getElementById('riscoNivelSelect');

            if (ct) { ct.classList.toggle('d-none', !mostraCapag); if (!mostraCapag) ct.value = 'geral'; }
            if (cn) { cn.classList.toggle('d-none', !mostraCapag); if (!mostraCapag) cn.value = 'todos'; }
            if (rt) { rt.classList.toggle('d-none', !mostraRisco); if (!mostraRisco) rt.value = 'media_ponderada'; }
            if (rn) { rn.classList.toggle('d-none', !mostraRisco); if (!mostraRisco) rn.value = 'todos'; }

            if (mostraCapag) atualizarOpcoesNotaCapag();

            const chartTooltip = document.getElementById('chart-info-tooltip');
            if (chartTooltip) {
                let tooltipText = "O gráfico apresenta a quantidade de pessoas que vivem nos municípios de cada quintil, para o ano de 2025 ou na comparação entre 2000 e 2025. <br>O primeiro quintil inclui os municípios com menor receita per capita, e o total de população nesse grupo mostra quantas pessoas vivem nessas áreas. <br>A lógica se repete nos demais quintis, até o último quintil, que representa os municípios com maior receita per capita.<br> Como cada grupo contém o mesmo número de municípios, se um quintil tiver mais habitantes, isso indica que seus municípios são mais populosos, em média, do que os de outros grupos.";
                if (e.target.value === 'capag') {
                    tooltipText = "O gráfico apresenta a quantidade de municípios em cada categoria de nota CAPAG, distribuídos por quintil de receita per capita. <br>O primeiro quintil inclui os municípios com menor receita per capita, enquanto o último representa aqueles com maior receita. <br>Isso permite visualizar se as melhores notas de Capacidade de Pagamento estão concentradas nos municípios mais ricos ou se distribuem de forma uniforme.";
                } else if (e.target.value === 'risco_climatico') {
                    tooltipText = "O gráfico apresenta a quantidade de municípios em cada nível de Risco Climático, distribuídos por quintil de receita per capita. <br>O primeiro quintil inclui os municípios com menor receita per capita, enquanto o último agrupa os de maior receita. <br>Isso permite observar como os municípios mais vulneráveis a eventos climáticos estão distribuídos em relação à sua capacidade de arrecadação.";
                }
                chartTooltip.setAttribute('data-bs-original-title', tooltipText);
                const bsTooltip = bootstrap.Tooltip.getInstance(chartTooltip);
                if (bsTooltip) {
                    bsTooltip.setContent({ '.tooltip-inner': tooltipText });
                }
            }

            atualizarFiltros();
        });
    }

    // Listeners para os dois filtros de nota CAPAG
    const capagTipoSelectEl = document.getElementById('capagTipoSelect');
    const capagNotaSelectEl = document.getElementById('capagNotaSelect');
    if (capagTipoSelectEl) {
        capagTipoSelectEl.addEventListener('change', () => {
            atualizarOpcoesNotaCapag();
            atualizarFiltros();
        });
    }
    if (capagNotaSelectEl) capagNotaSelectEl.addEventListener('change', atualizarFiltros);

    // Listeners para os dois novos filtros de risco climático
    const riscoTipoSelectEl = document.getElementById('riscoTipoSelect');
    const riscoNivelSelectEl = document.getElementById('riscoNivelSelect');
    if (riscoTipoSelectEl) riscoTipoSelectEl.addEventListener('change', atualizarFiltros);
    if (riscoNivelSelectEl) riscoNivelSelectEl.addEventListener('change', atualizarFiltros);

    if (toggle2025) {
        toggle2025.addEventListener('click', () => {
            document.querySelectorAll('.toggle-option').forEach(opt => opt.classList.remove('active'));
            toggle2025.classList.add('active');
            atualizarFiltros();
        });
    }

    if (toggle2000e2025) {
        toggle2000e2025.addEventListener('click', () => {
            document.querySelectorAll('.toggle-option').forEach(opt => opt.classList.remove('active'));
            toggle2000e2025.classList.add('active');
            atualizarFiltros();
        });
    }

    if (btnLimpar) {
        btnLimpar.addEventListener('click', () => {
            if (filtroRegiao) filtroRegiao.value = 'todos';
            if (filtroUf) filtroUf.value = 'todos';
            if (filtroRm) filtroRm.value = 'todos';
            if (filtroConsorcio) filtroConsorcio.value = 'todos';
            if (filtroPorte) filtroPorte.value = 'todos';

            if (quantilQuintilRadio) quantilQuintilRadio.checked = true;
            if (formatNumeroRadio) formatNumeroRadio.checked = true;
            if (calcModeTotalRadio) calcModeTotalRadio.checked = true;
            
            if (variavelAnalisadaSelect) variavelAnalisadaSelect.value = 'populacao';
            if (toggle2000e2025) {
                toggle2000e2025.classList.remove('d-none');
            }

            // Reseta os filtros extras de CAPAG e de risco climático
            const ctEl = document.getElementById('capagTipoSelect');
            const cnEl = document.getElementById('capagNotaSelect');
            const rtEl = document.getElementById('riscoTipoSelect');
            const rnEl = document.getElementById('riscoNivelSelect');
            if (ctEl) { ctEl.classList.add('d-none'); ctEl.value = 'geral'; }
            if (cnEl) { cnEl.classList.add('d-none'); cnEl.value = 'todos'; }
            if (rtEl) { rtEl.classList.add('d-none'); rtEl.value = 'media_ponderada'; }
            if (rnEl) { rnEl.classList.add('d-none'); rnEl.value = 'todos'; }
            atualizarOpcoesNotaCapag();

            document.querySelectorAll('.toggle-option').forEach(opt => opt.classList.remove('active'));
            if (toggle2025) toggle2025.classList.add('active');

            updateDependentFilters(true).then(atualizarFiltros);
        });
    }

    // Chamada inicial
    updateDependentFilters(true).then(atualizarFiltros);
});

// Hover sincronizado entre tabelas 2025 e 2000
function enableSynchronizedHover(tableId1, tableId2) {
    const table1 = document.querySelector(tableId1); // 2025
    const table2 = document.querySelector(tableId2); // 2000
    if (!table1 || !table2) return;

    const tables = [table1, table2];
    tables.forEach((table, tableIndex) => {
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach((row, rowIndex) => {
            const cells = row.querySelectorAll('td');
            cells.forEach((cell, colIndex) => {
                cell.addEventListener('mouseenter', () => {
                    const otherTable = tables[tableIndex === 0 ? 1 : 0];
                    const otherRow = otherTable.querySelectorAll('tbody tr')[rowIndex];
                    if (!otherRow) return;
                    const otherCell = otherRow.querySelectorAll('td')[colIndex];
                    if (!otherCell) return;

                    if (tableIndex === 0) {
                        otherCell.classList.add('highlight2');
                        cell.classList.add('highlight');
                    } else {
                        otherCell.classList.add('highlight');
                        cell.classList.add('highlight2');
                    }
                });
                cell.addEventListener('mouseleave', () => {
                    const otherTable = tables[tableIndex === 0 ? 1 : 0];
                    const otherRow = otherTable.querySelectorAll('tbody tr')[rowIndex];
                    if (!otherRow) return;
                    const otherCell = otherRow.querySelectorAll('td')[colIndex];
                    if (!otherCell) return;

                    if (tableIndex === 0) {
                        otherCell.classList.remove('highlight2');
                        cell.classList.remove('highlight');
                    } else {
                        otherCell.classList.remove('highlight');
                        cell.classList.remove('highlight2');
                    }
                });
            });
        });
    });
}