from django.urls import path
from .views import DerivativesView


urlpatterns = [
    path('', DerivativesView.as_view(), name='derivatives'),
]
