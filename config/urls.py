from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from apps.core.healthcheck import healthcheck

urlpatterns = [
    path('admin/', admin.site.urls),
    # Healthcheck (no auth required)
    path('api/health', healthcheck, name='healthcheck'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    # Auth (JWT)
    path('api/auth/token', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/issuance/', include('apps.issuance.urls')),
    path('api/derivatives/', include('apps.derivatives.urls')),
    path('api/settlement/', include('apps.settlement.urls')),
    path('api/corporate-actions/', include('apps.corporate_actions.urls')),
    path('api/clearstream/', include('apps.clearstream.urls')),
    path('api/webhooks/', include('apps.webhooks.urls')),
    path('api/dex/', include('apps.dex.urls')),
    path('api/compliance/', include('apps.compliance.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('api/storage/', include('apps.storage.urls')),
    path('api/xetra/', include('apps.xetra.urls')),
    path('api/receipts/', include('apps.receipts.urls')),
    path('api/neo-bank/', include('apps.neo_bank.urls')),
    path('api/fx-market/', include('apps.fx_market.urls')),
    path('api/', include('apps.api.urls')),
    # Issuer Onboarding (BD Integration)
    path('api/', include('apps.issuers.urls')),
    # Bill Bitts / NEO Bank Payment Integration
    path('', include('apps.payments.urls')),
]
