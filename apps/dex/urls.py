from django.urls import path
from .views import (
    WalletView, WalletBalanceView,
    OrderView, OrderDetailView, OrderBookView,
    SwapView, SwapDetailView,
    TradeView
)

urlpatterns = [
    # Wallets
    path('wallets', WalletView.as_view(), name='dex-wallets'),
    path('wallets/<str:address>/balance', WalletBalanceView.as_view(), name='dex-wallet-balance'),
    
    # Orders
    path('orders', OrderView.as_view(), name='dex-orders'),
    path('orders/<uuid:pk>', OrderDetailView.as_view(), name='dex-order-detail'),
    path('orders/<uuid:pk>/cancel', OrderDetailView.as_view(), name='dex-order-cancel'),
    path('orderbook', OrderBookView.as_view(), name='dex-orderbook'),
    
    # Swaps
    path('swaps', SwapView.as_view(), name='dex-swaps'),
    path('swaps/<uuid:pk>', SwapDetailView.as_view(), name='dex-swap-detail'),
    
    # Trades
    path('trades', TradeView.as_view(), name='dex-trades'),
]

