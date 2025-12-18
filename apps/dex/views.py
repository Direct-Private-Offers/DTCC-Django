"""
DEX API views for trading, swaps, and wallet management.
"""
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from apps.core.responses import ok, bad_request, not_found
from apps.core.idempotency import idempotent
from ratelimit.decorators import ratelimit
from .models import Wallet, Order, Swap, Trade
from .serializers import (
    WalletCreateSerializer, OrderCreateSerializer, OrderUpdateSerializer,
    SwapCreateSerializer, TradeSerializer, OrderBookSerializer
)
from .services import (
    create_order, match_orders, execute_trade, create_swap,
    cancel_order, get_order_book, validate_wallet_balance
)
from .blockchain import get_token_balance, transfer_tokens
from apps.core.blockchain import get_web3_provider
from drf_spectacular.utils import (
    extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
)
from apps.core.schemas import ERROR_400, ERROR_401, ERROR_403, ERROR_404, ERROR_500


class WalletView(APIView):
    """Wallet management endpoints."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["DEX"],
        summary="Create or link wallet",
        description="Create or link a blockchain wallet to the authenticated user.",
        request=WalletCreateSerializer,
        responses={
            200: OpenApiResponse(description="Wallet created/linked successfully"),
            400: ERROR_400,
            401: ERROR_401,
        }
    )
    @idempotent
    @ratelimit(key='user', rate='10/m', method='POST', block=True)
    def post(self, request: Request):
        """Create or link a wallet."""
        ser = WalletCreateSerializer(data=request.data)
        if not ser.is_valid():
            return bad_request(ser.errors)
        
        data = ser.validated_data
        wallet, created = Wallet.objects.get_or_create(
            address=data['address'],
            defaults={
                'user': request.user,
                'network': data.get('network', 'BSC'),
            }
        )
        
        if not created and wallet.user != request.user:
            return bad_request("Wallet already linked to another user")
        
        return ok({
            'walletId': str(wallet.id),
            'address': wallet.address,
            'network': wallet.network,
            'created': created
        })
    
    @extend_schema(
        tags=["DEX"],
        summary="List user wallets",
        description="Get all wallets linked to the authenticated user.",
        responses={200: OpenApiResponse(description="List of wallets")}
    )
    def get(self, request: Request):
        """List user wallets."""
        wallets = Wallet.objects.filter(user=request.user, is_active=True)
        return ok({
            'wallets': [
                {
                    'id': str(w.id),
                    'address': w.address,
                    'network': w.network,
                    'created_at': w.created_at.isoformat(),
                }
                for w in wallets
            ]
        })


class WalletBalanceView(APIView):
    """Get wallet balance."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["DEX"],
        summary="Get wallet balance",
        description="Get token balance for a wallet address.",
        parameters=[
            OpenApiParameter(name="tokenAddress", location=OpenApiParameter.QUERY, type=str, required=True)
        ],
        responses={200: OpenApiResponse(description="Wallet balance")}
    )
    def get(self, request: Request, address: str):
        """Get wallet balance."""
        wallet = get_object_or_404(Wallet, address=address, user=request.user)
        token_address = request.query_params.get('tokenAddress')
        
        if not token_address:
            return bad_request("tokenAddress parameter required")
        
        try:
            w3 = get_web3_provider()
            balance = get_token_balance(w3, token_address, wallet.address)
            return ok({
                'address': wallet.address,
                'tokenAddress': token_address,
                'balance': str(balance)
            })
        except Exception as e:
            return bad_request(f"Failed to get balance: {str(e)}", status=500)


class OrderView(APIView):
    """Order management endpoints."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["DEX"],
        summary="Create order",
        description="Create a buy or sell order.",
        request=OrderCreateSerializer,
        responses={200: OpenApiResponse(description="Order created successfully")}
    )
    @idempotent
    @ratelimit(key='user', rate='30/m', method='POST', block=True)
    def post(self, request: Request):
        """Create an order."""
        ser = OrderCreateSerializer(data=request.data)
        if not ser.is_valid():
            return bad_request(ser.errors)
        
        wallet_address = request.data.get('walletAddress')
        if not wallet_address:
            return bad_request("walletAddress required")
        
        wallet = get_object_or_404(Wallet, address=wallet_address, user=request.user)
        order = create_order(wallet, ser.validated_data)
        
        # Try to match orders
        match_orders(order.isin)
        
        return ok({
            'orderId': str(order.id),
            'status': order.status,
            'isin': order.isin,
            'orderType': order.order_type,
        })
    
    @extend_schema(
        tags=["DEX"],
        summary="List orders",
        description="List orders with optional filters.",
        parameters=[
            OpenApiParameter(name="isin", location=OpenApiParameter.QUERY, type=str),
            OpenApiParameter(name="status", location=OpenApiParameter.QUERY, type=str),
        ],
        responses={200: OpenApiResponse(description="List of orders")}
    )
    def get(self, request: Request):
        """List orders."""
        wallets = Wallet.objects.filter(user=request.user)
        orders = Order.objects.filter(wallet__in=wallets)
        
        if isin := request.query_params.get('isin'):
            orders = orders.filter(isin=isin)
        if status := request.query_params.get('status'):
            orders = orders.filter(status=status)
        
        orders = orders.order_by('-created_at')[:50]
        
        return ok({
            'orders': [
                {
                    'id': str(o.id),
                    'isin': o.isin,
                    'orderType': o.order_type,
                    'quantity': str(o.quantity),
                    'filledQuantity': str(o.filled_quantity),
                    'pricePerUnit': str(o.price_per_unit),
                    'status': o.status,
                    'createdAt': o.created_at.isoformat(),
                }
                for o in orders
            ]
        })


class OrderDetailView(APIView):
    """Order detail and cancellation."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(tags=["DEX"], summary="Get order details")
    def get(self, request: Request, pk: str):
        """Get order details."""
        order = get_object_or_404(Order, pk=pk)
        if order.wallet.user != request.user:
            return bad_request("Unauthorized", status=403)
        
        return ok({
            'id': str(order.id),
            'isin': order.isin,
            'orderType': order.order_type,
            'quantity': str(order.quantity),
            'filledQuantity': str(order.filled_quantity),
            'pricePerUnit': str(order.price_per_unit),
            'status': order.status,
            'txHash': order.tx_hash,
            'createdAt': order.created_at.isoformat(),
        })
    
    @extend_schema(tags=["DEX"], summary="Cancel order")
    def patch(self, request: Request, pk: str):
        """Cancel an order."""
        order = get_object_or_404(Order, pk=pk)
        if order.wallet.user != request.user:
            return bad_request("Unauthorized", status=403)
        
        if cancel_order(order):
            return ok({'message': 'Order cancelled', 'orderId': str(order.id)})
        return bad_request("Order cannot be cancelled")


