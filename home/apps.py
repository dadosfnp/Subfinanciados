from django.apps import AppConfig


class HomeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'home'

    def ready(self):
        # Registra as verificacoes de sistema do projeto (ver home/checks.py).
        from . import checks  # noqa: F401

