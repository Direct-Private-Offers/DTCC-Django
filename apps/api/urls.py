"""
URL patterns for system endpoints.
"""
from django.urls import path
from .views import HealthView, ReadinessView, MetricsView

urlpatterns = [
    path('health', HealthView.as_view(), name='health'),
    path('ready', ReadinessView.as_view(), name='ready'),
    path('metrics', MetricsView.as_view(), name='metrics'),
]

