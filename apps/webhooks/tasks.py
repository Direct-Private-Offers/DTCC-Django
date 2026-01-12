from celery import shared_task
from django.utils import timezone
from apps.core.models import WebhookEvent
import logging

logger = logging.getLogger(__name__)


@shared_task
def process_webhook_event(event_id):
    """Process a webhook event asynchronously."""
    event = None
    try:
        event = WebhookEvent.objects.get(id=event_id)
        event.status = WebhookEvent.Status.PROCESSING
        event.save()

        # Process based on source
        if event.source == WebhookEvent.Source.EUROCLEAR:
            _process_euroclear_event(event)
        elif event.source == WebhookEvent.Source.CLEARSTREAM:
            _process_clearstream_event(event)
        elif event.source == WebhookEvent.Source.CHAINLINK:
            _process_chainlink_event(event)
        elif event.source == WebhookEvent.Source.NEO_BANK:
            _process_neo_bank_event(event)
        elif event.source == WebhookEvent.Source.FX_MARKET:
            _process_fx_market_event(event)
        else:
            raise ValueError(f"Unknown webhook source: {event.source}")

        event.status = WebhookEvent.Status.PROCESSED
        event.processed_at = timezone.now()
        event.save()

    except WebhookEvent.DoesNotExist:
        logger.error(f"WebhookEvent {event_id} not found")
    except Exception as e:
        logger.error(f"Error processing webhook event {event_id}: {str(e)}")
        if event:
            event.status = WebhookEvent.Status.FAILED
            event.error_message = str(e)
            event.save()


def _process_euroclear_event(event):
    """Process Euroclear webhook event."""
    # Placeholder processing; integrate with Euroclear reconciliation when available
    logger.info(f"Processing Euroclear event: {event.event_type} ref={event.reference}")
    # Example: update settlement timeline or enqueue downstream task
    return True


def _process_clearstream_event(event):
    """Process Clearstream webhook event."""
    logger.info(f"Processing Clearstream event: {event.event_type} ref={event.reference}")
    # Example: update positions or settlements
    return True


def _process_chainlink_event(event):
    """Process Chainlink oracle webhook event."""
    logger.info(f"Processing Chainlink event: {event.event_type} ref={event.reference}")
    # Example: update price feeds or trigger settlement
    return True


@shared_task
def process_neo_bank_webhook(event_id):
    """Process NEO Bank webhook event asynchronously."""
    event = None
    try:
        event = WebhookEvent.objects.get(id=event_id)
        event.status = WebhookEvent.Status.PROCESSING
        event.save()
        
        _process_neo_bank_event(event)
        
        event.status = WebhookEvent.Status.PROCESSED
        event.processed_at = timezone.now()
        event.save()
    except WebhookEvent.DoesNotExist:
        logger.error(f"WebhookEvent {event_id} not found")
    except Exception as e:
        logger.error(f"Error processing NEO Bank webhook {event_id}: {str(e)}")
        if event:
            event.status = WebhookEvent.Status.FAILED
            event.error_message = str(e)
            event.save()


