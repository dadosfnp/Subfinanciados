# [NOVO ARQUIVO] Criação das rotas para o app ifem (Landing Page)
from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
]