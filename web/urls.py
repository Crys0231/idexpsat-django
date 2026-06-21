from django.urls import path
from . import views

urlpatterns = [
    path('importacao/', views.importacao_view, name='importacao'),
    path('clientes/', views.crm_clientes_view, name='crm_clientes'),
    path('clientes/<uuid:pesquisa_id>/tratado/', views.alternar_tratado_view, name='alternar_tratado'),
]