from django.urls import path
from .views import NotificationView, NotificationPreferenceView

urlpatterns = [
    path('', NotificationView.as_view(), name='notifications'),
    path('preferences', NotificationPreferenceView.as_view(), name='notification-preferences'),
]

