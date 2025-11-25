from django.urls import path
from .views import CorporateActionsView

urlpatterns = [
    path('', CorporateActionsView.as_view(), name='corporate-actions'),
]
