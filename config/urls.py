from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # 1. Landing do IFEM como home
    path("", include("ifem.urls")),

    # 3. Análise Gráfica
    path("analise/", include("home.urls")),

    # 4. Análise Municipal
    path("mapa/", include("map.urls")),

    # 5. Análise Agregada
    path("analise-municipal/", include("detail.urls")),
]
