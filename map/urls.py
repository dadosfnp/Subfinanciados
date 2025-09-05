from django.urls import path
from . import views

urlpatterns = [
    path('mapa',views.map, name='home'),
    path('api/dados-municipios/', views.municipios_geojson_api, name='api_dados_municipios'), # API para o mapa
    #path('api/get-dependent-filters/', views.api_get_dependent_filters, name='api_get_dependent_filters'), # Nova API para os filtros
    #path('api/dashboard-data/', views.dados_dashboard_api, name='dashboard_data_api'), 

]