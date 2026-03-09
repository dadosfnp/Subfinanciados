// >>> HOME filters: lista em cascata e atualização de dados <<<

// Variáveis globais para elementos DOM e instância do gráfico
let filtroRegiao;
let filtroUf;
let filtroRm;
let filtroPorte;
let btnLimpar;

let quantilQuintilRadio;
let quantilDecilRadio;

let formatNumeroRadio;
let formatPorcentagemRadio;

let calcModeTotalRadio;
let calcModeFilteredRadio;

let toggle2024;
let toggle2000e2024;

let populacaoQuintilCtx;
let populacaoQuintilChart;

// Variáveis das tabelas
let tableCard2024;
let table2024Head;
let table2024Body;

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
    const selectedPorte = filtroPorte ? filtroPorte.value : 'todos';

    const classificationFilter = quantilDecilRadio?.checked ? 'decil' : 'quintil';
    const displayFormat = formatPorcentagemRadio?.checked ? 'porcentagem' : 'numero';
    const calculationMode = calcModeFilteredRadio.checked ? 'por_filtro' : 'total';

    const selectedYearOptionElement = document.querySelector('.toggle-option.active');
    const selectedYearOption = selectedYearOptionElement ? selectedYearOptionElement.dataset.option : '2024';
    const include2000Data = (selectedYearOption === '2000 e 2024');

    const apiUrl =
        `/api/dashboard-data/?regiao=${selectedRegiao}` +
        `&uf=${selectedUf}` +
        `&rm=${selectedRm}` +
        `&porte=${selectedPorte}` +
        `&classification=${classificationFilter}` +
        `&display_format=${displayFormat}` +
        `&calculation_mode=${calculationMode}` +
        `&include_2000_data=${include2000Data}`;

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

        // ==== Gráfico ====
        populacaoQuintilChart.data.labels = data.chartData.labels;
        populacaoQuintilChart.data.datasets = [];

        // =====================================================
        // PALETA E RENDERIZAÇÃO DE DADOS NO GRÁFICO
        // =====================================================
        const QUINTIL_PALETTE = [
            '#A33242', // 1º Quintil
            '#D97636', // 2º Quintil
            '#E8C83E', // 3º Quintil
            '#72BA6A', // 4º Quintil
            '#2D8A4E'  // 5º Quintil
        ];

        const getColors = (count) => {
            if (count <= 5) return QUINTIL_PALETTE;
            return QUINTIL_PALETTE.concat(QUINTIL_PALETTE); 
        };

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

            if (data.chartData.datasets.length === 2) {
                data.chartData.datasets.sort((a, b) => {
                    if (a.label.includes('2000')) return -1;
                    if (b.label.includes('2000')) return 1;
                    return 0;
                });
            }

            data.chartData.datasets.forEach((dataset) => {
                const barColors = getColors(dataset.data.length);
                const is2024 = dataset.label.toString().includes('2024');

                const backgroundColors = barColors.map(color => 
                    is2024 ? color : createDiagonalPattern(color) 
                );

                populacaoQuintilChart.data.datasets.push({
                    label: dataset.label,
                    data: dataset.data,
                    backgroundColor: backgroundColors,
                    borderColor: barColors, 
                    borderWidth: 2,
                    fill: true,
                    barPercentage: 0.6,      
                    categoryPercentage: 0.6, 
                    grouped: true
                });
            });

        } else {
            console.warn('A API não retornou dados para o gráfico.');
        }

        populacaoQuintilChart.options.scales.y.title.text = data.chartData.yAxisTitle;
        populacaoQuintilChart.options.scales.y.ticks.callback = function (value) {
            return formatPorcentagemRadio.checked
                ? value.toFixed(0) + '%'
                : value.toLocaleString('pt-BR') + 'M';
        };

        populacaoQuintilChart.update();

        // ==== Tabelas ====
        if (data.tableData24 && tableCard2024) {
            tableCard2024.classList.remove('d-none');
            renderTable(table2024Head, table2024Body, data.tableHeaders24, data.tableData24);
        } else if (tableCard2024) {
            tableCard2024.classList.add('d-none');
        }

        if (include2000Data && data.tableData00 && data.tableHeaders00 && tableCard2000) {
            tableCard2000.classList.remove('d-none');
            renderTable(table2000Head, table2000Body, data.tableHeaders00, data.tableData00);
        } else if (tableCard2000) {
            tableCard2000.classList.add('d-none');
        }

        enableSynchronizedHover('#table-2024', '#table-2000');

    } catch (error) {
        console.error('Erro ao atualizar filtros:', error);
        alert('Ocorreu um erro ao carregar os dados do dashboard. Por favor, tente novamente.');
    }
}

