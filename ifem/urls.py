from django.urls import path
from . import views

app_name = "ifem"

urlpatterns = [
    path("", views.ifem_landing, name="landing"),
]
