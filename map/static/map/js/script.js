// Configuração do Mapbox
mapboxgl.accessToken = "pk.eyJ1IjoiZ2F0b2NhbmdhY2Vpcm8iLCJhIjoiY21iaWNwZ243MDQ4bDJvb2tvZnR6bzZydCJ9.B_FIB-HTTgMdliNktSMDnw";
const map = new mapboxgl.Map({
    container: "map",
    style: "mapbox://styles/gatocangaceiro/cmbicxxq2006g01s2e0ht9l0l", // Estilo do mapa
    zoom: 3.5, // Zoom inicial
    center: [-54, -15] // Centro inicial (aproximadamente Brasil)
});
map.addControl(new mapboxgl.NavigationControl()); // Adiciona controles de navegação

// Referências aos elementos HTML dos filtros
const filtroRegiao = document.getElementById('filtro-regiao');
const filtroUf = document.getElementById('filtro-uf');
const filtroMunicipio = document.getElementById('filtro-municipio');
const filtroPorte = document.getElementById('filtro-porte');
const filtroSubgrupo = document.getElementById('filtro-subgrupo');
const filtroRm = document.getElementById('filtro-rm');
const filtroClassificacao = document.getElementById('filtro-classificacao');
const filtroModoCalculo = document.getElementById('filtro-modo-calculo'); // NOVO: Referência ao filtro de modo de cálculo

/**
 * Atualiza os dropdowns de filtros dependentes (Região, UF, Município, RM)
 * com base nos filtros atualmente selecionados.
 * @param {string} [trigger] - O ID do filtro que disparou a atualização (ex: 'regiao', 'uf', 'rm').
 * Usado para preservar o estado do filtro que não foi alterado.
 */
async function updateDependentFilters(trigger = null) {
    // Guarda os valores atuais dos filtros para tentar restaurá-los após a atualização
    const regiaoAtual = filtroRegiao.value;
    const ufAtual = filtroUf.value;
    const rmAtual = filtroRm.value;
    const municipioAtual = filtroMunicipio.value;

    // Monta a URL da API para obter as opções filtradas
    const apiUrl = `/api/get-dependent-filters/?regiao=${regiaoAtual}&uf=${ufAtual}&rm=${rmAtual}`;

    try {
        const response = await fetch(apiUrl);
        const data = await response.json();

        // Bloco para popular e restaurar o estado do filtro de REGIÃO
        filtroRegiao.innerHTML = '<option value="todos">Todas</option>';
        data.regioes.forEach(item => filtroRegiao.add(new Option(item, item)));
        filtroRegiao.value = regiaoAtual; // Restaura o estado

        // Bloco para popular e restaurar o estado do filtro de RM
        filtroRm.innerHTML = '<option value="todos">Todas</option>';
        data.rms.forEach(item => filtroRm.add(new Option(item, item)));
        // Restaura o estado da RM apenas se o trigger não for UF ou Região (que a afetam)
        if (trigger !== 'regiao' && trigger !== 'uf') {
            filtroRm.value = rmAtual;
        }

        // Bloco para popular e restaurar o estado do filtro de UF
        filtroUf.innerHTML = '<option value="todos">Todos</option>';
        data.ufs.forEach(item => filtroUf.add(new Option(item, item)));
        // Restaura o estado da UF apenas se o trigger não for Região (que a afeta)
        if (trigger !== 'regiao') {
            filtroUf.value = ufAtual;
        }
        
        // Bloco para popular e restaurar o estado do filtro de Município
        filtroMunicipio.innerHTML = '<option value="todos">Todos</option>';
        data.municipios.forEach(item => filtroMunicipio.add(new Option(item, item)));
        filtroMunicipio.value = municipioAtual; // Restaura o estado
        
    } catch (error) {
        console.error("Erro ao atualizar filtros dependentes:", error);
    }
}

/**
 * Atualiza os dados exibidos no mapa e o card de resumo.
 * Faz uma requisição à API de dados de municípios com base nos filtros atuais.
 */