// ==== Eventos e inicialização ====
document.addEventListener('DOMContentLoaded', () => {
    filtroRegiao = document.getElementById('filtro-regiao');
    filtroUf = document.getElementById('filtro-uf');
    filtroRm = document.getElementById('filtro-rm');
    filtroPorte = document.getElementById('filtro-porte');
    btnLimpar = document.getElementById('btn-limpar-filtros');

    quantilQuintilRadio = document.getElementById('quantilQuintil');
    quantilDecilRadio = document.getElementById('quantilDecil');

    formatNumeroRadio = document.getElementById('formatNumero');
    formatPorcentagemRadio = document.getElementById('formatPorcentagem');

    calcModeTotalRadio = document.getElementById('calcModeTotal');
    calcModeFilteredRadio = document.getElementById('calcModeFiltered');

    toggle2024 = document.querySelector('.toggle-option[data-option="2024"]');
    toggle2000e2024 = document.querySelector('.toggle-option[data-option="2000 e 2024"]');

    tableCard2024 = document.getElementById('table-card-2024');
    table2024Head = document.querySelector('#table-2024 thead');
    table2024Body = document.querySelector('#table-2024 tbody');

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
                            original.forEach(label => {
                                label.strokeStyle = '#000000';
                                label.lineWidth = 1;

                                if (label.text.includes('2000')) {
                                    const patternCanvas = document.createElement('canvas');
                                    patternCanvas.width = 10;
                                    patternCanvas.height = 10;
                                    const ctx = patternCanvas.getContext('2d');
                                    ctx.fillStyle = '#000000';
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
                                    label.fillStyle = '#000000'; 
                                }
                            });
                            return original;
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
    [filtroRegiao, filtroUf, filtroRm, filtroPorte].forEach(select => {
        if (select) select.addEventListener('change', handleHomeFilterChange);
    });

    // Filtros visuais/cálculo afetam apenas os dados (não a estrutura dos selects)
    [quantilQuintilRadio, quantilDecilRadio, formatNumeroRadio, formatPorcentagemRadio, calcModeTotalRadio, calcModeFilteredRadio].forEach(radio => {
        if (radio) radio.addEventListener('change', atualizarFiltros);
    });

    if (toggle2024) {
        toggle2024.addEventListener('click', () => {
            document.querySelectorAll('.toggle-option').forEach(opt => opt.classList.remove('active'));
            toggle2024.classList.add('active');
            atualizarFiltros();
        });
    }

    if (toggle2000e2024) {
        toggle2000e2024.addEventListener('click', () => {
            document.querySelectorAll('.toggle-option').forEach(opt => opt.classList.remove('active'));
            toggle2000e2024.classList.add('active');
            atualizarFiltros();
        });
    }

    if (btnLimpar) {
        btnLimpar.addEventListener('click', () => {
            if (filtroRegiao) filtroRegiao.value = 'todos';
            if (filtroUf) filtroUf.value = 'todos';
            if (filtroRm) filtroRm.value = 'todos';
            if (filtroPorte) filtroPorte.value = 'todos';

            if (quantilQuintilRadio) quantilQuintilRadio.checked = true;
            if (formatNumeroRadio) formatNumeroRadio.checked = true;
            if (calcModeTotalRadio) calcModeTotalRadio.checked = true;

            document.querySelectorAll('.toggle-option').forEach(opt => opt.classList.remove('active'));
            if (toggle2024) toggle2024.classList.add('active');

            updateDependentFilters(true).then(atualizarFiltros);
        });
    }

    // Chamada inicial
    updateDependentFilters(true).then(atualizarFiltros);
});

// Hover sincronizado entre tabelas 2024 e 2000
function enableSynchronizedHover(tableId1, tableId2) {
    const table1 = document.querySelector(tableId1); // 2024
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