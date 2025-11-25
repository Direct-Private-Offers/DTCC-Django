from django.urls import path
from .views import IssuanceView


urlpatterns = [
    path('', IssuanceView.as_view(), name='issuance'),
]
