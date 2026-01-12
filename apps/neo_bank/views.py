from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from .models import NeoBankAccountLink, KycSyncStatus, TransactionSync
from .serializers import NeoBankAccountLinkSerializer, KycSyncStatusSerializer, TransactionSyncSerializer
from .services import NeoBankSyncService
from apps.core.permissions import IsIssuerOrOps


class NeoBankAccountLinkViewSet(viewsets.ModelViewSet):
    """ViewSet for NEO bank account linking"""
    queryset = NeoBankAccountLink.objects.all()
    serializer_class = NeoBankAccountLinkSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter to user's own account links"""
        return self.queryset.filter(user=self.request.user)
    
    @extend_schema(
        summary="Link NEO bank account",
        description="Link DPO account with NEO bank account"
    )
    def create(self, request, *args, **kwargs):
        """Link account with NEO bank"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        service = NeoBankSyncService()
        link = service.link_account(
            user=request.user,
            neo_account_id=serializer.validated_data['neo_account_id'],
            permissions=serializer.validated_data.get('permissions')
        )
        
        if link:
            return Response(
                NeoBankAccountLinkSerializer(link).data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            {'error': 'Failed to link account'},
            status=status.HTTP_400_BAD_REQUEST
        )


class KycSyncStatusViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for KYC sync status"""
    queryset = KycSyncStatus.objects.all()
    serializer_class = KycSyncStatusSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter to user's own sync statuses"""
        return self.queryset.filter(user=self.request.user)
    
    @extend_schema(
        summary="Sync KYC with NEO bank",
        description="Synchronize KYC data with NEO bank"
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def sync(self, request):
        """Sync KYC data"""
        kyc_data = request.data.get('kyc_data', {})
        
        service = NeoBankSyncService()
        sync_status = service.sync_kyc(request.user, kyc_data)
        
        if sync_status:
            return Response(
                KycSyncStatusSerializer(sync_status).data,
                status=status.HTTP_200_OK
            )
        return Response(
            {'error': 'Failed to sync KYC'},
            status=status.HTTP_400_BAD_REQUEST
        )


class TransactionSyncViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for transaction sync"""
    queryset = TransactionSync.objects.all()
    serializer_class = TransactionSyncSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter to user's own transaction syncs"""
        return self.queryset.filter(user=self.request.user)

