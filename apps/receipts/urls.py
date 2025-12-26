from django.urls import path
from .views import ReceiptView, ReceiptDetailView

app_name = 'receipts'

urlpatterns = [
    path('generate', ReceiptView.as_view(), name='receipts-generate'),
    path('', ReceiptView.as_view(), name='receipts-list'),
    path('<uuid:receipt_id>', ReceiptDetailView.as_view(), name='receipt-detail'),
    path('<uuid:receipt_id>/download', ReceiptDetailView.as_view(), name='receipt-download'),
]
