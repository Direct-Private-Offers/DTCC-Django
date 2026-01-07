from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
# Ratelimit: provide a no-op fallback in dev if package unavailable
try:
    from django_ratelimit.decorators import ratelimit
except Exception:
    def ratelimit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
from apps.core.permissions import IsInGroup
from apps.core.responses import ok, bad_request
from apps.core.idempotency import idempotent
from .serializers import SettlementCreateSerializer
from .models import Settlement
from drf_spectacular.utils import (
    extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
)
from apps.core.schemas import ERROR_400, ERROR_401, ERROR_403, ERROR_404, ERROR_500


class SettlementView(APIView):

    def get_permissions(self):
        # POST requires issuer; GET requires authentication
        if getattr(self.request, 'method', '').upper() == 'POST':
            return [IsAuthenticated(), IsInGroup.with_names(["issuer"]) ]
        return [IsAuthenticated()]

    @extend_schema(
        tags=["Settlement"],
        summary="Create Euroclear settlement instruction",
        description=(
            "Creates a settlement instruction for Euroclear. Requires group 'issuer'. "
            "Idempotent with Idempotency-Key header. Supports both simplified and full formats."
        ),
        request=SettlementCreateSerializer,
        examples=[
            OpenApiExample(
                "Simplified format",
                value={
                    "isin": "US0378331005",
                    "quantity": "10.0",
                    "tradeDate": "2025-01-15",
                    "valueDate": "2025-01-17",
                    "counterparty": "EUROCLEAR-CP",
                    "account": "ACC-001"
                }
            ),
            OpenApiExample(
                "Full format with addresses",
                value={
                    "isin": "US0378331005",
                    "tradeRef": "TRADE-2025-001",
                    "fromAddress": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                    "toAddress": "0x8ba1f109551bD432803012645Hac136c22C9e8",
                    "amount": "1000.50",
                    "euroclearRef": "EUR-REF-2025-001",
                    "tradeDate": "2025-01-15",
                    "valueDate": "2025-01-17"
                }
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Settlement created successfully",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "timestamp": {"type": "string", "example": "2025-01-15T10:30:00Z"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "settlementId": {"type": "string", "format": "uuid", "example": "550e8400-e29b-41d4-a716-446655440000"},
                                "status": {"type": "string", "enum": ["INITIATED", "MATCHED", "SETTLED", "FAILED"], "example": "INITIATED"}
                            }
                        }
                    }
                },
                examples=[
                    {
                        "success": True,
                        "timestamp": "2025-01-15T10:30:00Z",
                        "data": {
                            "settlementId": "550e8400-e29b-41d4-a716-446655440000",
                            "status": "INITIATED"
                        }
                    }
                ]
            ),
            400: ERROR_400,
            401: ERROR_401,
            403: ERROR_403,
            500: ERROR_500,
        }
    )
    @idempotent
    @ratelimit(key='user', rate='60/m', method='POST', block=True)
    def post(self, request: Request) -> Response:
        ser = SettlementCreateSerializer(data=request.data)
        if not ser.is_valid():
            return bad_request(ser.errors)
        v = ser.validated_data
        
        # Handle both formats: simplified and full (with addresses)
        quantity = v.get('quantity') or v.get('amount')
        if quantity is None:
            return bad_request("Either 'quantity' or 'amount' must be provided")
        
        timeline_data = {'created': True}
        
        # Store additional fields in timeline if using new format
        if v.get('tradeRef'):
            timeline_data['tradeRef'] = v['tradeRef']
        if v.get('fromAddress'):
            timeline_data['fromAddress'] = v['fromAddress']
        if v.get('toAddress'):
            timeline_data['toAddress'] = v['toAddress']
        if v.get('euroclearRef'):
            timeline_data['euroclearRef'] = v['euroclearRef']
        
        try:
            s = Settlement.objects.create(
                source=Settlement.Source.EUROCLEAR,
                isin=v['isin'],
                quantity=quantity,
                trade_date=v.get('tradeDate'),
                value_date=v.get('valueDate'),
                counterparty=v.get('counterparty') or v.get('fromAddress'),
                account=v.get('account'),
                status=Settlement.Status.INITIATED,
                timeline=timeline_data,
            )
        except Exception as e:
            return bad_request(f"Failed to create settlement: {str(e)}", status=500)
        # In a later step: enqueue Celery job to sync lifecycle
        return ok({
            'settlementId': str(s.id),
            'status': s.status,
        })

    @extend_schema(
        tags=["Settlement"],
        summary="Get settlement status",
        description="Retrieves detailed status and information for a settlement by its UUID.",
        parameters=[
            OpenApiParameter(
                name="pk",
                location=OpenApiParameter.PATH,
                type=str,
                description="Settlement UUID",
                examples=[OpenApiExample("Example UUID", value="550e8400-e29b-41d4-a716-446655440000")]
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Settlement details retrieved successfully",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "timestamp": {"type": "string", "example": "2025-01-15T10:30:00Z"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "settlementId": {"type": "string", "format": "uuid"},
                                "source": {"type": "string", "enum": ["euroclear", "clearstream"]},
                                "isin": {"type": "string"},
                                "quantity": {"type": "string"},
                                "status": {"type": "string", "enum": ["INITIATED", "MATCHED", "SETTLED", "FAILED"]},
                                "timeline": {"type": "object"},
                                "tradeDate": {"type": "string", "format": "date", "nullable": True},
                                "valueDate": {"type": "string", "format": "date", "nullable": True},
                                "counterparty": {"type": "string", "nullable": True},
                                "account": {"type": "string", "nullable": True},
                                "txHash": {"type": "string", "nullable": True}
                            }
                        }
                    }
                },
                examples=[
                    {
                        "success": True,
                        "timestamp": "2025-01-15T10:30:00Z",
                        "data": {
                            "settlementId": "550e8400-e29b-41d4-a716-446655440000",
                            "source": "euroclear",
                            "isin": "US0378331005",
                            "quantity": "10.0",
                            "status": "INITIATED",
                            "timeline": {"created": True},
                            "tradeDate": "2025-01-15",
                            "valueDate": "2025-01-17",
                            "counterparty": "EUROCLEAR-CP",
                            "account": "ACC-001",
                            "txHash": None
                        }
                    }
                ]
            ),
            401: ERROR_401,
            404: ERROR_404,
        }
    )
    def get(self, request: Request, pk: str) -> Response:
        s = get_object_or_404(Settlement, pk=pk)
        return ok({
            'settlementId': str(s.id),
            'source': s.source,
            'isin': s.isin,
            'quantity': str(s.quantity),
            'status': s.status,
            'timeline': s.timeline,
            'tradeDate': s.trade_date,
            'valueDate': s.value_date,
            'counterparty': s.counterparty,
            'account': s.account,
            'txHash': s.tx_hash,
        })
