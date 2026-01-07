"""
Issuer Admin Configuration
Django admin interface for managing issuers and documents.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Issuer, IssuerDocument


@admin.register(Issuer)
class IssuerAdmin(admin.ModelAdmin):
    """Admin interface for Issuer model"""
    
    list_display = [
        'company_name',
        'security_name',
        'isin',
        'status_badge',
        'total_offering_display',
        'created_at',
        'offering_link',
    ]
    
    list_filter = [
        'status',
        'created_at',
        'published_at',
    ]
    
    search_fields = [
        'company_name',
        'security_name',
        'isin',
        'slug',
    ]
    
    readonly_fields = [
        'id',
        'slug',
        'offering_page_url',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id',
                'company_name',
                'slug',
                'logo',
                'security_name',
                'isin',
            )
        }),
        ('Offering Details', {
            'fields': (
                'price_per_token',
                'total_offering',
                'min_investment',
                'status',
                'offering_page_url',
            )
        }),
        ('Social Media', {
            'fields': (
                'website',
                'linkedin',
                'twitter',
                'youtube',
                'facebook',
                'instagram',
            ),
            'classes': ('collapse',),
        }),
        ('Payment Rails', {
            'fields': (
                'paypal_account',
                'wire_bank_name',
                'wire_account_number',
                'wire_routing_number',
                'wire_swift',
                'crypto_merchant_id',
            ),
            'classes': ('collapse',),
        }),
        ('Documents', {
            'fields': (
                'doc_prospectus',
                'doc_terms',
                'doc_risks',
                'doc_subscription',
            ),
            'classes': ('collapse',),
        }),
        ('Description', {
            'fields': ('description',),
        }),
        ('SEC Form Data', {
            'fields': ('sec_form_data',),
            'classes': ('collapse',),
        }),
        ('Integration', {
            'fields': (
                'bd_post_id',
            ),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
                'published_at',
            ),
        }),
        ('Admin Notes', {
            'fields': ('notes',),
            'classes': ('collapse',),
        }),
    )
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'draft': 'gray',
            'pending_review': 'orange',
            'active': 'green',
            'paused': 'blue',
            'closed': 'red',
            'archived': 'gray',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def total_offering_display(self, obj):
        """Format total offering as currency"""
        return f"${obj.total_offering:,.2f}"
    total_offering_display.short_description = 'Total Offering'
    total_offering_display.admin_order_field = 'total_offering'
    
    def offering_link(self, obj):
        """Display clickable link to offering page"""
        if obj.offering_page_url:
            return format_html(
                '<a href="{}" target="_blank">View Page →</a>',
                obj.offering_page_url
            )
        return '-'
    offering_link.short_description = 'Offering Page'
    
    actions = ['publish_offerings', 'pause_offerings']
    
    def publish_offerings(self, request, queryset):
        """Bulk action to publish offerings"""
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} offering(s) published successfully.')
    publish_offerings.short_description = 'Publish selected offerings'
    
    def pause_offerings(self, request, queryset):
        """Bulk action to pause offerings"""
        updated = queryset.update(status='paused')
        self.message_user(request, f'{updated} offering(s) paused successfully.')
    pause_offerings.short_description = 'Pause selected offerings'


@admin.register(IssuerDocument)
class IssuerDocumentAdmin(admin.ModelAdmin):
    """Admin interface for IssuerDocument model"""
    
    list_display = [
        'issuer',
        'document_type',
        'template_version',
        'is_current',
        'generated_at',
        'file_link',
    ]
    
    list_filter = [
        'document_type',
        'is_current',
        'generated_at',
    ]
    
    search_fields = [
        'issuer__company_name',
        'document_type',
    ]
    
    readonly_fields = [
        'id',
        'generated_at',
        'file_hash',
    ]
    
    def file_link(self, obj):
        """Display clickable link to document"""
        if obj.file_url:
            return format_html(
                '<a href="{}" target="_blank">Download PDF →</a>',
                obj.file_url
            )
        return '-'
    file_link.short_description = 'Document'
