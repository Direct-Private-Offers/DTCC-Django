from django.urls import path
from .views import IssuanceView
from .event_views import EventIngestionView


urlpatterns = [
    path('', IssuanceView.as_view(), name='issuance'),
    path('events/ingest', EventIngestionView.as_view(), name='event-ingestion'),
]
