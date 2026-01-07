from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from apps.core.responses import ok, bad_request, not_found
from .serializers import DerivativeRequestSerializer
from apps.euroclear.client import EuroclearClient
from apps.core.permissions import IsInGroup
# Ratelimit: provide a no-op fallback in dev if package unavailable
try:
    from django_ratelimit.decorators import ratelimit
except Exception:
    def ratelimit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
from apps.core.idempotency import idempotent
from drf_spectacular.utils import (
    extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
)
from apps.core.schemas import ERROR_400, ERROR_401, ERROR_403, ERROR_404, ERROR_500


class DerivativesView(APIView):

    def get_permissions(self):
        # Require 'reporter' group for POST; GET requires authentication only
        if getattr(self.request, 'method', '').upper() == 'POST':
            return [IsAuthenticated(), IsInGroup.with_names(["reporter"]) ]
        return [IsAuthenticated()]

    @extend_schema(
        tags=["Derivatives"],
        summary="Report a derivative trade (DTCC/CSA)",
        description=(
            "Reports a derivative trade associated with an ISIN for DTCC/CSA compliance. "
            "Requires group 'reporter'. Idempotent: pass Idempotency-Key header."
        ),
        request=DerivativeRequestSerializer,
        examples=[
            OpenApiExample(
                "New derivative report",
                value={
                    "isin": "US0378331005",
                    "uti": "",
                    "priorUti": "",
                    "upi": "UPI-TEST-001",
                    "effectiveDate": "2025-01-01",
                    "expirationDate": "2026-01-01",
                    "executionTimestamp": "2025-01-01T12:00:00Z",
                    "notionalAmount": "1000000",
                    "notionalCurrency": "USD",
                    "productType": "SWAP",
                    "underlyingAsset": "AAPL",
                    "counterpartyLei": "5493001KJTIIGC8Y1R12",
                    "reportingEntityLei": "5493001KJTIIGC8Y1R12",
                    "action": "NEW"
                }
            ),
            OpenApiExample(
                "Amend existing derivative",
                value={
                    "isin": "US0378331005",
                    "uti": "UTI-2025-001-ABC",
                    "priorUti": "UTI-2025-001-ABC",
                    "upi": "UPI-TEST-001",
                    "effectiveDate": "2025-01-01",
                    "expirationDate": "2026-06-01",
                    "executionTimestamp": "2025-01-01T12:00:00Z",
                    "notionalAmount": "1500000",
                    "notionalCurrency": "USD",
                    "productType": "SWAP",
                    "underlyingAsset": "AAPL",
                    "action": "AMEND"
                }
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Derivative reported successfully",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "timestamp": {"type": "string", "example": "2025-01-15T10:30:00Z"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "uti": {"type": "string", "example": "UTI-US0378331005"},
                                "isin": {"type": "string", "example": "US0378331005"},
                                "status": {"type": "string", "example": "REPORTED"}
                            }
                        }
                    }
                },
                examples=[
                    {
                        "success": True,
                        "timestamp": "2025-01-15T10:30:00Z",
                        "data": {
                            "uti": "UTI-US0378331005",
                            "isin": "US0378331005",
                            "status": "REPORTED"
                        }
                    }
                ]
            ),
            400: ERROR_400,
            401: ERROR_401,
            403: ERROR_403,
            404: ERROR_404,
            500: ERROR_500,
        }
    )
    @idempotent
    @ratelimit(key='user', rate='60/m', method='POST', block=True)
    def post(self, request: Request):
        ser = DerivativeRequestSerializer(data=request.data)
        if not ser.is_valid():
            return bad_request(ser.errors)
        payload = ser.validated_data

        try:
            client = EuroclearClient()
            security = client.get_security_details(payload['isin'])
            if not security:
                return not_found(f"Security with ISIN {payload['isin']} not found")

            uti = client.report_derivative(payload)
            return ok({
                'uti': uti,
                'isin': payload['isin'],
                'status': 'REPORTED'
            })
        except Exception as e:
            return bad_request(f"Failed to report derivative: {str(e)}", status=500)

    @extend_schema(
        tags=["Derivatives"],
        summary="Get derivative by UTI or ISIN",
        description="Returns derivative details using either UTI (Unique Trade Identifier) or ISIN. At least one parameter is required.",
        parameters=[
            OpenApiParameter(
                name="uti",
                description="Unique Trade Identifier",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
                examples=[OpenApiExample("Example UTI", value="UTI-2025-001-ABC")]
            ),
            OpenApiParameter(
                name="isin",
                description="Underlying ISIN",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
                examples=[OpenApiExample("Apple Inc", value="US0378331005")]
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Derivative details retrieved successfully",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "timestamp": {"type": "string", "example": "2025-01-15T10:30:00Z"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "uti": {"type": "string", "example": "UTI-2025-001-ABC"},
                                "isin": {"type": "string", "example": "US0378331005"},
                                "derivativeData": {
                                    "type": "object",
                                    "properties": {
                                        "uti": {"type": "string"},
                                        "priorUti": {"type": "string"},
                                        "upi": {"type": "string"},
                                        "effectiveDate": {"type": "string", "format": "date-time", "nullable": True},
                                        "expirationDate": {"type": "string", "format": "date-time", "nullable": True},
                                        "executionTimestamp": {"type": "string", "format": "date-time", "nullable": True},
                                        "notionalAmount": {"type": "number"},
                                        "notionalCurrency": {"type": "string"},
                                        "productType": {"type": "string"},
                                        "underlyingAsset": {"type": "string"}
                                    }
                                },
                                "status": {"type": "string", "example": "ACTIVE"}
                            }
                        }
                    }
                },
                examples=[
                    {
                        "success": True,
                        "timestamp": "2025-01-15T10:30:00Z",
                        "data": {
                            "uti": "UTI-2025-001-ABC",
                            "isin": "US0378331005",
                            "derivativeData": {
                                "uti": "UTI-2025-001-ABC",
                                "priorUti": "",
                                "upi": "UPI_MOCK_001",
                                "effectiveDate": None,
                                "expirationDate": None,
                                "executionTimestamp": None,
                                "notionalAmount": 1000000,
                                "notionalCurrency": "USD",
                                "productType": "SWAP",
                                "underlyingAsset": "AAPL"
                            },
                            "status": "ACTIVE"
                        }
                    }
                ]
            ),
            400: ERROR_400,
            401: ERROR_401,
            500: ERROR_500,
        }
    )
    def get(self, request: Request):
        uti = request.query_params.get('uti')
        isin = request.query_params.get('isin')
        if not uti and not isin:
            return bad_request('UTI or ISIN parameter required')
        # return mock shape for now
        data = {
            'uti': uti or 'MOCK_UTI_123',
            'isin': isin or 'US0378331005',
            'derivativeData': {
                'uti': uti or 'MOCK_UTI_123',
                'priorUti': '',
                'upi': 'UPI_MOCK_001',
                'effectiveDate': None,
                'expirationDate': None,
                'executionTimestamp': None,
                'notionalAmount': 1000000,
                'notionalCurrency': 'USD',
                'productType': 'SWAP',
                'underlyingAsset': 'AAPL',
            },
            'status': 'ACTIVE',
        }
        return ok(data)
