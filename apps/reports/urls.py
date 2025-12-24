from django.urls import path
from .views import (
    TradingReportView, SettlementReportView,
    IssuanceReportView, ReconciliationReportView
)

urlpatterns = [
    path('trading', TradingReportView.as_view(), name='report-trading'),
    path('settlement', SettlementReportView.as_view(), name='report-settlement'),
    path('issuance', IssuanceReportView.as_view(), name='report-issuance'),
    path('reconciliation', ReconciliationReportView.as_view(), name='report-reconciliation'),
]

