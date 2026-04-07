from django.urls import path
from .views import (
    TradingReportView, SettlementReportView,
    IssuanceReportView, UnifiedReportingView, ReportingStatusView
)

urlpatterns = [
    path('trading', TradingReportView.as_view(), name='report-trading'),
    path('settlement', SettlementReportView.as_view(), name='report-settlement'),
    path('issuance', IssuanceReportView.as_view(), name='report-issuance'),
    path('unified', UnifiedReportingView.as_view(), name='report-unified'),
    path('status', ReportingStatusView.as_view(), name='report-status'),
]
