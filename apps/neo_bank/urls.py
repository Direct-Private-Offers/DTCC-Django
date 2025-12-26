from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NeoBankAccountLinkViewSet, KycSyncStatusViewSet, TransactionSyncViewSet

router = DefaultRouter()
router.register(r'accounts', NeoBankAccountLinkViewSet, basename='neo-bank-account')
router.register(r'kyc-sync', KycSyncStatusViewSet, basename='kyc-sync')
router.register(r'transaction-sync', TransactionSyncViewSet, basename='transaction-sync')

urlpatterns = [
    path('', include(router.urls)),
]

