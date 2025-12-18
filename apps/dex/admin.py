from django.contrib import admin
from .models import Wallet, Order, Swap, Trade


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['address', 'user', 'network', 'is_active', 'created_at']
    list_filter = ['network', 'is_active', 'created_at']
    search_fields = ['address', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'isin', 'order_type', 'quantity', 'filled_quantity', 'price_per_unit', 'status', 'created_at']
    list_filter = ['order_type', 'status', 'isin', 'created_at']
    search_fields = ['isin', 'wallet__address', 'tx_hash']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(Swap)
class SwapAdmin(admin.ModelAdmin):
    list_display = ['id', 'token_from', 'token_to', 'amount_from', 'amount_to', 'status', 'is_p2p', 'created_at']
    list_filter = ['status', 'is_p2p', 'created_at']
    search_fields = ['token_from', 'token_to', 'tx_hash_from', 'tx_hash_to']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ['id', 'isin', 'quantity', 'price_per_unit', 'total_value', 'created_at']
    list_filter = ['isin', 'created_at']
    search_fields = ['isin', 'tx_hash']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'

