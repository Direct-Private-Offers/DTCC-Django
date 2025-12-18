from rest_framework.views import APIView
from rest_framework.response import Response
from apps.core.crypto import verify_hmac
from apps.core.responses import ok, unauthorized
from apps.core.models import WebhookEvent
from apps.webhooks.tasks import process_webhook_event
from drf_spectacular.utils import (
    extend_schema, OpenApiExample, OpenApiResponse, OpenApiParameter
)
from apps.core.schemas import ERROR_401


class EuroclearWebhook(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        tags=["Webhooks"],
        summary="Euroclear webhook (HMAC)",
        description=(
            "Inbound webhook from Euroclear secured by HMAC SHA256 signature. "
            "Required headers: X-Signature: sha256=<hex>, X-Timestamp (epoch seconds or ISO8601), X-Nonce (unique string). "
            "Timestamp must be within ±300 seconds. Nonces are checked for replay protection."
        ),
        request={
            "type": "object",
            "properties": {
                "event": {"type": "string", "example": "status_update"},
                "reference": {"type": "string", "example": "ABC123"},
                "data": {"type": "object"}
            }
        },
        parameters=[
            OpenApiParameter(
                name="X-Signature",
                location=OpenApiParameter.HEADER,
                type=str,
                description="HMAC SHA256 signature: sha256=<hex>",
                required=True
            ),
            OpenApiParameter(
                name="X-Timestamp",
                location=OpenApiParameter.HEADER,
                type=str,
                description="Timestamp (epoch seconds or ISO8601)",
                required=True
            ),
            OpenApiParameter(
                name="X-Nonce",
                location=OpenApiParameter.HEADER,
                type=str,
                description="Unique nonce string",
                required=True
            )
        ],
        examples=[
            OpenApiExample(
                "Status update webhook",
                value={"event": "status_update", "reference": "ABC123", "data": {"status": "SETTLED"}}
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Webhook received and verified successfully",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "timestamp": {"type": "string", "example": "2025-01-15T10:30:00Z"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "received": {"type": "boolean", "example": True},
                                "source": {"type": "string", "example": "euroclear"}
                            }
                        }
                    }
                },
                examples=[
                    {
                        "success": True,
                        "timestamp": "2025-01-15T10:30:00Z",
                        "data": {
                            "received": True,
                            "source": "euroclear"
                        }
                    }
                ]
            ),
            401: ERROR_401,
        }
    )
    def post(self, request):
        if not verify_hmac(request):
            return unauthorized('invalid signature')
        
        # Persist event and enqueue processing task
        event_data = request.data
        event = WebhookEvent.objects.create(
            source=WebhookEvent.Source.EUROCLEAR,
            event_type=event_data.get('event', 'unknown'),
            event_data=event_data,
            reference=event_data.get('reference'),
        )
        process_webhook_event.delay(str(event.id))
        
        return ok({'received': True, 'source': 'euroclear', 'eventId': str(event.id)})


class ClearstreamWebhook(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        tags=["Webhooks"],
        summary="Clearstream webhook (HMAC)",
        description=(
            "Inbound webhook from Clearstream secured by HMAC SHA256 signature with timestamp + nonce replay protection. "
            "Required headers: X-Signature: sha256=<hex>, X-Timestamp, X-Nonce."
        ),
        request={
            "type": "object",
            "properties": {
                "event": {"type": "string"},
                "reference": {"type": "string"},
                "data": {"type": "object"}
            }
        },
        parameters=[
            OpenApiParameter(name="X-Signature", location=OpenApiParameter.HEADER, type=str, required=True),
            OpenApiParameter(name="X-Timestamp", location=OpenApiParameter.HEADER, type=str, required=True),
            OpenApiParameter(name="X-Nonce", location=OpenApiParameter.HEADER, type=str, required=True)
        ],
        responses={
            200: OpenApiResponse(
                description="Webhook received and verified successfully",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "timestamp": {"type": "string", "example": "2025-01-15T10:30:00Z"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "received": {"type": "boolean", "example": True},
                                "source": {"type": "string", "example": "clearstream"}
                            }
                        }
                    }
                }
            ),
            401: ERROR_401,
        }
    )
    def post(self, request):
        if not verify_hmac(request):
            return unauthorized('invalid signature')
        
        # Persist event and enqueue processing task
        event_data = request.data
        event = WebhookEvent.objects.create(
            source=WebhookEvent.Source.CLEARSTREAM,
            event_type=event_data.get('event', 'unknown'),
            event_data=event_data,
            reference=event_data.get('reference'),
        )
        process_webhook_event.delay(str(event.id))
        
        return ok({'received': True, 'source': 'clearstream', 'eventId': str(event.id)})


class ChainlinkWebhook(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        tags=["Webhooks"],
        summary="Chainlink webhook (HMAC)",
        description=(
            "Oracle callback endpoint from Chainlink secured by HMAC SHA256 signature. "
            "Required headers: X-Signature: sha256=<hex>, X-Timestamp, X-Nonce."
        ),
        request={
            "type": "object",
            "properties": {
                "requestId": {"type": "string"},
                "data": {"type": "object"}
            }
        },
        parameters=[
            OpenApiParameter(name="X-Signature", location=OpenApiParameter.HEADER, type=str, required=True),
            OpenApiParameter(name="X-Timestamp", location=OpenApiParameter.HEADER, type=str, required=True),
            OpenApiParameter(name="X-Nonce", location=OpenApiParameter.HEADER, type=str, required=True)
        ],
        responses={
            200: OpenApiResponse(
                description="Webhook received and verified successfully",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "timestamp": {"type": "string", "example": "2025-01-15T10:30:00Z"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "received": {"type": "boolean", "example": True},
                                "source": {"type": "string", "example": "chainlink"}
                            }
                        }
                    }
                }
            ),
            401: ERROR_401,
        }
    )
    def post(self, request):
        if not verify_hmac(request):
            return unauthorized('invalid signature')
        
        # Persist event and enqueue processing task
        event_data = request.data
        event = WebhookEvent.objects.create(
            source=WebhookEvent.Source.CHAINLINK,
            event_type=event_data.get('requestId', 'oracle_callback'),
            event_data=event_data,
            reference=event_data.get('requestId'),
        )
        process_webhook_event.delay(str(event.id))
        
        return ok({'received': True, 'source': 'chainlink', 'eventId': str(event.id)})
