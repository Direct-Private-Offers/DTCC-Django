from django.contrib import admin
from .models import ClearstreamAccount, Position


@admin.register(ClearstreamAccount)
class ClearstreamAccountAdmin(admin.ModelAdmin):
    list_display = ("id", "csd_participant", "csd_account", "linked")
    search_fields = ("csd_account", "csd_participant", "lei")
    list_filter = ("linked",)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("account", "isin", "settled_qty", "pending_qty", "as_of")
    search_fields = ("account", "isin")
    list_filter = ("isin",)
