"""
File storage API views.
"""
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404
from apps.core.responses import ok, bad_request, not_found
from apps.core.idempotency import idempotent
from .models import StoredFile
from .services import get_storage_service
from drf_spectacular.utils import extend_schema, OpenApiResponse
from apps.core.schemas import ERROR_400, ERROR_401, ERROR_404
import logging

logger = logging.getLogger(__name__)


class FileUploadView(APIView):
    """File upload endpoint."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Storage"],
        summary="Upload file",
        description="Upload a file for storage (KYC documents, contracts, etc.).",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {'type': 'string', 'format': 'binary'},
                    'file_type': {'type': 'string', 'enum': ['KYC_DOCUMENT', 'CONTRACT', 'STATEMENT', 'OTHER']},
                }
            }
        },
        responses={200: OpenApiResponse(description="File uploaded")}
    )
    @idempotent
    def post(self, request: Request):
        """Upload file."""
        if 'file' not in request.FILES:
            return bad_request("file is required")
        
        uploaded_file = request.FILES['file']
        file_type = request.data.get('file_type', StoredFile.FileType.OTHER)
        
        # Validate file type
        if file_type not in [choice[0] for choice in StoredFile.FileType.choices]:
            return bad_request(f"Invalid file_type. Must be one of: {', '.join([c[0] for c in StoredFile.FileType.choices])}")
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if uploaded_file.size > max_size:
            return bad_request(f"File size exceeds maximum of {max_size} bytes")
        
        # Store file
        service = get_storage_service()
        try:
            stored_file = service.store_file(
                user=request.user,
                uploaded_file=uploaded_file,
                file_type=file_type,
                metadata={'uploaded_via': 'api'}
            )
            
            return ok({
                'id': str(stored_file.id),
                'original_filename': stored_file.original_filename,
                'file_type': stored_file.file_type,
                'file_size': stored_file.file_size,
                'mime_type': stored_file.mime_type,
                'ipfs_cid': stored_file.ipfs_cid,
                'ipfs_url': stored_file.ipfs_url,
                'checksum': stored_file.checksum,
                'created_at': stored_file.created_at.isoformat(),
            })
        except Exception as e:
            logger.error(f"Error storing file: {str(e)}")
            return bad_request(f"Failed to store file: {str(e)}")


class FileListView(APIView):
    """List user's stored files."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Storage"],
        summary="List stored files",
        description="List all files stored by authenticated user.",
        responses={200: OpenApiResponse(description="List of files")}
    )
    def get(self, request: Request):
        """List stored files."""
        files = StoredFile.objects.filter(user=request.user)
        
        file_type_filter = request.query_params.get('file_type')
        if file_type_filter:
            files = files.filter(file_type=file_type_filter)
        
        return ok({
            'files': [
                {
                    'id': str(f.id),
                    'original_filename': f.original_filename,
                    'file_type': f.file_type,
                    'file_size': f.file_size,
                    'mime_type': f.mime_type,
                    'ipfs_cid': f.ipfs_cid,
                    'ipfs_url': f.ipfs_url,
                    'created_at': f.created_at.isoformat(),
                }
                for f in files
            ]
        })


class FileDownloadView(APIView):
    """Download stored file."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Storage"],
        summary="Download file",
        description="Download a stored file.",
        responses={200: OpenApiResponse(description="File content")}
    )
    def get(self, request: Request, file_id: str):
        """Download file."""
        stored_file = get_object_or_404(StoredFile, id=file_id, user=request.user)
        
        service = get_storage_service()
        file_path = service.get_file_path(stored_file)
        
        try:
            file_handle = open(file_path, 'rb')
            response = FileResponse(
                file_handle,
                content_type=stored_file.mime_type,
                filename=stored_file.original_filename
            )
            return response
        except FileNotFoundError:
            raise Http404("File not found on disk")


class FileDeleteView(APIView):
    """Delete stored file."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Storage"],
        summary="Delete file",
        description="Delete a stored file.",
        responses={200: OpenApiResponse(description="File deleted")}
    )
    def delete(self, request: Request, file_id: str):
        """Delete file."""
        stored_file = get_object_or_404(StoredFile, id=file_id, user=request.user)
        
        service = get_storage_service()
        service.delete_file(stored_file)
        
        return ok({'message': 'File deleted'})

