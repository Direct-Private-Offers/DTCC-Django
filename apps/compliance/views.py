"""
Compliance API views for KYC/AML operations.
"""
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from django.shortcuts import get_object_or_404
from apps.core.responses import ok, bad_request, not_found
from apps.core.permissions import IsInGroup
from apps.core.idempotency import idempotent
from apps.compliance.models import InvestorProfile, KYCDocument, AMLCheck, AuditLog
from apps.compliance.serializers import (
    InvestorProfileSerializer, KYCDocumentSerializer, AMLCheckSerializer
)
try:
    from django_ratelimit.decorators import ratelimit
except ImportError:
    # Fallback: try alternative package name
    try:
        from ratelimit.decorators import ratelimit
    except ImportError:
        # Fallback no-op decorator for local/dev when ratelimit is unavailable
        def ratelimit(*args, **kwargs):
            def _decorator(func):
                return func
            return _decorator
from apps.neo_bank.models import KycSyncStatus
from apps.neo_bank.services import NeoBankSyncService
from drf_spectacular.utils import extend_schema, OpenApiResponse
from apps.core.schemas import ERROR_400, ERROR_401, ERROR_403, ERROR_404
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class InvestorProfileView(APIView):
    """Investor profile management."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Compliance"],
        summary="Get or create investor profile",
        description="Get investor profile for authenticated user or create if not exists.",
        responses={
            200: OpenApiResponse(description="Investor profile"),
            401: ERROR_401,
        }
    )
    def get(self, request: Request):
        """Get investor profile."""
        profile, created = InvestorProfile.objects.get_or_create(
            user=request.user,
            defaults={'wallet_address': request.query_params.get('wallet_address', '')}
        )
        serializer = InvestorProfileSerializer(profile)
        return ok(serializer.data)
    
    @extend_schema(
        tags=["Compliance"],
        summary="Update investor profile",
        description="Update investor profile information.",
        request=InvestorProfileSerializer,
        responses={200: OpenApiResponse(description="Profile updated")}
    )
    @idempotent
    @ratelimit(key='user', rate='10/m', method='PATCH', block=True)
    def patch(self, request: Request):
        """Update investor profile."""
        profile = get_object_or_404(InvestorProfile, user=request.user)
        serializer = InvestorProfileSerializer(profile, data=request.data, partial=True)
        if not serializer.is_valid():
            return bad_request(serializer.errors)
        
        serializer.save()
        
        # Log audit
        AuditLog.objects.create(
            user=request.user,
            action_type=AuditLog.ActionType.UPDATE,
            resource_type='InvestorProfile',
            resource_id=str(profile.id),
            description=f"Updated investor profile: {request.user.username}",
            ip_address=request.META.get('REMOTE_ADDR'),
            request_id=getattr(request, 'request_id', None),
        )
        
        return ok(serializer.data)


class KYCDocumentView(APIView):
    """KYC document management."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Compliance"],
        summary="List KYC documents",
        description="List KYC documents for authenticated user.",
        responses={200: OpenApiResponse(description="List of documents")}
    )
    def get(self, request: Request):
        """List KYC documents."""
        profile = get_object_or_404(InvestorProfile, user=request.user)
        documents = KYCDocument.objects.filter(investor=profile)
        serializer = KYCDocumentSerializer(documents, many=True)
        return ok({'documents': serializer.data})
    
    @extend_schema(
        tags=["Compliance"],
        summary="Upload KYC document",
        description="Upload a KYC verification document.",
        request=KYCDocumentSerializer,
        responses={200: OpenApiResponse(description="Document uploaded")}
    )
    @idempotent
    @ratelimit(key='user', rate='5/m', method='POST', block=True)
    def post(self, request: Request):
        """Upload KYC document."""
        profile = get_object_or_404(InvestorProfile, user=request.user)
        serializer = KYCDocumentSerializer(data=request.data)
        if not serializer.is_valid():
            return bad_request(serializer.errors)
        
        document = serializer.save(investor=profile)
        
        # Log audit
        AuditLog.objects.create(
            user=request.user,
            action_type=AuditLog.ActionType.CREATE,
            resource_type='KYCDocument',
            resource_id=str(document.id),
            description=f"Uploaded KYC document: {document.document_type}",
            ip_address=request.META.get('REMOTE_ADDR'),
            request_id=getattr(request, 'request_id', None),
        )
        
        return ok(serializer.data)


class AMLCheckView(APIView):
    """AML check management."""
    permission_classes = [IsAuthenticated, IsInGroup.with_names(["ops", "issuer"])]
    
    @extend_schema(
        tags=["Compliance"],
        summary="Get AML checks",
        description="Get AML check results for an investor.",
        responses={200: OpenApiResponse(description="AML check results")}
    )
    def get(self, request: Request):
        """Get AML checks."""
        wallet_address = request.query_params.get('wallet_address')
        if not wallet_address:
            return bad_request("wallet_address parameter required")
        
        profile = get_object_or_404(InvestorProfile, wallet_address=wallet_address)
        checks = AMLCheck.objects.filter(investor=profile).order_by('-created_at')
        serializer = AMLCheckSerializer(checks, many=True)
        return ok({'checks': serializer.data})


