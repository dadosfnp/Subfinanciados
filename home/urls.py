from django.urls import path
from . import views

urlpatterns = [
    path('',views.home, name='home'),
    path('api/get-dependent-filters/', views.api_get_dependent_filters, name='api_get_dependent_filters'), 
    path('api/dashboard-data/', views.api_get_dashboard_data, name='dashboard_data_api'), 

]