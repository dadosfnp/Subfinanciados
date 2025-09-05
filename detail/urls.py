from django.urls import path, include
from rest_framework.routers import DefaultRouter    
from . import views

router = DefaultRouter()
router.register(r'municipios', views.MunicipioAPIView)

urlpatterns = [
    path('municipio/<str:cod_ibge>/', views.municipio_detalhe_view, name='municipio_detalhe'),
    path('api/', include(router.urls)),

]