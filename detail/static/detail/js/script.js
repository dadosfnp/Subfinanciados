// Variável global para armazenar todos os dados do município carregados do HTML
let municipioData = {};

// Variáveis globais para armazenar as instâncias dos gráficos Chart.js
let mainRevenueChart;
let detailedRevenueChart;

// --- FUNÇÕES GLOBAIS DE RANKING E CORES ---

/**
 * Aplica uma classe CSS ao elemento com base no número do quintil (1-5).
 * @param {HTMLElement} element O elemento HTML ao qual a cor será aplicada.
 * @param {number} quintileNumber O número do quintil (1 a 5).
 */
function applyQuintilColor(element, quintileNumber) {
    // Remove todas as classes de quintil existentes para garantir apenas uma seja aplicada
    element.classList.remove('quintil-1', 'quintil-2', 'quintil-3', 'quintil-4', 'quintil-5');
    // Adiciona a classe correta baseada no número do quintil
    element.classList.add(`quintil-${quintileNumber}`);
}

/**
 * Aplica uma classe CSS ao elemento com base no valor do percentil.
 * Usa as mesmas classes de quintil para consistência visual.
 * @param {HTMLElement} element O elemento HTML ao qual a cor será aplicada.
 * @param {number} percentile O valor do percentil (0 a 100).
 */
function applyPercentileColor(element, percentile) {
    element.classList.remove('quintil-1', 'quintil-2', 'quintil-3', 'quintil-4', 'quintil-5');
    if (percentile <= 20) { // 1º quintil
        element.classList.add('quintil-1');
    } else if (percentile <= 40) { // 2º quintil
        element.classList.add('quintil-2');
    } else if (percentile <= 60) { // 3º quintil
        element.classList.add('quintil-3');
    } else if (percentile <= 80) { // 4º quintil
        element.classList.add('quintil-4');
    } else { // 5º quintil
        element.classList.add('quintil-5');
    }
}

/**
 * Retorna o valor do percentil para um campo específico e tipo de ranking.
 * Os dados são obtidos da variável global `municipioData`.
 * @param {string} fieldBaseName O nome base do campo (ex: 'rc_23_pc', 'imposto').
 * @param {string} rankingType O tipo de ranking ('nacional', 'estadual', 'faixa').
 * @returns {number} O valor do percentil, ou 0 se não encontrado.
 */
function getPercentileForField(fieldBaseName, rankingType) {
    // Mapeamento de 'faixa' para 'regional', já que é como a API e os modelos o chamam.
    const rankingSuffix = (rankingType === 'faixa') ? 'regional' : rankingType;
    const percentileKey = `${fieldBaseName}_${rankingSuffix}`;

    let percentileValue = 0;

    // Use a estrutura aninhada para encontrar o objeto correto
    // O 'rc_23_pc' está no nível superior
    if (fieldBaseName === 'rc_23_pc') {
        percentileValue = municipioData.rc_23_pc_percentile[rankingSuffix];
    } 
    // Campos detalhados
    else if (['imposto_taxas_contribuicoes', 'contribuicoes', 'transferencias_correntes', 'outras_receita'].includes(fieldBaseName)) {
        if (municipioData.conta_detalhada_percentil) {
            percentileValue = municipioData.conta_detalhada_percentil[percentileKey];
        }
    } 
    // Campos específicos
    else if (['imposto', 'taxas', 'contribuicoes', 'contribuicoes_sociais', 'contribuicoes_iluminacao_publica', 'outras_contribuicoes', 'tranferencias_uniao', 'tranferencias_estados', 'outras_tranferencias', 'receita_patrimonial', 'receita_agropecuaria', 'receita_industrial', 'receita_servicos', 'outras_receitas'].includes(fieldBaseName)) {
        if (municipioData.conta_especifica_percentil) {
            percentileValue = municipioData.conta_especifica_percentil[percentileKey];
        }
    } 
    // Campos mais específicos
    else {
        if (municipioData.conta_mais_especifica_percentil) {
            percentileValue = municipioData.conta_mais_especifica_percentil[percentileKey];
        }
    }

    return percentileValue !== undefined && !isNaN(percentileValue) ? percentileValue : 0;
}

/**
 * Atualiza todos os indicadores de ranking na página com base no tipo de ranking selecionado.
 * @param {string} rankingType O tipo de ranking ('nacional', 'estadual', 'faixa').
 */
