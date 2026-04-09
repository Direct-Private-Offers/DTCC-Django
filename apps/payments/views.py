"""
Webhook Listener Views
Handles incoming payment notifications from NEO Bank / Bill Bitts PSP
"""
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction as db_transaction
from decimal import Decimal, InvalidOperation
from .models import PaymentProfile, Transaction
from .omnisend_service import OmnisendClient
from apps.webhooks.models import WebhookEvent
from apps.receipts.services import create_receipt, _coerce_transaction_uuid
import json
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def neo_bank_webhook(request):
    """
    Endpoint for NEO Bank PSP to post transaction updates.
    
    Expected payload:
    {
        "cprn": "CPRN-XXXXXXXX",
        "status": "SUCCESS" | "SETTLED" | "FAILED",
        "amount": "250.00",
        "tx_id": "TXN-XXXXXX",
        "currency": "USD",
        "token_contract_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb" (optional),
        "token_symbol": "DPO-STO" (optional)
    }
    """
    try:
        # Parse incoming webhook data
        data = json.loads(request.body)
        logger.info(f"Received NEO Bank webhook: {data.get('tx_id')}")
        
        # Extract critical fields
        cprn = data.get('cprn')
        transaction_status = data.get('status')
        amount = data.get('amount')
        tx_id = data.get('tx_id')
        currency = data.get('currency', 'USD')
        token_contract_address = data.get('token_contract_address', '')
        token_symbol = data.get('token_symbol', 'DPO-STO')
        
        # Validate required fields
        if not all([cprn, transaction_status, amount, tx_id]):
            logger.error("Missing required fields in webhook payload")
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Find user by CPRN
        try:
            profile = PaymentProfile.objects.get(cprn_number=cprn)
        except PaymentProfile.DoesNotExist:
            logger.error(f"Payment profile not found for CPRN: {cprn}")
            return JsonResponse({'error': 'User/CPRN not found'}, status=404)
        
        # Create or update transaction record (atomic for idempotency)
        with db_transaction.atomic():
            transaction, created = Transaction.objects.get_or_create(
                transaction_id=tx_id,
                defaults={
                    'profile': profile,
                    'amount': float(amount),
                    'currency': currency,
                    'status': transaction_status,
                    'token_contract_address': token_contract_address,
                    'token_symbol': token_symbol,
                    'webhook_payload': data
                }
            )

            if not created:
                # Update existing transaction
                transaction.status = transaction_status
                transaction.webhook_payload = data
                if transaction_status == 'SETTLED':
                    transaction.settled_at = timezone.now()
                transaction.save()

            # Persist raw webhook event for audit/debug
            try:
                WebhookEvent.objects.create(
                    source=WebhookEvent.Source.NEO_BANK,
                    event_type=str(transaction_status),
                    event_data=data,
                    reference=str(tx_id),
                    status=WebhookEvent.Status.PROCESSED
                )
            except Exception as webhook_error:
                logger.error(f"Failed to persist webhook event for {tx_id}: {webhook_error}")
        
        # Process based on status
        if transaction_status in ['SUCCESS', 'SETTLED']:
            # Update user balance
            try:
                amount_decimal = Decimal(str(amount))
            except (InvalidOperation, TypeError):
                amount_decimal = Decimal('0')
            profile.neo_balance += float(amount_decimal)
            profile.save()
            
            logger.info(f"Updated balance for {profile.user.username}: ${profile.neo_balance}")
            
            # Trigger Omnisend marketing automation
            omni = OmnisendClient()
            email_sent = omni.trigger_trade_confirmation(
                email=profile.user.email,
                amount=amount,
                token_symbol=token_symbol
            )
            
            if email_sent:
                logger.info(f"Omnisend email triggered for {profile.user.email}")
            
            # Generate receipt (idempotent-ish per transaction id)
            try:
                tx_uuid = _coerce_transaction_uuid(str(tx_id))
                existing = profile.user.receipts.filter(
                    receipt_type='SETTLEMENT',
                    transaction_id=tx_uuid
                ).first()
                if existing is None:
                    create_receipt(
                        receipt_type='SETTLEMENT',
                        investor=profile.user,
                        transaction_id=str(tx_id),
                        amount=amount_decimal,
                        currency=currency,
                        metadata={
                            'buyer_name': profile.user.get_full_name() or profile.user.username,
                            'seller_name': 'PayBito',
                            'transaction_id': str(tx_id),
                            'source': 'neo_bank_webhook'
                        }
                    )
            except Exception as receipt_error:
                logger.error(f"Failed to generate receipt for {tx_id}: {receipt_error}")

            return JsonResponse({
                'status': 'verified',
                'message': 'Account Updated',
                'new_balance': str(profile.neo_balance),
                'transaction_id': tx_id
            }, status=200)
        
        elif transaction_status == 'FAILED':
            logger.warning(f"Transaction {tx_id} failed for CPRN: {cprn}")
            return JsonResponse({
                'status': 'acknowledged',
                'message': 'Transaction failed',
                'transaction_id': tx_id
            }, status=200)
        
        else:
            # Unknown status
            logger.warning(f"Unknown transaction status: {transaction_status}")
            return JsonResponse({
                'status': 'acknowledged',
                'message': f'Status {transaction_status} recorded',
                'transaction_id': tx_id
            }, status=200)
    
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook request body")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def execute_trade(request):
    """
    API endpoint for front-end to initiate a trade
    
    Payload:
    {
        "token_contract_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        "token_symbol": "DPO-STO",
        "amount": "500.00",
        "currency": "USD"
    }
    """
    try:
        data = json.loads(request.body)
        
        # Get user's payment profile
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        try:
            profile = PaymentProfile.objects.get(user=request.user)
        except PaymentProfile.DoesNotExist:
            return JsonResponse({'error': 'Payment profile not found'}, status=404)
        
        # Validate CPRN exists
        if not profile.cprn_number:
            return JsonResponse({'error': 'CPRN not registered'}, status=400)
        
        # Extract trade details
        token_contract_address = data.get('token_contract_address')
        token_symbol = data.get('token_symbol', 'DPO-STO')
        amount = data.get('amount')
        currency = data.get('currency', 'USD')
        
        if not all([token_contract_address, amount]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Here you would call Bill Bitts to initiate payment
        # For now, we'll create a pending transaction
        from .services import BillBittsClient
        
        client = BillBittsClient()
        payment_result = client.initiate_payment({
            'cprn': profile.cprn_number,
            'amount': amount,
            'currency': currency,
            'description': f'ERC-1400 Security Token Purchase: {token_symbol}'
        })
        
        if payment_result.get('status') == 'success':
            return JsonResponse({
                'status': 'success',
                'message': 'Payment initiated',
                'transaction_id': payment_result.get('tx_id')
            }, status=200)
        else:
            return JsonResponse({
                'status': 'failed',
                'error': payment_result.get('error', 'Payment initiation failed')
            }, status=400)
    
    except Exception as e:
        logger.exception(f"Error executing trade: {e}")
        return JsonResponse({'error': str(e)}, status=500)