class AuditLogView(APIView):
    """Audit log query endpoint."""
    permission_classes = [IsAuthenticated, IsInGroup.with_names(["ops"])]
    
    @extend_schema(
        tags=["Compliance"],
        summary="Query audit logs",
        description="Query audit logs with filters. Requires 'ops' group.",
        responses={200: OpenApiResponse(description="Audit log entries")}
    )
    def get(self, request: Request):
        """Query audit logs."""
        logs = AuditLog.objects.all()
        
        # Filters
        if user_id := request.query_params.get('user_id'):
            logs = logs.filter(user_id=user_id)
        if resource_type := request.query_params.get('resource_type'):
            logs = logs.filter(resource_type=resource_type)
        if resource_id := request.query_params.get('resource_id'):
            logs = logs.filter(resource_id=resource_id)
        if action_type := request.query_params.get('action_type'):
            logs = logs.filter(action_type=action_type)
        
        logs = logs[:100]  # Limit to 100 results
        
        return ok({
            'logs': [
                {
                    'id': str(log.id),
                    'user': log.user.username if log.user else None,
                    'action_type': log.action_type,
                    'resource_type': log.resource_type,
                    'resource_id': log.resource_id,
                    'description': log.description,
                    'ip_address': str(log.ip_address) if log.ip_address else None,
                    'created_at': log.created_at.isoformat(),
                }
                for log in logs
            ]
        })


class ComplianceStatusView(APIView):
    """Compliance status synchronization endpoint."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Compliance"],
        summary="Get compliance status",
        description="Get comprehensive compliance status including DPO and NEO Bank sync status.",
        responses={200: OpenApiResponse(description="Compliance status")}
    )
    def get(self, request: Request):
        """Get compliance status."""
        profile = get_object_or_404(InvestorProfile, user=request.user)
        
        # Get NEO Bank sync status
        neo_sync_status = None
        try:
            neo_sync_status = KycSyncStatus.objects.filter(user=request.user).order_by('-last_synced').first()
        except KycSyncStatus.DoesNotExist:
            pass
        
        # Get latest AML checks
        latest_aml = AMLCheck.objects.filter(investor=profile).order_by('-created_at').first()
        
        status = {
            'dpo': {
                'kyc_status': profile.kyc_status,
                'aml_status': profile.aml_status,
                'accredited_investor': profile.accredited_investor,
                'kyc_verified_at': profile.kyc_verified_at.isoformat() if profile.kyc_verified_at else None,
                'kyc_expires_at': profile.kyc_expires_at.isoformat() if profile.kyc_expires_at else None,
            },
            'neo_bank': {
                'synced': profile.neo_bank_synced,
                'sync_status': profile.neo_bank_sync_status,
                'last_synced': profile.neo_bank_last_synced.isoformat() if profile.neo_bank_last_synced else None,
                'account_id': profile.neo_bank_account_id,
                'latest_sync': {
                    'status': neo_sync_status.sync_status if neo_sync_status else None,
                    'last_synced': neo_sync_status.last_synced.isoformat() if neo_sync_status and neo_sync_status.last_synced else None,
                    'has_conflict': neo_sync_status.sync_status == 'CONFLICT' if neo_sync_status else False,
                } if neo_sync_status else None,
            },
            'aml': {
                'status': latest_aml.status if latest_aml else None,
                'risk_score': float(latest_aml.risk_score) if latest_aml and latest_aml.risk_score else None,
                'checked_at': latest_aml.checked_at.isoformat() if latest_aml and latest_aml.checked_at else None,
            },
            'overall': {
                'compliant': (
                    profile.kyc_status == InvestorProfile.KYCStatus.APPROVED and
                    profile.aml_status == 'CLEAR' and
                    (not latest_aml or latest_aml.status == AMLCheck.CheckStatus.CLEAR)
                ),
                'warnings': [],
            }
        }
        
        # Add warnings
        if profile.kyc_status != InvestorProfile.KYCStatus.APPROVED:
            status['overall']['warnings'].append('KYC not approved')
        if profile.aml_status != 'CLEAR':
            status['overall']['warnings'].append('AML check not clear')
        if neo_sync_status and neo_sync_status.sync_status == 'CONFLICT':
            status['overall']['warnings'].append('NEO Bank sync conflict detected')
        if profile.kyc_expires_at and profile.kyc_expires_at < timezone.now():
            status['overall']['warnings'].append('KYC verification expired')
        
        return ok(status)


class ComplianceSyncView(APIView):
    """Trigger compliance synchronization with NEO Bank."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Compliance"],
        summary="Sync compliance with NEO Bank",
        description="Manually trigger synchronization of compliance status with NEO Bank.",
        responses={200: OpenApiResponse(description="Sync initiated")}
    )
    @idempotent
    @ratelimit(key='user', rate='5/m', method='POST', block=True)
    def post(self, request: Request):
        """Sync compliance with NEO Bank."""
        profile = get_object_or_404(InvestorProfile, user=request.user)
        
        # Prepare KYC data from profile
        kyc_data = {
            'status': profile.kyc_status,
            'aml_status': profile.aml_status,
            'accredited_investor': profile.accredited_investor,
            'country_code': profile.country_code,
            'tax_id': profile.tax_id,
            'kyc_verified_at': profile.kyc_verified_at.isoformat() if profile.kyc_verified_at else None,
            'kyc_expires_at': profile.kyc_expires_at.isoformat() if profile.kyc_expires_at else None,
        }
        
        # Sync with NEO Bank
        service = NeoBankSyncService()
        sync_status = service.sync_kyc(request.user, kyc_data)
        
        if sync_status:
            # Update profile sync status
            profile.neo_bank_synced = True
            profile.neo_bank_sync_status = sync_status.sync_status
            profile.neo_bank_last_synced = sync_status.last_synced
            profile.save()
            
            return ok({
                'synced': True,
                'sync_status': sync_status.sync_status,
                'sync_id': str(sync_status.id),
            })
        else:
            return bad_request('Failed to sync with NEO Bank')

