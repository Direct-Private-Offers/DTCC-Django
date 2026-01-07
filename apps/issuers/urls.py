"""
Issuer URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IssuerViewSet, IssuerDocumentViewSet
from .webhooks import bd_form_submission

app_name = 'issuers'

# REST API Router
router = DefaultRouter()
router.register(r'issuers', IssuerViewSet, basename='issuer')
router.register(r'documents', IssuerDocumentViewSet, basename='document')

urlpatterns = [
    path('', include(router.urls)),
    
    # Webhooks
    path('webhooks/bd-form-submission/', bd_form_submission, name='bd-webhook'),
]
