from django.urls import path
from . import views

app_name = "map"

urlpatterns = [
    path("", views.map, name="mapa"),
    path("api/dados-municipios/", views.municipios_geojson_api, name="api_dados_municipios"),
]
