from django.db import models
import uuid


class XetraTrade(models.Model):
    """XETRA trade record"""
    TRADE_STATUS = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('SETTLED', 'Settled'),
        ('CANCELLED', 'Cancelled'),
        ('REJECTED', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    xetra_trade_id = models.CharField(max_length=64, unique=True, db_index=True)
    isin = models.CharField(max_length=12, db_index=True)
    buyer_account = models.CharField(max_length=64)
    seller_account = models.CharField(max_length=64)
    quantity = models.DecimalField(max_digits=36, decimal_places=18)
    price = models.DecimalField(max_digits=36, decimal_places=18)
    currency = models.CharField(max_length=3, default='EUR')
    trade_date = models.DateTimeField(db_index=True)
    settlement_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=TRADE_STATUS, default='PENDING')
    xetra_reference = models.CharField(max_length=128, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'xetra_trades'
        indexes = [
            models.Index(fields=['isin', 'trade_date']),
            models.Index(fields=['status', 'settlement_date']),
        ]
    
    def __str__(self):
        return f"XetraTrade({self.xetra_trade_id}, {self.isin})"


class XetraOrder(models.Model):
    """XETRA order record"""
    ORDER_TYPE = [
        ('MARKET', 'Market Order'),
        ('LIMIT', 'Limit Order'),
        ('STOP', 'Stop Order'),
    ]
    
    ORDER_SIDE = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]
    
    ORDER_STATUS = [
        ('NEW', 'New'),
        ('PARTIAL', 'Partially Filled'),
        ('FILLED', 'Filled'),
        ('CANCELLED', 'Cancelled'),
        ('REJECTED', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    xetra_order_id = models.CharField(max_length=64, unique=True, db_index=True)
    isin = models.CharField(max_length=12, db_index=True)
    account = models.CharField(max_length=64)
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE)
    side = models.CharField(max_length=10, choices=ORDER_SIDE)
    quantity = models.DecimalField(max_digits=36, decimal_places=18)
    price = models.DecimalField(max_digits=36, decimal_places=18, null=True, blank=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='NEW')
    filled_quantity = models.DecimalField(max_digits=36, decimal_places=18, default=0)
    xetra_reference = models.CharField(max_length=128, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'xetra_orders'
        indexes = [
            models.Index(fields=['isin', 'status']),
            models.Index(fields=['account', 'created_at']),
        ]
    
    def __str__(self):
        return f"XetraOrder({self.xetra_order_id}, {self.isin}, {self.side})"


class XetraSettlement(models.Model):
    """XETRA settlement instruction"""
    SETTLEMENT_STATUS = [
        ('PENDING', 'Pending'),
        ('INSTRUCTED', 'Instructed'),
        ('CONFIRMED', 'Confirmed'),
        ('SETTLED', 'Settled'),
        ('FAILED', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    settlement_id = models.CharField(max_length=64, unique=True, db_index=True)
    trade = models.ForeignKey(XetraTrade, on_delete=models.PROTECT, related_name='settlements')
    isin = models.CharField(max_length=12, db_index=True)
    buyer_account = models.CharField(max_length=64)
    seller_account = models.CharField(max_length=64)
    quantity = models.DecimalField(max_digits=36, decimal_places=18)
    amount = models.DecimalField(max_digits=36, decimal_places=18)
    currency = models.CharField(max_length=3, default='EUR')
    value_date = models.DateTimeField(db_index=True)
    status = models.CharField(max_length=20, choices=SETTLEMENT_STATUS, default='PENDING')
    xetra_instruction_id = models.CharField(max_length=128, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'xetra_settlements'
        indexes = [
            models.Index(fields=['isin', 'value_date']),
            models.Index(fields=['status', 'value_date']),
        ]
    
    def __str__(self):
        return f"XetraSettlement({self.settlement_id}, {self.isin})"


class XetraPosition(models.Model):
    """XETRA position tracking"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.CharField(max_length=64, db_index=True)
    isin = models.CharField(max_length=12, db_index=True)
    settled_quantity = models.DecimalField(max_digits=36, decimal_places=18)
    pending_quantity = models.DecimalField(max_digits=36, decimal_places=18)
    as_of = models.DateTimeField(db_index=True)
    last_reconciled = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'xetra_positions'
        unique_together = [['account', 'isin']]
        indexes = [
            models.Index(fields=['account', 'isin']),
        ]
    
    def __str__(self):
        return f"XetraPosition({self.account}, {self.isin})"


class XetraMarketData(models.Model):
    """XETRA market data snapshot"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    isin = models.CharField(max_length=12, db_index=True)
    bid_price = models.DecimalField(max_digits=36, decimal_places=18, null=True, blank=True)
    ask_price = models.DecimalField(max_digits=36, decimal_places=18, null=True, blank=True)
    last_price = models.DecimalField(max_digits=36, decimal_places=18, null=True, blank=True)
    volume = models.DecimalField(max_digits=36, decimal_places=18, default=0)
    timestamp = models.DateTimeField(db_index=True)
    
    class Meta:
        db_table = 'xetra_market_data'
        indexes = [
            models.Index(fields=['isin', '-timestamp']),
        ]
    
    def __str__(self):
        return f"XetraMarketData({self.isin}, {self.timestamp})"
