import logging
from typing import Optional, Dict
from decimal import Decimal
from django.contrib.auth.models import User
from .client import FxMarketClient
from .models import FxConversion, CrossPlatformSettlement, TokenFlow
from apps.settlement.models import Settlement

logger = logging.getLogger(__name__)


class FxMarketService:
    """Service for FX conversion and cross-platform operations"""
    
    def __init__(self):
        self.client = FxMarketClient()
    
    def convert_fx_to_token(
        self,
        user: User,
        amount: Decimal,
        currency: str,
        token_address: str
    ) -> Optional[FxConversion]:
        """
        Convert FX (fiat) to security token.
        
        Args:
            user: User instance
            amount: Amount in fiat
            currency: Fiat currency code
            token_address: Token contract address
            
        Returns:
            FxConversion instance
        """
        try:
            result = self.client.convert_fx_to_token(
                float(amount),
                currency,
                token_address,
                str(user.id)
            )
            
            if result:
                conversion = FxConversion.objects.create(
                    user=user,
                    conversion_type='FX_TO_TOKEN',
                    status='COMPLETED',
                    source_amount=amount,
                    source_currency=currency,
                    target_amount=Decimal(result.get('token_amount', '0')),
                    token_address=token_address,
                    fx_transaction_id=result.get('transaction_id'),
                    conversion_rate=Decimal(result.get('conversion_rate', '0.001'))
                )
                return conversion
            else:
                conversion = FxConversion.objects.create(
                    user=user,
                    conversion_type='FX_TO_TOKEN',
                    status='FAILED',
                    source_amount=amount,
                    source_currency=currency,
                    token_address=token_address
                )
                return conversion
        except Exception as e:
            logger.error(f"Error converting FX to token: {str(e)}")
            return None
    
    def convert_token_to_fx(
        self,
        user: User,
        token_amount: Decimal,
        token_address: str,
        target_currency: str
    ) -> Optional[FxConversion]:
        """
        Convert security token to FX (fiat).
        
        Args:
            user: User instance
            token_amount: Token amount
            token_address: Token contract address
            target_currency: Target fiat currency
            
        Returns:
            FxConversion instance
        """
        try:
            result = self.client.convert_token_to_fx(
                float(token_amount),
                token_address,
                target_currency,
                str(user.id)
            )
            
            if result:
                conversion = FxConversion.objects.create(
                    user=user,
                    conversion_type='TOKEN_TO_FX',
                    status='COMPLETED',
                    source_amount=token_amount,
                    source_currency='TOKEN',
                    target_amount=Decimal(result.get('fiat_amount', '0')),
                    target_currency=target_currency,
                    token_address=token_address,
                    fx_transaction_id=result.get('transaction_id'),
                    conversion_rate=Decimal(result.get('conversion_rate', '1000'))
                )
                return conversion
            else:
                conversion = FxConversion.objects.create(
                    user=user,
                    conversion_type='TOKEN_TO_FX',
                    status='FAILED',
                    source_amount=token_amount,
                    source_currency='TOKEN',
                    target_currency=target_currency,
                    token_address=token_address
                )
                return conversion
        except Exception as e:
            logger.error(f"Error converting token to FX: {str(e)}")
            return None
    
    def initiate_cross_platform_settlement(
        self,
        settlement: Settlement
    ) -> Optional[CrossPlatformSettlement]:
        """
        Initiate cross-platform settlement on FX-to-market.
        
        Args:
            settlement: Settlement instance
            
        Returns:
            CrossPlatformSettlement instance
        """
        try:
            settlement_data = {
                'isin': settlement.isin,
                'quantity': str(settlement.quantity),
                'amount': str(settlement.amount) if settlement.amount else None,
                'currency': settlement.currency,
                'counterparty': settlement.counterparty,
            }
            
            result = self.client.initiate_cross_platform_settlement(
                str(settlement.id),
                settlement_data
            )
            
            if result:
                cross_settlement = CrossPlatformSettlement.objects.create(
                    dpo_settlement_id=settlement.id,
                    fx_settlement_id=result.get('fx_settlement_id'),
                    status='INITIATED',
                    isin=settlement.isin,
                    quantity=settlement.quantity,
                    amount=settlement.amount,
                    currency=settlement.currency,
                    dpo_status=settlement.status
                )
                return cross_settlement
            return None
        except Exception as e:
            logger.error(f"Error initiating cross-platform settlement: {str(e)}")
            return None
    
    def reconcile_settlement(
        self,
        cross_settlement: CrossPlatformSettlement
    ) -> bool:
        """
        Reconcile settlement status between DPO and FX-to-market.
        
        Args:
            cross_settlement: CrossPlatformSettlement instance
            
        Returns:
            True if reconciled, False otherwise
        """
        try:
            # Get DPO settlement status
            try:
                dpo_settlement = Settlement.objects.get(id=cross_settlement.dpo_settlement_id)
                cross_settlement.dpo_status = dpo_settlement.status
            except Settlement.DoesNotExist:
                logger.warning(f"DPO settlement {cross_settlement.dpo_settlement_id} not found")
            
            # Get FX-to-market settlement status
            fx_status = self.client.get_settlement_status(cross_settlement.fx_settlement_id or '')
            if fx_status:
                cross_settlement.fx_status = fx_status.get('status')
            
            # Check if both are completed
            if (cross_settlement.dpo_status == 'COMPLETED' and 
                cross_settlement.fx_status == 'COMPLETED'):
                cross_settlement.status = 'COMPLETED'
                cross_settlement.reconciled = True
                from django.utils import timezone
                cross_settlement.reconciled_at = timezone.now()
                cross_settlement.save()
                return True
            
            cross_settlement.save()
            return False
        except Exception as e:
            logger.error(f"Error reconciling settlement: {str(e)}")
            return False
    
    def transfer_token(
        self,
        user: User,
        flow_direction: str,
        token_address: str,
        amount: Decimal
    ) -> Optional[TokenFlow]:
        """
        Transfer token between DPO and FX-to-market.
        
        Args:
            user: User instance
            flow_direction: 'DPO_TO_FX' or 'FX_TO_DPO'
            token_address: Token contract address
            amount: Token amount
            
        Returns:
            TokenFlow instance
        """
        try:
            # Determine from/to user IDs
            if flow_direction == 'DPO_TO_FX':
                from_user_id = str(user.id)
                to_user_id = 'FX_MARKET'
            else:
                from_user_id = 'FX_MARKET'
                to_user_id = str(user.id)
            
            result = self.client.transfer_token(
                from_user_id,
                to_user_id,
                token_address,
                float(amount)
            )
            
            if result:
                token_flow = TokenFlow.objects.create(
                    user=user,
                    flow_direction=flow_direction,
                    status='COMPLETED',
                    token_address=token_address,
                    amount=amount,
                    blockchain_tx_hash=result.get('blockchain_tx_hash'),
                    fx_transaction_id=result.get('transaction_id')
                )
                return token_flow
            else:
                token_flow = TokenFlow.objects.create(
                    user=user,
                    flow_direction=flow_direction,
                    status='FAILED',
                    token_address=token_address,
                    amount=amount
                )
                return token_flow
        except Exception as e:
            logger.error(f"Error transferring token: {str(e)}")
            return None

