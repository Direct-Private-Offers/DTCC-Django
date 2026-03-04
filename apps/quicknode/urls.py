from django.urls import path
from .views import QuickNodeHealth, QuickNodeContract, QuickNodeSupply, QuickNodeTx, QuickNodeEvents

urlpatterns = [
    path('health', QuickNodeHealth.as_view(), name='quicknode-health'),
    path('contract/<str:address>', QuickNodeContract.as_view(), name='quicknode-contract'),
    path('supply/<str:address>', QuickNodeSupply.as_view(), name='quicknode-supply'),
    path('tx/<str:txhash>', QuickNodeTx.as_view(), name='quicknode-tx'),
    path('events/<str:address>', QuickNodeEvents.as_view(), name='quicknode-events'),
]
