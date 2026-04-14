from django.contrib import admin
from django.utils.html import format_html
from .models import Noticia


@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tag', 'data', 'preview_imagem')
    search_fields = ('titulo', 'tag')
    list_filter = ('tag', 'data')
    fields = ('titulo', 'data', 'tag', 'imagem_url', 'link')

    def preview_imagem(self, obj):
        if not obj.imagem_embed_url:
            return '—'
        return format_html(
            '<img src="{}" style="height:40px;border-radius:4px;" referrerpolicy="no-referrer"/>',
            obj.imagem_embed_url,
        )
    preview_imagem.short_description = 'Capa'