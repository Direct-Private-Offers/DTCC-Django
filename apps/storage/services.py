"""
File storage services for local and IPFS storage.
"""
import os
import uuid
import hashlib
import logging
from typing import Optional, BinaryIO
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings
from .models import StoredFile

logger = logging.getLogger(__name__)


class FileStorageService:
    """Service for file storage operations."""
    
    def __init__(self):
        self.storage_root = getattr(settings, 'FILE_STORAGE_ROOT', os.path.join(settings.BASE_DIR, 'storage'))
        self.ipfs_enabled = getattr(settings, 'IPFS_ENABLED', False)
        self.ipfs_gateway = getattr(settings, 'IPFS_GATEWAY_URL', 'https://ipfs.io/ipfs/')
    
    def store_file(
        self,
        user,
        uploaded_file: UploadedFile,
        file_type: str,
        metadata: Optional[dict] = None
    ) -> StoredFile:
        """
        Store an uploaded file locally and optionally to IPFS.
        
        Args:
            user: User uploading the file
            uploaded_file: Django UploadedFile instance
            file_type: File type (KYC_DOCUMENT, CONTRACT, etc.)
            metadata: Optional metadata dictionary
        
        Returns:
            StoredFile instance
        """
        # Ensure storage directory exists
        os.makedirs(self.storage_root, exist_ok=True)
        
        # Generate file path
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(uploaded_file.name)[1]
        file_path = os.path.join(self.storage_root, f"{file_id}{file_extension}")
        
        # Save file locally
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        # Calculate checksum
        checksum = self._calculate_checksum(file_path)
        
        # Upload to IPFS if enabled
        ipfs_cid = None
        ipfs_url = None
        if self.ipfs_enabled:
            try:
                ipfs_cid = self._upload_to_ipfs(file_path)
                if ipfs_cid:
                    ipfs_url = f"{self.ipfs_gateway}{ipfs_cid}"
            except Exception as e:
                logger.error(f"Failed to upload to IPFS: {str(e)}")
        
        # Create database record
        stored_file = StoredFile.objects.create(
            user=user,
            file_type=file_type,
            original_filename=uploaded_file.name,
            file_size=uploaded_file.size,
            mime_type=uploaded_file.content_type or 'application/octet-stream',
            file_path=file_path,
            ipfs_cid=ipfs_cid,
            ipfs_url=ipfs_url,
            checksum=checksum,
            metadata=metadata or {},
        )
        
        logger.info(f"File stored: {stored_file.id} ({uploaded_file.name})")
        return stored_file
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _upload_to_ipfs(self, file_path: str) -> Optional[str]:
        """
        Upload file to IPFS.
        
        Args:
            file_path: Local file path
        
        Returns:
            IPFS CID or None
        """
        # TODO: Implement IPFS upload
        # Options:
        # 1. Use ipfshttpclient library
        # 2. Use Pinata API
        # 3. Use Infura IPFS API
        # 4. Use local IPFS node
        
        logger.warning("IPFS upload not implemented - returning None")
        return None
    
    def get_file_path(self, stored_file: StoredFile) -> str:
        """Get local file path for a stored file."""
        return stored_file.file_path
    
    def delete_file(self, stored_file: StoredFile):
        """Delete a stored file from disk and database."""
        # Delete local file
        if os.path.exists(stored_file.file_path):
            try:
                os.remove(stored_file.file_path)
            except Exception as e:
                logger.error(f"Failed to delete file {stored_file.file_path}: {str(e)}")
        
        # TODO: Unpin from IPFS if enabled
        
        # Delete database record
        stored_file.delete()


def get_storage_service() -> FileStorageService:
    """Get file storage service instance."""
    return FileStorageService()

