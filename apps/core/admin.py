from django.contrib import admin

from .models import ApiSession, IdempotencyKey, WebhookEvent, WebhookReplay, RedirectEvent


@admin.register(RedirectEvent)
class RedirectEventAdmin(admin.ModelAdmin):
    list_display = ('route', 'target_url', 'created_at', 'ip')
    list_filter = ('route', 'created_at')
    search_fields = ('route', 'target_url', 'referrer', 'ip', 'user_agent')
    readonly_fields = ('created_at',)


@admin.register(ApiSession)
class ApiSessionAdmin(admin.ModelAdmin):
    list_display = ('jti', 'subject', 'last_seen', 'request_count')
    search_fields = ('jti', 'subject')
    readonly_fields = ('first_seen', 'last_seen')


@admin.register(IdempotencyKey)
class IdempotencyKeyAdmin(admin.ModelAdmin):
    list_display = ('key', 'method', 'path', 'expires_at')
    search_fields = ('key', 'path')
    readonly_fields = ('expires_at',)


@admin.register(WebhookReplay)
class WebhookReplayAdmin(admin.ModelAdmin):
    list_display = ('nonce', 'created_at')
    search_fields = ('nonce',)
    readonly_fields = ('created_at',)


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ('source', 'event_type', 'status', 'created_at')
    list_filter = ('source', 'status', 'created_at')
    search_fields = ('event_type', 'reference')
    readonly_fields = ('created_at', 'updated_at')
