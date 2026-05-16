from django.urls import path
from . import views

urlpatterns = [
    path('importacao/', views.importacao_view, name='importacao'),
]