from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from .models import FxConversion, CrossPlatformSettlement, TokenFlow
from .serializers import (
    FxConversionSerializer, FxConversionRequestSerializer,
    CrossPlatformSettlementSerializer, TokenFlowSerializer
)
from .services import FxMarketService
from apps.core.permissions import IsIssuerOrOps


class FxConversionViewSet(viewsets.ModelViewSet):
    """ViewSet for FX conversions"""
    queryset = FxConversion.objects.all()
    serializer_class = FxConversionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter to user's own conversions"""
        return self.queryset.filter(user=self.request.user)
    
    @extend_schema(
        summary="Convert FX to Token",
        description="Convert fiat currency to security token",
        request=FxConversionRequestSerializer,
        responses={201: FxConversionSerializer}
    )
    @action(detail=False, methods=['post'], url_path='convert-fx-to-token')
    def convert_fx_to_token(self, request):
        """Convert FX to token"""
        serializer = FxConversionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        service = FxMarketService()
        
        conversion = service.convert_fx_to_token(
            user=request.user,
            amount=data['source_amount'],
            currency=data['source_currency'],
            token_address=data.get('token_address', '')
        )
        
        if conversion:
            return Response(
                FxConversionSerializer(conversion).data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            {'error': 'Conversion failed'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @extend_schema(
        summary="Convert Token to FX",
        description="Convert security token to fiat currency",
        request=FxConversionRequestSerializer,
        responses={201: FxConversionSerializer}
    )
    @action(detail=False, methods=['post'], url_path='convert-token-to-fx')
    def convert_token_to_fx(self, request):
        """Convert token to FX"""
        serializer = FxConversionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        service = FxMarketService()
        
        conversion = service.convert_token_to_fx(
            user=request.user,
            token_amount=data['source_amount'],
            token_address=data.get('token_address', ''),
            target_currency=data.get('target_currency', 'USD')
        )
        
        if conversion:
            return Response(
                FxConversionSerializer(conversion).data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            {'error': 'Conversion failed'},
            status=status.HTTP_400_BAD_REQUEST
        )


class CrossPlatformSettlementViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for cross-platform settlements"""
    queryset = CrossPlatformSettlement.objects.all()
    serializer_class = CrossPlatformSettlementSerializer
    permission_classes = [IsIssuerOrOps]
    
    @extend_schema(
        summary="Initiate cross-platform settlement",
        description="Initiate settlement on FX-to-market platform"
    )
    @action(detail=False, methods=['post'], permission_classes=[IsIssuerOrOps])
    def initiate(self, request):
        """Initiate cross-platform settlement"""
        from apps.settlement.models import Settlement
        
        settlement_id = request.data.get('settlement_id')
        if not settlement_id:
            return Response(
                {'error': 'settlement_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            settlement = Settlement.objects.get(id=settlement_id)
        except Settlement.DoesNotExist:
            return Response(
                {'error': 'Settlement not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        service = FxMarketService()
        cross_settlement = service.initiate_cross_platform_settlement(settlement)
        
        if cross_settlement:
            return Response(
                CrossPlatformSettlementSerializer(cross_settlement).data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            {'error': 'Failed to initiate cross-platform settlement'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @extend_schema(
        summary="Reconcile settlement",
        description="Reconcile settlement status between DPO and FX-to-market"
    )
    @action(detail=True, methods=['post'], permission_classes=[IsIssuerOrOps])
    def reconcile(self, request, pk=None):
        """Reconcile settlement"""
        cross_settlement = self.get_object()
        service = FxMarketService()
        
        reconciled = service.reconcile_settlement(cross_settlement)
        
        if reconciled:
            return Response(
                CrossPlatformSettlementSerializer(cross_settlement).data,
                status=status.HTTP_200_OK
            )
        return Response(
            {'error': 'Settlement not yet reconciled'},
            status=status.HTTP_400_BAD_REQUEST
        )


class TokenFlowViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for token flows"""
    queryset = TokenFlow.objects.all()
    serializer_class = TokenFlowSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter to user's own token flows"""
        return self.queryset.filter(user=self.request.user)
    
    @extend_schema(
        summary="Transfer token",
        description="Transfer token between DPO and FX-to-market"
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def transfer(self, request):
        """Transfer token"""
        flow_direction = request.data.get('flow_direction')
        token_address = request.data.get('token_address')
        amount = request.data.get('amount')
        
        if not all([flow_direction, token_address, amount]):
            return Response(
                {'error': 'flow_direction, token_address, and amount are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service = FxMarketService()
        token_flow = service.transfer_token(
            user=request.user,
            flow_direction=flow_direction,
            token_address=token_address,
            amount=amount
        )
        
        if token_flow:
            return Response(
                TokenFlowSerializer(token_flow).data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            {'error': 'Transfer failed'},
            status=status.HTTP_400_BAD_REQUEST
        )

