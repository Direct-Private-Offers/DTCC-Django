from django.contrib import admin
from .models import XetraTrade, XetraOrder, XetraSettlement, XetraPosition, XetraMarketData


@admin.register(XetraTrade)
class XetraTradeAdmin(admin.ModelAdmin):
    list_display = ['xetra_trade_id', 'isin', 'buyer_account', 'seller_account', 'quantity', 'price', 'status', 'trade_date']
    list_filter = ['status', 'currency', 'trade_date']
    search_fields = ['xetra_trade_id', 'isin', 'xetra_reference']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(XetraOrder)
class XetraOrderAdmin(admin.ModelAdmin):
    list_display = ['xetra_order_id', 'isin', 'account', 'side', 'order_type', 'quantity', 'price', 'status', 'created_at']
    list_filter = ['status', 'side', 'order_type']
    search_fields = ['xetra_order_id', 'isin', 'account']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(XetraSettlement)
class XetraSettlementAdmin(admin.ModelAdmin):
    list_display = ['settlement_id', 'isin', 'buyer_account', 'seller_account', 'quantity', 'amount', 'status', 'value_date']
    list_filter = ['status', 'currency', 'value_date']
    search_fields = ['settlement_id', 'isin', 'xetra_instruction_id']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(XetraPosition)
class XetraPositionAdmin(admin.ModelAdmin):
    list_display = ['account', 'isin', 'settled_quantity', 'pending_quantity', 'as_of', 'last_reconciled']
    list_filter = ['as_of']
    search_fields = ['account', 'isin']
    readonly_fields = ['id']


@admin.register(XetraMarketData)
class XetraMarketDataAdmin(admin.ModelAdmin):
    list_display = ['isin', 'bid_price', 'ask_price', 'last_price', 'volume', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['isin']
    readonly_fields = ['id']
