from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from django_ratelimit.decorators import ratelimit
from apps.core.permissions import IsInGroup
from apps.core.responses import ok, bad_request, not_found
from apps.core.idempotency import idempotent
from apps.settlement.models import Settlement
from .models import ClearstreamAccount, Position
from .serializers import (
    AccountCreateSerializer,
    InstructionCreateSerializer,
    ClearstreamSettlementCreateSerializer,
)
from drf_spectacular.utils import (
    extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
)
from apps.core.schemas import ERROR_400, ERROR_401, ERROR_403, ERROR_404, ERROR_500
from .client import ClearstreamClient


class ClearstreamAccountView(APIView):
    def get_permissions(self):
        # Account linking requires privileged role (ops or issuer)
        return [IsAuthenticated(), IsInGroup.with_names(["ops", "issuer"]) ]

    @extend_schema(
        tags=["Clearstream"],
        summary="Link Clearstream CSD account",
        description=(
            "Creates or links a Clearstream CSD (Central Securities Depository) account record. "
            "Requires group 'ops' or 'issuer'. Idempotent with Idempotency-Key header."
        ),
        request=AccountCreateSerializer,
        examples=[
            OpenApiExample(
                "Account link with LEI",
                value={
                    "csd_participant": "P1",
                    "csd_account": "ACC-001",
                    "lei": "5493001KJTIIGC8Y1R12",
                    "permissions": ["TRADE", "SETTLE"]
                }
            ),
            OpenApiExample(
                "Basic account link",
                value={
                    "csd_participant": "P1",
                    "csd_account": "ACC-001"
                }
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Account linked successfully",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "timestamp": {"type": "string", "example": "2025-01-15T10:30:00Z"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "accountId": {"type": "string", "format": "uuid", "example": "550e8400-e29b-41d4-a716-446655440000"},
                                "linked": {"type": "boolean", "example": True}
                            }
                        }
                    }
                },
                examples=[
                    {
                        "success": True,
                        "timestamp": "2025-01-15T10:30:00Z",
                        "data": {
                            "accountId": "550e8400-e29b-41d4-a716-446655440000",
                            "linked": True
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
        ser = AccountCreateSerializer(data=request.data)
        if not ser.is_valid():
            return bad_request(ser.errors)
        v = ser.validated_data
        try:
            # Link account via Clearstream PMI API
            client = ClearstreamClient()
            result = client.link_account(
                csd_participant=v['csd_participant'],
                csd_account=v['csd_account'],
                lei=v.get('lei'),
                permissions=v.get('permissions')
            )
            
            if not result:
                return bad_request("Failed to link account in Clearstream PMI", status=500)
            
            # Create or update local account record
            acct, _ = ClearstreamAccount.objects.get_or_create(
                csd_account=v['csd_account'],
                defaults={
                    'csd_participant': v['csd_participant'],
                    'lei': v.get('lei'),
                    'permissions': v.get('permissions') or [],
                    'linked': result.get('linked', True),
                },
            )
            
            # Update linked status if account already existed
            if acct.linked != result.get('linked', True):
                acct.linked = result.get('linked', True)
                acct.save()
            
            return ok({'accountId': str(acct.id), 'linked': acct.linked})
        except Exception as e:
            return bad_request(f"Failed to create/link account: {str(e)}", status=500)


class PositionsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Clearstream"],
        summary="Get Clearstream positions",
        description="Retrieves position balances for a specific Clearstream CSD account.",
        parameters=[
            OpenApiParameter(
                name="account",
                location=OpenApiParameter.PATH,
                type=str,
                description="CSD account number",
                examples=[OpenApiExample("Example account", value="ACC-001")]
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Positions retrieved successfully",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "timestamp": {"type": "string", "example": "2025-01-15T10:30:00Z"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "balances": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "isin": {"type": "string"},
                                            "quantity": {"type": "string"},
                                            "settled": {"type": "string"},
                                            "pending": {"type": "string"},
                                            "asOf": {"type": "string", "format": "date-time", "nullable": True}
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
                            "balances": [
                                {
                                    "isin": "US0378331005",
                                    "quantity": "1000",
                                    "settled": "950",
                                    "pending": "50",
                                    "asOf": "2025-01-15T10:00:00Z"
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
    def get(self, request: Request, account: str) -> Response:
        try:
            # Sync positions from Clearstream PMI
            client = ClearstreamClient()
            positions_data = client.get_positions(account)
            
            # Update local positions
            from django.utils import timezone
            for pos_data in positions_data:
                Position.objects.update_or_create(
                    account=pos_data['account'],
                    isin=pos_data['isin'],
                    defaults={
                        'settled_qty': pos_data.get('settled_quantity', 0),
                        'pending_qty': pos_data.get('pending_quantity', 0),
                        'as_of': timezone.now(),
                    }
                )
            
            # Return positions from database
            items = [
                {
                    'isin': p.isin,
                    'quantity': str((p.settled_qty or 0) + (p.pending_qty or 0)),
                    'settled': str(p.settled_qty or 0),
                    'pending': str(p.pending_qty or 0),
                    'asOf': p.as_of.isoformat() if p.as_of else None,
                }
                for p in Position.objects.filter(account=account).order_by('-as_of')[:200]
            ]
            return ok({'balances': items})
        except Exception as e:
            return bad_request(f"Failed to fetch positions: {str(e)}", status=500)


class InstructionsView(APIView):
    def get_permissions(self):
        return [IsAuthenticated(), IsInGroup.with_names(["ops", "issuer"]) ]

    @extend_schema(
        tags=["Clearstream"],
        summary="Create Clearstream instruction",
        description=(
            "Creates a delivery or receipt instruction in Clearstream PMI. "
            "Requires group 'ops' or 'issuer'. Idempotent with Idempotency-Key header."
        ),
        request=InstructionCreateSerializer,
        examples=[
            OpenApiExample(
                "Delivery instruction",
                value={
                    "type": "DELIVERY",
                    "isin": "US0378331005",
                    "quantity": "5",
                    "counterparty": "CP-LEI",
                    "settlementDate": "2025-01-17",
                    "priority": 1,
                    "partialAllowed": False
                }
            ),
            OpenApiExample(
                "Receipt instruction",
                value={
                    "type": "RECEIPT",
                    "isin": "US0378331005",
                    "quantity": "10",
                    "counterparty": "CP-LEI-002",
                    "settlementDate": "2025-01-17"
                }
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Instruction created successfully",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "timestamp": {"type": "string", "example": "2025-01-15T10:30:00Z"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "instructionId": {"type": "string", "example": "PMI-INSTR-US0378331005"},
                                "status": {"type": "string", "example": "ACCEPTED"}
                            }
                        }
                    }
                },
                examples=[
                    {
                        "success": True,
                        "timestamp": "2025-01-15T10:30:00Z",
                        "data": {
                            "instructionId": "PMI-INSTR-US0378331005",
                            "status": "ACCEPTED"
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
        ser = InstructionCreateSerializer(data=request.data)
        if not ser.is_valid():
            return bad_request(ser.errors)
        
        v = ser.validated_data
        try:
            # Create instruction via Clearstream PMI API
            client = ClearstreamClient()
            result = client.create_instruction(
                instruction_type=v['type'],
                isin=v['isin'],
                quantity=float(v['quantity']),
                counterparty=v['counterparty'],
                settlement_date=v.get('settlementDate').isoformat() if v.get('settlementDate') else None,
                priority=v.get('priority'),
                partial_allowed=v.get('partialAllowed')
            )
            
            if not result:
                return bad_request("Failed to create instruction in Clearstream PMI", status=500)
            
            return ok({
                'instructionId': result.get('instruction_id', f'PMI-INSTR-{v["isin"]}'),
                'status': result.get('status', 'ACCEPTED')
            })
        except Exception as e:
            return bad_request(f"Failed to create instruction: {str(e)}", status=500)


class ClearstreamSettlementView(APIView):
    def get_permissions(self):
        # POST requires ops/issuer; GET requires auth
        if getattr(self.request, 'method', '').upper() == 'POST':
            return [IsAuthenticated(), IsInGroup.with_names(["ops", "issuer"]) ]
        return [IsAuthenticated()]

    @extend_schema(
        tags=["Clearstream"],
        summary="Create Clearstream settlement",
        description=(
            "Creates a Clearstream settlement record tied to Settlement model. "
            "Requires group 'ops' or 'issuer'. Idempotent with Idempotency-Key header."
        ),
        request=ClearstreamSettlementCreateSerializer,
        examples=[
            OpenApiExample(
                "Clearstream settlement",
                value={
                    "isin": "US0378331005",
                    "quantity": "10",
                    "account": "ACC-001",
                    "counterparty": "CP-LEI-001"
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
        ser = ClearstreamSettlementCreateSerializer(data=request.data)
        if not ser.is_valid():
            return bad_request(ser.errors)
        v = ser.validated_data
        try:
            # Create settlement via Clearstream PMI API
            client = ClearstreamClient()
            result = client.create_settlement(
                isin=v['isin'],
                quantity=float(v['quantity']),
                account=v.get('account'),
                counterparty=v.get('counterparty')
            )
            
            if not result:
                return bad_request("Failed to create settlement in Clearstream PMI", status=500)
            
            # Create local settlement record
            s = Settlement.objects.create(
                source=Settlement.Source.CLEARSTREAM,
                isin=v['isin'],
                quantity=v['quantity'],
                account=v.get('account'),
                counterparty=v.get('counterparty'),
                status=Settlement.Status.INITIATED,
                timeline={'created': True, 'clearstream_settlement_id': result.get('settlement_id')},
            )
            return ok({'settlementId': str(s.id), 'status': s.status})
        except Exception as e:
            return bad_request(f"Failed to create settlement: {str(e)}", status=500)

    @extend_schema(
        tags=["Clearstream"],
        summary="Get Clearstream settlement status",
        description="Retrieves detailed status and information for a Clearstream settlement by its UUID.",
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
                                "source": {"type": "string", "example": "clearstream"},
                                "isin": {"type": "string"},
                                "quantity": {"type": "string"},
                                "status": {"type": "string", "enum": ["INITIATED", "MATCHED", "SETTLED", "FAILED"]},
                                "timeline": {"type": "object"}
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
                            "source": "clearstream",
                            "isin": "US0378331005",
                            "quantity": "10",
                            "status": "INITIATED",
                            "timeline": {"created": True}
                        }
                    }
                ]
            ),
            401: ERROR_401,
            404: ERROR_404,
        }
    )
    def get(self, request: Request, pk: str) -> Response:
        try:
            s = Settlement.objects.get(pk=pk)
        except Settlement.DoesNotExist:
            return not_found('Settlement not found')
        return ok({
            'settlementId': str(s.id),
            'source': s.source,
            'isin': s.isin,
            'quantity': str(s.quantity),
            'status': s.status,
            'timeline': s.timeline,
        })