async function atualizarMapa() {
    const classificacaoAtual = filtroClassificacao.value;
    const subgroupAtual = filtroSubgrupo.value;
    const modoCalculoAtual = filtroModoCalculo.value; // NOVO: Obtenha o valor do modo de cálculo
    
    // Constrói a URL da API com todos os filtros
    const apiUrl = `/api/dados-municipios/?regiao=${filtroRegiao.value}&uf=${filtroUf.value}&municipio=${filtroMunicipio.value}&porte=${filtroPorte.value}&subgrupo=${subgroupAtual}&rm=${filtroRm.value}&classification=${classificacaoAtual}&calculation_mode=${modoCalculoAtual}`; // NOVO: Adicionado calculation_mode
    
    try {
        const response = await fetch(apiUrl);
        const geojsonData = await response.json();

        // Lógica para calcular e exibir o resumo dos municípios filtrados
        const features = geojsonData.features;
        const count = features.length;

        // Calcula a soma da receita per capita e a média
        const totalRevenue = features.reduce((sum, feature) => {
            return sum + (feature.properties.rc_23_pc || 0);
        }, 0);
        const averageRevenue = count > 0 ? totalRevenue / count : 0;

        // Atualiza os elementos HTML do card de resumo
        document.getElementById('summary-count').textContent = count.toLocaleString('pt-BR');
        document.getElementById('summary-avg-revenue').textContent = averageRevenue.toLocaleString('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        });

        // Atualiza os dados da fonte 'municipios' no Mapbox
        if (map.getSource('municipios')) {
            map.getSource('municipios').setData(geojsonData);
        }

    } catch (error) {
        console.error("Erro ao atualizar os dados do mapa ou resumo:", error);
        // Em caso de erro, zera o card de resumo
        document.getElementById('summary-count').textContent = '0';
        document.getElementById('summary-avg-revenue').textContent = 'R$ 0,00';
    }
}

// --- Configuração do Mapa Mapbox GL JS ---
map.on("load", () => {
    // Adiciona a fonte de dados 'municipios' ao mapa (inicialmente vazia)
    map.addSource("municipios", { type: "geojson", data: { type: "FeatureCollection", features: [] } });

    // Adiciona a camada de círculos para representar a população
    map.addLayer({
        "id": "populacao-circulos",
        "type": "circle",
        "source": "municipios",
        "paint": {
            // Raio do círculo baseado na população (interpolação linear)
            "circle-radius": ["interpolate", ["linear"], ["get", "Populacao23"], 100000, 7, 1000000, 14, 10000000, 28],
            "circle-opacity": 0.8,
            "circle-stroke-width": 1,
            "circle-stroke-color": "#ffffff"
        }
    });

    // Adiciona a camada de rótulos de município (nomes)
    map.addLayer({
        "id": "municipio-labels",
        "type": "symbol",
        "source": "municipios",
        "minzoom": 7, // Os rótulos aparecem a partir do zoom 7
        "layout": {
            "text-field": ["get", "name_muni"], // Pega o nome do município da propriedade GeoJSON
            "text-font": ["Open Sans Semibold", "Arial Unicode MS Bold"],
            "text-size": 11,
            "text-offset": [0, 0.9], // Desloca o texto ligeiramente acima do ponto
            "text-anchor": "top"     // Ancoragem do texto na parte superior
        },
        "paint": {
            "text-color": "#2c3e50", // Cor escura para o texto
            "text-halo-color": "rgba(255, 255, 255, 0.9)", // Contorno branco para legibilidade
            "text-halo-width": 1.5
        }
    });
    
    // Chamadas iniciais para popular os filtros dependentes e carregar o mapa
    updateDependentFilters();
    atualizarClassificacao(); // Garante que a coloração e o sub-filtro estejam corretos no carregamento
    // `atualizarMapa` já é chamada dentro de `atualizarClassificacao`
});

/**
 * Lida com o clique em um círculo de município no mapa.
 * Exibe um popup com detalhes do município e um link para a página de detalhes.
 */
map.on("click", "populacao-circulos", (e) => {
    if (e.features.length === 0) { return; } // Retorna se nenhum recurso foi clicado
    const properties = e.features[0].properties;
    const coordinates = e.features[0].geometry.coordinates.slice();
    if (!properties.cod_ibge) { return; } // Retorna se não houver código IBGE

    // Lógica para criar o texto do percentil de forma dinâmica
    let percentil_texto = '';
    if (properties.percentil_n != null) {
        const percentil_n = Math.round(properties.percentil_n);
        percentil_texto = properties.percentil_n > 50
            ? `<p class="mt-3 fst-italic small">Este município tem receita per capita <b>superior a ${percentil_n}%</b> dos municípios do país.</p>`
            : `<p class="mt-3 fst-italic small">Este município tem receita per capita <b>inferior a ${100 - percentil_n}%</b> dos municípios do país.</p>`;
    }

    // Determine o texto do quantil dinâmico para o popup
    let dynamicQuantileText = 'N/D';
    if (properties.dynamic_quantile !== null && properties.dynamic_quantile !== undefined) {
        if (filtroClassificacao.value === 'quintil') {
            dynamicQuantileText = `${properties.dynamic_quantile}º quintil`;
        } else if (filtroClassificacao.value === 'decil') {
            dynamicQuantileText = `${properties.dynamic_quantile}º decil`;
        }
        // Para 'natural', não há um 'quantil' específico para exibir no popup, pois é uma faixa de valor.
    }


    // Conteúdo HTML do popup
    const popup_html = `
        <h5 class="text-center mb-2"><strong><i class="fa-solid fa-city"></i> ${properties.name_muni_uf}</strong></h5>
        <hr class="mt-0 mb-2">
        <div class="popup-details">
            <p><i class="fa-solid fa-users"></i> <strong>População:</strong> ${properties.Populacao23.toLocaleString("pt-BR")}</p>
            <p><i class="fa-solid fa-coins"></i> <strong>Receita p/c:</strong> ${properties.rc_23_pc.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}</p>
            <p><i class="fa-solid fa-chart-column"></i> <strong>Classificação:</strong> ${dynamicQuantileText}</p>
            <p><i class="fa-solid fa-ranking-star"></i> <strong>Percentil Nacional:</strong> ${properties.percentil || 'N/D'}</p>
        </div>
        ${percentil_texto}
        <div class="d-grid mt-3">
            <a href="/municipio/${properties.cod_ibge}/" class="btn btn-primary btn-sm" target="_blank">
                Ver Mais Detalhes
            </a>
        </div>
    `;

    // Cria e adiciona o popup ao mapa
    new mapboxgl.Popup({ minWidth: '400px', maxWidth: '500px' })
        .setLngLat(coordinates)
        .setHTML(popup_html)
        .addTo(map);
});

/**
 * Reseta todos os filtros para seus valores padrão ('todos')
 * e atualiza o mapa e os filtros dependentes.
 */
function limparFiltros() {
    // Reseta o valor de todos os seletores para "todos"
    filtroRegiao.value = 'todos';
    filtroRm.value = 'todos';
    filtroUf.value = 'todos';
    filtroMunicipio.value = 'todos';
    filtroPorte.value = 'todos';
    filtroSubgrupo.value = 'todos';
    filtroClassificacao.value = 'quintil'; // Reseta a classificação para o padrão
    filtroModoCalculo.value = 'total'; // NOVO: Reseta o modo de cálculo

    // Atualiza as listas dos filtros dinâmicos e o mapa
    updateDependentFilters('limpar');
    atualizarClassificacao(); // Reconfigura o subfiltro e a legenda, e chama atualizarMapa()
}

// --- Event Listeners para os Filtros ---
document.getElementById('btn-limpar-filtros').addEventListener('click', limparFiltros);

filtroRegiao.addEventListener('change', () => {
    updateDependentFilters('regiao'); // Atualiza UFs e Municípios com base na Região
    atualizarMapa(); // Atualiza o mapa com a nova seleção
});

filtroUf.addEventListener('change', () => {
    updateDependentFilters('uf'); // Atualiza Municípios com base na UF
    atualizarMapa(); // Atualiza o mapa
});

filtroRm.addEventListener('change', () => {
    updateDependentFilters('rm'); // Atualiza Região, UF e Municípios com base na RM
    atualizarMapa(); // Atualiza o mapa
});

filtroMunicipio.addEventListener('change', atualizarMapa); // Apenas atualiza o mapa
filtroPorte.addEventListener('change', atualizarMapa); // Apenas atualiza o mapa
filtroSubgrupo.addEventListener('change', atualizarMapa); // Apenas atualiza o mapa

// NOVO: Listener para o modo de cálculo do quantil
filtroModoCalculo.addEventListener('change', () => {
    atualizarClassificacao(); // Recalcula a coloração e o filtro de subgrupo com base no novo modo
});

// Altera o cursor do mouse ao passar sobre os círculos do mapa
map.on("mouseenter", "populacao-circulos", () => { map.getCanvas().style.cursor = "pointer"; });
map.on("mouseleave", "populacao-circulos", () => { map.getCanvas().style.cursor = ""; });

/**
 * Retorna a configuração de pintura para a camada de círculos do Mapbox
 * com base na classificação selecionada (quintil, decil, natural).
 * @param {string} classification - O tipo de classificação ('quintil', 'decil', 'natural').
 * @returns {Array} - Array de configuração de pintura para 'circle-color'.
 */
function getMapPaintConfig(classification) {
    // A propriedade 'dynamic_quantile' é a que sempre conterá o resultado do cálculo
    // de quantil do backend, seja ele 'total' ou 'por_filtro'.
    const propertyToUse = 'dynamic_quantile';

    switch (classification) {
        case 'decil':
            // Mapeia deciis (valores numéricos de 1 a 10 de 'dynamic_quantile') para cores específicas
            return [
                'match', ['get', propertyToUse],
                1, '#a50026', 2, '#d73027',
                3, '#f46d43', 4, '#fdae61',
                5, '#fee090', 6, '#e0f3f8',
                7, '#abd9e9', 8, '#74add1',
                9, '#4575b4', 10, '#313695',
                '#cccccc' // Cor padrão para valores não correspondentes
            ];
        case 'natural':
            // Usa interpolação 'step' para classificar por faixas de receita per capita
            // Este caso usa 'rc_23_pc' diretamente, não o quantil dinâmico
            return [
                'step', ['get', 'rc_23_pc'],
                '#d73027', // Cor para valores abaixo de 2500
                2500, '#fc8d59',
                4000, '#fee08b',
                6000, '#91cf60',
                10000, '#1a9850'
            ];
        case 'quintil':
        default:
            // Configuração padrão para quintis (valores numéricos de 1 a 5 de 'dynamic_quantile')
            return [
                'match', ['get', propertyToUse],
                1, '#d73027', 2, '#fc8d59',
                3, '#fee08b', 4, '#91cf60',
                5, '#1a9850', '#cccccc'
            ];
    }
}

/**
 * Atualiza a legenda do mapa dinamicamente com base na classificação selecionada.
 * @param {string} classification - O tipo de classificação ('quintil', 'decil', 'natural').
 */
function updateLegend(classification) {
    const legend = document.getElementById('legend');
    let content = '';

    // Função auxiliar para gerar labels de quantis
    const getQuantileLabel = (index, type) => `${index}º ${type}`;

    switch (classification) {
        case 'decil':
            const decileColors = {
                1: '#a50026', 2: '#d73027', 3: '#f46d43',
                4: '#fdae61', 5: '#fee090', 6: '#e0f3f8',
                7: '#abd9e9', 8: '#74add1', 9: '#4575b4',
                10: '#313695'
            };
            content = '<h5>Decil</h5><div class="legend-container"><div class="legend-colors">';
            for (let i = 1; i <= 10; i++) {
                content += `<span class="legend-key" style="background-color: ${decileColors[i]};"></span>`;
            }
            content += '</div><div class="legend-labels">';
            for (let i = 1; i <= 10; i++) {
                content += `<span>${getQuantileLabel(i, 'decil')}</span>`;
            }
            content += '</div></div>';
            break;
        case 'natural':
            const naturalBreaks = {
                '< R$ 2.500': '#d73027', 'R$ 2.500 - 4.000': '#fc8d59',
                'R$ 4.000 - 6.000': '#fee08b', 'R$ 6.000 - 10.000': '#91cf60',
                '> R$ 10.000': '#1a9850'
            };
            content = '<h5>Receita p/c (R$)</h5><div class="legend-container"><div class="legend-colors">';
            for (const key in naturalBreaks) {
                content += `<span class="legend-key" style="background-color: ${naturalBreaks[key]};"></span>`;
            }
            content += '</div><div class="legend-labels">';
            for (const key in naturalBreaks) {
                content += `<span>${key}</span>`;
            }
            content += '</div></div>';
            break;
        case 'quintil':
        default:
            // Legenda padrão para quintis
            content = `
                <h5>Quintil</h5>
                <div class="legend-container">
                    <div class="legend-colors">
                        <span class="legend-key" style="background-color: #d73027;"></span>
                        <span class="legend-key" style="background-color: #fc8d59;"></span>
                        <span class="legend-key" style="background-color: #fee08b;"></span>
                        <span class="legend-key" style="background-color: #91cf60;"></span>
                        <span class="legend-key" style="background-color: #1a9850;"></span>
                    </div>
                    <div class="legend-labels">
                        <span>${getQuantileLabel(1, 'quintil')}</span>
                        <span>${getQuantileLabel(2, 'quintil')}</span>
                        <span>${getQuantileLabel(3, 'quintil')}</span>
                        <span>${getQuantileLabel(4, 'quintil')}</span>
                        <span>${getQuantileLabel(5, 'quintil')}</span>
                    </div>
                </div>`;
            break;
    }
    legend.innerHTML = content;
}

/**
 * Atualiza a coloração do mapa e as opções do filtro de subgrupo (Quintil/Decil/Faixa de Receita)
 * com base na classificação selecionada pelo usuário.
 */
function atualizarClassificacao() {
    const classificacao = filtroClassificacao.value;

    // --- PARTE 1: Atualiza a coloração do mapa e a legenda ---
    const novaCor = getMapPaintConfig(classificacao);
    map.setPaintProperty('populacao-circulos', 'circle-color', novaCor);
    updateLegend(classificacao);

    // --- PARTE 2: Atualiza o filtro de subgrupo dinamicamente ---
    const subgrupoLabel = document.querySelector('label[for="filtro-subgrupo"]');
    const subgrupoSelect = document.getElementById('filtro-subgrupo');
    
    // Limpa as opções atuais do subfiltro
    subgrupoSelect.innerHTML = '<option value="todos">Todos</option>';

    switch (classificacao) {
        case 'decil':
            subgrupoLabel.textContent = 'Decil:';
            // Os valores para o subfiltro devem ser numéricos (1, 2, etc.)
            // para corresponder ao que o backend espera para `subgroup_filter`
            // quando `calculation_mode='por_filtro'`.
            const decileOptions = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'];
            decileOptions.forEach(opt => {
                subgrupoSelect.add(new Option(`${opt}º decil`, opt)); // Ex: label '1º decil', value '1'
            });
            break;
        case 'natural':
            subgrupoLabel.textContent = 'Faixa de Receita:';
            const naturalOptions = {
                'Menos de R$ 2.500': '0-2500',
                'R$ 2.500 a 4.000': '2500-4000',
                'R$ 4.000 a 6.000': '4000-6000',
                'R$ 6.000 a 10.000': '6000-10000',
                'Acima de R$ 10.000': '10000-999999'
            };
            for (const text in naturalOptions) {
                subgrupoSelect.add(new Option(text, naturalOptions[text]));
            }
            break;
        case 'quintil':
        default:
            subgrupoLabel.textContent = 'Quintil:';
            // Os valores para o subfiltro devem ser numéricos (1, 2, etc.)
            const quintileOptions = ['1', '2', '3', '4', '5'];
            quintileOptions.forEach(opt => {
                subgrupoSelect.add(new Option(`${opt}º quintil`, opt)); // Ex: label '1º quintil', value '1'
            });
            break;
    }
    
    // --- PARTE 3: Atualiza o mapa para refletir a nova classificação ---
    // Como a classificação principal mudou, o sub-filtro foi resetado para "Todos".
    // Chamamos atualizarMapa() para garantir que o mapa reflita a nova coloração.
    atualizarMapa();
}

// Listener para o evento 'change' do filtro de classificação
filtroClassificacao.addEventListener('change', atualizarClassificacao);


async function downloadTableData() {
    // Obter os filtros atuais para usar na requisição
    const regiaoAtual = filtroRegiao.value;
    const ufAtual = filtroUf.value;
    const municipioAtual = filtroMunicipio.value;
    const porteAtual = filtroPorte.value;
    const subgrupoAtual = filtroSubgrupo.value;
    const rmAtual = filtroRm.value;
    const classificacaoAtual = filtroClassificacao.value;
    const modoCalculoAtual = filtroModoCalculo.value; // NOVO: Obtenha o valor do modo de cálculo

    // Constrói a URL da API para obter os dados filtrados
    const apiUrl = `/api/dados-municipios/?regiao=${regiaoAtual}&uf=${ufAtual}&municipio=${municipioAtual}&porte=${porteAtual}&subgrupo=${subgrupoAtual}&rm=${rmAtual}&classification=${classificacaoAtual}&calculation_mode=${modoCalculoAtual}`;

    try {
        const response = await fetch(apiUrl);
        const geojsonData = await response.json();

        const features = geojsonData.features;

        if (features.length === 0) {
            alert("Não há dados de municípios para baixar com os filtros atuais.");
            return;
        }

        // Define as colunas que você quer no CSV
        const columns = [
            { header: "Município", property: "name_muni_uf" },
            { header: "População 2023", property: "Populacao23" },
            { header: "Receita Per Capita 2023", property: "rc_23_pc" },
            // NOVO: Usa a propriedade 'dynamic_quantile' para o CSV
            // E os campos pré-calculados para referência, se desejar
            { header: "Quantil Dinâmico", property: "dynamic_quantile" }, 
            { header: "Quintil Pré-Calculado", property: "quintil23_pre_calculado" }, // Para referência
            { header: "Decil Pré-Calculado", property: "decil23_pre_calculado" },     // Para referência
            { header: "Percentil Nacional", property: "percentil" },
            { header: "Percentil N", property: "percentil_n" }, // Adicionado para download
            { header: "Cód. IBGE", property: "cod_ibge" }
        ];

        // Cria o cabeçalho do CSV
        let csvContent = columns.map(col => `"${col.header}"`).join(";") + "\n";

        // Adiciona as linhas de dados
        features.forEach(feature => {
            const row = columns.map(col => {
                let value = feature.properties[col.property];
                if (value === null || value === undefined) {
                    value = "N/D"; // Trata valores nulos/indefinidos
                }
                // Formata números para CSV (ex: substitui vírgula por ponto para evitar problemas)
                if (typeof value === 'number') {
                    // Para o Excel brasileiro, '.' como separador de milhar e ',' para decimal
                    // Pode ser necessário um tratamento mais robusto se os números forem muito grandes
                    value = String(value).replace(".", ",");
                }
                return `"${value}"`; // Garante que valores com vírgulas ou aspas sejam tratados corretamente
            }).join(";");
            csvContent += row + "\n";
        });

        // Cria um Blob com o conteúdo CSV
        const blob = new Blob(["\uFEFF" + csvContent], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);

        // Cria um link temporário para download
        const a = document.createElement("a");
        a.href = url;
        a.download = "dados_municipios_filtrados.csv"; // Nome do arquivo
        document.body.appendChild(a); // Adiciona ao DOM (necessário para Firefox)
        a.click(); // Aciona o clique para iniciar o download
        document.body.removeChild(a); // Remove o link
        URL.revokeObjectURL(url); // Libera o URL do objeto
        
    } catch (error) {
        console.error("Erro ao baixar dados da tabela:", error);
        alert("Ocorreu um erro ao tentar baixar os dados. Por favor, tente novamente.");
    }
}

// Listener para o botão de download
document.getElementById('download-table-btn').addEventListener('click', downloadTableData);