# Plano: Área de Análise de Crescimento (2000 vs 2024) no Mapa
Data: 2026-06-02
Branch: feat/mapa-crescimento (a partir de infra/dockerizar-ifem)

## Goal
Adicionar ao mapa um "modo de análise" de crescimento 2000→2024, colorindo as bolas por:
taxa de crescimento da população, taxa de crescimento da receita per capita, e variação de
posição (ranking nacional / quintil / decil / percentil de receita por habitante).

## Decisões (com Pedro)
- UI: **modo de análise dedicado** — toggle "Receita atual" ↔ "Crescimento 2000–2024";
  no modo crescimento, aparece um seletor de métrica.
- Receita: crescimento **per capita** (rc_00_pc → rc_24_pc).
- "Coroplético" = bolas coloridas (o mapa só tem pontos, não polígonos).
- Escala de cor **divergente**: vermelho (queda) → neutro → verde (crescimento/melhora).
- Sem migração: tudo derivado de campos existentes do Municipio.

## Métricas do modo Crescimento (select único)
1. Crescimento da população (%) = (populacao24-populacao00)/populacao00*100
2. Crescimento da receita p/c (%) = (rc_24_pc-rc_00_pc)/rc_00_pc*100
3. Variação no ranking nacional = rank_nacional_00 - rank_nacional (positivo = subiu)
4. Variação no quintil = nº(quintil24) - nº(quintil00)
5. Variação no decil = nº(decil24) - nº(decil00)
6. Variação no percentil = percentil24_n - percentil00_n

## Scope
### Modificar
- map/views.py — API geojson: parâmetro `analise=crescimento` adiciona campos calculados + bases p/ popup.
- map/static/map/js/script.js — estado de modo, paint divergente, legenda, popup 2000×2024, fetch.
- map/templates/map/map.html — seletor "Modo de análise" + seletor de métrica de crescimento.
- map/static/map/css/style.css — ajustes de legenda/UI do novo modo (se necessário).
- (após editar JS/CSS source) collectstatic regenera no entrypoint — não versionar staticfiles.

### NÃO tocar
- Models/migrations (sem schema novo). Modo "Receita atual" deve permanecer idêntico.

## Subtasks
- [ ] 1. Backend: estender municipios_geojson_api com `analise=crescimento` (campos: cresc_pop_pct,
      cresc_rcpc_pct, var_rank, var_quintil, var_decil, var_percentil + bases: populacao00, rc_00_pc,
      quintil00, decil00, percentil00_n, rank_nacional, rank_nacional_00, total_nacional).
      Helpers p/ extrair nº de "Xº quintil/decil" e divisão segura.
- [ ] 2. HTML: bloco "Modo de análise" (Receita atual | Crescimento) + select "Métrica de crescimento"
      (oculto no modo receita).
- [ ] 3. JS: estado modoAnalise/metricaCrescimento; fetch com analise; getCrescimentoPaint(metrica)
      com escala divergente (step); updateLegend p/ crescimento; popup 2000×2024.
- [ ] 4. CSS: estilos da legenda divergente / seletor de modo.
- [ ] 5. Validar: build Docker local + smoke (manage.py check) + subir e conferir os 4 endpoints/modos.
- [ ] 6. Commit semântico + push; deploy no droplet (pull+rebuild+up) e validar via túnel.

## Risks & Open Questions
- Divisão por zero / nulos em pop00/rc_00_pc → tratar (retornar null e pintar como "sem dado" cinza).
- quintil/decil como string "Xº quintil" → parsear nº com regex; se nulo, variação = null.
- Ranking: rank menor = melhor; "subir" = rank_00 - rank_24 positivo. Deixar claro na legenda.
- Payload: campos extras só no modo crescimento (analise=crescimento), mantém modo receita leve. Gzip ativo.
- Popup: precisa ramificar conteúdo por modo sem quebrar o popup atual.

## Definition of Done
- [ ] Modo "Receita atual" inalterado.
- [ ] Modo "Crescimento" com as 6 métricas, escala divergente, legenda e popup 2000×2024 coerentes.
- [ ] Sem migração; build OK; rodando no droplet e validado por túnel.
- [ ] Código comentado; plano atualizado.
