from django.urls import path
from .views import (
    InvestorProfileView, KYCDocumentView,
    AMLCheckView, AuditLogView
)

urlpatterns = [
    path('profile', InvestorProfileView.as_view(), name='compliance-profile'),
    path('documents', KYCDocumentView.as_view(), name='compliance-documents'),
    path('aml-checks', AMLCheckView.as_view(), name='compliance-aml-checks'),
    path('audit-logs', AuditLogView.as_view(), name='compliance-audit-logs'),
]

