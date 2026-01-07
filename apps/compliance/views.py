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
from django_ratelimit.decorators import ratelimit
from drf_spectacular.utils import extend_schema, OpenApiResponse
from apps.core.schemas import ERROR_400, ERROR_401, ERROR_403, ERROR_404
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

