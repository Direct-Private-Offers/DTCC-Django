from django.db import models
from django.contrib.auth.models import User
import uuid
from decimal import Decimal


class Wallet(models.Model):
    """User wallet linked to blockchain address."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallets')
    address = models.CharField(max_length=128, unique=True, db_index=True)
    network = models.CharField(max_length=32, default='BSC')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dex_wallets'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['address', 'network']),
        ]

    def __str__(self):
        return f"Wallet({self.address}, {self.network})"


class Order(models.Model):
    """P2P trading order (buy/sell)."""
    class OrderType(models.TextChoices):
        BUY = 'BUY', 'Buy'
        SELL = 'SELL', 'Sell'

    class OrderStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PARTIAL = 'PARTIAL', 'Partially Filled'
        FILLED = 'FILLED', 'Filled'
        CANCELLED = 'CANCELLED', 'Cancelled'
        EXPIRED = 'EXPIRED', 'Expired'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='orders')
    order_type = models.CharField(max_length=4, choices=OrderType.choices)
    isin = models.CharField(max_length=12, db_index=True)
    quantity = models.DecimalField(max_digits=36, decimal_places=18)
    filled_quantity = models.DecimalField(max_digits=36, decimal_places=18, default=Decimal('0'))
    price_per_unit = models.DecimalField(max_digits=36, decimal_places=18)
    payment_token = models.CharField(max_length=128, default='USDC')
    status = models.CharField(max_length=16, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    expires_at = models.DateTimeField(null=True, blank=True)
    tx_hash = models.CharField(max_length=128, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dex_orders'
        indexes = [
            models.Index(fields=['isin', 'status', 'order_type']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['wallet', 'status']),
        ]

    def __str__(self):
        return f"Order({self.order_type}, {self.isin}, {self.quantity}, {self.status})"


class Swap(models.Model):
    """Token swap transaction."""
    class SwapStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        EXECUTING = 'EXECUTING', 'Executing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet_from = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='swaps_from')
    wallet_to = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='swaps_to', null=True, blank=True)
    token_from = models.CharField(max_length=128)
    token_to = models.CharField(max_length=128)
    amount_from = models.DecimalField(max_digits=36, decimal_places=18)
    amount_to = models.DecimalField(max_digits=36, decimal_places=18)
    exchange_rate = models.DecimalField(max_digits=36, decimal_places=18)
    status = models.CharField(max_length=16, choices=SwapStatus.choices, default=SwapStatus.PENDING)
    tx_hash_from = models.CharField(max_length=128, null=True, blank=True)
    tx_hash_to = models.CharField(max_length=128, null=True, blank=True)
    is_p2p = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dex_swaps'
        indexes = [
            models.Index(fields=['wallet_from', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['tx_hash_from', 'tx_hash_to']),
        ]

    def __str__(self):
        return f"Swap({self.token_from} -> {self.token_to}, {self.status})"


class Trade(models.Model):
    """Executed trade between two orders."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buy_order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='trades_as_buy')
    sell_order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='trades_as_sell')
    isin = models.CharField(max_length=12, db_index=True)
    quantity = models.DecimalField(max_digits=36, decimal_places=18)
    price_per_unit = models.DecimalField(max_digits=36, decimal_places=18)
    total_value = models.DecimalField(max_digits=36, decimal_places=18)
    tx_hash = models.CharField(max_length=128, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'dex_trades'
        indexes = [
            models.Index(fields=['isin', 'created_at']),
            models.Index(fields=['tx_hash']),
        ]

    def __str__(self):
        return f"Trade({self.isin}, {self.quantity}, {self.price_per_unit})"

