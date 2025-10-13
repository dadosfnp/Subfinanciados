// Configuração do Mapbox
const token = window.MAPBOX_PUBLIC_TOKEN || "";
if (!token) {
  console.error("MAPBOX_PUBLIC_TOKEN não definido no template.");
}

mapboxgl.accessToken = token;

const map = new mapboxgl.Map({
    container: "map",
    style: "mapbox://styles/gatocangaceiro/cmbicxxq2006g01s2e0ht9l0l",
    zoom: 3.5,
    center: [-54, -15]
});
map.addControl(new mapboxgl.NavigationControl()); // Adiciona controles de navegação
const DEFAULT_VIEW = { center: [-54, -15], zoom: 3.5 }; // Visão padrão
const q = (v) => encodeURIComponent(v ?? ""); // Helper para encode de parâmetros

// Referências aos elementos HTML dos filtros
const filtroRegiao = document.getElementById('filtro-regiao');
const filtroUf = document.getElementById('filtro-uf');
const filtroMunicipio = document.getElementById('filtro-municipio');
const filtroPorte = document.getElementById('filtro-porte');
const filtroSubgrupo = document.getElementById('filtro-subgrupo');
const filtroRm = document.getElementById('filtro-rm');
const filtroClassificacao = document.getElementById('filtro-classificacao');
const filtroModoCalculo = document.getElementById('filtro-modo-calculo'); // NOVO: Referência ao filtro de modo de cálculo

// Controle de corrida: debounce + request-id
let debounceTimer = null;
let lastRequestId = 0;         // id crescente de requisições

/**
 * Restaura o valor de um <select> apenas se existir entre as opções.
 * Caso contrário, cai para 'todos'.
 */
function restoreSelectValue(selectEl, value) {
    const has = Array.from(selectEl.options).some(o => o.value === value);
    selectEl.value = has ? value : 'todos';
}

// Monta a query removendo filtros com valor "todos" (ou string vazia)
function buildApiUrl(basePath, params) {
    const usp = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '' && v !== 'todos') {
            usp.append(k, v);
        }
    });
    const qs = usp.toString();
    return qs ? `${basePath}?${qs}` : basePath;
}

// Cria uma “chave” imutável dos parâmetros relevantes (sem "todos") para detectar respostas obsoletas
function paramsKeyFromSelects() {
    const raw = {
        regiao: filtroRegiao.value,
        uf: filtroUf.value,
        municipio: filtroMunicipio.value,
        porte: filtroPorte.value,
        subgrupo: filtroSubgrupo.value,
        rm: filtroRm.value,
        classification: filtroClassificacao.value,
        calculation_mode: filtroModoCalculo.value
    };
    const cleaned = {};
    Object.entries(raw).forEach(([k, v]) => {
        if (v && v !== 'todos') cleaned[k] = v;
    });
    return JSON.stringify(Object.keys(cleaned).sort().reduce((acc, k) => { acc[k] = cleaned[k]; return acc; }, {}));
}

/**
 * Atualiza os dropdowns (Região, UF, Município, RM) SEM RESTRIÇÃO,
 * sempre listando TODAS as opções disponíveis.
 * Mantém o valor selecionado, se existir; senão, cai para 'todos'.
 */
async function updateDependentFilters() {
    // Guarda os valores atuais
    const regiaoAtual = filtroRegiao.value;
    const ufAtual = filtroUf.value;
    const rmAtual = filtroRm.value;
    const municipioAtual = filtroMunicipio.value;

    // Busca SEM parâmetros → listas completas
    const apiUrl = '/api/get-dependent-filters/';

    try {
        const response = await fetch(apiUrl);
        const data = await response.json();

        // REGIÃO
        filtroRegiao.innerHTML = '<option value="todos">Todas</option>';
        data.regioes.forEach(item => filtroRegiao.add(new Option(item, item)));
        restoreSelectValue(filtroRegiao, regiaoAtual);

        // RM
        filtroRm.innerHTML = '<option value="todos">Todas</option>';
        data.rms.forEach(item => filtroRm.add(new Option(item, item)));
        restoreSelectValue(filtroRm, rmAtual);

        // UF
        filtroUf.innerHTML = '<option value="todos">Todos</option>';
        data.ufs.forEach(item => filtroUf.add(new Option(item, item)));
        restoreSelectValue(filtroUf, ufAtual);

        // MUNICÍPIO
        filtroMunicipio.innerHTML = '<option value="todos">Todos</option>';
        data.municipios.forEach(item => filtroMunicipio.add(new Option(item, item)));
        restoreSelectValue(filtroMunicipio, municipioAtual);

    } catch (error) {
        console.error("Erro ao atualizar filtros dependentes:", error);
    }
}

