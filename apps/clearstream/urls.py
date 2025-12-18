from django.urls import path
from .views import (
    ClearstreamAccountView,
    PositionsView,
    InstructionsView,
    ClearstreamSettlementView,
)

urlpatterns = [
    path('accounts', ClearstreamAccountView.as_view(), name='cs-accounts'),
    path('positions/<str:account>', PositionsView.as_view(), name='cs-positions'),
    path('instructions', InstructionsView.as_view(), name='cs-instructions'),
    path('settlement', ClearstreamSettlementView.as_view(), name='cs-settlement-create'),
    path('settlement/<uuid:pk>', ClearstreamSettlementView.as_view(), name='cs-settlement-detail'),
]
