// ===================== Config Mapbox =====================
const token = window.MAPBOX_PUBLIC_TOKEN || "";
if (!token) console.error("MAPBOX_PUBLIC_TOKEN não definido no template.");
mapboxgl.accessToken = token;

const map = new mapboxgl.Map({
  container: "map",
  style: "mapbox://styles/gatocangaceiro/cmbicxxq2006g01s2e0ht9l0l",
  zoom: 3.5,
  center: [-54, -15]
});
map.addControl(new mapboxgl.NavigationControl());

const DEFAULT_VIEW = { center: [-54, -15], zoom: 3.5 };

// ===================== Filtros (refs) =====================
const filtroRegiao         = document.getElementById('filtro-regiao');
const filtroUf             = document.getElementById('filtro-uf');
const filtroMunicipio      = document.getElementById('filtro-municipio');
const filtroPorte          = document.getElementById('filtro-porte');
const filtroSubgrupo       = document.getElementById('filtro-subgrupo');
const filtroRm             = document.getElementById('filtro-rm');
const filtroClassificacao  = document.getElementById('filtro-classificacao');
const filtroModoCalculo    = document.getElementById('filtro-modo-calculo');

let debounceTimer = null;
let lastRequestId = 0;

// ===================== Helpers =====================
function restoreSelectValue(selectEl, value) {
  const has = Array.from(selectEl.options).some(o => o.value === value);
  selectEl.value = has ? value : 'todos';
}

function buildApiUrl(basePath, params) {
  const usp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '' && v !== 'todos') usp.append(k, v);
  });
  const qs = usp.toString();
  return qs ? `${basePath}?${qs}` : basePath;
}

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
  Object.entries(raw).forEach(([k, v]) => { if (v && v !== 'todos') cleaned[k] = v; });
  return JSON.stringify(Object.keys(cleaned).sort().reduce((acc, k) => (acc[k] = cleaned[k], acc), {}));
}

// ===================== Filtros dependentes =====================
async function updateDependentFilters() {
  const regiaoAtual    = filtroRegiao.value;
  const ufAtual        = filtroUf.value;
  const rmAtual        = filtroRm.value;
  const municipioAtual = filtroMunicipio.value;

  try {
    const response = await fetch('/api/get-dependent-filters/');
    const data = await response.json();

    filtroRegiao.innerHTML = '<option value="todos">Todas</option>';
    data.regioes.forEach(v => filtroRegiao.add(new Option(v, v)));
    restoreSelectValue(filtroRegiao, regiaoAtual);

    filtroRm.innerHTML = '<option value="todos">Todas</option>';
    data.rms.forEach(v => filtroRm.add(new Option(v, v)));
    restoreSelectValue(filtroRm, rmAtual);

    filtroUf.innerHTML = '<option value="todos">Todos</option>';
    data.ufs.forEach(v => filtroUf.add(new Option(v, v)));
    restoreSelectValue(filtroUf, ufAtual);

    filtroMunicipio.innerHTML = '<option value="todos">Todos</option>';
    data.municipios.forEach(v => filtroMunicipio.add(new Option(v, v)));
    restoreSelectValue(filtroMunicipio, municipioAtual);
  } catch (err) {
    console.error("Erro ao atualizar filtros dependentes:", err);
  }
}

