// Global variables for DOM elements and Chart instance
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

// New global variables for table elements
let tableCard2023;
let table2023Head;
let table2023Body;

let tableCard2000;
let table2000Head;
let table2000Body;

/**
 * Helper function to retrieve and parse JSON data from a script tag.
 * Assumes the HTML contains a <script type="application/json" id="your-id"> tag.
 */
function getJsonData(id) {
    const element = document.getElementById(id);
    if (element && element.textContent) {
        try {
            return JSON.parse(element.textContent);
        } catch (e) {
            console.error(`Error parsing JSON from element #${id}:`, e);
            return null;
        }
    }
    return null;
}

/**
 * Updates the dependent filter dropdowns (UF, RM) based on selected region, UF, or RM.
 * @param {string} trigger - Indicates which filter triggered the update ('regiao', 'uf', 'rm').
 */
async function updateDependentFilters(trigger = null) {
    const regiaoAtual = filtroRegiao.value;
    const ufAtual = filtroUf.value;
    const rmAtual = filtroRm.value;

    const apiUrl = `/api/get-dependent-filters/?regiao=${regiaoAtual}&uf=${ufAtual}&rm=${rmAtual}`;

    try {
        const response = await fetch(apiUrl);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        filtroRegiao.innerHTML = '<option value="todos">Todas</option>';
        data.regioes.forEach(item => filtroRegiao.add(new Option(item, item)));
        filtroRegiao.value = regiaoAtual;

        filtroRm.innerHTML = '<option value="todos">Todos</option>';
        data.rms.forEach(item => filtroRm.add(new Option(item, item)));
        if (trigger !== 'regiao' && trigger !== 'uf') {
            filtroRm.value = rmAtual;
        }

        filtroUf.innerHTML = '<option value="todos">Todas</option>';
        data.ufs.forEach(item => filtroUf.add(new Option(item, item)));
        if (trigger !== 'regiao') {
            filtroUf.value = ufAtual;
        }

    } catch (error) {
        console.error("Error updating dependent filters:", error);
    }
}

/**
 * Renders a table with given headers and data into specified tbody and thead elements.
 * @param {HTMLElement} tableHeadElement - The <thead> element.
 * @param {HTMLElement} tableBodyElement - The <tbody> element.
 * @param {Array<string>} headers - Array of header strings.
 * @param {Array<Object>} data - Array of row objects.
 */
function renderTable(tableHeadElement, tableBodyElement, headers, data) {
    tableHeadElement.innerHTML = '';
    tableBodyElement.innerHTML = '';

    const headerRow = tableHeadElement.insertRow();
    headers.forEach(headerText => {
        const th = document.createElement('th');
        th.textContent = headerText;
        if (headerText === 'Faixas' || headerText === 'Total') {
            th.style.fontWeight = 'bold';
        }
        headerRow.appendChild(th);
    });

    data.forEach(rowData => {
        const row = tableBodyElement.insertRow();
        headers.forEach(headerKey => {
            const cell = row.insertCell();
            const cellValue = rowData[headerKey];
            cell.textContent = cellValue;
            if (headerKey === 'Faixas' || headerKey === 'Total') {
                cell.style.fontWeight = 'bold';
            }
        });
    });
}

/**
 * Fetches and updates dashboard data, including summary cards, chart, and dynamic table.
 */
