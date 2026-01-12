from django.urls import path
from .views import (
    XetraOrderView, XetraOrderDetailView, XetraTradeView,
    XetraSettlementView, XetraPositionView, XetraMarketDataView
)

app_name = 'xetra'

urlpatterns = [
    path('orders', XetraOrderView.as_view(), name='xetra-orders'),
    path('orders/<uuid:order_id>', XetraOrderDetailView.as_view(), name='xetra-order-detail'),
    path('trades', XetraTradeView.as_view(), name='xetra-trades'),
    path('settlements', XetraSettlementView.as_view(), name='xetra-settlements'),
    path('positions', XetraPositionView.as_view(), name='xetra-positions'),
    path('market-data', XetraMarketDataView.as_view(), name='xetra-market-data'),
]
