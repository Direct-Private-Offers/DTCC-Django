from django.contrib import admin
from .models import FxConversion, CrossPlatformSettlement, TokenFlow


@admin.register(FxConversion)
class FxConversionAdmin(admin.ModelAdmin):
    list_display = ['user', 'conversion_type', 'status', 'source_amount', 'source_currency', 'target_amount', 'created_at']
    list_filter = ['conversion_type', 'status', 'created_at']
    search_fields = ['user__username', 'fx_transaction_id', 'blockchain_tx_hash']


@admin.register(CrossPlatformSettlement)
class CrossPlatformSettlementAdmin(admin.ModelAdmin):
    list_display = ['dpo_settlement_id', 'fx_settlement_id', 'status', 'reconciled', 'created_at']
    list_filter = ['status', 'reconciled', 'created_at']
    search_fields = ['dpo_settlement_id', 'fx_settlement_id', 'isin']


@admin.register(TokenFlow)
class TokenFlowAdmin(admin.ModelAdmin):
    list_display = ['user', 'flow_direction', 'status', 'token_address', 'amount', 'created_at']
    list_filter = ['flow_direction', 'status', 'created_at']
    search_fields = ['user__username', 'blockchain_tx_hash', 'fx_transaction_id']

