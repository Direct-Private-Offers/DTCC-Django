from django.contrib import admin
from .models import InvestorProfile, KYCDocument, AMLCheck, AuditLog


@admin.register(InvestorProfile)
class InvestorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'wallet_address', 'investor_type', 'kyc_status', 'aml_status', 'created_at']
    list_filter = ['kyc_status', 'aml_status', 'investor_type', 'accredited_investor']
    search_fields = ['user__username', 'wallet_address', 'tax_id']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(KYCDocument)
class KYCDocumentAdmin(admin.ModelAdmin):
    list_display = ['investor', 'document_type', 'verified', 'created_at']
    list_filter = ['document_type', 'verified', 'created_at']
    search_fields = ['investor__user__username', 'ipfs_cid']
    readonly_fields = ['id', 'created_at']


@admin.register(AMLCheck)
class AMLCheckAdmin(admin.ModelAdmin):
    list_display = ['investor', 'check_type', 'status', 'risk_score', 'checked_at']
    list_filter = ['check_type', 'status', 'checked_at']
    search_fields = ['investor__user__username', 'reference_id']
    readonly_fields = ['id', 'created_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action_type', 'resource_type', 'resource_id', 'created_at']
    list_filter = ['action_type', 'resource_type', 'created_at']
    search_fields = ['user__username', 'resource_id', 'request_id', 'description']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'

