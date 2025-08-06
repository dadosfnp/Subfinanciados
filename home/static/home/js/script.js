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

// Novas variáveis globais para elementos das tabelas
let tableCard2023;
let table2023Head;
let table2023Body;

let tableCard2000;
let table2000Head;
let table2000Body;

/**
 * Função auxiliar para obter e converter dados JSON de uma tag <script>.
 * Pressupõe que o HTML contenha uma tag <script type="application/json" id="seu-id">.
 */
function getJsonData(id) {
    const element = document.getElementById(id);
    if (element && element.textContent) {
        try {
            return JSON.parse(element.textContent);
        } catch (e) {
            console.error(`Erro ao processar JSON do elemento #${id}:`, e);
            return null;
        }
    }
    return null;
}

/**
 * Atualiza os filtros dependentes (UF, RM) com base na região, UF ou RM selecionada.
 * @param {string} trigger - Indica qual filtro acionou a atualização ('regiao', 'uf', 'rm').
 */
async function updateDependentFilters(trigger = null) {
    const regiaoAtual = filtroRegiao.value;
    const ufAtual = filtroUf.value;
    const rmAtual = filtroRm.value;

    const apiUrl = `/api/get-dependent-filters/?regiao=${regiaoAtual}&uf=${ufAtual}&rm=${rmAtual}`;

    try {
        const response = await fetch(apiUrl);
        if (!response.ok) throw new Error(`Erro HTTP! status: ${response.status}`);

        const data = await response.json();

        filtroRegiao.innerHTML = '<option value="todos">Todas</option>';
        data.regioes.forEach(item => filtroRegiao.add(new Option(item, item)));
        filtroRegiao.value = regiaoAtual;

        filtroRm.innerHTML = '<option value="todos">Todos</option>';
        data.rms.forEach(item => filtroRm.add(new Option(item, item)));
        if (trigger !== 'regiao' && trigger !== 'uf') filtroRm.value = rmAtual;

        filtroUf.innerHTML = '<option value="todos">Todas</option>';
        data.ufs.forEach(item => filtroUf.add(new Option(item, item)));
        if (trigger !== 'regiao') filtroUf.value = ufAtual;

    } catch (error) {
        console.error("Erro ao atualizar filtros dependentes:", error);
    }
}

/**
 * Renderiza uma tabela com base nos cabeçalhos e dados fornecidos.
 * @param {HTMLElement} tableHeadElement - Elemento <thead>.
 * @param {HTMLElement} tableBodyElement - Elemento <tbody>.
 * @param {Array<string>} headers - Lista de cabeçalhos.
 * @param {Array<Object>} data - Lista de objetos para as linhas.
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
 * Busca e atualiza os dados do dashboard (cards, gráfico e tabela dinâmica).
 */