// ===================== Atualização do mapa =====================
async function atualizarMapa() {
  const classificacaoAtual = filtroClassificacao.value;

  const params = {
    regiao: filtroRegiao.value,
    uf: filtroUf.value,
    municipio: filtroMunicipio.value,
    porte: filtroPorte.value,
    subgrupo: filtroSubgrupo.value,
    rm: filtroRm.value,
    classification: classificacaoAtual,
    calculation_mode: filtroModoCalculo.value
  };
  const desiredKey = paramsKeyFromSelects();
  const apiUrl = buildApiUrl('/api/dados-municipios/', params);
  const myId = ++lastRequestId;

  try {
    const response = await fetch(apiUrl);
    const geojsonData = await response.json();

    if (myId !== lastRequestId) return;
    if (paramsKeyFromSelects() !== desiredKey) return;

    const features = geojsonData.features || [];
    const count = features.length;
    const totalRevenue = features.reduce((s, f) => s + (f.properties.rc_23_pc || 0), 0);
    const averageRevenue = count > 0 ? totalRevenue / count : 0;

    document.getElementById('summary-count').textContent = count.toLocaleString('pt-BR');
    document.getElementById('summary-avg-revenue').textContent = averageRevenue.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

    if (map.getSource('municipios')) {
      map.getSource('municipios').setData(geojsonData);
      applyZoom(geojsonData);
    }
  } catch (err) {
    console.error("Erro ao atualizar os dados do mapa ou resumo:", err);
    document.getElementById('summary-count').textContent = '0';
    document.getElementById('summary-avg-revenue').textContent = 'R$ 0,00';
  }
}

function scheduleAtualizarMapa(delay = 150) {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(atualizarMapa, delay);
}

