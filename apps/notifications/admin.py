from django.contrib import admin
from .models import NotificationTemplate, Notification, NotificationPreference


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'event_type', 'notification_type', 'is_active']
    list_filter = ['notification_type', 'is_active', 'event_type']
    search_fields = ['name', 'event_type']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'status', 'recipient', 'created_at']
    list_filter = ['notification_type', 'status', 'created_at']
    search_fields = ['user__username', 'recipient', 'subject']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_enabled', 'sms_enabled', 'in_app_enabled']
    search_fields = ['user__username']