/**
 * Atualiza os dados exibidos no mapa e o card de resumo.
 * Faz uma requisição à API de dados de municípios com base nos filtros atuais.
 * Protegido contra “race condition” usando request-id e conferindo a chave de parâmetros.
 */
async function atualizarMapa() {
    const classificacaoAtual = filtroClassificacao.value;
    const subgroupAtual = filtroSubgrupo.value;
    const modoCalculoAtual = filtroModoCalculo.value; // NOVO: Obtenha o valor do modo de cálculo

    const params = {
        regiao: filtroRegiao.value,
        uf: filtroUf.value,
        municipio: filtroMunicipio.value,
        porte: filtroPorte.value,
        subgrupo: subgroupAtual,
        rm: filtroRm.value,
        classification: classificacaoAtual,
        calculation_mode: modoCalculoAtual
    };
    const desiredKey = paramsKeyFromSelects();
    const apiUrl = buildApiUrl('/api/dados-municipios/', params);

    const myId = ++lastRequestId;

    try {
        const response = await fetch(apiUrl);
        const geojsonData = await response.json();
        console.log('[dados]', apiUrl, 'features:', geojsonData.features?.length);

        if (myId !== lastRequestId) return; // resposta obsoleta, ignora

        const currentKey = paramsKeyFromSelects();
        if (currentKey !== desiredKey) return; // parâmetros mudaram, ignora

        // Lógica para calcular e exibir o resumo dos municípios filtrados
        const features = geojsonData.features || [];
        const count = features.length;

        const totalRevenue = features.reduce((sum, feature) => {
            return sum + (feature.properties.rc_23_pc || 0);
        }, 0);
        const averageRevenue = count > 0 ? totalRevenue / count : 0;

        document.getElementById('summary-count').textContent = count.toLocaleString('pt-BR');
        document.getElementById('summary-avg-revenue').textContent = averageRevenue.toLocaleString('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        });

        if (map.getSource('municipios')) {
            map.getSource('municipios').setData(geojsonData);
            applyZoom(geojsonData); // aplica zoom conforme filtros
        }

    } catch (error) {
        console.error("Erro ao atualizar os dados do mapa ou resumo:", error);
        document.getElementById('summary-count').textContent = '0';
        document.getElementById('summary-avg-revenue').textContent = 'R$ 0,00';
    }
}

/**
 * Pequeno debounce para evitar várias chamadas seguidas durante interação rápida.
 */
function scheduleAtualizarMapa(delay = 150) {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
        atualizarMapa();
    }, delay);
}

