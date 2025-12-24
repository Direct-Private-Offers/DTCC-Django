from django.urls import path
from .views import EuroclearWebhook, ClearstreamWebhook, ChainlinkWebhook
from .outbound_views import (
    OutboundWebhookView, OutboundWebhookDeliveryView, OutboundWebhookRetryView
)

urlpatterns = [
    # Inbound webhooks
    path('euroclear', EuroclearWebhook.as_view(), name='wh-euroclear'),
    path('clearstream', ClearstreamWebhook.as_view(), name='wh-clearstream'),
    path('chainlink', ChainlinkWebhook.as_view(), name='wh-chainlink'),
    # Outbound webhooks
    path('outbound', OutboundWebhookView.as_view(), name='webhook-outbound-list'),
    path('outbound/<uuid:webhook_id>', OutboundWebhookView.as_view(), name='webhook-outbound-detail'),
    path('outbound/<uuid:webhook_id>/deliveries', OutboundWebhookDeliveryView.as_view(), name='webhook-deliveries'),
    path('outbound/deliveries/<uuid:delivery_id>/retry', OutboundWebhookRetryView.as_view(), name='webhook-retry'),
]