def _process_neo_bank_event(event):
    """Process NEO Bank webhook event."""
    from apps.neo_bank.services import NeoBankSyncService
    from apps.compliance.models import InvestorProfile
    from django.contrib.auth.models import User
    
    logger.info(f"Processing NEO Bank event: {event.event_type} ref={event.reference}")
    
    event_data = event.event_data
    event_type = event.event_type
    
    if event_type == 'kyc_updated':
        # Handle KYC update from NEO Bank
        user_id = event_data.get('user_id')
        kyc_data = event_data.get('kyc_data', {})
        
        try:
            user = User.objects.get(id=user_id)
            service = NeoBankSyncService()
            sync_status = service.sync_kyc(user, kyc_data)
            
            # Update investor profile sync status
            if hasattr(user, 'investor_profile'):
                profile = user.investor_profile
                profile.neo_bank_synced = True
                profile.neo_bank_sync_status = sync_status.sync_status if sync_status else 'ERROR'
                profile.neo_bank_last_synced = timezone.now()
                profile.save()
            
            logger.info(f"KYC sync completed for user {user_id}")
        except User.DoesNotExist:
            logger.warning(f"User {user_id} not found for KYC sync")
        except Exception as e:
            logger.error(f"Error syncing KYC for user {user_id}: {str(e)}")
            raise
    
    elif event_type == 'account_linked':
        # Handle account linking confirmation
        user_id = event_data.get('user_id')
        neo_account_id = event_data.get('neo_account_id')
        
        logger.info(f"Account linked: user {user_id} -> NEO account {neo_account_id}")
    
    elif event_type == 'transaction_sync':
        # Handle transaction synchronization
        user_id = event_data.get('user_id')
        transaction_id = event_data.get('transaction_id')
        transaction_data = event_data.get('transaction_data', {})
        
        try:
            user = User.objects.get(id=user_id)
            service = NeoBankSyncService()
            service.sync_transaction(user, transaction_id, transaction_data)
            logger.info(f"Transaction sync completed: {transaction_id}")
        except User.DoesNotExist:
            logger.warning(f"User {user_id} not found for transaction sync")
        except Exception as e:
            logger.error(f"Error syncing transaction {transaction_id}: {str(e)}")
            raise
    
    return True


@shared_task
def process_fx_market_webhook(event_id):
    """Process FX-to-Market webhook event asynchronously."""
    event = None
    try:
        event = WebhookEvent.objects.get(id=event_id)
        event.status = WebhookEvent.Status.PROCESSING
        event.save()
        
        _process_fx_market_event(event)
        
        event.status = WebhookEvent.Status.PROCESSED
        event.processed_at = timezone.now()
        event.save()
    except WebhookEvent.DoesNotExist:
        logger.error(f"WebhookEvent {event_id} not found")
    except Exception as e:
        logger.error(f"Error processing FX-to-Market webhook {event_id}: {str(e)}")
        if event:
            event.status = WebhookEvent.Status.FAILED
            event.error_message = str(e)
            event.save()


def _process_fx_market_event(event):
    """Process FX-to-Market webhook event."""
    from apps.fx_market.services import FxMarketService
    from apps.fx_market.models import CrossPlatformSettlement
    from apps.settlement.models import Settlement
    
    logger.info(f"Processing FX-to-Market event: {event.event_type} ref={event.reference}")
    
    event_data = event.event_data
    event_type = event.event_type
    
    if event_type == 'settlement_updated':
        # Handle settlement status update from FX-to-Market
        fx_settlement_id = event_data.get('settlement_id')
        status = event_data.get('status')
        
        try:
            cross_settlement = CrossPlatformSettlement.objects.get(fx_settlement_id=fx_settlement_id)
            cross_settlement.fx_status = status
            cross_settlement.save()
            
            # Reconcile if both sides are complete
            service = FxMarketService()
            service.reconcile_settlement(cross_settlement)
            
            # Update DPO settlement sync status
            try:
                dpo_settlement = Settlement.objects.get(id=cross_settlement.dpo_settlement_id)
                dpo_settlement.fx_market_synced = True
                dpo_settlement.fx_market_settlement_id = fx_settlement_id
                dpo_settlement.fx_market_status = status
                dpo_settlement.save()
            except Settlement.DoesNotExist:
                logger.warning(f"DPO settlement {cross_settlement.dpo_settlement_id} not found")
            
            logger.info(f"Settlement status updated: {fx_settlement_id} -> {status}")
        except CrossPlatformSettlement.DoesNotExist:
            logger.warning(f"Cross-platform settlement {fx_settlement_id} not found")
        except Exception as e:
            logger.error(f"Error updating settlement {fx_settlement_id}: {str(e)}")
            raise
    
    elif event_type == 'conversion_completed':
        # Handle conversion completion
        transaction_id = event_data.get('transaction_id')
        status = event_data.get('status')
        
        logger.info(f"Conversion completed: {transaction_id} -> {status}")
    
    elif event_type == 'token_transfer_completed':
        # Handle token transfer completion
        transaction_id = event_data.get('transaction_id')
        status = event_data.get('status')
        
        logger.info(f"Token transfer completed: {transaction_id} -> {status}")
    
    return True

