from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from home import views as home_views
from detail import views as detail_views
from map import views as map_views
from ifem import views as ifem_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- PÁGINAS PRINCIPAIS ---
    path('', home_views.index, name='index'),
    path('analise/', home_views.home, name='home'),
    path('mapa/', map_views.map, name='mapa'),
    path('analise-municipal/', detail_views.conjunto_detalhe_view, name='analise_municipal'),
    path('municipio/<str:municipio_id>/', detail_views.municipio_detalhe_view, name='municipio_detalhe'),

    # --- APIS: HOME ---
    path('api/get-dependent-filters/', home_views.api_get_dependent_filters, name='api_get_dependent_filters'),
    path('api/dashboard-data/', home_views.api_get_dashboard_data, name='api_get_dashboard_data'),

    # --- APIS: DETAIL ---
    path('api/dados-detalhados/', detail_views.municipio_details_api, name='municipio_details_api'),
    path('api/fiscal-details/', detail_views.conjunto_fiscal_api, name='conjunto_fiscal_api'),
    path('api/conjunto-chart-data/', detail_views.conjunto_chart_api, name='conjunto_chart_api'),
    path('api/conjunto-data/', detail_views.conjunto_data_api, name='conjunto_data_api'),

    # --- APIS: MAPA ---
    path('api/dados-municipios/', map_views.municipios_geojson_api, name='municipios_geojson_api'),

    # --- APIS: LANDING PAGE ---
    path('api/busca-municipio/', ifem_views.busca_municipio_simples_api, name='busca_municipio_api'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)