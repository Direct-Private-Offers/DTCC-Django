from django.contrib import admin
from .models import StoredFile


@admin.register(StoredFile)
class StoredFileAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'user', 'file_type', 'file_size', 'ipfs_cid', 'created_at']
    list_filter = ['file_type', 'created_at']
    search_fields = ['original_filename', 'user__username', 'ipfs_cid']
    readonly_fields = ['id', 'checksum', 'created_at']
    date_hierarchy = 'created_at'

