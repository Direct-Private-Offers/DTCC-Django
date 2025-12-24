"""
Decorators for audit logging and common functionality.
"""
from functools import wraps
from typing import Callable, Any
from apps.compliance.services import log_audit_event
import logging

logger = logging.getLogger(__name__)


def audit_log(action_type: str, resource_type: str):
    """
    Decorator to automatically log audit events for view methods.
    
    Args:
        action_type: Type of action (CREATE, UPDATE, DELETE, etc.)
        resource_type: Type of resource (Order, Swap, Settlement, etc.)
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def _wrapped(self, request, *args, **kwargs):
            response = view_func(self, request, *args, **kwargs)
            
            # Extract resource ID from response if available
            resource_id = None
            if hasattr(response, 'data') and isinstance(response.data, dict):
                data = response.data.get('data', {})
                resource_id = data.get('id') or data.get('orderId') or data.get('swapId') or data.get('settlementId')
            
            # Log audit event
            if request.user.is_authenticated:
                log_audit_event(
                    user=request.user,
                    action_type=action_type,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    description=f"{action_type} {resource_type} via {request.method} {request.path}",
                    ip_address=request.META.get('REMOTE_ADDR'),
                    request_id=getattr(request, 'request_id', None),
                )
            
            return response
        return _wrapped
    return decorator