// ===================== Mapa: load =====================
map.on("load", async () => {
  map.addSource("municipios", { type: "geojson", data: { type: "FeatureCollection", features: [] } });

  map.addLayer({
    id: "populacao-circulos",
    type: "circle",
    source: "municipios",
    paint: {
      "circle-radius": ["interpolate", ["linear"], ["get", "Populacao23"],
        100000, 7, 1000000, 14, 10000000, 28],
      "circle-opacity": 0.8,
      "circle-stroke-width": 1,
      "circle-stroke-color": "#ffffff"
    }
  });

  map.addLayer({
    id: "municipio-labels",
    type: "symbol",
    source: "municipios",
    minzoom: 7,
    layout: {
      "text-field": ["get", "name_muni"],
      "text-font": ["Open Sans Semibold", "Arial Unicode MS Bold"],
      "text-size": 11,
      "text-offset": [0, 0.9],
      "text-anchor": "top"
    },
    paint: {
      "text-color": "#2c3e50",
      "text-halo-color": "rgba(255,255,255,0.9)",
      "text-halo-width": 1.5
    }
  });

  hideBaseMunicipalityLayers();
  await updateDependentFilters();
  atualizarClassificacao(); // seta cores + legenda e chama o debounce internamente

  // ------------ Badge Xambioá (opcional, preservado) ------------
  const MUNICIPIO_NOME = 'Xambioá - TO';
  const XAMBIOA_COORD  = [-48.536, -6.415];
  const IMG_URL        = '/static/map/images/xambioa.png';

  map.loadImage(IMG_URL, (err, img) => {
    if (err) { console.error('Erro ao carregar imagem de Xambioá:', err); return; }
    if (!map.hasImage('xambioa-badge')) map.addImage('xambioa-badge', img);

    if (!map.getSource('municipio-highlight')) {
      map.addSource('municipio-highlight', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    }
    if (!map.getLayer('municipio-badge')) {
      map.addLayer({
        id: 'municipio-badge',
        type: 'symbol',
        source: 'municipio-highlight',
        layout: { 'icon-image': 'xambioa-badge', 'icon-size': 0.75, 'icon-allow-overlap': true, 'visibility': 'none' }
      });
    }

    const municipioSelect = document.getElementById('filtro-municipio');
    function atualizarBadgeMunicipio() {
      const src = map.getSource('municipio-highlight');
      if (!src || !map.getLayer('municipio-badge')) return;
      const val = municipioSelect?.value || '';
      const label = municipioSelect?.selectedOptions?.[0]?.text?.trim() || '';
      const on = (val === MUNICIPIO_NOME) || (label === MUNICIPIO_NOME);

      if (on) {
        src.setData({ type: 'FeatureCollection', features: [{ type:'Feature', geometry:{ type:'Point', coordinates:XAMBIOA_COORD }, properties:{ name:MUNICIPIO_NOME } }] });
        map.setLayoutProperty('municipio-badge','visibility','visible');
      } else {
        src.setData({ type:'FeatureCollection', features:[] });
        map.setLayoutProperty('municipio-badge','visibility','none');
      }
    }

    map.setLayoutProperty('municipio-badge','icon-size',
      ['interpolate',['linear'],['zoom'],5,0.08,8,0.12,10,0.16,12,0.22]);
    map.setLayoutProperty('municipio-badge','icon-anchor','bottom');
    map.setPaintProperty('municipio-badge','icon-translate',[0,-18]);
    map.setPaintProperty('municipio-badge','icon-translate-anchor','viewport');

    municipioSelect?.addEventListener('change', atualizarBadgeMunicipio);
    if (municipioSelect) {
      const mo = new MutationObserver(() => atualizarBadgeMunicipio());
      mo.observe(municipioSelect, { childList:true, subtree:true });
    }
    atualizarBadgeMunicipio();
  });
});

// ===================== Popup =====================
map.on("click", "populacao-circulos", (e) => {
  if (e.features.length === 0) return;
  const properties  = e.features[0].properties;
  const coordinates = e.features[0].geometry.coordinates.slice();
  if (!properties.cod_ibge) return;

  let percentil_texto = '';
  if (properties.percentil_n != null) {
    const percentil_n = Math.round(properties.percentil_n);
    percentil_texto = properties.percentil_n > 50
      ? `<p class="mt-3 fst-italic small">Este município tem receita per capita <b>superior a ${percentil_n}%</b> dos municípios do país.</p>`
      : `<p class="mt-3 fst-italic small">Este município tem receita per capita <b>inferior a ${100 - percentil_n}%</b> dos municípios do país.</p>`;
  }

  let dynamicQuantileText = 'N/D';
  if (properties.dynamic_quantile !== null && properties.dynamic_quantile !== undefined) {
    if (filtroClassificacao.value === 'quintil') dynamicQuantileText = `${properties.dynamic_quantile}º quintil`;
    else if (filtroClassificacao.value === 'decil') dynamicQuantileText = `${properties.dynamic_quantile}º decil`;
  }

  const html = `
    <h5 class="text-center mb-2"><strong><i class="fa-solid fa-city"></i> ${properties.name_muni_uf}</strong></h5>
    <hr class="mt-0 mb-2">
    <div class="popup-details">
      <p><i class="fa-solid fa-users"></i> <strong>População:</strong> ${(+properties.Populacao23).toLocaleString("pt-BR")}</p>
      <p><i class="fa-solid fa-coins"></i> <strong>Receita p/c:</strong> ${(+properties.rc_23_pc).toLocaleString("pt-BR",{style:"currency",currency:"BRL"})}</p>
      <p><i class="fa-solid fa-chart-column"></i> <strong>Classificação:</strong> ${dynamicQuantileText}</p>
      <p><i class="fa-solid fa-ranking-star"></i> <strong>Percentil Nacional:</strong> ${properties.percentil || 'N/D'}</p>
    </div>
    ${percentil_texto}
    <div class="d-grid mt-3">
      <a href="/municipio/${properties.cod_ibge}/" class="btn btn-primary btn-sm" target="_blank">Ver Mais Detalhes</a>
    </div>
  `;
  new mapboxgl.Popup({ minWidth:'400px', maxWidth:'500px' }).setLngLat(coordinates).setHTML(html).addTo(map);
});

// ===================== Zoom helpers =====================
function getGeoJSONBounds(geojson) {
  const coords = [];
  geojson.features.forEach(f => {
    const g = f.geometry; if (!g) return;
    const push = (c) => coords.push(c);
    const walk = (arr) => Array.isArray(arr[0]) ? arr.forEach(walk) : push(arr);
    walk(g.coordinates);
  });
  if (!coords.length) return null;
  let [minX, minY] = coords[0], [maxX, maxY] = coords[0];
  coords.forEach(([x,y]) => { if (x<minX)minX=x; if (x>maxX)maxX=x; if (y<minY)minY=y; if (y>maxY)maxY=y; });
  return [[minX,minY],[maxX,maxY]];
}

function applyZoom(geojsonData) {
  if (filtroMunicipio.value !== 'todos') {
    const f = geojsonData.features?.find(ft =>
      (ft.properties?.name_muni === filtroMunicipio.value) ||
      (ft.properties?.name_muni_uf === filtroMunicipio.value)
    );
    if (f && f.geometry) {
      if (f.geometry.type === 'Point') {
        const [lng, lat] = f.geometry.coordinates;
        map.flyTo({ center:[lng,lat], zoom:9, speed:0.8, curve:1.3 });
      } else {
        const bbox = getGeoJSONBounds({ type:'FeatureCollection', features:[f] });
        if (bbox) map.fitBounds(bbox, { padding:50, maxZoom:9, duration:700 });
      }
      return;
    }
  }

  if (filtroUf.value !== 'todos' || filtroRm.value !== 'todos' ||
      filtroRegiao.value !== 'todos' || filtroPorte.value !== 'todos' ||
      filtroSubgrupo.value !== 'todos') {
    const bbox = getGeoJSONBounds(geojsonData);
    if (bbox) { map.fitBounds(bbox, { padding:50, maxZoom:7.5, duration:700 }); return; }
  }

  map.flyTo({ center: DEFAULT_VIEW.center, zoom: DEFAULT_VIEW.zoom, speed:0.8, curve:1.3 });
}

function hideBaseMunicipalityLayers() {
  const keywords = ['munic','muni','municip','cidade','cidades','cities','municipios','municipios-pontos'];
  const style = map.getStyle();
  if (!style || !style.layers) return;
  style.layers.forEach(layer => {
    const id = (layer.id||'').toLowerCase();
    const srcLayer = (layer['source-layer']||'').toLowerCase();
    const hay = id + ' ' + srcLayer;
    const match = keywords.some(k => hay.includes(k));
    const isOur = id.startsWith('populacao-circulos') || id.startsWith('municipio-labels');
    if (!isOur && match && (layer.type === 'circle' || layer.type === 'fill')) {
      try { map.setLayoutProperty(layer.id,'visibility','none'); } catch(_) {}
    }
  });
}

// ===================== Pintura (cores do mapa) =====================
function getMapPaintConfig(classification) {
  const prop = 'dynamic_quantile';
  switch (classification) {
    case 'decil':
      return ['match',['get',prop],
        1,'#a50026',2,'#d73027',3,'#f46d43',4,'#fdae61',5,'#fee08b',
        6,'#d9ef8b',7,'#a6d96a',8,'#66bd63',9,'#1a9850',10,'#006837',
        '#cccccc'];
    case 'natural':
      return ['step',['get','rc_23_pc'],
        '#d73027', 2500,'#fc8d59', 4000,'#fee08b', 6000,'#91cf60', 10000,'#1a9850'];
    case 'quintil':
    default:
      return ['match',['get',prop],
        1,'#d73027',2,'#fc8d59',3,'#fee08b',4,'#91cf60',5,'#1a9850','#cccccc'];
  }
}

// ===================== Legenda: Faixa Populacional (3 bolinhas) =====================
function buildSizeLegendSVGRow(config = [
  { label: '≤ 200 mil',   value: 120_000 },
  { label: '200–500 mil', value: 350_000 },
  { label: '> 500 mil',   value: 800_000 }
]) {
  const radiusFromPopulation = (pop) => {
    if (!Number.isFinite(pop) || pop <= 0) return 6;
    if (pop <= 100000)  return Math.max(6, 7 * (pop / 100000));
    if (pop <= 1000000) return 7 + (14-7) * ((pop-100000) / 900000);
    if (pop <= 10000000) return 14 + (28-14) * ((pop-1000000) / 9000000);
    return 28 + Math.log10(pop/10000000)*5;
  };

  const width = 240, height = 90;
  const startX = 50, gapX = 70, cy = 60;

  const radii = config.map(c => Math.max(6, radiusFromPopulation(c.value)));
  const parts = [
    `<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">`,
    `<g fill="#fff" stroke="#111827" stroke-width="1" opacity="0.95">`
  ];

  radii.forEach((r, i) => {
    const cx = startX + i * gapX;
    parts.push(`<circle cx="${cx}" cy="${cy}" r="${r}"></circle>`);
    const ty = Math.max(14, cy - r - 8);
    parts.push(`<text x="${cx}" y="${ty}" font-size="12" fill="#374151" text-anchor="middle" dominant-baseline="central">${config[i].label}</text>`);
  });

  parts.push(`</g></svg>`);
  return parts.join('');
}

// ===================== Legenda: Cores (100% alinhada) =====================
function updateLegend(classification) {
  const legend = document.getElementById('legend');

  let header = 'Quintil';
  let items  = []; // {color, text}

  if (classification === 'decil') {
    header = 'Decil';
    items = [
      { color:'#a50026', text:'1º decil'  },
      { color:'#d73027', text:'2º decil'  },
      { color:'#f46d43', text:'3º decil'  },
      { color:'#fdae61', text:'4º decil'  },
      { color:'#fee08b', text:'5º decil'  },
      { color:'#d9ef8b', text:'6º decil'  },
      { color:'#a6d96a', text:'7º decil'  },
      { color:'#66bd63', text:'8º decil'  },
      { color:'#1a9850', text:'9º decil'  },
      { color:'#006837', text:'10º decil' }
    ];
  } else if (classification === 'natural') {
    header = 'Receita p/c (R$)';
    items = [
      { color:'#d73027', text:'< R$ 2.500' },
      { color:'#fc8d59', text:'R$ 2.500 – 4.000' },
      { color:'#fee08b', text:'R$ 4.000 – 6.000' },
      { color:'#91cf60', text:'R$ 6.000 – 10.000' },
      { color:'#1a9850', text:'> R$ 10.000' }
    ];
  } else {
    header = 'Quintil';
    items = [
      { color:'#d73027', text:'1º quintil' },
      { color:'#fc8d59', text:'2º quintil' },
      { color:'#fee08b', text:'3º quintil' },
      { color:'#91cf60', text:'4º quintil' },
      { color:'#1a9850', text:'5º quintil' }
    ];
  }

  const listHTML = `
    <h5>${header}</h5>
    <ul style="list-style:none;margin:.25rem 0 .5rem 0;padding:0;">
      ${items.map(it => `
        <li style="display:flex;align-items:center;gap:.5rem;margin:.15rem 0;font-size:.9rem;color:#444;">
          <span style="width:16px;height:12px;border-radius:3px;display:inline-block;border:1px solid rgba(0,0,0,.25);background-color:${it.color}"></span>
          <span>${it.text}</span>
        </li>`).join('')}
    </ul>
    <h6 class="legend-subtitle" style="margin-top:.5rem;border-top:1px solid #e5e7eb;padding-top:.5rem;">Faixa Populacional</h6>
    <div id="size-legend" class="size-legend"></div>
  `;

  legend.innerHTML = listHTML;
  legend.querySelector('#size-legend').innerHTML = buildSizeLegendSVGRow([
    { label: '≤ 200 mil',   value: 120_000 },
    { label: '200–500 mil', value: 350_000 },
    { label: '> 500 mil',   value: 800_000 }
  ]);
}

// ===================== Classificação (cores + subfiltro) =====================
function atualizarClassificacao() {
  const classificacao = filtroClassificacao.value;

  const novaCor = getMapPaintConfig(classificacao);
  map.setPaintProperty('populacao-circulos', 'circle-color', novaCor);
  updateLegend(classificacao);

  const subgrupoLabel  = document.querySelector('label[for="filtro-subgrupo"]');
  const subgrupoSelect = document.getElementById('filtro-subgrupo');
  subgrupoSelect.innerHTML = '<option value="todos">Todos</option>';

  switch (classificacao) {
    case 'decil':
      subgrupoLabel.textContent = 'Decil:';
      ['1','2','3','4','5','6','7','8','9','10'].forEach(v => subgrupoSelect.add(new Option(`${v}º decil`, v)));
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
      Object.entries(naturalOptions).forEach(([txt,val]) => subgrupoSelect.add(new Option(txt, val)));
      break;
    case 'quintil':
    default:
      subgrupoLabel.textContent = 'Quintil:';
      ['1','2','3','4','5'].forEach(v => subgrupoSelect.add(new Option(`${v}º quintil`, v)));
      break;
  }

  scheduleAtualizarMapa();
}

// ===================== Listeners =====================
document.getElementById('btn-limpar-filtros').addEventListener('click', async () => {
  filtroRegiao.value = 'todos';
  filtroRm.value = 'todos';
  filtroUf.value = 'todos';
  filtroMunicipio.value = 'todos';
  filtroPorte.value = 'todos';
  filtroSubgrupo.value = 'todos';
  filtroClassificacao.value = 'quintil';
  filtroModoCalculo.value = 'total';
  map.flyTo({ center: DEFAULT_VIEW.center, zoom: DEFAULT_VIEW.zoom, speed: 0.8, curve: 1.3 });
  await updateDependentFilters();
  atualizarClassificacao();
});

[filtroRegiao, filtroUf, filtroRm, filtroMunicipio, filtroPorte, filtroSubgrupo]
  .forEach(sel => sel.addEventListener('change', () => scheduleAtualizarMapa()));

filtroModoCalculo.addEventListener('change', atualizarClassificacao);
filtroClassificacao.addEventListener('change', atualizarClassificacao);

map.on("mouseenter", "populacao-circulos", () => { map.getCanvas().style.cursor = "pointer"; });
map.on("mouseleave", "populacao-circulos", () => { map.getCanvas().style.cursor = ""; });

// ===================== Download CSV =====================
async function downloadTableData() {
  const apiUrl = buildApiUrl('/api/dados-municipios/', {
    regiao: filtroRegiao.value,
    uf: filtroUf.value,
    municipio: filtroMunicipio.value,
    porte: filtroPorte.value,
    subgrupo: filtroSubgrupo.value,
    rm: filtroRm.value,
    classification: filtroClassificacao.value,
    calculation_mode: filtroModoCalculo.value
  });

  try {
    const response = await fetch(apiUrl);
    const geojsonData = await response.json();
    const features = geojsonData.features || [];

    if (!features.length) { alert("Não há dados de municípios para baixar com os filtros atuais."); return; }

    const columns = [
      { header:"Município", property:"name_muni_uf" },
      { header:"População 2023", property:"Populacao23" },
      { header:"Receita Per Capita 2023", property:"rc_23_pc" },
      { header:"Quantil Dinâmico", property:"dynamic_quantile" },
      { header:"Quintil Pré-Calculado", property:"quintil23_pre_calculado" },
      { header:"Decil Pré-Calculado", property:"decil23_pre_calculado" },
      { header:"Percentil Nacional", property:"percentil" },
      { header:"Percentil N", property:"percentil_n" },
      { header:"Cód. IBGE", property:"cod_ibge" }
    ];

    let csvContent = columns.map(c => `"${c.header}"`).join(";") + "\n";
    features.forEach(f => {
      const row = columns.map(c => {
        let v = f.properties[c.property];
        if (v === null || v === undefined) v = "N/D";
        if (typeof v === 'number') v = String(v).replace(".", ",");
        return `"${v}"`;
      }).join(";");
      csvContent += row + "\n";
    });

    const blob = new Blob(["\uFEFF" + csvContent], { type:"text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "dados_municipios_filtrados.csv";
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (err) {
    console.error("Erro ao baixar dados da tabela:", err);
    alert("Ocorreu um erro ao tentar baixar os dados. Por favor, tente novamente.");
  }
}
document.getElementById('download-table-btn').addEventListener('click', downloadTableData);
