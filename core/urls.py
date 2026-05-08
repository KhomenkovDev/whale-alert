from django.urls import path
from core import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/transactions/', views.api_transactions, name='api_transactions'),
    path('api/stats/', views.api_stats, name='api_stats'),
    path('api/report/<int:pk>/', views.api_whale_report, name='api_whale_report'),
]
