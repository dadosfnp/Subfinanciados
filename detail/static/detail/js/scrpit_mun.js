document.addEventListener('DOMContentLoaded', function() {
    // --- DATA PARSING ---
    const allRevenueChartData = JSON.parse(document.getElementById('chart-data').textContent);
    const percentileData = JSON.parse(document.getElementById('percentile-data').textContent);
    // Correção: Lendo os dados do município a partir do DOM
    const municipioData = JSON.parse(document.getElementById('municipio-data').textContent);

    // --- TOGGLE LOGIC ---
    function handleToggleClick(event) {
        event.stopPropagation();
        const targetId = this.dataset.target;
        if (!targetId) return;
        const targetElement = document.getElementById(targetId);
        if (targetElement) {
            this.classList.toggle('open');
            targetElement.classList.toggle('hidden');
        }
    }

    function initializeToggleListeners(scopeElement = document) {
        const toggleElements = scopeElement.querySelectorAll('.toggle-heading, .toggle-subheading');
        toggleElements.forEach(element => {
            element.removeEventListener('click', handleToggleClick);
            element.addEventListener('click', handleToggleClick);
        });
    }

    // --- SORTING LOGIC ---
    function parseCurrencyValue(str) {
        if (!str) return 0;
        return parseFloat(str.replace('R$', '').replace(/\./g, '').replace(',', '.').trim());
    }

    function sortChildrenByValue(container, isPerCapita) {
        const children = Array.from(container.children);
        children.sort((a, b) => {
            const valueSelector = isPerCapita ? '.valor-per-capita' : '.valor-absoluto';
            const valA = parseCurrencyValue(a.querySelector(valueSelector)?.textContent);
            const valB = parseCurrencyValue(b.querySelector(valueSelector)?.textContent);
            return valB - valA;
        });
        children.forEach(child => container.appendChild(child));
    }

    function sortAllRevenueSections(isPerCapita) {
        const containers = document.querySelectorAll('#main-revenue-details-container, [id^="detalhe-"]');
        containers.forEach(container => {
            sortChildrenByValue(container, isPerCapita);
        });
        initializeToggleListeners();
    }

    // --- VALUE TOGGLE BUTTON ---
    let isShowingPerCapita = true;
    const toggleBtn = document.getElementById('valor-toggle-btn');
    const valoresAbsolutos = document.querySelectorAll('.valor-absoluto');
    const valoresPerCapita = document.querySelectorAll('.valor-per-capita');
    
    toggleBtn.addEventListener('click', function() {
        isShowingPerCapita = !isShowingPerCapita;
        if (isShowingPerCapita) {
            toggleBtn.textContent = 'Valores Reais';
            valoresAbsolutos.forEach(el => el.classList.add('hidden'));
            valoresPerCapita.forEach(el => el.classList.remove('hidden'));
        } else {
            toggleBtn.textContent = 'Per Capita';
            valoresAbsolutos.forEach(el => el.classList.remove('hidden'));
            valoresPerCapita.forEach(el => el.classList.add('hidden'));
        }
        sortAllRevenueSections(isShowingPerCapita);
    });

    // --- RANKING LOGIC ---
    const rankingSelect = document.getElementById('ranking-select');
    const rankingValueElement = document.getElementById('ranking-value');
    const headerQuintilContainer = document.getElementById('header-quintil-indicator-container');

    function updateQuintilIndicator(element, percentile) {
        element.classList.remove('quintil-1', 'quintil-2', 'quintil-3', 'quintil-4', 'quintil-5');
        if (percentile <= 20) {
            element.classList.add('quintil-1');
        } else if (percentile > 20 && percentile <= 40) {
            element.classList.add('quintil-2');
        } else if (percentile > 40 && percentile <= 60) {
            element.classList.add('quintil-3');
        } else if (percentile > 60 && percentile <= 80) {
            element.classList.add('quintil-4');
        } else {
            element.classList.add('quintil-5');
        }
    }

    rankingSelect.addEventListener('change', function() {
        const selectedRanking = this.value;
        let rank, total;

        switch (selectedRanking) {
            case 'nacional':
                rank = municipioData.rank_nacional;
                total = municipioData.total_nacional;
                break;
            case 'estadual':
                rank = municipioData.rank_estadual;
                total = municipioData.total_estadual;
                break;
            case 'faixa':
                rank = municipioData.rank_faixa;
                total = municipioData.total_faixa;
                break;
            default:
                rank = 'N/A';
                total = 'N/A';
        }

        rankingValueElement.textContent = `${rank} / ${total}`;

        const allRevenueItems = document.querySelectorAll('.revenue-item-wrapper');
        allRevenueItems.forEach(itemWrapper => {
            const fieldBase = itemWrapper.querySelector('[data-field-base]').dataset.fieldBase;
            const indicatorContainer = itemWrapper.querySelector('.ranking-indicator-container');
            const indicator = indicatorContainer.querySelector('.ranking-indicator');
            const tooltip = indicatorContainer.querySelector('.ranking-tooltip');

            if (percentileData[fieldBase] && percentileData[fieldBase][selectedRanking]) {
                const percentile = percentileData[fieldBase][selectedRanking];
                
                updateQuintilIndicator(indicator, percentile);
                tooltip.textContent = `O município supera ${percentile}% dos outros municípios`;
            } else {
                indicator.classList.remove('quintil-1', 'quintil-2', 'quintil-3', 'quintil-4', 'quintil-5');
                tooltip.textContent = 'Ranking não disponível';
            }
        });
        
        // ATUALIZAÇÃO PARA O INDICADOR PRINCIPAL DE RECEITA CORRENTE
        const headerQuintilIndicator = headerQuintilContainer.querySelector('.ranking-indicator');
        const headerQuintilTooltip = headerQuintilContainer.querySelector('.ranking-tooltip');

        // Verifica se a chave 'rc' existe no objeto de dados. Se não existir, a chave padrão será usada.
        const main_rc_percentile = percentileData['rc'] ? percentileData['rc'][selectedRanking] : null;

        if (main_rc_percentile !== null && main_rc_percentile !== undefined) {
            updateQuintilIndicator(headerQuintilIndicator, main_rc_percentile);
            headerQuintilTooltip.textContent = `O município supera ${main_rc_percentile}% dos outros municípios`;
        } else {
            headerQuintilIndicator.classList.remove('quintil-1', 'quintil-2', 'quintil-3', 'quintil-4', 'quintil-5');
            headerQuintilTooltip.textContent = 'Ranking não disponível';
        }
    });

    // --- INITIALIZATION CALLS ---
    sortAllRevenueSections(isShowingPerCapita);
    initializeToggleListeners();
    // Dispara o evento 'change' manualmente para inicializar o ranking com o valor padrão
    rankingSelect.dispatchEvent(new Event('change'));
});