# Projeto Subfinanciados - Documentação de Desenvolvimento (Conductor)

Este arquivo serve como guia de contexto para o desenvolvimento do projeto **Subfinanciados**, um sistema Django para análise de dados fiscais e populacionais de municípios brasileiros.

## 🚀 Visão Geral do Projeto
- **Framework:** Django 5.2.x
- **Frontend:** Templates Django, CSS Vanilla, Mapbox (para o mapa).
- **Backend:** Python com Django Rest Framework (DRF).
- **Dados:** Processamento de planilhas Excel (`base_datas`) para o banco de dados SQLite.

## 🛠 Decisões de Arquitetura e Configurações
- **Arquivos Estáticos:** Configurado para usar o `WhiteNoise` com compressão (`CompressedManifestStaticFilesStorage`).
- **Produção (DEBUG=False):** Para o site funcionar corretamente com `DEBUG=False`, é necessário rodar `python manage.py collectstatic`.
- **Media Files:** Configurados em `/media/` para lidar com uploads de notícias/imagens.
- **UI/UX - Sticky Header:** Implementado cabeçalho fixo na página de detalhes do município (`sticky_header.css` e lógica em `script_mun.js`).

## 📁 Estrutura de Apps
- `home`: Dashboard principal e filtros.
- `detail`: Análise detalhada por município ou conjunto.
- `map`: Visualização geográfica dos dados.
- `ifem`: Landing page e busca simples.

## 📝 Tarefas Pendentes / Próximos Passos
- [x] Implementar Sticky Header no detalhe do município.
- [ ] Validar carregamento de dados das novas planilhas em `base_datas`.
- [ ] Testar a interface com o novo backend de estáticos em um ambiente de homologação.
- [ ] Otimizar as queries de filtragem de municípios (APIs de dashboard).

---
*Atualizado em: 11 de março de 2026 por Gemini CLI (via Conductor extension)*
