from django.contrib import admin
from .models import Receipt


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ['receipt_id', 'receipt_type', 'investor', 'isin', 'quantity', 'amount', 'currency', 'created_at']
    list_filter = ['receipt_type', 'currency', 'created_at']
    search_fields = ['receipt_id', 'transaction_id', 'isin', 'investor__username']
    readonly_fields = ['id', 'receipt_id', 'created_at']
    fields = ['receipt_id', 'receipt_type', 'investor', 'transaction_id', 'isin', 'quantity', 'amount', 'currency', 'pdf_file', 'metadata', 'created_at']
