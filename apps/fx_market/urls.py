from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FxConversionViewSet, CrossPlatformSettlementViewSet, TokenFlowViewSet

router = DefaultRouter()
router.register(r'conversions', FxConversionViewSet, basename='fx-conversion')
router.register(r'settlements', CrossPlatformSettlementViewSet, basename='cross-platform-settlement')
router.register(r'token-flows', TokenFlowViewSet, basename='token-flow')

urlpatterns = [
    path('', include(router.urls)),
]

