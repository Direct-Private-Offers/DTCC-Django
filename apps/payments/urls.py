"""
Payment App URLs
"""
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Webhook endpoint for NEO Bank/Bill Bitts notifications
    path('webhooks/neo-payment/', views.neo_bank_webhook, name='neo_webhook'),
    
    # API endpoint for front-end to initiate trades
    path('api/execute-trade/', views.execute_trade, name='execute_trade'),
]
