"""
Payment Profile Models
Integrates with Bill Bitts / NEO Bank PSP for payment processing
"""
from django.db import models
from django.conf import settings


class PaymentProfile(models.Model):
    """
    Links Django users to Bill Bitts banking ecosystem via CPRN
    (Customer Presentment Registration Number)
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='payment_profile'
    )
    
    # Bill Bitts Identity: Unique ID for the user in the banking system
    cprn_number = models.CharField(
        max_length=100, 
        unique=True, 
        blank=True, 
        null=True,
        help_text="Customer Presentment Registration Number from Bill Bitts"
    )
    
    # Web3 Identity: User's public wallet address
    web3_wallet_address = models.CharField(
        max_length=42, 
        blank=True,
        help_text="Ethereum wallet address for ERC-1400 security token transactions"
    )
    
    # Real-time Balance from NEO Bank (Settled Funds)
    neo_balance = models.DecimalField(
        max_digits=20, 
        decimal_places=2, 
        default=0.00,
        help_text="Current balance from NEO Bank PSP"
    )
    
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether the payment profile has been verified"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payment_profiles'
        verbose_name = 'Payment Profile'
        verbose_name_plural = 'Payment Profiles'
        indexes = [
            models.Index(fields=['cprn_number']),
            models.Index(fields=['web3_wallet_address']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.cprn_number or 'No CPRN'}"


class Transaction(models.Model):
    """
    Tracks individual payment transactions
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('SETTLED', 'Settled'),
    ]
    
    profile = models.ForeignKey(
        PaymentProfile,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Transaction ID from NEO Bank/Bill Bitts"
    )
    
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # ERC-1400 Security Token details
    token_contract_address = models.CharField(
        max_length=42, 
        blank=True,
        help_text="ERC-1400 token contract address"
    )
    token_symbol = models.CharField(
        max_length=20, 
        blank=True,
        help_text="Symbol of the ERC-1400 security token (e.g., DPO-STO)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    settled_at = models.DateTimeField(null=True, blank=True)
    
    # Raw webhook data
    webhook_payload = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'payment_transactions'
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - {self.status} - ${self.amount}"
