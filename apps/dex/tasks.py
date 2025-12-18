"""
Celery tasks for DEX operations.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Order, Swap
from .services import match_orders
import logging

logger = logging.getLogger(__name__)


@shared_task
def match_orders_task(isin: str = None):
    """
    Periodic task to match pending orders.
    
    Args:
        isin: Optional ISIN to match. If None, matches all ISINs.
    """
    try:
        if isin:
            match_orders(isin)
        else:
            # Get all unique ISINs with pending orders
            isins = Order.objects.filter(
                status__in=[Order.OrderStatus.PENDING, Order.OrderStatus.PARTIAL]
            ).values_list('isin', flat=True).distinct()
            
            for isin_value in isins:
                match_orders(isin_value)
        
        logger.info(f"Order matching task completed for ISIN: {isin or 'all'}")
    except Exception as e:
        logger.error(f"Error in order matching task: {str(e)}")


@shared_task
def execute_trade_on_chain(trade_id: str):
    """
    Execute trade on blockchain.
    
    Args:
        trade_id: Trade UUID
    """
    try:
        from .models import Trade
        trade = Trade.objects.get(id=trade_id)
        
        # Placeholder: integrate on-chain settlement when token contract and payment rails are ready.
        # Suggested flow:
        # 1. Transfer tokens from seller to buyer
        # 2. Transfer payment tokens from buyer to seller
        # 3. Update trade with tx_hash and mark orders as filled
        logger.info(f"Skipping on-chain execution for trade {trade_id} (not configured)")
        
        logger.info(f"Trade execution on chain: {trade_id}")
    except Trade.DoesNotExist:
        logger.error(f"Trade not found: {trade_id}")
    except Exception as e:
        logger.error(f"Error executing trade on chain: {str(e)}")


@shared_task
def update_order_status(order_id: str):
    """
    Update order status from blockchain.
    
    Args:
        order_id: Order UUID
    """
    try:
        order = Order.objects.get(id=order_id)
        
        if order.tx_hash:
            # Placeholder: check transaction status on-chain and update order.
            logger.info(f"Order {order_id} has tx_hash {order.tx_hash}; on-chain status check not configured.")
        
        logger.info(f"Order status update: {order_id}")
    except Order.DoesNotExist:
        logger.error(f"Order not found: {order_id}")
    except Exception as e:
        logger.error(f"Error updating order status: {str(e)}")


@shared_task
def cleanup_expired_orders():
    """Remove expired orders."""
    try:
        expired_orders = Order.objects.filter(
            status=Order.OrderStatus.PENDING,
            expires_at__lt=timezone.now()
        )
        
        count = expired_orders.update(status=Order.OrderStatus.EXPIRED)
        logger.info(f"Expired {count} orders")
    except Exception as e:
        logger.error(f"Error cleaning up expired orders: {str(e)}")

