"""
Compliance services for KYC/AML operations.
"""
import logging
from typing import Optional, Dict, Any
from django.contrib.auth.models import User
from .models import InvestorProfile, AMLCheck, AuditLog

logger = logging.getLogger(__name__)


def verify_investor_kyc(wallet_address: str) -> bool:
    """
    Verify if investor has valid KYC.
    
    Args:
        wallet_address: Investor wallet address
    
    Returns:
        True if KYC is approved and not expired
    """
    try:
        profile = InvestorProfile.objects.get(wallet_address=wallet_address)
        if profile.kyc_status != InvestorProfile.KYCStatus.APPROVED:
            return False
        
        from django.utils import timezone
        if profile.kyc_expires_at and profile.kyc_expires_at < timezone.now():
            return False
        
        return True
    except InvestorProfile.DoesNotExist:
        return False


def check_aml_status(wallet_address: str) -> str:
    """
    Check AML status for an investor.
    
    Args:
        wallet_address: Investor wallet address
    
    Returns:
        AML status string
    """
    try:
        profile = InvestorProfile.objects.get(wallet_address=wallet_address)
        return profile.aml_status
    except InvestorProfile.DoesNotExist:
        return 'PENDING'


def is_accredited_investor(wallet_address: str) -> bool:
    """
    Check if investor is accredited.
    
    Args:
        wallet_address: Investor wallet address
    
    Returns:
        True if accredited investor
    """
    try:
        profile = InvestorProfile.objects.get(wallet_address=wallet_address)
        return profile.accredited_investor
    except InvestorProfile.DoesNotExist:
        return False


def log_audit_event(
    user: Optional[User],
    action_type: str,
    resource_type: str,
    resource_id: Optional[str],
    description: str,
    ip_address: Optional[str] = None,
    request_id: Optional[str] = None,
    changes: Optional[Dict[str, Any]] = None
):
    """
    Log an audit event.
    
    Args:
        user: User performing the action
        action_type: Type of action
        resource_type: Type of resource
        resource_id: Resource identifier
        description: Description of the action
        ip_address: IP address
        request_id: Request ID
        changes: Before/after changes
    """
    AuditLog.objects.create(
        user=user,
        action_type=action_type,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        ip_address=ip_address,
        request_id=request_id,
        changes=changes,
    )

