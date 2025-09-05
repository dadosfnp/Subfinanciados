<<<<<<< HEAD
from django.urls import path, include
from rest_framework.routers import DefaultRouter    
from . import views

router = DefaultRouter()
router.register(r'municipios', views.MunicipioAPIView)

urlpatterns = [
    path('municipio/<str:cod_ibge>/', views.municipio_detalhe_view, name='municipio_detalhe'),
    path('api/', include(router.urls)),

=======
from django.urls import path
from . import views


app_name = 'detatil'

urlpatterns = [
    path('municipio/<int:municipio_id>/', views.municipio_detalhe_view, name='municipio_detalhe'),
    path('api/dados-detalhados/', views.municipio_details_api, name='municipio_details_api'),
    path('analise-municipal/', views.conjunto_detalhe_view, name='detalhes_conjunto'),
    path('api/fiscal-details/', views.conjunto_fiscal_api, name='conjunto_fiscal_api'),
    path('api/conjunto-chart-data/', views.conjunto_chart_api, name='conjunto_chart_api'),

>>>>>>> origin/main
]