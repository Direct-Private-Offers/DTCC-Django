"""
Blockchain service module for Web3 integration.
Provides centralized blockchain operations including Web3 provider initialization,
contract interaction, and event parsing.
"""
import os
import json
import logging
from typing import Optional, Dict, Any
from web3 import Web3

logger = logging.getLogger(__name__)


def get_web3_provider(rpc_url: Optional[str] = None) -> Web3:
    """
    Initialize and return a Web3 provider instance.
    
    Args:
        rpc_url: Optional RPC URL. If not provided, uses QUICKNODE_URL or default.
    
    Returns:
        Web3 instance connected to the provider
    """
    url = rpc_url or os.getenv('QUICKNODE_URL') or os.getenv('BLOCKCHAIN_RPC_URL')
    if not url:
        raise ValueError(
            "No RPC URL provided. Set QUICKNODE_URL or BLOCKCHAIN_RPC_URL environment variable."
        )
    
    w3 = Web3(Web3.HTTPProvider(url))
    
    # Add POA middleware for networks like BSC that use Proof of Authority
    network = os.getenv('BLOCKCHAIN_NETWORK', '').upper()
    if network in ['BSC', 'BINANCE', 'POLYGON']:
        # Try Web3 v5 style middleware first, then v6 fallback, else warn
        try:
            from web3.middleware import geth_poa_middleware  # Web3 v5
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            logger.info("Injected geth_poa_middleware for POA network")
        except Exception:
            try:
                # Web3 v6 moved POA middleware
                from web3.middleware.proof_of_authority import POA
                w3.middleware_onion.inject(POA, layer=0)
                logger.info("Injected POA middleware for POA network (Web3 v6)")
            except Exception as e:
                logger.warning(f"POA middleware not available; continuing without. Error: {e}")
    
    # Verify connection
    try:
        block_number = w3.eth.block_number
        logger.info(f"Connected to blockchain at block {block_number}")
    except Exception as e:
        logger.error(f"Failed to connect to blockchain: {str(e)}")
        raise
    
    return w3


def get_contract_instance(w3: Web3, contract_address: str, abi_path: Optional[str] = None) -> Any:
    """
    Load smart contract ABI and create contract instance.
    
    Args:
        w3: Web3 instance
        contract_address: Smart contract address
        abi_path: Optional path to ABI JSON file. If not provided, uses ISSUANCE_CONTRACT_ABI env var or default path.
    
    Returns:
        Contract instance
    """
    address = Web3.to_checksum_address(contract_address)
    
    # Load ABI
    abi_str = os.getenv('ISSUANCE_CONTRACT_ABI')
    if abi_path:
        with open(abi_path, 'r') as f:
            abi = json.load(f)
    elif abi_str:
        try:
            abi = json.loads(abi_str)
        except json.JSONDecodeError:
            # Try as file path
            with open(abi_str, 'r') as f:
                abi = json.load(f)
    else:
        # Default ABI path
        default_path = os.path.join(os.path.dirname(__file__), '..', 'contracts', 'IssuanceContract.abi.json')
        if os.path.exists(default_path):
            with open(default_path, 'r') as f:
                abi = json.load(f)
        else:
            raise ValueError("No ABI provided. Set ISSUANCE_CONTRACT_ABI or provide abi_path.")
    
    contract = w3.eth.contract(address=address, abi=abi)
    logger.info(f"Loaded contract at {address}")
    return contract


def get_latest_block(w3: Web3) -> int:
    """
    Get the latest block number.
    
    Args:
        w3: Web3 instance
    
    Returns:
        Latest block number
    """
    return w3.eth.block_number


def parse_event_log(w3: Web3, contract, tx_hash: str, event_name: str) -> Optional[Dict[str, Any]]:
    """
    Parse event logs from a transaction receipt.
    
    Args:
        w3: Web3 instance
        contract: Contract instance
        tx_hash: Transaction hash
        event_name: Name of the event to parse
    
    Returns:
        Parsed event data or None if not found
    """
    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        event_abi = [e for e in contract.abi if e.get('type') == 'event' and e.get('name') == event_name]
        
        if not event_abi:
            logger.warning(f"Event {event_name} not found in contract ABI")
            return None
        
        event = contract.events[event_name]()
        logs = event.process_receipt(receipt)
        
        if logs:
            return logs[0]['args']
        return None
    except Exception as e:
        logger.error(f"Error parsing event log: {str(e)}")
        return None


def wait_for_confirmation(w3: Web3, tx_hash: str, timeout: int = 300, poll_interval: int = 2) -> bool:
    """
    Wait for transaction confirmation.
    
    Args:
        w3: Web3 instance
        tx_hash: Transaction hash
        timeout: Maximum time to wait in seconds
        poll_interval: Time between polls in seconds
    
    Returns:
        True if confirmed, False if timeout
    """
    import time
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            if receipt:
                return True
        except Exception:
            pass
        time.sleep(poll_interval)
    
    return False

