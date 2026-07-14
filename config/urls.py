from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from home import views as home_views
from detail_mun import views as detail_mun_views
from detail_agg import views as detail_agg_views
from map import views as map_views
from ifem import views as ifem_views
from metodologia import views as metodologia_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin', RedirectView.as_view(url='/admin/', permanent=True)),


    # --- PÁGINAS PRINCIPAIS ---
    path('', home_views.index, name='index'),
    path('analise/', home_views.home, name='home'),
    path('mapa/', map_views.map, name='mapa'),
    path('selecionar-municipio/', detail_mun_views.selecionar_municipio_view, name='selecionar_municipio'), # NOVA ROTA AQUI
    path('analise-municipal/', detail_agg_views.conjunto_detalhe_view, name='analise_municipal'),
    path('municipio/<str:municipio_id>/', detail_mun_views.municipio_detalhe_view, name='municipio_detalhe'),
    path('metodologia/', metodologia_views.metodologia_page, name='metodologia'),

    # --- APIS: HOME ---
    path('api/get-dependent-filters/', home_views.api_get_dependent_filters, name='api_get_dependent_filters'),
    path('api/debug-status/', home_views.api_debug_status, name='debug_status'),
    path('api/dashboard-data/', home_views.api_get_dashboard_data, name='api_get_dashboard_data'),

    # --- APIS: DETAIL ---
    path('api/dados-detalhados/', detail_mun_views.municipio_details_api, name='municipio_details_api'),
    path('api/fiscal-details/', detail_agg_views.conjunto_fiscal_api, name='conjunto_fiscal_api'),
    path('api/conjunto-chart-data/', detail_agg_views.conjunto_chart_api, name='conjunto_chart_api'),
    path('api/conjunto-data/', detail_agg_views.conjunto_data_api, name='conjunto_data_api'),

    # --- APIS: MAPA ---
    path('api/dados-municipios/', map_views.municipios_geojson_api, name='municipios_geojson_api'),

    # --- APIS: LANDING PAGE ---
    path('api/busca-municipio/', ifem_views.busca_municipio_simples_api, name='busca_municipio_api'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)