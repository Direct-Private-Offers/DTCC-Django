from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.utils import timezone
from decimal import Decimal

from apps.core.responses import ok, bad_request, not_found
from apps.core.permissions import IsAuthenticated, HasGroupPermission
from .models import XetraTrade, XetraOrder, XetraSettlement, XetraPosition, XetraMarketData
from .serializers import (
    XetraTradeSerializer, XetraOrderSerializer, XetraSettlementSerializer,
    XetraPositionSerializer, XetraMarketDataSerializer, XetraOrderCreateSerializer
)
from .client import XetraClient

logger = __import__('logging').getLogger(__name__)


class XetraOrderView(APIView):
    """XETRA order management endpoints"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Submit XETRA order",
        description="Submit a trading order to XETRA T7 system",
        request=XetraOrderCreateSerializer,
        responses={200: XetraOrderSerializer}
    )
    def post(self, request):
        """Submit new order to XETRA"""
        serializer = XetraOrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return bad_request(serializer.errors)
        
        data = serializer.validated_data
        client = XetraClient()
        
        # Submit order to XETRA
        result = client.submit_order(
            isin=data['isin'],
            account=data['account'],
            order_type=data['order_type'],
            side=data['side'],
            quantity=float(data['quantity']),
            price=float(data['price']) if data.get('price') else None
        )
        
        if not result:
            return bad_request("Failed to submit order to XETRA")
        
        # Create order record
        order = XetraOrder.objects.create(
            xetra_order_id=result['xetra_order_id'],
            isin=data['isin'],
            account=data['account'],
            order_type=data['order_type'],
            side=data['side'],
            quantity=data['quantity'],
            price=data.get('price'),
            status=result.get('status', 'NEW'),
            xetra_reference=result.get('xetra_reference'),
        )
        
        return ok(XetraOrderSerializer(order).data)
    
    @extend_schema(
        summary="List XETRA orders",
        description="List orders for authenticated user",
        responses={200: XetraOrderSerializer(many=True)}
    )
    def get(self, request):
        """List orders"""
        isin = request.query_params.get('isin')
        status_filter = request.query_params.get('status')
        
        queryset = XetraOrder.objects.all()
        
        if isin:
            queryset = queryset.filter(isin=isin)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        serializer = XetraOrderSerializer(queryset, many=True)
        return ok(serializer.data)


class XetraOrderDetailView(APIView):
    """XETRA order detail and cancellation"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get XETRA order details",
        responses={200: XetraOrderSerializer}
    )
    def get(self, request, order_id):
        """Get order details"""
        try:
            order = XetraOrder.objects.get(id=order_id)
            
            # Sync status from XETRA
            client = XetraClient()
            status_data = client.get_order_status(order.xetra_order_id)
            if status_data:
                order.status = status_data.get('status', order.status)
                if 'filled_quantity' in status_data:
                    order.filled_quantity = Decimal(status_data['filled_quantity'])
                order.save()
            
            return ok(XetraOrderSerializer(order).data)
        except XetraOrder.DoesNotExist:
            return not_found("Order not found")
    
    @extend_schema(
        summary="Cancel XETRA order",
        responses={200: OpenApiResponse(description="Order cancelled")}
    )
    def post(self, request, order_id):
        """Cancel order"""
        try:
            order = XetraOrder.objects.get(id=order_id)
            
            if order.status in ['FILLED', 'CANCELLED', 'REJECTED']:
                return bad_request(f"Cannot cancel order with status {order.status}")
            
            client = XetraClient()
            if client.cancel_order(order.xetra_order_id):
                order.status = 'CANCELLED'
                order.save()
                return ok({"message": "Order cancelled successfully"})
            else:
                return bad_request("Failed to cancel order in XETRA")
        except XetraOrder.DoesNotExist:
            return not_found("Order not found")