// --- Configuração do Mapa Mapbox GL JS ---
map.on("load", async () => {
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

  // Esconde camadas do estilo base que mostram todos os municípios/pontos
  hideBaseMunicipalityLayers();

  // Carrega listas completas nos selects (sem restringir por outros filtros)
  await updateDependentFilters();

  // Define coloração/legenda + faz a primeira atualização do mapa (com debounce)
  atualizarClassificacao(); // chama scheduleAtualizarMapa internamente

  // ============================================================
  // === Destaque exclusivo p/ "Xambioá - TO" (ícone condicional)
  // ============================================================

  const MUNICIPIO_NOME = 'Xambioá - TO';
  const XAMBIOA_COORD  = [-48.536, -6.415]; // lon, lat (ajuste fino se necessário)
  const IMG_URL        = '/static/map/images/xambioa.png'; // coloque a imagem aí

  // Garante que a imagem, a source e a layer existem (depois do style carregar)
  map.loadImage(IMG_URL, (err, img) => {
    if (err) { console.error('Erro ao carregar imagem de Xambioá:', err); return; }

    if (!map.hasImage('xambioa-badge')) map.addImage('xambioa-badge', img);

    if (!map.getSource('municipio-highlight')) {
      map.addSource('municipio-highlight', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      });
    }

    if (!map.getLayer('municipio-badge')) {
      map.addLayer({
        id: 'municipio-badge',
        type: 'symbol',
        source: 'municipio-highlight',
        layout: {
          'icon-image': 'xambioa-badge',
          'icon-size': 0.75,
          'icon-allow-overlap': true,
          'visibility': 'none' // começa invisível
        }
      });
    }

    // ---- ligação com o seletor de município ----
    const municipioSelect = document.getElementById('filtro-municipio');

    function atualizarBadgeMunicipio() {
      const src = map.getSource('municipio-highlight');
      if (!src || !map.getLayer('municipio-badge')) return;

      const val   = municipioSelect?.value || '';
      const label = municipioSelect?.selectedOptions?.[0]?.text?.trim() || '';

      // bate por value OU pelo texto exibido (caso o value seja um código IBGE)
      const selecionouXambioa = (val === MUNICIPIO_NOME) || (label === MUNICIPIO_NOME);

      if (selecionouXambioa) {
        src.setData({
          type: 'FeatureCollection',
          features: [{
            type: 'Feature',
            geometry: { type: 'Point', coordinates: XAMBIOA_COORD },
            properties: { name: MUNICIPIO_NOME }
          }]
        });
        map.setLayoutProperty('municipio-badge', 'visibility', 'visible');
        // opcional: focar no ponto
        // map.easeTo({ center: XAMBIOA_COORD, zoom: 9 });
      } else {
        src.setData({ type: 'FeatureCollection', features: [] });
        map.setLayoutProperty('municipio-badge', 'visibility', 'none');
      }
    }
    // deixe o navio menor e responsivo ao zoom
    map.setLayoutProperty('municipio-badge', 'icon-size', [
    'interpolate', ['linear'], ['zoom'],
    5, 0.08,   // longe
    8, 0.12,   // médio
    10, 0.16,  // perto
    12, 0.22   // bem perto
    ]);

    // ancora a base do ícone no ponto (a “quilha” na coordenada)
    map.setLayoutProperty('municipio-badge', 'icon-anchor', 'bottom');

    // move o ícone um pouco para cima do ponto/label
    map.setPaintProperty('municipio-badge', 'icon-translate', [0, -18]);
    // usa coordenadas de tela pra manter o offset estável
    map.setPaintProperty('municipio-badge', 'icon-translate-anchor', 'viewport');


    // 1) Reage à troca manual do usuário
    municipioSelect?.addEventListener('change', atualizarBadgeMunicipio);

    // 2) Reage a repopulação dinâmica do <select> (quando outros filtros mudam)
    //    Se sua lógica recria <option>s sem disparar "change", o observer pega.
    if (municipioSelect) {
      const mo = new MutationObserver(() => atualizarBadgeMunicipio());
      mo.observe(municipioSelect, { childList: true, subtree: true });
    }

    // 3) Aplica imediatamente ao estado atual
    atualizarBadgeMunicipio();
  });
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
 * Zoom do filtro.
 */
// Calcula o bbox (minX,minY,maxX,maxY) de um GeoJSON de pontos/linhas/polígonos
function getGeoJSONBounds(geojson) {
    const coords = [];
    geojson.features.forEach(f => {
        const g = f.geometry;
        if (!g) return;

        const pushCoord = (c) => coords.push(c);
        const walk = (arr) => Array.isArray(arr[0]) ? arr.forEach(walk) : pushCoord(arr);

        walk(g.coordinates);
    });
    if (!coords.length) return null;

    let minX = coords[0][0], minY = coords[0][1], maxX = minX, maxY = minY;
    coords.forEach(([x, y]) => {
        if (x < minX) minX = x; if (x > maxX) maxX = x;
        if (y < minY) minY = y; if (y > maxY) maxY = y;
    });
    return [[minX, minY], [maxX, maxY]];
}

// Aplica zoom conforme seleção atual
function applyZoom(geojsonData) {
    // 1) Município selecionado: foca nele
    if (filtroMunicipio.value !== 'todos') {
        const f = geojsonData.features?.find(ft =>
            (ft.properties?.name_muni === filtroMunicipio.value) ||
            (ft.properties?.name_muni_uf === filtroMunicipio.value)
        );
        if (f && f.geometry) {
            if (f.geometry.type === 'Point') {
                const [lng, lat] = f.geometry.coordinates;
                map.flyTo({ center: [lng, lat], zoom: 9, speed: 0.8, curve: 1.3 });
            } else {
                const bbox = getGeoJSONBounds({ type: 'FeatureCollection', features: [f] });
                if (bbox) map.fitBounds(bbox, { padding: 50, maxZoom: 9, duration: 700 });
            }
            return;
        }
    }

    // 2) Qualquer outro filtro selecionado: ajusta aos resultados filtrados
    if (
        filtroUf.value !== 'todos' ||
        filtroRm.value !== 'todos' ||
        filtroRegiao.value !== 'todos' ||
        filtroPorte.value !== 'todos' ||
        filtroSubgrupo.value !== 'todos'
    ) {
        const bbox = getGeoJSONBounds(geojsonData);
        if (bbox) {
            map.fitBounds(bbox, { padding: 50, maxZoom: 7.5, duration: 700 });
            return;
        }
    }

    // 3) Sem filtros: visão padrão
    map.flyTo({ center: DEFAULT_VIEW.center, zoom: DEFAULT_VIEW.zoom, speed: 0.8, curve: 1.3 });
}

/**
 * Esconde camadas do estilo base que desenham todos os municípios/pontos (para evitar "todos + selecionado").
 * Heurística: camadas do tipo 'circle' ou 'fill' e com id/source-layer contendo palavras-chave.
 */
function hideBaseMunicipalityLayers() {
    const keywords = ['munic', 'muni', 'municip', 'cidade', 'cidades', 'cities', 'municipios', 'municipios-pontos'];
    const style = map.getStyle();
    if (!style || !style.layers) return;

    style.layers.forEach(layer => {
        const id = (layer.id || '').toLowerCase();
        const srcLayer = (layer['source-layer'] || '').toLowerCase();
        const hay = id + ' ' + srcLayer;
        const match = keywords.some(k => hay.includes(k));

        // Evita esconder nossas próprias camadas
        const isOurLayer = id.startsWith('populacao-circulos') || id.startsWith('municipio-labels');

        if (!isOurLayer && match && (layer.type === 'circle' || layer.type === 'fill')) {
            try {
                map.setLayoutProperty(layer.id, 'visibility', 'none');
            } catch (_) {}
        }
    });
}

/**
 * Reseta todos os filtros para seus valores padrão ('todos')
 * e atualiza o mapa e os filtros dependentes.
 */
async function limparFiltros() {
    filtroRegiao.value = 'todos';
    filtroRm.value = 'todos';
    filtroUf.value = 'todos';
    filtroMunicipio.value = 'todos';
    filtroPorte.value = 'todos';
    filtroSubgrupo.value = 'todos';
    filtroClassificacao.value = 'quintil';
    filtroModoCalculo.value = 'total';
    map.flyTo({ center: DEFAULT_VIEW.center, zoom: DEFAULT_VIEW.zoom, speed: 0.8, curve: 1.3 });

    await updateDependentFilters(); // repovoa com listas completas
    atualizarClassificacao();       // reconfigura subfiltro + colore
}

// --- Event Listeners para os Filtros ---
document.getElementById('btn-limpar-filtros').addEventListener('click', async () => {
    await limparFiltros();
});

// Não resetamos selects "filhos": cada dropdown sempre mostra todas as opções.
// Apenas atualizamos o mapa (com debounce).
filtroRegiao.addEventListener('change', () => scheduleAtualizarMapa());
filtroUf.addEventListener('change', () => scheduleAtualizarMapa());
filtroRm.addEventListener('change', () => scheduleAtualizarMapa());
filtroMunicipio.addEventListener('change', () => scheduleAtualizarMapa());
filtroPorte.addEventListener('change', () => scheduleAtualizarMapa());
filtroSubgrupo.addEventListener('change', () => scheduleAtualizarMapa());

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
    const propertyToUse = 'dynamic_quantile'; // resultado do backend

    switch (classification) {
        case 'decil':
            return [
                'match', ['get', propertyToUse],
                1, '#a50026', 2, '#d73027',
                3, '#f46d43', 4, '#fdae61',
                5, '#fee08b', 6, '#d9ef8b',
                7, '#a6d96a', 8, '#66bd63',
                9, '#1a9850', 10, '#006837',
                '#cccccc'
            ];
        case 'natural':
            return [
                'step', ['get', 'rc_23_pc'],
                '#d73027',
                2500, '#fc8d59',
                4000, '#fee08b',
                6000, '#91cf60',
                10000, '#1a9850'
            ];
        case 'quintil':
        default:
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

    const getQuantileLabel = (index, type) => `${index}º ${type}`;

    switch (classification) {
        case 'decil':
            const decileColors = {
                1: '#a50026', 2: '#d73027', 3: '#f46d43',
                4: '#fdae61', 5: '#fee08b', 6: '#d9ef8b',
                7: '#a6d96a', 8: '#66bd63', 9: '#1a9850',
                10: '#006837'
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
            ['1','2','3','4','5','6','7','8','9','10'].forEach(opt => {
                subgrupoSelect.add(new Option(`${opt}º decil`, opt));
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
            ['1','2','3','4','5'].forEach(opt => {
                subgrupoSelect.add(new Option(`${opt}º quintil`, opt));
            });
            break;
    }
    
    // --- PARTE 3: Atualiza o mapa para refletir a nova classificação ---
    scheduleAtualizarMapa(); // usa debounce
}

// Listener para o evento 'change' do filtro de classificação
filtroClassificacao.addEventListener('change', atualizarClassificacao);

/**
 * Download dos dados da tabela (CSV) com base nos filtros atuais.
 */
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

    // Constrói a URL da API para obter os dados filtrados (sem "todos")
    const apiUrl = buildApiUrl('/api/dados-municipios/', {
        regiao: regiaoAtual,
        uf: ufAtual,
        municipio: municipioAtual,
        porte: porteAtual,
        subgrupo: subgrupoAtual,
        rm: rmAtual,
        classification: classificacaoAtual,
        calculation_mode: modoCalculoAtual
    });

    try {
        const response = await fetch(apiUrl);
        const geojsonData = await response.json();

        const features = geojsonData.features || [];

        if (features.length === 0) {
            alert("Não há dados de municípios para baixar com os filtros atuais.");
            return;
        }

        // Define as colunas que você quer no CSV
        const columns = [
            { header: "Município", property: "name_muni_uf" },
            { header: "População 2023", property: "Populacao23" },
            { header: "Receita Per Capita 2023", property: "rc_23_pc" },
            { header: "Quantil Dinâmico", property: "dynamic_quantile" }, 
            { header: "Quintil Pré-Calculado", property: "quintil23_pre_calculado" },
            { header: "Decil Pré-Calculado", property: "decil23_pre_calculado" },
            { header: "Percentil Nacional", property: "percentil" },
            { header: "Percentil N", property: "percentil_n" },
            { header: "Cód. IBGE", property: "cod_ibge" }
        ];

        let csvContent = columns.map(col => `"${col.header}"`).join(";") + "\n";

        features.forEach(feature => {
            const row = columns.map(col => {
                let value = feature.properties[col.property];
                if (value === null || value === undefined) value = "N/D";
                if (typeof value === 'number') value = String(value).replace(".", ",");
                return `"${value}"`;
            }).join(";");
            csvContent += row + "\n";
        });

        const blob = new Blob(["\uFEFF" + csvContent], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = url;
        a.download = "dados_municipios_filtrados.csv";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
    } catch (error) {
        console.error("Erro ao baixar dados da tabela:", error);
        alert("Ocorreu um erro ao tentar baixar os dados. Por favor, tente novamente.");
    }
}

// Listener para o botão de download
document.getElementById('download-table-btn').addEventListener('click', downloadTableData);