class OrderBookView(APIView):
    """Order book endpoint."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["DEX"],
        summary="Get order book",
        description="Get order book for an ISIN.",
        parameters=[
            OpenApiParameter(name="isin", location=OpenApiParameter.QUERY, type=str, required=True)
        ],
        responses={200: OpenApiResponse(description="Order book")}
    )
    def get(self, request: Request):
        """Get order book."""
        isin = request.query_params.get('isin')
        if not isin:
            return bad_request("isin parameter required")
        
        order_book = get_order_book(isin)
        return ok(order_book)


class SwapView(APIView):
    """Swap management endpoints."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["DEX"],
        summary="Create swap",
        description="Create a token swap transaction.",
        request=SwapCreateSerializer,
        responses={200: OpenApiResponse(description="Swap created successfully")}
    )
    @idempotent
    @ratelimit(key='user', rate='20/m', method='POST', block=True)
    def post(self, request: Request):
        """Create a swap."""
        ser = SwapCreateSerializer(data=request.data)
        if not ser.is_valid():
            return bad_request(ser.errors)
        
        wallet_address = request.data.get('walletAddress')
        if not wallet_address:
            return bad_request("walletAddress required")
        
        wallet = get_object_or_404(Wallet, address=wallet_address, user=request.user)
        swap_data = ser.validated_data.copy()
        
        if swap_data.get('wallet_to_address'):
            wallet_to = Wallet.objects.filter(address=swap_data['wallet_to_address']).first()
            swap_data['wallet_to'] = wallet_to
        
        swap = create_swap(wallet, swap_data)
        return ok({
            'swapId': str(swap.id),
            'status': swap.status,
            'tokenFrom': swap.token_from,
            'tokenTo': swap.token_to,
        })
    
    @extend_schema(tags=["DEX"], summary="List swaps")
    def get(self, request: Request):
        """List swaps."""
        wallets = Wallet.objects.filter(user=request.user)
        swaps = Swap.objects.filter(wallet_from__in=wallets).order_by('-created_at')[:50]
        
        return ok({
            'swaps': [
                {
                    'id': str(s.id),
                    'tokenFrom': s.token_from,
                    'tokenTo': s.token_to,
                    'amountFrom': str(s.amount_from),
                    'amountTo': str(s.amount_to),
                    'status': s.status,
                    'isP2P': s.is_p2p,
                    'createdAt': s.created_at.isoformat(),
                }
                for s in swaps
            ]
        })


class SwapDetailView(APIView):
    """Swap detail endpoint."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(tags=["DEX"], summary="Get swap details")
    def get(self, request: Request, pk: str):
        """Get swap details."""
        swap = get_object_or_404(Swap, pk=pk)
        if swap.wallet_from.user != request.user:
            return bad_request("Unauthorized", status=403)
        
        return ok({
            'id': str(swap.id),
            'tokenFrom': swap.token_from,
            'tokenTo': swap.token_to,
            'amountFrom': str(swap.amount_from),
            'amountTo': str(swap.amount_to),
            'exchangeRate': str(swap.exchange_rate),
            'status': swap.status,
            'txHashFrom': swap.tx_hash_from,
            'txHashTo': swap.tx_hash_to,
            'isP2P': swap.is_p2p,
            'createdAt': swap.created_at.isoformat(),
        })


class TradeView(APIView):
    """Trade listing endpoint."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["DEX"],
        summary="List trades",
        description="List executed trades.",
        parameters=[
            OpenApiParameter(name="isin", location=OpenApiParameter.QUERY, type=str),
        ],
        responses={200: OpenApiResponse(description="List of trades")}
    )
    def get(self, request: Request):
        """List trades."""
        wallets = Wallet.objects.filter(user=request.user)
        trades = Trade.objects.filter(
            buy_order__wallet__in=wallets
        ) | Trade.objects.filter(
            sell_order__wallet__in=wallets
        )
        
        if isin := request.query_params.get('isin'):
            trades = trades.filter(isin=isin)
        
        trades = trades.order_by('-created_at')[:50]
        
        return ok({
            'trades': [
                {
                    'id': str(t.id),
                    'isin': t.isin,
                    'quantity': str(t.quantity),
                    'pricePerUnit': str(t.price_per_unit),
                    'totalValue': str(t.total_value),
                    'txHash': t.tx_hash,
                    'createdAt': t.created_at.isoformat(),
                }
                for t in trades
            ]
        })

