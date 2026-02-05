from django.contrib import admin
from .models import Noticia 

@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tag', 'data') # Colunas que aparecem na lista
    search_fields = ('titulo', 'tag')        # Barra de pesquisa
    list_filter = ('tag', 'data')            # Filtros laterais