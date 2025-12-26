from rest_framework import serializers
from .models import NeoBankAccountLink, KycSyncStatus, TransactionSync


class NeoBankAccountLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = NeoBankAccountLink
        fields = ['id', 'neo_account_id', 'permissions', 'linked_at', 'last_synced', 'is_active']
        read_only_fields = ['id', 'linked_at', 'last_synced']


class KycSyncStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = KycSyncStatus
        fields = ['id', 'sync_status', 'dpo_kyc_data', 'neo_kyc_data', 'conflict_details', 'last_synced', 'created_at']
        read_only_fields = ['id', 'last_synced', 'created_at']


class TransactionSyncSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionSync
        fields = ['id', 'transaction_id', 'synced_at', 'sync_status', 'neo_transaction_id']
        read_only_fields = ['id', 'synced_at']

