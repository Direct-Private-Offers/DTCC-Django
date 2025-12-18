"""
Event ingestion endpoint for blockchain events.
Allows manual ingestion of events or receives events from listener.
"""
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from apps.core.responses import ok, bad_request
from apps.core.permissions import IsInGroup
from apps.issuance.models import IssuanceEvent, TransferEvent
from apps.issuance.listener import EventListener
from drf_spectacular.utils import (
    extend_schema, OpenApiExample, OpenApiResponse
)
from apps.core.schemas import ERROR_400, ERROR_401, ERROR_403, ERROR_500
import logging

logger = logging.getLogger(__name__)


class EventIngestionView(APIView):
    """Endpoint for ingesting blockchain events."""
    
    permission_classes = [IsAuthenticated, IsInGroup.with_names(["ops", "issuer"])]
    
    @extend_schema(
        tags=["Issuance"],
        summary="Ingest blockchain event",
        description=(
            "Manually ingest a blockchain event. Requires 'ops' or 'issuer' group. "
            "Used for event reconciliation and manual event processing."
        ),
        request={
            "type": "object",
            "properties": {
                "eventType": {"type": "string", "enum": ["TokenIssued", "Transfer"]},
                "blockNumber": {"type": "integer"},
                "txHash": {"type": "string"},
                "eventData": {"type": "object"},
            },
            "required": ["eventType", "blockNumber", "txHash", "eventData"]
        },
        examples=[
            OpenApiExample(
                "TokenIssued event",
                value={
                    "eventType": "TokenIssued",
                    "blockNumber": 12345678,
                    "txHash": "0x1234...",
                    "eventData": {
                        "isin": "US0378331005",
                        "investor": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                        "amount": "1000",
                        "transactionId": "TX-001"
                    }
                }
            ),
            OpenApiExample(
                "Transfer event",
                value={
                    "eventType": "Transfer",
                    "blockNumber": 12345679,
                    "txHash": "0x5678...",
                    "eventData": {
                        "isin": "US0378331005",
                        "from": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                        "to": "0x8ba1f109551bD432803012645Hac136c22C9e8",
                        "amount": "100"
                    }
                }
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Event ingested successfully",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "timestamp": {"type": "string"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "eventId": {"type": "string", "format": "uuid"},
                                "eventType": {"type": "string"},
                                "processed": {"type": "boolean"}
                            }
                        }
                    }
                }
            ),
            400: ERROR_400,
            401: ERROR_401,
            403: ERROR_403,
            500: ERROR_500,
        }
    )
    def post(self, request: Request):
        """Ingest a blockchain event."""
        data = request.data
        event_type = data.get('eventType')
        block_number = data.get('blockNumber')
        tx_hash = data.get('txHash')
        event_data = data.get('eventData', {})
        
        if not all([event_type, block_number, tx_hash]):
            return bad_request("Missing required fields: eventType, blockNumber, txHash")
        
        try:
            if event_type == 'TokenIssued':
                event, created = IssuanceEvent.objects.get_or_create(
                    tx_hash=tx_hash,
                    defaults={
                        'block_number': block_number,
                        'event_type': event_type,
                        'event_data': event_data,
                        'isin': event_data.get('isin', ''),
                        'investor_address': event_data.get('investor', ''),
                        'amount': event_data.get('amount', 0),
                        'transaction_id': event_data.get('transactionId', ''),
                        'euroclear_ref': event_data.get('euroclearRef', ''),
                    }
                )
            elif event_type == 'Transfer':
                event, created = TransferEvent.objects.get_or_create(
                    tx_hash=tx_hash,
                    defaults={
                        'block_number': block_number,
                        'event_type': event_type,
                        'event_data': event_data,
                        'isin': event_data.get('isin', ''),
                        'from_address': event_data.get('from', ''),
                        'to_address': event_data.get('to', ''),
                        'amount': event_data.get('amount', 0),
                    }
                )
            else:
                return bad_request(f"Unknown event type: {event_type}")
            
            return ok({
                'eventId': str(event.id),
                'eventType': event_type,
                'processed': event.processed,
                'created': created
            })
        
        except Exception as e:
            logger.error(f"Error ingesting event: {str(e)}")
            return bad_request(f"Failed to ingest event: {str(e)}", status=500)

