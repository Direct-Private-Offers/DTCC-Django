from django.contrib import admin
from .models import CorporateAction


@admin.register(CorporateAction)
class CorporateActionAdmin(admin.ModelAdmin):
    list_display = ("id", "isin", "type", "status", "record_date", "payment_date")
    list_filter = ("type", "status")
    search_fields = ("id", "isin")
