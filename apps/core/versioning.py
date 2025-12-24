"""
API versioning utilities and middleware.
"""
from rest_framework.versioning import URLPathVersioning, AcceptHeaderVersioning
from rest_framework import versioning
from django.conf import settings
import re


class CustomURLPathVersioning(URLPathVersioning):
    """
    Custom URL path versioning that supports v1, v2, etc.
    """
    default_version = 'v1'
    allowed_versions = ['v1', 'v2']
    version_param = 'version'
    
    def determine_version(self, request, *args, **kwargs):
        # Check URL path first
        version = kwargs.get(self.version_param, self.default_version)
        
        # Validate version
        if version not in self.allowed_versions:
            version = self.default_version
        
        return version


class CustomAcceptHeaderVersioning(AcceptHeaderVersioning):
    """
    Custom accept header versioning.
    """
    default_version = 'v1'
    allowed_versions = ['v1', 'v2']
    
    def determine_version(self, request, *args, **kwargs):
        # Check Accept header
        media_type = request.META.get('HTTP_ACCEPT', '')
        
        # Parse version from Accept header (e.g., application/vnd.api.v1+json)
        version_match = re.search(r'v(\d+)', media_type)
        if version_match:
            version = f"v{version_match.group(1)}"
            if version in self.allowed_versions:
                return version
        
        return self.default_version


def get_api_version(request):
    """
    Get API version from request.
    
    Args:
        request: Django request object
    
    Returns:
        API version string (e.g., 'v1', 'v2')
    """
    # Try URL path versioning first
    if hasattr(request, 'version'):
        return request.version
    
    # Try Accept header
    media_type = request.META.get('HTTP_ACCEPT', '')
    version_match = re.search(r'v(\d+)', media_type)
    if version_match:
        version = f"v{version_match.group(1)}"
        if version in ['v1', 'v2']:
            return version
    
    return 'v1'  # Default version

