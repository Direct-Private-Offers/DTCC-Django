"""
Payment App Admin Configuration
"""
from django.contrib import admin
from .models import PaymentProfile, Transaction


@admin.register(PaymentProfile)
class PaymentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'cprn_number', 'web3_wallet_address', 'neo_balance', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['user__username', 'user__email', 'cprn_number', 'web3_wallet_address']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Info', {
            'fields': ('user',)
        }),
        ('Payment Details', {
            'fields': ('cprn_number', 'neo_balance', 'is_verified')
        }),
        ('Web3 Integration', {
            'fields': ('web3_wallet_address',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'profile', 'amount', 'currency', 'status', 'nft_name', 'created_at']
    list_filter = ['status', 'currency', 'created_at']
    search_fields = ['transaction_id', 'profile__user__username', 'nft_id', 'nft_name']
    readonly_fields = ['created_at', 'settled_at', 'webhook_payload']
    
    fieldsets = (
        ('Transaction Info', {
            'fields': ('transaction_id', 'profile', 'amount', 'currency', 'status')
        }),
        ('NFT/Asset Details', {
            'fields': ('nft_id', 'nft_name')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'settled_at')
        }),
        ('Raw Data', {
            'fields': ('webhook_payload',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Transactions should only be created via webhooks
        return False