async function atualizarFiltros() {
    const selectedRegiao = filtroRegiao.value;
    const selectedUf = filtroUf.value;
    const selectedRm = filtroRm.value;
    const selectedPorte = filtroPorte ? filtroPorte.value : 'todos';

    let classificationFilter = 'quintil';
    if (quantilDecilRadio && quantilDecilRadio.checked) {
        classificationFilter = 'decil';
    }

    let displayFormat = 'numero';
    if (formatPorcentagemRadio && formatPorcentagemRadio.checked) {
        displayFormat = 'porcentagem';
    }

    let calculationMode = calcModeFilteredRadio.checked ? 'por_filtro' : 'total';

    const selectedYearOptionElement = document.querySelector('.toggle-option.active');
    const selectedYearOption = selectedYearOptionElement ? selectedYearOptionElement.dataset.option : '2023';
    const include2000Data = (selectedYearOption === '2000 e 2023');

    const apiUrl = `/api/dashboard-data/?regiao=${selectedRegiao}&uf=${selectedUf}&rm=${selectedRm}&porte=${selectedPorte}&classification=${classificationFilter}&display_format=${displayFormat}&calculation_mode=${calculationMode}&include_2000_data=${include2000Data}`;

    try {
        const response = await fetch(apiUrl);
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP error! Status: ${response.status}, Message: ${errorText}`);
        }
        const data = await response.json();

        // ==============================================================================
        // LÓGICA PARA ATUALIZAR SUMMARY CARDS
        // ==============================================================================
        document.getElementById('summary-total-municipios').textContent =
            `${data.summaryCards.totalMunicipios.toLocaleString('pt-BR')} (${data.summaryCards.percTotalMunicipios.toFixed(1)}%)`;
        document.getElementById('summary-media-receita').textContent =
            data.summaryCards.mediaReceitaPerCapita.toLocaleString('pt-BR', {
                style: 'currency',
                currency: 'BRL'
            });

        const diffNational = data.summaryCards.diffMediaNacional;
        document.getElementById('summary-diff-nacional').textContent = `${diffNational.toFixed(1)}%`;
        const diffTrendElement = document.getElementById('summary-diff-nacional-trend');
        diffTrendElement.textContent = diffNational > 0 ? 'Acima da média nacional' : (diffNational < 0 ? 'Abaixo da média nacional' : 'Na média nacional');
        diffTrendElement.className = `sub-value ${diffNational < 0 ? 'negative' : ''} ${diffNational > 0 ? 'positive' : ''}`;

        document.getElementById('summary-gini').textContent = data.summaryCards.giniIndex;


        // ==============================================================================
        // LÓGICA PARA ATUALIZAR GRÁFICO
        // ==============================================================================
        populacaoQuintilChart.data.labels = data.chartData.labels;
        populacaoQuintilChart.data.datasets = [];

        const colors = ['#3498db', '#2ecc71'];

        if (data.chartData.datasets && data.chartData.datasets.length > 0) {
            data.chartData.datasets.forEach((dataset, index) => {
                populacaoQuintilChart.data.datasets.push({
                    label: dataset.label,
                    data: dataset.data,
                    backgroundColor: colors[index % colors.length],
                    borderColor: colors[index % colors.length],
                    borderWidth: 1,
                    barPercentage: 0.8,
                    categoryPercentage: 0.8
                });
            });
        } else {
            console.warn("API returned no data for the chart.");
        }

        populacaoQuintilChart.options.scales.x.title.text = data.chartData.xAxisTitle;
        populacaoQuintilChart.options.scales.y.title.text = data.chartData.yAxisTitle;

        populacaoQuintilChart.options.scales.y.ticks.callback = function(value, index, ticks) {
            if (formatPorcentagemRadio.checked) {
                return value.toFixed(0) + '%';
            } else {
                return value.toLocaleString('pt-BR') + 'M';
            }
        };

        populacaoQuintilChart.update();


        // ==============================================================================
        // LÓGICA PARA ATUALIZAR TABELAS
        // ==============================================================================

        // Always render 2023 table
        renderTable(table2023Head, table2023Body, data.tableHeaders23, data.tableData23);
        tableCard2023.classList.remove('d-none'); // Ensure 2023 table is visible

        // Handle 2000 table visibility and content
        if (include2000Data && data.tableData00 && data.tableHeaders00) {
            renderTable(table2000Head, table2000Body, data.tableHeaders00, data.tableData00);
            tableCard2000.classList.remove('d-none'); // Show 2000 table
        } else {
            tableCard2000.classList.add('d-none'); // Hide 2000 table
        }

    } catch (error) {
        console.error("Error loading dashboard data:", error);
        alert("Ocorreu um erro ao carregar os dados do dashboard. Por favor, tente novamente.");
    }
}

// Event Listeners and Initial Calls
document.addEventListener('DOMContentLoaded', () => {
    // 1. Get references to DOM elements and assign them to the GLOBAL variables.
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

    // Get references for table elements
    tableCard2023 = document.getElementById('table-card-2023');
    table2023Head = document.querySelector('#table-2023 thead');
    table2023Body = document.querySelector('#table-2023 tbody');

    tableCard2000 = document.getElementById('table-card-2000');
    table2000Head = document.querySelector('#table-2000 thead');
    table2000Body = document.querySelector('#table-2000 tbody');

    // 2. Initialize Chart.js once
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
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) label += ': ';
                            if (context.parsed.y !== null) {
                                if (formatPorcentagemRadio.checked) label += context.parsed.y.toFixed(1) + '%';
                                else label += context.parsed.y.toLocaleString('pt-BR') + ' milhões';
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'População (milhões)' },
                    ticks: {
                        callback: function(value, index, ticks) {
                            if (formatPorcentagemRadio.checked) return value.toFixed(0) + '%';
                            else return value.toLocaleString('pt-BR') + 'M';
                        }
                    }
                },
                x: {
                    title: { display: true, text: 'Quintil' }
                }
            }
        }
    });

    // 3. Initial calls to populate filters and dashboard data
    updateDependentFilters();

    const initialFiltersData = getJsonData('initial-filters-data');
    const currentFilters = getJsonData('current-filters-json');

    if (currentFilters) {
        if (currentFilters.regiao) filtroRegiao.value = currentFilters.regiao;
        if (currentFilters.uf) filtroUf.value = currentFilters.uf;
        if (currentFilters.rm) filtroRm.value = currentFilters.rm;
        if (filtroPorte && currentFilters.porte) filtroPorte.value = currentFilters.porte;

        if (currentFilters.classification === 'decil' && quantilDecilRadio) quantilDecilRadio.checked = true;
        else if (quantilQuintilRadio) quantilQuintilRadio.checked = true;

        if (currentFilters.display_format === 'porcentagem' && formatPorcentagemRadio) formatPorcentagemRadio.checked = true;
        else if (formatNumeroRadio) formatNumeroRadio.checked = true;

        if (currentFilters.calculation_mode === 'por_filtro' && calcModeFilteredRadio) calcModeFilteredRadio.checked = true;
        else if (calcModeTotalRadio) calcModeTotalRadio.checked = true;
        
        if (currentFilters.include_2000_data === 'true' && toggle2000e2023) {
            toggle2000e2023.classList.add('active');
            toggle2023.classList.remove('active');
        } else {
            toggle2023.classList.add('active');
            toggle2000e2023.classList.remove('active');
        }
    }

    atualizarFiltros();

    // 4. Event Listeners for filter changes
    filtroRegiao.addEventListener('change', () => { updateDependentFilters('regiao'); atualizarFiltros(); });
    filtroUf.addEventListener('change', () => { updateDependentFilters('uf'); atualizarFiltros(); });
    filtroRm.addEventListener('change', () => { updateDependentFilters('rm'); atualizarFiltros(); });
    if (filtroPorte) {
        filtroPorte.addEventListener('change', atualizarFiltros);
    }

    // 5. Event Listeners for radio buttons
    quantilQuintilRadio.addEventListener('change', atualizarFiltros);
    quantilDecilRadio.addEventListener('change', atualizarFiltros);
    formatNumeroRadio.addEventListener('change', atualizarFiltros);
    formatPorcentagemRadio.addEventListener('change', atualizarFiltros);
    calcModeTotalRadio.addEventListener('change', atualizarFiltros);
    calcModeFilteredRadio.addEventListener('change', atualizarFiltros);

    // 6. Event Listeners for year toggles
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

    // 7. Event Listener for "Clear Filters" button
    btnLimpar.addEventListener('click', () => {
        filtroRegiao.value = 'todos';
        filtroUf.value = 'todos';
        filtroRm.value = 'todos';
        if (filtroPorte) { filtroPorte.value = 'todos'; }
        
        if (quantilQuintilRadio) quantilQuintilRadio.checked = true;
        if (formatNumeroRadio) formatNumeroRadio.checked = true;
        if (calcModeTotalRadio) calcModeTotalRadio.checked = true;

        document.querySelectorAll('.toggle-option').forEach(opt => opt.classList.remove('active'));
        toggle2023.classList.add('active');

        updateDependentFilters();
        atualizarFiltros();
    });
});