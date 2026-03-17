from django.urls import path
from . import views


app_name = 'detail_agg'

urlpatterns = [
    path('api/fiscal-details/', views.conjunto_fiscal_api, name='conjunto_fiscal_api'),
    path('api/conjunto-chart-data/', views.conjunto_chart_api, name='conjunto_chart_api'),
    path('api/conjunto-data/', views.conjunto_data_api, name='conjunto_data_api'),


]