function updateAllRankingIndicators(rankingType) {
    // Atualiza o indicador principal de ranking (para o card 'Receita per capita')
    updateMainRankingIndicator(rankingType);

    // Atualiza o indicador de quintil do cabeçalho (este usa o quintil fixo do município)
    updateHeaderQuintilIndicator();

    // Atualiza todos os elementos que possuem indicadores de ranking
    const allElementsWithRanking = document.querySelectorAll('.toggle-heading, .toggle-subheading, .metric-detail-row');
    allElementsWithRanking.forEach(element => {
        const fieldBaseName = element.dataset.fieldBase;
        if (fieldBaseName) {
            const percentile = getPercentileForField(fieldBaseName, rankingType);
            const rankingIndicator = element.querySelector('.ranking-indicator');
            const rankingTooltip = element.querySelector('.ranking-tooltip');

            if (rankingIndicator && !isNaN(percentile)) {
                applyPercentileColor(rankingIndicator, percentile); // Aplica a cor baseada no percentil
                rankingTooltip.textContent = `O município supera ${percentile}% dos outros municípios`;
                rankingIndicator.style.display = ''; // Garante que o indicador esteja visível
            } else if (rankingIndicator) {
                rankingIndicator.style.display = 'none'; // Esconde se não houver dados válidos
                rankingTooltip.textContent = '';
            }
        }
    });
}

/**
 * Atualiza o indicador de ranking principal (Receita per capita).
 * @param {string} rankingType O tipo de ranking ('nacional', 'estadual', 'faixa').
 */
function updateMainRankingIndicator(rankingType) {
    // Sempre usa 'rc_23_pc' para este KPI
    const percentile = getPercentileForField('rc_23_pc', rankingType);
    const rankingIndicator = document.querySelector('#ranking-indicator-main .ranking-indicator');
    const rankingTooltip = document.querySelector('#ranking-indicator-main .ranking-tooltip');

    if (rankingIndicator && !isNaN(percentile)) {
        applyPercentileColor(rankingIndicator, percentile);
        rankingTooltip.textContent = `Seu município supera ${percentile}% dos outros municípios`;
        rankingIndicator.style.display = '';
    } else if (rankingIndicator) {
        rankingIndicator.style.display = 'none';
        rankingTooltip.textContent = '';
    }
}

/**
 * Atualiza o indicador de quintil exibido no cabeçalho da página.
 */
function updateHeaderQuintilIndicator() {
    // Obtém o texto do quintil a partir dos dados carregados
    const quintilText = municipioData.quintil23 || '1° quintil'; // Nome ajustado para quintil23 conforme serializer

    const quintilMatch = quintilText.match(/(\d+)° quintil/);
    let quintileNumber = 0;

    if (quintilMatch && quintilMatch[1]) {
        quintileNumber = parseInt(quintilMatch[1]);
    }

    const headerQuintilIndicator = document.querySelector('#header-quintil-indicator-container .ranking-indicator');
    const headerQuintilTooltip = document.querySelector('#header-quintil-indicator-container .ranking-tooltip');

    if (headerQuintilIndicator && quintileNumber >= 1 && quintileNumber <= 5) {
        applyQuintilColor(headerQuintilIndicator, quintileNumber);
        headerQuintilTooltip.textContent = `O município está no ${quintileNumber}° quintil`;
        headerQuintilIndicator.style.display = '';
    } else if (headerQuintilIndicator) {
        headerQuintilIndicator.style.display = 'none';
        headerQuintilTooltip.textContent = '';
        console.warn('Quintil inválido ou elemento não encontrado para o cabeçalho. Escondendo o indicador.');
    }
}

// --- FUNÇÕES DE GRÁFICOS ---

/**
 * Cria ou atualiza um gráfico de pizza usando Chart.js.
 * @param {string} canvasId O ID do elemento canvas.
 * @param {string} chartTitle O título do gráfico.
 * @param {object} chartData Os dados do gráfico contendo `labels` e `values`.
 */