class XetraTradeView(APIView):
    """XETRA trade endpoints"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="List XETRA trades",
        responses={200: XetraTradeSerializer(many=True)}
    )
    def get(self, request):
        """List trades"""
        isin = request.query_params.get('isin')
        status_filter = request.query_params.get('status')
        
        queryset = XetraTrade.objects.all()
        
        if isin:
            queryset = queryset.filter(isin=isin)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        serializer = XetraTradeSerializer(queryset, many=True)
        return ok(serializer.data)


class XetraSettlementView(APIView):
    """XETRA settlement endpoints"""
    permission_classes = [IsAuthenticated, HasGroupPermission]
    required_groups = ['ops', 'issuer']
    
    @extend_schema(
        summary="Create XETRA settlement instruction",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'trade_id': {'type': 'string'},
                    'isin': {'type': 'string'},
                    'buyer_account': {'type': 'string'},
                    'seller_account': {'type': 'string'},
                    'quantity': {'type': 'number'},
                    'amount': {'type': 'number'},
                    'value_date': {'type': 'string', 'format': 'date-time'},
                }
            }
        },
        responses={200: XetraSettlementSerializer}
    )
    def post(self, request):
        """Create settlement instruction"""
        trade_id = request.data.get('trade_id')
        if not trade_id:
            return bad_request("trade_id is required")
        
        try:
            trade = XetraTrade.objects.get(id=trade_id)
        except XetraTrade.DoesNotExist:
            return not_found("Trade not found")
        
        client = XetraClient()
        result = client.create_settlement_instruction(
            trade_id=str(trade.id),
            isin=trade.isin,
            buyer_account=trade.buyer_account,
            seller_account=trade.seller_account,
            quantity=float(trade.quantity),
            amount=float(trade.price * trade.quantity),
            value_date=trade.settlement_date or timezone.now()
        )
        
        if not result:
            return bad_request("Failed to create settlement instruction")
        
        settlement = XetraSettlement.objects.create(
            settlement_id=result['settlement_id'],
            trade=trade,
            isin=trade.isin,
            buyer_account=trade.buyer_account,
            seller_account=trade.seller_account,
            quantity=trade.quantity,
            amount=trade.price * trade.quantity,
            currency=trade.currency,
            value_date=trade.settlement_date or timezone.now(),
            status=result.get('status', 'PENDING'),
            xetra_instruction_id=result.get('xetra_instruction_id'),
        )
        
        return ok(XetraSettlementSerializer(settlement).data)
    
    @extend_schema(
        summary="List XETRA settlements",
        responses={200: XetraSettlementSerializer(many=True)}
    )
    def get(self, request):
        """List settlements"""
        isin = request.query_params.get('isin')
        status_filter = request.query_params.get('status')
        
        queryset = XetraSettlement.objects.all()
        
        if isin:
            queryset = queryset.filter(isin=isin)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        serializer = XetraSettlementSerializer(queryset, many=True)
        return ok(serializer.data)


class XetraPositionView(APIView):
    """XETRA position endpoints"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get XETRA positions",
        responses={200: XetraPositionSerializer(many=True)}
    )
    def get(self, request):
        """Get positions for account"""
        account = request.query_params.get('account')
        isin = request.query_params.get('isin')
        
        if not account:
            return bad_request("account parameter is required")
        
        # Sync positions from XETRA
        client = XetraClient()
        positions_data = client.get_positions(account, isin)
        
        # Update local positions
        for pos_data in positions_data:
            XetraPosition.objects.update_or_create(
                account=pos_data['account'],
                isin=pos_data['isin'],
                defaults={
                    'settled_quantity': Decimal(pos_data['settled_quantity']),
                    'pending_quantity': Decimal(pos_data.get('pending_quantity', '0')),
                    'as_of': timezone.now(),
                }
            )
        
        queryset = XetraPosition.objects.filter(account=account)
        if isin:
            queryset = queryset.filter(isin=isin)
        
        serializer = XetraPositionSerializer(queryset, many=True)
        return ok(serializer.data)


class XetraMarketDataView(APIView):
    """XETRA market data endpoints"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get XETRA market data",
        responses={200: XetraMarketDataSerializer}
    )
    def get(self, request):
        """Get market data for ISIN"""
        isin = request.query_params.get('isin')
        if not isin:
            return bad_request("isin parameter is required")
        
        client = XetraClient()
        market_data = client.get_market_data(isin)
        
        if not market_data:
            return not_found("Market data not available")
        
        # Store market data snapshot
        snapshot = XetraMarketData.objects.create(
            isin=isin,
            bid_price=Decimal(market_data.get('bid_price', '0')) if market_data.get('bid_price') else None,
            ask_price=Decimal(market_data.get('ask_price', '0')) if market_data.get('ask_price') else None,
            last_price=Decimal(market_data.get('last_price', '0')) if market_data.get('last_price') else None,
            volume=Decimal(market_data.get('volume', '0')),
            timestamp=timezone.now(),
        )
        
        return ok(XetraMarketDataSerializer(snapshot).data)
