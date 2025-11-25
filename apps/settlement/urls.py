from django.urls import path
from .views import SettlementView

urlpatterns = [
    path('', SettlementView.as_view(), name='settlement-create'),           # POST /api/settlement
    path('<uuid:pk>/', SettlementView.as_view(), name='settlement-detail'), # GET /api/settlement/<id>
]
