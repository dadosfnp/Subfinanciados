from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
# Importe as views do app 'home'
from home import views 

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Rota da Landing Page (Raiz do site) -> Chama a view index
    path('', views.index, name='index'),

    # Rota do Dashboard (Home/Análise) -> Chama a view home
    path('analise/', views.home, name='home'),

    # Rotas de API
    path('api/dependent-filters/', views.api_get_dependent_filters, name='api_get_dependent_filters'),
    path('api/dashboard-data/', views.api_get_dashboard_data, name='api_get_dashboard_data'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)