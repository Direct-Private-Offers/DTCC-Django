"""
DEX business logic services.
Handles order matching, trade execution, and swap operations.
"""
import logging
from typing import Optional
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from .models import Wallet, Order, Swap, Trade
from .blockchain import get_token_balance, transfer_tokens

logger = logging.getLogger(__name__)


def create_order(wallet: Wallet, order_data: dict) -> Order:
    """
    Create and validate a new order.
    
    Args:
        wallet: Wallet instance
        order_data: Order data dictionary
    
    Returns:
        Created Order instance
    """
    order = Order.objects.create(
        wallet=wallet,
        order_type=order_data['order_type'],
        isin=order_data['isin'],
        quantity=order_data['quantity'],
        price_per_unit=order_data['price_per_unit'],
        payment_token=order_data.get('payment_token', 'USDC'),
        expires_at=order_data.get('expires_at'),
    )
    
    logger.info(f"Created order: {order.id}")
    return order


def match_orders(isin: str) -> list:
    """
    Match pending buy and sell orders for an ISIN.
    Uses price-time priority matching.
    
    Args:
        isin: ISIN to match orders for
    
    Returns:
        List of executed trades
    """
    buy_orders = Order.objects.filter(
        isin=isin,
        order_type=Order.OrderType.BUY,
        status=Order.OrderStatus.PENDING
    ).order_by('-price_per_unit', 'created_at')
    
    sell_orders = Order.objects.filter(
        isin=isin,
        order_type=Order.OrderType.SELL,
        status=Order.OrderStatus.PENDING
    ).order_by('price_per_unit', 'created_at')
    
    trades = []
    
    for buy_order in buy_orders:
        if buy_order.status != Order.OrderStatus.PENDING:
            continue
        
        remaining_quantity = buy_order.quantity - buy_order.filled_quantity
        
        for sell_order in sell_orders:
            if sell_order.status != Order.OrderStatus.PENDING:
                continue
            
            if buy_order.price_per_unit < sell_order.price_per_unit:
                break  # No more matches possible
            
            sell_remaining = sell_order.quantity - sell_order.filled_quantity
            trade_quantity = min(remaining_quantity, sell_remaining)
            trade_price = sell_order.price_per_unit  # Price-time priority: use sell order price
            
            if trade_quantity > 0:
                trade = execute_trade(buy_order, sell_order, trade_quantity, trade_price)
                if trade:
                    trades.append(trade)
                    remaining_quantity -= trade_quantity
                    
                    if remaining_quantity <= 0:
                        break
    
    return trades


@transaction.atomic
def execute_trade(buy_order: Order, sell_order: Order, quantity: Decimal, price: Decimal) -> Optional[Trade]:
    """
    Execute a trade between two orders.
    
    Args:
        buy_order: Buy order
        sell_order: Sell order
        quantity: Trade quantity
        price: Trade price
    
    Returns:
        Created Trade instance or None on error
    """
    try:
        total_value = quantity * price
        
        # Create trade record
        trade = Trade.objects.create(
            buy_order=buy_order,
            sell_order=sell_order,
            isin=buy_order.isin,
            quantity=quantity,
            price_per_unit=price,
            total_value=total_value,
        )
        
        # Update order filled quantities
        buy_order.filled_quantity += quantity
        sell_order.filled_quantity += quantity
        
        # Update order statuses
        if buy_order.filled_quantity >= buy_order.quantity:
            buy_order.status = Order.OrderStatus.FILLED
        else:
            buy_order.status = Order.OrderStatus.PARTIAL
        
        if sell_order.filled_quantity >= sell_order.quantity:
            sell_order.status = Order.OrderStatus.FILLED
        else:
            sell_order.status = Order.OrderStatus.PARTIAL
        
        buy_order.save()
        sell_order.save()
        
        logger.info(f"Executed trade: {trade.id}, quantity: {quantity}, price: {price}")
        return trade
    
    except Exception as e:
        logger.error(f"Error executing trade: {str(e)}")
        return None


def create_swap(wallet_from: Wallet, swap_data: dict) -> Swap:
    """
    Create a swap transaction.
    
    Args:
        wallet_from: Source wallet
        swap_data: Swap data dictionary
    
    Returns:
        Created Swap instance
    """
    amount_from = Decimal(swap_data['amount_from'])
    amount_to = Decimal(swap_data['amount_to'])
    exchange_rate = amount_to / amount_from if amount_from > 0 else Decimal('0')
    
    swap = Swap.objects.create(
        wallet_from=wallet_from,
        wallet_to=swap_data.get('wallet_to'),
        token_from=swap_data['token_from'],
        token_to=swap_data['token_to'],
        amount_from=amount_from,
        amount_to=amount_to,
        exchange_rate=exchange_rate,
        is_p2p=swap_data.get('is_p2p', False),
    )
    
    logger.info(f"Created swap: {swap.id}")
    return swap


def cancel_order(order: Order) -> bool:
    """
    Cancel a pending order.
    
    Args:
        order: Order to cancel
    
    Returns:
        True if cancelled, False otherwise
    """
    if order.status not in [Order.OrderStatus.PENDING, Order.OrderStatus.PARTIAL]:
        return False
    
    order.status = Order.OrderStatus.CANCELLED
    order.save()
    
    logger.info(f"Cancelled order: {order.id}")
    return True


def get_order_book(isin: str, limit: int = 20) -> dict:
    """
    Get order book for an ISIN.
    
    Args:
        isin: ISIN to get order book for
        limit: Maximum number of orders per side
    
    Returns:
        Dictionary with buy_orders and sell_orders
    """
    buy_orders = Order.objects.filter(
        isin=isin,
        order_type=Order.OrderType.BUY,
        status=Order.OrderStatus.PENDING
    ).order_by('-price_per_unit', 'created_at')[:limit]
    
    sell_orders = Order.objects.filter(
        isin=isin,
        order_type=Order.OrderType.SELL,
        status=Order.OrderStatus.PENDING
    ).order_by('price_per_unit', 'created_at')[:limit]
    
    return {
        'isin': isin,
        'buy_orders': [
            {
                'id': str(o.id),
                'quantity': str(o.quantity - o.filled_quantity),
                'price': str(o.price_per_unit),
                'created_at': o.created_at.isoformat(),
            }
            for o in buy_orders
        ],
        'sell_orders': [
            {
                'id': str(o.id),
                'quantity': str(o.quantity - o.filled_quantity),
                'price': str(o.price_per_unit),
                'created_at': o.created_at.isoformat(),
            }
            for o in sell_orders
        ],
    }


def validate_wallet_balance(wallet: Wallet, token_address: str, required_amount: Decimal) -> bool:
    """
    Validate wallet has sufficient balance.
    
    Args:
        wallet: Wallet instance
        token_address: Token contract address
        required_amount: Required amount
    
    Returns:
        True if sufficient balance, False otherwise
    """
    try:
        from apps.core.blockchain import get_web3_provider
        w3 = get_web3_provider()
        balance = get_token_balance(w3, token_address, wallet.address)
        return balance >= required_amount
    except Exception as e:
        logger.error(f"Error validating wallet balance: {str(e)}")
        return False

