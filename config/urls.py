from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # Landing IFEM como HOME do projeto
    path("", include("ifem.urls")),

    # Análise Gráfica (antiga home)
    path("analise/", include("home.urls")),

    # Análise Municipal (mapa)
    path("mapa/", include("map.urls")),

    # Análise Agregada (detail)
    path("", include("detail.urls")),
]