async function atualizarFiltros() {
    const selectedRegiao = filtroRegiao.value;
    const selectedUf = filtroUf.value;
    const selectedRm = filtroRm.value;
    const selectedPorte = filtroPorte ? filtroPorte.value : 'todos';

    let classificationFilter = quantilDecilRadio?.checked ? 'decil' : 'quintil';
    let displayFormat = formatPorcentagemRadio?.checked ? 'porcentagem' : 'numero';
    let calculationMode = calcModeFilteredRadio.checked ? 'por_filtro' : 'total';

    const selectedYearOptionElement = document.querySelector('.toggle-option.active');
    const selectedYearOption = selectedYearOptionElement ? selectedYearOptionElement.dataset.option : '2023';
    const include2000Data = (selectedYearOption === '2000 e 2023');

    const apiUrl = `/api/dashboard-data/?regiao=${selectedRegiao}&uf=${selectedUf}&rm=${selectedRm}&porte=${selectedPorte}&classification=${classificationFilter}&display_format=${displayFormat}&calculation_mode=${calculationMode}&include_2000_data=${include2000Data}`;

    try {
        const response = await fetch(apiUrl);
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Erro HTTP! Status: ${response.status}, Mensagem: ${errorText}`);
        }
        const data = await response.json();

        // ==== Atualizar cards de resumo ====
        document.getElementById('summary-total-municipios').textContent =
            `${data.summaryCards.totalMunicipios.toLocaleString('pt-BR')} (${data.summaryCards.percTotalMunicipios.toFixed(1)}%)`;
        document.getElementById('summary-media-receita').textContent =
            data.summaryCards.mediaReceitaPerCapita.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

        const diffNational = data.summaryCards.diffMediaNacional;
        document.getElementById('summary-diff-nacional').textContent = `${diffNational.toFixed(1)}%`;
        const diffTrendElement = document.getElementById('summary-diff-nacional-trend');
        diffTrendElement.textContent = diffNational > 0 ? 'Acima da média nacional' :
            (diffNational < 0 ? 'Abaixo da média nacional' : 'Na média nacional');
        diffTrendElement.className = `sub-value ${diffNational < 0 ? 'negative' : ''} ${diffNational > 0 ? 'positive' : ''}`;

        document.getElementById('summary-gini').textContent = data.summaryCards.giniIndex;

        // ==== Atualizar gráfico ====
        populacaoQuintilChart.data.labels = data.chartData.labels;
        populacaoQuintilChart.data.datasets = [];

        // Usar cores da logo
        const colors = ['#194685', '#efae17'];

        if (data.chartData.datasets?.length > 0) {
            data.chartData.datasets.forEach((dataset, index) => {
                populacaoQuintilChart.data.datasets.push({
                    label: dataset.label,
                    data: dataset.data,
                    backgroundColor: dataset.data.map(() => colors[index % colors.length]),
                    borderColor: dataset.data.map(() => colors[index % colors.length]),
                    borderWidth: 1,
                    fill: true,
                    barPercentage: 1,
                    categoryPercentage: 1,
                    grouped: true,
                    barThickness: 50
                });
            });
        } else {
            console.warn("A API não retornou dados para o gráfico.");
        }

        populacaoQuintilChart.update();

        populacaoQuintilChart.options.scales.x.title.text = data.chartData.xAxisTitle;
        populacaoQuintilChart.options.scales.y.title.text = data.chartData.yAxisTitle;

        populacaoQuintilChart.options.scales.y.ticks.callback = function (value) {
            return formatPorcentagemRadio.checked ? value.toFixed(0) + '%' : value.toLocaleString('pt-BR') + 'M';
        };

        populacaoQuintilChart.update();

        // ==== Atualizar tabelas ====
        renderTable(table2023Head, table2023Body, data.tableHeaders23, data.tableData23);
        tableCard2023.classList.remove('d-none');

        if (include2000Data && data.tableData00 && data.tableHeaders00) {
            renderTable(table2000Head, table2000Body, data.tableHeaders00, data.tableData00);
            tableCard2000.classList.remove('d-none');
        } else {
            tableCard2000.classList.add('d-none');
        }

        // Ativar hover sincronizado agora que as tabelas existem
        enableSynchronizedHover('#table-2023', '#table-2000');

    } catch (error) {
        console.error("Erro ao carregar dados do dashboard:", error);
        alert("Ocorreu um erro ao carregar os dados do dashboard. Por favor, tente novamente.");
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

    populacaoQuintilCtx = document.getElementById('populacaoQuintilChart').getContext('2d');
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
                                if (formatPorcentagemRadio.checked) label += context.parsed.y.toFixed(1) + '%';
                                else label += context.parsed.y.toLocaleString('pt-BR') + ' milhões';
                            }
                            return label;
                        }
                    }
                },
                datalabels: { 
                    anchor: 'end',
                    align: 'top',
                    color: '#00000', // Cor do texto
                    font: {
                        weight: 'bold',
                        size: 12
                    },
                    formatter: function (value) {
                        return formatPorcentagemRadio.checked
                            ? value.toFixed(0) + '%'
                            : value.toLocaleString('pt-BR') + 'M';
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'População (milhões)' },
                    ticks: {
                        callback: function (value) {
                            return formatPorcentagemRadio.checked ? value.toFixed(0) + '%' : value.toLocaleString('pt-BR') + 'M';
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

    updateDependentFilters();
    atualizarFiltros();

    filtroRegiao.addEventListener('change', () => { updateDependentFilters('regiao'); atualizarFiltros(); });
    filtroUf.addEventListener('change', () => { updateDependentFilters('uf'); atualizarFiltros(); });
    filtroRm.addEventListener('change', () => { updateDependentFilters('rm'); atualizarFiltros(); });
    if (filtroPorte) filtroPorte.addEventListener('change', atualizarFiltros);

    quantilQuintilRadio.addEventListener('change', atualizarFiltros);
    quantilDecilRadio.addEventListener('change', atualizarFiltros);
    formatNumeroRadio.addEventListener('change', atualizarFiltros);
    formatPorcentagemRadio.addEventListener('change', atualizarFiltros);
    calcModeTotalRadio.addEventListener('change', atualizarFiltros);
    calcModeFilteredRadio.addEventListener('change', atualizarFiltros);

    toggle2023.addEventListener('click', () => {
        document.querySelectorAll('.toggle-option').forEach(opt => opt.classList.remove('active'));
        toggle2023.classList.add('active');
        atualizarFiltros();
    });

    toggle2000e2023.addEventListener('click', () => {
        document.querySelectorAll('.toggle-option').forEach(opt => opt.classList.remove('active'));
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

        document.querySelectorAll('.toggle-option').forEach(opt => opt.classList.remove('active'));
        toggle2023.classList.add('active');

        updateDependentFilters();
        atualizarFiltros();
    });
});

// Hover sincronizado entre tabelas 2023 e 2000
function enableSynchronizedHover(tableId1, tableId2) {
    const table1 = document.querySelector(tableId1);
    const table2 = document.querySelector(tableId2);

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
                    if (otherRow) {
                        const otherCell = otherRow.querySelectorAll('td')[colIndex];
                        if (otherCell) otherCell.classList.add('highlight');
                        cell.classList.add('highlight');
                    }
                });

                cell.addEventListener('mouseleave', () => {
                    const otherTable = tables[tableIndex === 0 ? 1 : 0];
                    const otherRow = otherTable.querySelectorAll('tbody tr')[rowIndex];
                    if (otherRow) {
                        const otherCell = otherRow.querySelectorAll('td')[colIndex];
                        if (otherCell) otherCell.classList.remove('highlight');
                        cell.classList.remove('highlight');
                    }
                });
            });
        });
    });
}
