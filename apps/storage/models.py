"""
File storage models for document management.
"""
from django.db import models
from django.contrib.auth.models import User
import uuid


class StoredFile(models.Model):
    """Stored file metadata."""
    class FileType(models.TextChoices):
        KYC_DOCUMENT = 'KYC_DOCUMENT', 'KYC Document'
        CONTRACT = 'CONTRACT', 'Contract'
        STATEMENT = 'STATEMENT', 'Statement'
        OTHER = 'OTHER', 'Other'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stored_files')
    file_type = models.CharField(max_length=32, choices=FileType.choices)
    original_filename = models.CharField(max_length=512)
    file_size = models.BigIntegerField()  # Size in bytes
    mime_type = models.CharField(max_length=128)
    file_path = models.CharField(max_length=512)  # Local storage path
    ipfs_cid = models.CharField(max_length=128, null=True, blank=True)  # IPFS content ID
    ipfs_url = models.URLField(null=True, blank=True)  # IPFS gateway URL
    checksum = models.CharField(max_length=64, null=True, blank=True)  # SHA256 hash
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'storage_files'
        indexes = [
            models.Index(fields=['user', 'file_type']),
            models.Index(fields=['ipfs_cid']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"StoredFile({self.original_filename}, {self.file_type})"

