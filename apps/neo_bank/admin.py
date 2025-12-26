from django.contrib import admin
from .models import NeoBankAccountLink, KycSyncStatus, TransactionSync


@admin.register(NeoBankAccountLink)
class NeoBankAccountLinkAdmin(admin.ModelAdmin):
    list_display = ['user', 'neo_account_id', 'is_active', 'linked_at', 'last_synced']
    list_filter = ['is_active', 'linked_at']
    search_fields = ['user__username', 'neo_account_id']


@admin.register(KycSyncStatus)
class KycSyncStatusAdmin(admin.ModelAdmin):
    list_display = ['user', 'sync_status', 'last_synced', 'created_at']
    list_filter = ['sync_status', 'created_at']
    search_fields = ['user__username']


@admin.register(TransactionSync)
class TransactionSyncAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'user', 'sync_status', 'synced_at', 'neo_transaction_id']
    list_filter = ['sync_status', 'synced_at']
    search_fields = ['transaction_id', 'user__username', 'neo_transaction_id']