function createOrUpdatePieChart(canvasId, chartTitle, chartData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) {
        console.warn(`Canvas com ID '${canvasId}' não encontrado. Não foi possível criar o gráfico.`);
        return;
    }
    const context = ctx.getContext('2d');

    // Destrói o gráfico existente se houver
    if (canvasId === 'mainRevenueChart' && mainRevenueChart) {
        mainRevenueChart.destroy();
    } else if (canvasId === 'detailedRevenueChart' && detailedRevenueChart) {
        detailedRevenueChart.destroy();
    }

    const chartInstance = new Chart(context, {
        type: 'pie',
        data: {
            labels: chartData.labels,
            datasets: [{
                label: chartTitle,
                data: chartData.values,
                backgroundColor: [
                    '#3b82f6', '#10b981', '#f97316', '#8b5cf6', '#ef4444', '#64748b', '#22d3ee', '#a78bfa', '#facc15', '#fb7185',
                    '#34d399', '#fcd34d', '#fb923c', '#c084fc', '#f87171', '#94a3b8', '#67e8f9', '#d8b4fe', '#fde047', '#fda4af'
                ],
                borderColor: '#ffffff',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.label || '';
                            if (context.parsed !== null) {
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((acc, current) => acc + current, 0);
                                const percentage = (value / total * 100).toFixed(2);
                                label += `: ${value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })} (${percentage}%)`;
                            }
                            return label;
                        }
                    }
                }
            }
        }
    });

    if (canvasId === 'mainRevenueChart') {
        mainRevenueChart = chartInstance;
    } else if (canvasId === 'detailedRevenueChart') {
        detailedRevenueChart = chartInstance;
    }
}

// --- FUNÇÕES DE SORAÇÃO E TOGGLE ---

/**
 * Converte uma string formatada de moeda para um valor numérico.
 * @param {string} str A string de moeda (ex: "R$ 1.234.567,89").
 * @returns {number} O valor numérico parseado.
 */
function parseCurrencyValue(str) {
    if (!str) return 0;
    // Remove "R$", pontos de milhar e substitui vírgula decimal por ponto
    const cleanedStr = str.replace('R$', '').replace(/\./g, '').replace(',', '.').trim();
    return parseFloat(cleanedStr);
}

/**
 * Ordena os elementos filhos de um contêiner com base nos seus valores (absolutos ou per capita).
 * Elementos com valor 0 são filtrados.
 * @param {HTMLElement} containerElement O elemento contêiner cujos filhos serão ordenados.
 * @param {boolean} isPerCapita Indica se deve ordenar por valores per capita ou absolutos.
 */
function sortChildrenByValue(containerElement, isPerCapita) {
    let children = Array.from(containerElement.children);

    // Filtra elementos com valor 0 antes de ordenar
    children = children.filter(child => {
        const valueElement = child.querySelector(isPerCapita ? '.valor-per-capita' : '.valor-absoluto');
        if (valueElement) {
            const value = parseCurrencyValue(valueElement.textContent);
            return value !== 0; // Mantém o elemento se o valor não for 0
        }
        return false; // Remove se não houver elemento de valor ou não puder ser parseado
    });

    children.sort((a, b) => {
        let valueA = 0;
        let valueB = 0;

        const valueAElement = a.querySelector(isPerCapita ? '.valor-per-capita' : '.valor-absoluto');
        const valueBElement = b.querySelector(isPerCapita ? '.valor-per-capita' : '.valor-absoluto');

        if (valueAElement) {
            valueA = parseCurrencyValue(valueAElement.textContent);
        }
        if (valueBElement) {
            valueB = parseCurrencyValue(valueBElement.textContent);
        }

        // Ordena em ordem decrescente (do maior para o menor)
        return valueB - valueA;
    });

    // Limpa os filhos existentes antes de re-adicionar para evitar duplicatas
    while (containerElement.firstChild) {
        containerElement.removeChild(containerElement.firstChild);
    }

    // Anexa os filhos ordenados de volta ao contêiner
    children.forEach(child => containerElement.appendChild(child));

    // Re-inicializa os listeners de toggle para os novos filhos do contêiner
    initializeToggleListeners(containerElement);
}

/**
 * Inicializa (ou re-inicializa) os listeners de clique para elementos de toggle.
 * Garante que os eventos de clique funcionem após reordenação do DOM.
 * @param {HTMLElement} scopeElement O elemento dentro do qual os toggles serão procurados (padrão: document).
 */
function initializeToggleListeners(scopeElement = document) {
    const toggleElements = scopeElement.querySelectorAll('.toggle-heading, .toggle-subheading');

    toggleElements.forEach(element => {
        // Remove quaisquer listeners existentes para evitar duplicatas
        element.removeEventListener('click', handleToggleClick);
        // Adiciona o novo (ou re-adicionado) listener
        element.addEventListener('click', handleToggleClick);
    });
}

/**
 * Função manipuladora de clique para elementos de toggle.
 * Alterna a visibilidade do elemento de destino e a classe 'open' no toggle.
 */
