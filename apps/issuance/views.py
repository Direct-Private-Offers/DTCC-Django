from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from apps.core.responses import ok, bad_request, not_found
from apps.core.idempotency import idempotent
from .serializers import IssuanceRequestSerializer
from apps.euroclear.client import EuroclearClient
from apps.core.permissions import IsInGroup
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
from apps.receipts.services import create_receipt
from decimal import Decimal
import uuid
from drf_spectacular.utils import (
    extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
)
from drf_spectacular.types import OpenApiTypes
from apps.core.schemas import ERROR_400, ERROR_401, ERROR_403, ERROR_404, ERROR_500


class IssuanceView(APIView):

    def get_permissions(self):
        # POST requires 'issuer' group; GET requires authentication only
        if getattr(self.request, 'method', '').upper() == 'POST':
            return [IsAuthenticated(), IsInGroup.with_names(["issuer"]) ]
        return [IsAuthenticated()]

    @extend_schema(
        tags=["Issuance"],
        summary="Initiate token issuance",
        description=(
            "Validates investor eligibility and initiates tokenization for a given ISIN. "
            "Requires group 'issuer'. Idempotent: pass Idempotency-Key header."
        ),
        request=IssuanceRequestSerializer,
        examples=[
            OpenApiExample(
                "Basic issuance",
                value={
                    "isin": "US0378331005",
                    "investorAddress": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                    "amount": "1000",
                    "offeringType": "RegD",
                    "metadata": {"note": "Initial tokenization"}
                },
            ),
            OpenApiExample(
                "Full issuance with Euroclear reference",
                value={
                    "isin": "US0378331005",
                    "investorAddress": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                    "amount": "5000.50",
                    "euroclearRef": "EUR-REF-2025-001",
                    "ipfsCID": "QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG",
                    "offeringType": "144A",
                    "metadata": {
                        "note": "Institutional investor",
                        "kycStatus": "approved"
                    }
                },
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Tokenization initiated successfully",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "timestamp": {"type": "string", "example": "2025-01-15T10:30:00Z"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "transactionId": {"type": "string", "example": "TX-US0378331005"},
                                "isin": {"type": "string", "example": "US0378331005"},
                                "investor": {"type": "string", "example": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"},
                                "amount": {"type": "string", "example": "1000"},
                                "status": {"type": "string", "enum": ["PENDING", "CONFIRMED"], "example": "PENDING"}
                            }
                        }
                    }
                },
                examples=[
                    {
                        "success": True,
                        "timestamp": "2025-01-15T10:30:00Z",
                        "data": {
                            "transactionId": "TX-US0378331005",
                            "isin": "US0378331005",
                            "investor": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                            "amount": "1000",
                            "status": "PENDING"
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
        ser = IssuanceRequestSerializer(data=request.data)
        if not ser.is_valid():
            return bad_request(ser.errors)
        payload = ser.validated_data

        try:
            client = EuroclearClient()
            security = client.get_security_details(payload['isin'])
            if not security:
                return not_found(f"Security with ISIN {payload['isin']} not found")

            if not client.validate_investor(payload['isin'], payload['investorAddress']):
                return bad_request('Investor not authorized for this security', status=403)

            tx_id = client.initiate_tokenization(payload)
            
            # Generate receipt for issuance
            try:
                transaction_uuid = str(uuid.uuid4())
                receipt = create_receipt(
                    receipt_type='ISSUANCE',
                    investor=request.user,  # Link to issuer user, investor address in metadata
                    transaction_id=transaction_uuid,
                    isin=payload['isin'],
                    quantity=Decimal(str(payload['amount'])),
                    currency=security.get('currency', 'USD'),
                    metadata={
                        'investor_address': payload['investorAddress'],
                        'transaction_id': tx_id,
                        'offering_type': payload.get('offeringType', 'RegD'),
                        'euroclear_ref': payload.get('euroclearRef'),
                        'issuer_name': request.user.username,
                    }
                )
            except Exception as receipt_error:
                # Log receipt generation error but don't fail the issuance
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to generate receipt for issuance {tx_id}: {str(receipt_error)}")
            
            return ok({
                'transactionId': tx_id,
                'isin': payload['isin'],
                'investor': payload['investorAddress'],
                'amount': str(payload['amount']),
                'status': 'PENDING',
            })
        except Exception as e:
            return bad_request(f"Failed to process issuance: {str(e)}", status=500)

    @extend_schema(
        tags=["Issuance"],
        summary="Get security details by ISIN",
        description="Returns Euroclear security details for the provided ISIN.",
        parameters=[
            OpenApiParameter(
                name="isin",
                description="Security ISIN (12 characters, e.g., US0378331005)",
                required=True,
                type=str,
                location=OpenApiParameter.QUERY,
                examples=[
                    OpenApiExample("Apple Inc", value="US0378331005"),
                    OpenApiExample("Microsoft Corp", value="US5949181045"),
                ]
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Security details retrieved successfully",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "timestamp": {"type": "string", "example": "2025-01-15T10:30:00Z"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "isin": {"type": "string", "example": "US0378331005"},
                                "name": {"type": "string", "example": "Mock Security"},
                                "currency": {"type": "string", "example": "USD"}
                            }
                        }
                    }
                },
                examples=[
                    {
                        "success": True,
                        "timestamp": "2025-01-15T10:30:00Z",
                        "data": {
                            "isin": "US0378331005",
                            "name": "Mock Security",
                            "currency": "USD"
                        }
                    }
                ]
            ),
            400: ERROR_400,
            401: ERROR_401,
            404: ERROR_404,
            500: ERROR_500,
        }
    )
    def get(self, request: Request):
        isin = request.query_params.get('isin')
        if not isin:
            return bad_request('ISIN parameter required')
        try:
            client = EuroclearClient()
            security = client.get_security_details(isin)
            if not security:
                return not_found(f"Security with ISIN {isin} not found")
            return ok(security)
        except Exception as e:
            return bad_request(f"Failed to fetch security details: {str(e)}", status=500)
