"""
Blockchain event listener service for issuance contract.
Listens to blockchain events via QuickNode and processes them.
"""
import os
import logging
import time
from typing import Optional, Dict, Any
from django.utils import timezone
from web3 import Web3
from apps.core.blockchain import get_web3_provider, get_contract_instance, parse_event_log
from apps.issuance.models import IssuanceEvent, TransferEvent

logger = logging.getLogger(__name__)


class EventListener:
    """Listens to blockchain events and processes them."""
    
    def __init__(self):
        self.w3: Optional[Web3] = None
        self.contract = None
        self.contract_address = os.getenv('ISSUANCE_CONTRACT_ADDRESS')
        self.start_block = int(os.getenv('START_BLOCK_NUMBER', '0'))
        self.last_processed_block = self.start_block
        self.running = False
    
    def initialize(self):
        """Initialize Web3 connection and contract."""
        try:
            self.w3 = get_web3_provider()
            if not self.contract_address:
                raise ValueError("ISSUANCE_CONTRACT_ADDRESS environment variable not set")
            
            self.contract = get_contract_instance(self.w3, self.contract_address)
            
            # Get last processed block from database
            last_event = IssuanceEvent.objects.order_by('-block_number').first()
            if last_event:
                self.last_processed_block = last_event.block_number
            
            logger.info(f"Event listener initialized. Starting from block {self.last_processed_block}")
        except Exception as e:
            logger.error(f"Failed to initialize event listener: {str(e)}")
            raise
    
    def start_event_listener(self, poll_interval: int = 5):
        """
        Start the event listener loop.
        
        Args:
            poll_interval: Time between polls in seconds
        """
        if not self.w3 or not self.contract:
            self.initialize()
        
        self.running = True
        logger.info("Event listener started")
        
        try:
            while self.running:
                try:
                    latest_block = self.w3.eth.block_number
                    
                    if latest_block > self.last_processed_block:
                        self._process_blocks(self.last_processed_block + 1, latest_block)
                        self.last_processed_block = latest_block
                    
                    time.sleep(poll_interval)
                except KeyboardInterrupt:
                    logger.info("Event listener stopped by user")
                    self.running = False
                    break
                except Exception as e:
                    logger.error(f"Error in event listener loop: {str(e)}")
                    time.sleep(poll_interval)
        finally:
            self.running = False
            logger.info("Event listener stopped")
    
    def _process_blocks(self, from_block: int, to_block: int):
        """Process events in a range of blocks."""
        logger.info(f"Processing blocks {from_block} to {to_block}")
        
        try:
            # Get TokenIssued events
            issuance_events = self.contract.events.TokenIssued.get_logs(
                fromBlock=from_block,
                toBlock=to_block
            )
            for event in issuance_events:
                self.process_issuance_event(event)
            
            # Get Transfer events
            transfer_events = self.contract.events.Transfer.get_logs(
                fromBlock=from_block,
                toBlock=to_block
            )
            for event in transfer_events:
                self.process_transfer_event(event)
        
        except Exception as e:
            logger.error(f"Error processing blocks {from_block}-{to_block}: {str(e)}")
            self.handle_event_error(e, from_block, to_block)
    
    def process_issuance_event(self, event: Dict[str, Any]):
        """Process a TokenIssued event."""
        try:
            args = event.get('args', {})
            block_number = event.get('blockNumber')
            tx_hash = event.get('transactionHash').hex()
            
            # Extract event data
            isin = args.get('isin', '')
            investor_address = args.get('investor', '')
            amount = args.get('amount', 0)
            
            # Create or update issuance event
            issuance_event, created = IssuanceEvent.objects.get_or_create(
                tx_hash=tx_hash,
                defaults={
                    'block_number': block_number,
                    'event_type': 'TokenIssued',
                    'event_data': dict(args),
                    'isin': isin,
                    'investor_address': investor_address,
                    'amount': amount,
                    'transaction_id': args.get('transactionId', ''),
                    'euroclear_ref': args.get('euroclearRef', ''),
                }
            )
            
            if created:
                logger.info(f"Created IssuanceEvent: {isin} -> {investor_address}, amount: {amount}")
            else:
                logger.debug(f"IssuanceEvent already exists: {tx_hash}")
        
        except Exception as e:
            logger.error(f"Error processing issuance event: {str(e)}")
            raise
    
    def process_transfer_event(self, event: Dict[str, Any]):
        """Process a Transfer event."""
        try:
            args = event.get('args', {})
            block_number = event.get('blockNumber')
            tx_hash = event.get('transactionHash').hex()
            
            # Extract event data
            isin = args.get('isin', '')
            from_address = args.get('from', '')
            to_address = args.get('to', '')
            amount = args.get('amount', 0)
            
            # Create or update transfer event
            transfer_event, created = TransferEvent.objects.get_or_create(
                tx_hash=tx_hash,
                defaults={
                    'block_number': block_number,
                    'event_type': 'Transfer',
                    'event_data': dict(args),
                    'isin': isin,
                    'from_address': from_address,
                    'to_address': to_address,
                    'amount': amount,
                }
            )
            
            if created:
                logger.info(f"Created TransferEvent: {isin}, {from_address} -> {to_address}, amount: {amount}")
            else:
                logger.debug(f"TransferEvent already exists: {tx_hash}")
        
        except Exception as e:
            logger.error(f"Error processing transfer event: {str(e)}")
            raise
    
    def handle_event_error(self, error: Exception, from_block: int, to_block: int):
        """Handle errors during event processing."""
        logger.error(
            f"Error processing events in blocks {from_block}-{to_block}: {str(error)}"
        )
        # Could implement retry logic or alerting here
        pass
    
    def stop(self):
        """Stop the event listener."""
        self.running = False
        logger.info("Event listener stop requested")


# Global listener instance
_listener: Optional[EventListener] = None


def get_listener() -> EventListener:
    """Get or create the global event listener instance."""
    global _listener
    if _listener is None:
        _listener = EventListener()
    return _listener


def start_listener(poll_interval: int = 5):
    """Start the event listener."""
    listener = get_listener()
    listener.start_event_listener(poll_interval=poll_interval)

