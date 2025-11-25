from django.urls import path
from .views import EuroclearWebhook, ClearstreamWebhook, ChainlinkWebhook

urlpatterns = [
    path('euroclear', EuroclearWebhook.as_view(), name='wh-euroclear'),
    path('clearstream', ClearstreamWebhook.as_view(), name='wh-clearstream'),
    path('chainlink', ChainlinkWebhook.as_view(), name='wh-chainlink'),
]
