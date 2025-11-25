from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from ratelimit.decorators import ratelimit
from django.utils.dateparse import parse_date
from apps.core.permissions import IsInGroup
from apps.core.responses import ok, bad_request
from apps.core.idempotency import idempotent
from .serializers import CorporateActionCreateSerializer
from .models import CorporateAction
from drf_spectacular.utils import (
    extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
)
from apps.core.schemas import ERROR_400, ERROR_401, ERROR_403, ERROR_500


class CorporateActionsView(APIView):

    def get_permissions(self):
        # POST requires issuer; GET requires authentication
        if getattr(self.request, 'method', '').upper() == 'POST':
            return [IsAuthenticated(), IsInGroup.with_names(["issuer"]) ]
        return [IsAuthenticated()]

    @extend_schema(
        tags=["Corporate Actions"],
        summary="Schedule/apply a corporate action",
        description=(
            "Creates a corporate action record (e.g., DIVIDEND, SPLIT, MERGER, RIGHTS_ISSUE). "
            "Requires group 'issuer'. Idempotent with Idempotency-Key header. "
            "Supports both simplified and full formats."
        ),
        request=CorporateActionCreateSerializer,
        examples=[
            OpenApiExample(
                "Dividend - simplified",
                value={
                    "isin": "US0378331005",
                    "type": "DIVIDEND",
                    "recordDate": "2025-12-31",
                    "paymentDate": "2026-01-15",
                    "amountPerShare": "1.00",
                    "currency": "USD"
                }
            ),
            OpenApiExample(
                "Stock split",
                value={
                    "isin": "US0378331005",
                    "type": "SPLIT",
                    "recordDate": "2025-06-01",
                    "effectiveDate": "2025-06-15",
                    "factor": "2.0",
                    "reference": "SPLIT-2025-001"
                }
            ),
            OpenApiExample(
                "Full format with reference",
                value={
                    "isin": "US0378331005",
                    "actionType": "DIVIDEND",
                    "recordDate": "2025-12-31",
                    "effectiveDate": "2026-01-15",
                    "paymentDate": "2026-01-20",
                    "reference": "DIV-2025-Q4",
                    "data": {
                        "dividendType": "regular",
                        "taxWithholding": "0.15"
                    },
                    "amountPerShare": "1.00",
                    "currency": "USD"
                }
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Corporate action created successfully",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "timestamp": {"type": "string", "example": "2025-01-15T10:30:00Z"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "corporateActionId": {"type": "string", "format": "uuid", "example": "550e8400-e29b-41d4-a716-446655440000"},
                                "status": {"type": "string", "example": "SCHEDULED"}
                            }
                        }
                    }
                },
                examples=[
                    {
                        "success": True,
                        "timestamp": "2025-01-15T10:30:00Z",
                        "data": {
                            "corporateActionId": "550e8400-e29b-41d4-a716-446655440000",
                            "status": "SCHEDULED"
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
    @ratelimit(key='user', rate='60/m', method='POST', block=True)
    @idempotent
    def post(self, request: Request) -> Response:
        ser = CorporateActionCreateSerializer(data=request.data)
        if not ser.is_valid():
            return bad_request(ser.errors)
        v = ser.validated_data
        try:
            ca = CorporateAction.objects.create(
                isin=v['isin'],
                type=v['type'],
                record_date=v['recordDate'],
                effective_date=v.get('effectiveDate'),
                payment_date=v.get('paymentDate'),
                factor=v.get('factor'),
                amount_per_share=v.get('amountPerShare'),
                currency=v.get('currency'),
                reference=v.get('reference'),
                action_data=v.get('data') or {},
                status='SCHEDULED',
            )
        except Exception as e:
            return bad_request(f"Failed to create corporate action: {str(e)}", status=500)
        # In a later step: enqueue Celery task to apply on chain at record/payment date
        return ok({
            'corporateActionId': str(ca.id),
            'status': ca.status,
        })

    @extend_schema(
        tags=["Corporate Actions"],
        summary="List corporate actions",
        description="Retrieves a list of corporate actions with optional filtering by ISIN, type, and date range.",
        parameters=[
            OpenApiParameter(
                name="isin",
                location=OpenApiParameter.QUERY,
                required=False,
                type=str,
                description="Filter by ISIN",
                examples=[OpenApiExample("Apple Inc", value="US0378331005")]
            ),
            OpenApiParameter(
                name="type",
                location=OpenApiParameter.QUERY,
                required=False,
                type=str,
                description="Filter by action type",
                enum=["DIVIDEND", "SPLIT", "MERGER", "RIGHTS_ISSUE"],
                examples=[OpenApiExample("Dividend", value="DIVIDEND")]
            ),
            OpenApiParameter(
                name="from",
                location=OpenApiParameter.QUERY,
                required=False,
                type=str,
                format="date",
                description="Record date from (YYYY-MM-DD)",
                examples=[OpenApiExample("Start date", value="2025-01-01")]
            ),
            OpenApiParameter(
                name="to",
                location=OpenApiParameter.QUERY,
                required=False,
                type=str,
                format="date",
                description="Record date to (YYYY-MM-DD)",
                examples=[OpenApiExample("End date", value="2025-12-31")]
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Corporate actions retrieved successfully",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "timestamp": {"type": "string", "example": "2025-01-15T10:30:00Z"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "items": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "string", "format": "uuid"},
                                            "isin": {"type": "string"},
                                            "type": {"type": "string"},
                                            "recordDate": {"type": "string", "format": "date"},
                                            "effectiveDate": {"type": "string", "format": "date", "nullable": True},
                                            "paymentDate": {"type": "string", "format": "date", "nullable": True},
                                            "reference": {"type": "string", "nullable": True},
                                            "data": {"type": "object", "nullable": True},
                                            "status": {"type": "string"},
                                            "txHash": {"type": "string", "nullable": True}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                examples=[
                    {
                        "success": True,
                        "timestamp": "2025-01-15T10:30:00Z",
                        "data": {
                            "items": [
                                {
                                    "id": "550e8400-e29b-41d4-a716-446655440000",
                                    "isin": "US0378331005",
                                    "type": "DIVIDEND",
                                    "recordDate": "2025-12-31",
                                    "effectiveDate": "2026-01-15",
                                    "paymentDate": "2026-01-20",
                                    "reference": "DIV-2025-Q4",
                                    "data": {},
                                    "status": "SCHEDULED",
                                    "txHash": None
                                }
                            ]
                        }
                    }
                ]
            ),
            401: ERROR_401,
            500: ERROR_500,
        }
    )
    def get(self, request: Request) -> Response:
        isin = request.query_params.get('isin')
        type_ = request.query_params.get('type')
        from_ = request.query_params.get('from')
        to_ = request.query_params.get('to')
        qs = CorporateAction.objects.all()
        if isin:
            qs = qs.filter(isin=isin)
        if type_:
            qs = qs.filter(type=type_)
        if from_:
            d = parse_date(from_)
            if d:
                qs = qs.filter(record_date__gte=d)
        if to_:
            d = parse_date(to_)
            if d:
                qs = qs.filter(record_date__lte=d)
        data = [
            {
                'id': str(x.id),
                'isin': x.isin,
                'type': x.type,
                'recordDate': x.record_date,
                'effectiveDate': x.effective_date,
                'paymentDate': x.payment_date,
                'reference': x.reference,
                'data': x.action_data,
                'status': x.status,
                'txHash': x.tx_hash,
            }
            for x in qs.order_by('-record_date')[:200]
        ]
        return ok({'items': data})