function handleToggleClick() {
    const targetId = this.dataset.target;
    const targetElement = document.getElementById(targetId);
    const isCurrentlyOpen = this.classList.contains('open');
    const arrow = this.querySelector('.arrow'); // Seleciona a seta dentro do elemento clicado

    // Se o elemento estiver atualmente aberto e for ser fechado, fecha também quaisquer toggles aninhados
    if (isCurrentlyOpen && targetElement && !targetElement.classList.contains('hidden')) {
        const nestedToggles = targetElement.querySelectorAll('.toggle-subheading.open');
        nestedToggles.forEach(nestedToggle => {
            nestedToggle.classList.remove('open');
            const nestedTargetId = nestedToggle.dataset.target;
            const nestedTargetElement = document.getElementById(nestedTargetId);
            if (nestedTargetElement) {
                nestedTargetElement.classList.add('hidden'); // Garante que o conteúdo aninhado esteja oculto
            }
            const nestedArrow = nestedToggle.querySelector('.arrow');
            if (nestedArrow) {
                nestedArrow.style.transform = 'rotate(0deg)';
            }
        });
    }

    if (targetElement) {
        targetElement.classList.toggle('hidden');
        this.classList.toggle('open'); // Alterna a classe 'open' no cabeçalho
        if (arrow) {
            // Rotaciona a seta
            arrow.style.transform = this.classList.contains('open') ? 'rotate(90deg)' : 'rotate(0deg)';
        }
    }
}

/**
 * Orquestra a ordenação de todas as seções de receita relevantes na página.
 * @param {boolean} isPerCapita Indica se a ordenação deve ser baseada em valores per capita ou absolutos.
 */
function sortAllRevenueSections(isPerCapita) {
    // Obtenha todos os contêineres que possuem itens ordenáveis
    const containersToSort = [
        document.getElementById('main-revenue-details-container'),
        document.getElementById('detalhe-impostos'), // Certifique-se de que estes IDs existam no seu HTML
        document.getElementById('detalhe-sub-impostos'),
        document.getElementById('detalhe-sub-taxas'),
        document.getElementById('detalhe-sub-contribuicoes-melhoria'),
        document.getElementById('detalhe-contribuicoes'),
        document.getElementById('detalhe-transferencias'),
        document.getElementById('detalhe-sub-transferencias-uniao'),
        document.getElementById('detalhe-sub-transferencias-estados'),
        document.getElementById('detalhe-outras-receitas')
    ].filter(Boolean); // Filtra quaisquer elementos nulos/indefinidos

    containersToSort.forEach(container => {
        if (container) { // Certifica-se de que o contêiner existe
            sortChildrenByValue(container, isPerCapita);
        }
    });
}

