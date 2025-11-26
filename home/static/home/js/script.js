// >>> HOME filters: lista completa SEMPRE (espelhando o Mapa) <<<

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

let toggle2023;
let toggle2000e2023;

let populacaoQuintilCtx;
let populacaoQuintilChart;

// Variáveis das tabelas
let tableCard2023;
let table2023Head;
let table2023Body;

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
 * (Opcional) Lê JSON de uma <script type="application/json" id="...">
 */
function getJsonData(id) {
    const element = document.getElementById(id);
    if (element && element.textContent) {
        try { return JSON.parse(element.textContent); }
        catch (e) {
            console.error(`Erro ao processar JSON do elemento #${id}:`, e);
            return null;
        }
    }
    return null;
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
 * Atualiza os filtros SEM RESTRIÇÃO (lista completa da API, sem parâmetros).
 * Mantém o valor selecionado quando possível; caso contrário, define 'todos'.
 */
async function updateDependentFilters(initial = false) {
    const regiaoAtual = filtroRegiao.value;
    const ufAtual     = filtroUf.value;
    const rmAtual     = filtroRm.value;

    try {
        // Busca SEM parâmetros → servidor devolve listas completas
        const resp = await fetch('/api/get-dependent-filters/');
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();

        // Regiões (label "Todas")
        filtroRegiao.innerHTML = '<option value="todos">Todas</option>';
        (data.regioes || []).forEach(v => filtroRegiao.add(new Option(v, v)));
        restoreSelectValue(filtroRegiao, regiaoAtual);

        // RM (label "Todos")
        filtroRm.innerHTML = '<option value="todos">Todos</option>';
        (data.rms || []).forEach(v => filtroRm.add(new Option(v, v)));
        restoreSelectValue(filtroRm, rmAtual);

        // UF (label "Todas")
        filtroUf.innerHTML = '<option value="todos">Todas</option>';
        (data.ufs || []).forEach(v => filtroUf.add(new Option(v, v)));
        restoreSelectValue(filtroUf, ufAtual);

    } catch (error) {
        console.error('Erro ao atualizar filtros (listas completas):', error);
    }

    // Igual ao mapa: não repovoa a cada mudança; só atualiza dados
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
    const selectedYearOption = selectedYearOptionElement ? selectedYearOptionElement.dataset.option : '2023';
    const include2000Data = (selectedYearOption === '2000 e 2023');

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

        const diffNational = data.summaryCards.diffMediaNacional; // valor em %
        const diffValueEl = document.getElementById('summary-diff-nacional');
        diffValueEl.textContent = `${diffNational.toFixed(1)}%`;

        const diffTrendElement = document.getElementById('summary-diff-nacional-trend');
        diffTrendElement.textContent = diffNational > 0
            ? 'Acima da média nacional'
            : (diffNational < 0 ? 'Abaixo da média nacional' : 'Na média nacional');
        diffTrendElement.className =
            `sub-value ${diffNational < 0 ? 'negative' : ''} ${diffNational > 0 ? 'positive' : ''}`;

        // pinta o número conforme sinal
        applyDiffColor(diffNational);

        document.getElementById('summary-gini').textContent = data.summaryCards.giniIndex;

        // ==== Gráfico ====
        populacaoQuintilChart.data.labels = data.chartData.labels;
        populacaoQuintilChart.data.datasets = [];

        // Paleta fixa por ano: 2000 = amarelo, 2023 = azul
        const COLOR_2000 = '#efae17';
        const COLOR_2023 = '#194685';

        if (data.chartData.datasets?.length > 0) {

            // (Opcional) Garante que 2000 venha antes de 2023 na legenda
            if (data.chartData.datasets.length === 2) {
                data.chartData.datasets.sort((a, b) => {
                    if (a.label.includes('2000')) return -1;
                    if (b.label.includes('2000')) return 1;
                    return 0;
                });
            }

            // Insere datasets com cor DEFINIDA PELO LABEL, não pelo índice
            data.chartData.datasets.forEach((dataset) => {
                let bgColor = COLOR_2023; // padrão = azul (2023)

                if (dataset.label && dataset.label.toString().includes('2000')) {
                    bgColor = COLOR_2000; // se for 2000 -> amarelo
                }

                populacaoQuintilChart.data.datasets.push({
                    label: dataset.label,
                    data: dataset.data,
                    backgroundColor: dataset.data.map(() => bgColor),
                    borderColor: dataset.data.map(() => bgColor),
                    borderWidth: 1,
                    fill: true,
                    barPercentage: 1,
                    categoryPercentage: 1,
                    grouped: true,
                    barThickness: 50
                });
            });

        } else {
            console.warn('A API não retornou dados para o gráfico.');
        }

        populacaoQuintilChart.options.scales.x.title.text = data.chartData.xAxisTitle;
        populacaoQuintilChart.options.scales.y.title.text = data.chartData.yAxisTitle;

        populacaoQuintilChart.options.scales.y.ticks.callback = function (value) {
            return formatPorcentagemRadio.checked
                ? value.toFixed(0) + '%'
                : value.toLocaleString('pt-BR') + 'M';
        };

        populacaoQuintilChart.update();

        // ==== Tabelas ====
        renderTable(table2023Head, table2023Body, data.tableHeaders23, data.tableData23);
        tableCard2023.classList.remove('d-none');

        if (include2000Data && data.tableData00 && data.tableHeaders00) {
            renderTable(table2000Head, table2000Body, data.tableHeaders00, data.tableData00);
            tableCard2000.classList.remove('d-none');
        } else {
            tableCard2000.classList.add('d-none');
        }

        // Hover sincronizado
        enableSynchronizedHover('#table-2023', '#table-2000');

    } catch (error) {
        console.error('Erro ao carregar dados do dashboard:', error);
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

    toggle2023 = document.querySelector('.toggle-option[data-option="2023"]');
    toggle2000e2023 = document.querySelector('.toggle-option[data-option="2000 e 2023"]');

    tableCard2023 = document.getElementById('table-card-2023');
    table2023Head = document.querySelector('#table-2023 thead');
    table2023Body = document.querySelector('#table-2023 tbody');

    tableCard2000 = document.getElementById('table-card-2000');
    table2000Head = document.querySelector('#table-2000 thead');
    table2000Body = document.querySelector('#table-2000 tbody');

    populacaoQuintilCtx = document
        .getElementById('populacaoQuintilChart')
        .getContext('2d');

    populacaoQuintilChart = new Chart(populacaoQuintilCtx, {
        type: 'bar',
        data: { labels: [], datasets: [] },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: true, position: 'top' },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            let label = context.dataset.label || '';
                            if (label) label += ': ';
                            if (context.parsed.y !== null) {
                                if (formatPorcentagemRadio.checked) {
                                    label += context.parsed.y.toFixed(1) + '%';
                                } else {
                                    label += context.parsed.y.toLocaleString('pt-BR') + ' milhões';
                                }
                            }
                            return label;
                        }
                    }
                },
                datalabels: {
                    anchor: 'end',
                    align: 'top',
                    color: '#000000',
                    font: { size: 12 },
                    formatter: function (value) {
                        const isPercentage =
                            document.getElementById('formatPorcentagem').checked;
                        return isPercentage
                            ? value.toFixed(1) + '%'
                            : value.toLocaleString(
                                  'pt-BR',
                                  { minimumFractionDigits: 1, maximumFractionDigits: 1 }
                              ) + 'M';
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'População (milhões)' },
                    ticks: {
                        callback: function (value) {
                            return formatPorcentagemRadio.checked
                                ? value.toFixed(0) + '%'
                                : value.toLocaleString('pt-BR') + 'M';
                        }
                    }
                },
                x: {
                    title: { display: true, text: 'Quintil' }
                }
            }
        },
        plugins: [ChartDataLabels]
    });

    // Carrega listas completas e depois pinta a tela
    updateDependentFilters(true).then(atualizarFiltros);

    // Em cada mudança, NÃO repopular selects — só atualiza os dados
    filtroRegiao.addEventListener('change', atualizarFiltros);
    filtroUf.addEventListener('change', atualizarFiltros);
    filtroRm.addEventListener('change', atualizarFiltros);
    if (filtroPorte) filtroPorte.addEventListener('change', atualizarFiltros);

    quantilQuintilRadio.addEventListener('change', atualizarFiltros);
    quantilDecilRadio.addEventListener('change', atualizarFiltros);
    formatNumeroRadio.addEventListener('change', atualizarFiltros);
    formatPorcentagemRadio.addEventListener('change', atualizarFiltros);
    calcModeTotalRadio.addEventListener('change', atualizarFiltros);
    calcModeFilteredRadio.addEventListener('change', atualizarFiltros);

    toggle2023.addEventListener('click', () => {
        document.querySelectorAll('.toggle-option')
            .forEach(opt => opt.classList.remove('active'));
        toggle2023.classList.add('active');
        atualizarFiltros();
    });

    toggle2000e2023.addEventListener('click', () => {
        document.querySelectorAll('.toggle-option')
            .forEach(opt => opt.classList.remove('active'));
        toggle2000e2023.classList.add('active');
        atualizarFiltros();
    });

    btnLimpar.addEventListener('click', () => {
        filtroRegiao.value = 'todos';
        filtroUf.value = 'todos';
        filtroRm.value = 'todos';
        if (filtroPorte) filtroPorte.value = 'todos';

        quantilQuintilRadio.checked = true;
        formatNumeroRadio.checked = true;
        calcModeTotalRadio.checked = true;

        document.querySelectorAll('.toggle-option')
            .forEach(opt => opt.classList.remove('active'));
        toggle2023.classList.add('active');

        // Repovoa com listas completas e atualiza a tela
        updateDependentFilters(true).then(atualizarFiltros);
    });
});

// Hover sincronizado entre tabelas 2023 e 2000
function enableSynchronizedHover(tableId1, tableId2) {
    const table1 = document.querySelector(tableId1); // 2023
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
