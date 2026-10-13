"""Verificação de sistema: comentário de template que vaza na página.

No Django, `{# ... #}` é comentário de UMA linha. Se o fechamento `#}` estiver
em outra linha, nada é tratado como comentário: o texto aparece na página para
quem visita, e qualquer `{{ variavel }}` dentro dele é renderizado. Já vazou em
produção mais de uma vez (agregado e município).

Esta verificação roda em todo `manage.py check`, `runserver` e `migrate`. No
deploy, o `migrate` acontece antes de o container novo subir (deploy.sh):
um template com o problema derruba o deploy e o site anterior continua no ar.

Correção: comentário de mais de uma linha usa {% comment %} ... {% endcomment %}.
"""
import re
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.checks import Error, Tags, register

# `{#` cujo `#}` não está na mesma linha.
_ABERTO = re.compile(r'\{#(?:(?!#\}).)*$', re.MULTILINE)


def _pastas_de_templates():
    for config in settings.TEMPLATES:
        for pasta in config.get('DIRS', []):
            yield Path(pasta)
    for app in apps.get_app_configs():
        pasta = Path(app.path) / 'templates'
        if pasta.is_dir():
            yield pasta


@register(Tags.templates)
def comentario_multilinha(app_configs, **kwargs):
    """Acusa `{# #}` que atravessa linhas em qualquer template do projeto."""
    erros = []
    vistos = set()
    for pasta in _pastas_de_templates():
        for arquivo in pasta.rglob('*.html'):
            if arquivo in vistos:
                continue
            vistos.add(arquivo)
            try:
                texto = arquivo.read_text(encoding='utf-8')
            except (OSError, UnicodeDecodeError) as erro:
                erros.append(Error(
                    f'Não foi possível ler o template {arquivo}: {erro}',
                    id='ifem.E002',
                ))
                continue
            for m in _ABERTO.finditer(texto):
                linha = texto.count('\n', 0, m.start()) + 1
                erros.append(Error(
                    f'Comentário {{# #}} de várias linhas em {arquivo}:{linha}: '
                    'esse texto apareceria na página.',
                    hint='Use {% comment %} ... {% endcomment %} para comentários de mais de uma linha.',
                    id='ifem.E001',
                ))
    return erros