// --- SCRIPTS PRINCIPAIS (EXECUTAM APÓS O CARREGAMENTO DO DOM) ---
document.addEventListener('DOMContentLoaded', function() {
    // 1. Carregar Dados do JSON no HTML
    const dataElement = document.getElementById('municipio-data-json');
    if (dataElement) {
        municipioData = JSON.parse(dataElement.textContent);
    } else {
        console.error('Elemento #municipio-data-json não encontrado. Os dados do município não foram carregados.');
        // Pode ser útil exibir uma mensagem de erro na UI também
        return; // Sai da função se os dados essenciais não puderem ser carregados
    }

    // 2. Script para o Dropdown de Ranking (Nacional/Estadual/Faixa)
    const rankingSelect = document.getElementById('ranking-select');
    const rankingValue = document.getElementById('ranking-value');

    // Inicializa o texto do ranking com o valor nacional por padrão
    if (municipioData.ranking_data && municipioData.ranking_data.nacional) {
        rankingValue.textContent = municipioData.ranking_data.nacional;
    } else {
        rankingValue.textContent = 'N/A';
    }
    
    rankingSelect.addEventListener('change', (event) => {
        const selectedRankingType = event.target.value;
        if (municipioData.ranking_data && municipioData.ranking_data[selectedRankingType]) {
            rankingValue.textContent = municipioData.ranking_data[selectedRankingType];
        } else {
            rankingValue.textContent = 'N/A';
        }
        updateAllRankingIndicators(selectedRankingType); // Chama a função que atualiza todos os indicadores
    });

    // 3. Script para os Gráficos de Receita
    const detailedRevenueChartsData = municipioData.all_revenue_chart_data; // Já vem parseado do JSON principal
    const detailedRevenueSelect = document.getElementById('detailed-revenue-select'); // Certifique-se que este ID existe
    const detailedChartTitle = document.getElementById('detailed-chart-title'); // Certifique-se que este ID existe

    if (detailedRevenueChartsData) {
        // Inicializa o Gráfico de Receita Principal (categorias fixas)
        createOrUpdatePieChart('mainRevenueChart', 'Receita Corrente', detailedRevenueChartsData['main_categories']);

        // Inicializa o Gráfico de Receita Detalhada (padrão: "Todas as Categorias Principais")
        createOrUpdatePieChart('detailedRevenueChart', 'Todas as Categorias Principais', detailedRevenueChartsData['main_categories']);
        if (detailedRevenueSelect) {
            detailedRevenueSelect.value = 'main_categories'; // Define o dropdown para este valor inicial
            detailedChartTitle.textContent = `Receita Detalhada: ${detailedRevenueSelect.options[detailedRevenueSelect.selectedIndex].text.replace('   - ', '')}`;
        }
    } else {
        const mainChartContainer = document.getElementById('mainRevenueChart');
        const detailedChartContainer = document.getElementById('detailedRevenueChart');
        if (mainChartContainer) {
            mainChartContainer.parentElement.innerHTML = '<div class="text-center text-gray-500 py-8">Dados de receita não disponíveis para o gráfico principal.</div>';
        }
        if (detailedChartContainer) {
            detailedChartContainer.parentElement.innerHTML = '<div class="text-center text-gray-500 py-8">Dados de receita não disponíveis para o gráfico detalhado.</div>';
        }
    }

    // Event listener para o dropdown do Gráfico de Receita Detalhada
    if (detailedRevenueSelect) {
        detailedRevenueSelect.addEventListener('change', (event) => {
            const selectedCategory = event.target.value;
            const selectedCategoryText = event.target.options[event.target.selectedIndex].text;
            
            if (detailedRevenueChartsData[selectedCategory]) {
                createOrUpdatePieChart('detailedRevenueChart', selectedCategoryText, detailedRevenueChartsData[selectedCategory]);
                detailedChartTitle.textContent = `Receita Detalhada: ${selectedCategoryText.replace('   - ', '')}`; // Limpa o título
            } else {
                console.error('Nenhum dado encontrado para a categoria detalhada selecionada:', selectedCategory);
            }
        });
    }


    // 4. Script para o Toggle de Valores (Absoluto/Per Capita)
    let isShowingPerCapita = true; // Define como true para iniciar mostrando Per Capita
    const toggleBtn = document.getElementById('valor-toggle-btn');
    const valoresAbsolutos = document.querySelectorAll('.valor-absoluto');
    const valoresPerCapita = document.querySelectorAll('.valor-per-capita');
    
    // Configura o texto inicial do botão
    if (toggleBtn) {
        toggleBtn.textContent = 'Ver Valores Reais';

        // Configura a visibilidade inicial com base em `isShowingPerCapita`
        valoresAbsolutos.forEach(el => el.classList.add('hidden'));
        valoresPerCapita.forEach(el => el.classList.remove('hidden'));

        toggleBtn.addEventListener('click', function() {
            isShowingPerCapita = !isShowingPerCapita;
            if (isShowingPerCapita) {
                toggleBtn.textContent = 'Ver Valores Reais';
                valoresAbsolutos.forEach(el => el.classList.add('hidden'));
                valoresPerCapita.forEach(el => el.classList.remove('hidden'));
            } else {
                toggleBtn.textContent = 'Ver Per Capita';
                valoresAbsolutos.forEach(el => el.classList.remove('hidden'));
                valoresPerCapita.forEach(el => el.classList.add('hidden'));
            }
            // Re-ordena todas as seções após mudar a exibição dos valores
            sortAllRevenueSections(isShowingPerCapita);
        });
    }

    // 5. Inicializa todos os listeners de toggle
    initializeToggleListeners();

    // 6. Ordenação inicial ao carregar a página (baseado nos valores per capita)
    sortAllRevenueSections(isShowingPerCapita);

    // 7. Chamada inicial para atualizar o indicador de quintil do cabeçalho
    updateHeaderQuintilIndicator();

    // 8. Chamada inicial para atualizar todos os indicadores de ranking (usa o valor padrão 'nacional' do dropdown)
    updateAllRankingIndicators(rankingSelect.value);
});