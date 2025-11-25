from django.contrib import admin
from .models import Settlement


@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ("id", "source", "isin", "quantity", "status", "updated_at")
    list_filter = ("source", "status")
    search_fields = ("id", "isin", "account", "counterparty")
