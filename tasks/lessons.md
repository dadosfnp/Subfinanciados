# Lessons — Subfinanciados

Registro de padrões aprendidos com correções. Ler no início de tarefas de infra/deploy.

## Deploy / Infra

### Confirmar a branch ativa do droplet antes de commitar/deployar (2026-07-10)
- **Contexto**: ao publicar `ifem.fnp.org.br`, commitei o `SECURE_PROXY_SSL_HEADER` na branch
  `infra/dockerizar-ifem` porque o runbook de junho a indicava como a do droplet.
- **Realidade**: o droplet havia migrado para `feat/pagina-metodologia`. O commit foi para uma
  branch que o droplet não usa; o rebuild ligou `SECURE_SSL_REDIRECT=True` sem o header no código
  → **loop de redirect** (site fora do ar por ~1 min).
- **Regra**: antes de qualquer commit/deploy que dependa da branch do servidor, rodar
  `git branch --show-current && git log --oneline -1` **no droplet** e commitar exatamente em cima
  desse commit. Não confiar em runbooks antigos para saber a branch ativa.
- **Salvaguarda**: em deploys que ativam redirect/flag de segurança condicional, validar no servidor
  que a dependência está no código antes de ligar a flag. Ex.: só setar `SECURE_SSL_REDIRECT=True`
  se `grep -q SECURE_PROXY_SSL_HEADER config/settings.py` casar.
- **Rollback rápido que funcionou**: reverter a env var (`SECURE_SSL_REDIRECT=False`) +
  `docker compose up -d --force-recreate` restaura o estado anterior sem rebuild.
