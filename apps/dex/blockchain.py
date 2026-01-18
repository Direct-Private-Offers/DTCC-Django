"""
Blockchain integration for DEX operations.
Handles wallet-to-wallet transfers, swaps, and token operations.
"""
import os
import logging
from typing import Optional, Dict, Any
from decimal import Decimal
from web3 import Web3
from apps.core.blockchain import get_web3_provider, wait_for_confirmation
from web3.middleware import geth_poa_middleware

logger = logging.getLogger(__name__)


def transfer_tokens(
    from_address: str,
    to_address: str,
    token_address: str,
    amount: Decimal,
    private_key: Optional[str] = None
) -> Optional[str]:
    """
    Execute wallet-to-wallet token transfer.
    
    Args:
        from_address: Sender wallet address
        to_address: Recipient wallet address
        token_address: ERC20 token contract address
        amount: Amount to transfer
        private_key: Optional private key for signing (if not provided, uses env var)
    
    Returns:
        Transaction hash or None on error
    """
    try:
        w3 = get_web3_provider()
        
        # Load ERC20 ABI (standard)
        erc20_abi = [
            {
                "constant": False,
                "inputs": [
                    {"name": "_to", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "transfer",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }
        ]
        
        token_contract = w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=erc20_abi
        )
        
        # Get private key
        if not private_key:
            private_key = os.getenv('WALLET_PRIVATE_KEY')
        if not private_key:
            raise ValueError("Private key not provided")
        
        account = w3.eth.account.from_key(private_key)
        
        # Build transaction
        nonce = w3.eth.get_transaction_count(account.address)
        amount_wei = int(amount * Decimal(10**18))  # Assuming 18 decimals
        
        tx = token_contract.functions.transfer(
            Web3.to_checksum_address(to_address),
            amount_wei
        ).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
        })
        
        # Sign and send
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        logger.info(f"Token transfer initiated: {tx_hash.hex()}")
        return tx_hash.hex()
    
    except Exception as e:
        logger.error(f"Error transferring tokens: {str(e)}")
        return None


def get_token_balance(w3: Web3, token_address: str, wallet_address: str) -> Decimal:
    """
    Query token balance for an address.
    
    Args:
        w3: Web3 instance
        token_address: ERC20 token contract address
        wallet_address: Wallet address to check
    
    Returns:
        Token balance
    """
    try:
        erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }
        ]
        
        token_contract = w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=erc20_abi
        )
        
        balance = token_contract.functions.balanceOf(
            Web3.to_checksum_address(wallet_address)
        ).call()
        
        return Decimal(balance) / Decimal(10**18)  # Assuming 18 decimals
    
    except Exception as e:
        logger.error(f"Error getting token balance: {str(e)}")
        return Decimal('0')


def get_token_allowance(w3: Web3, token_address: str, owner_address: str, spender_address: str) -> Decimal:
    """
    Check token allowance.
    
    Args:
        w3: Web3 instance
        token_address: ERC20 token contract address
        owner_address: Token owner address
        spender_address: Spender address
    
    Returns:
        Allowance amount
    """
    try:
        erc20_abi = [
            {
                "constant": True,
                "inputs": [
                    {"name": "_owner", "type": "address"},
                    {"name": "_spender", "type": "address"}
                ],
                "name": "allowance",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            }
        ]
        
        token_contract = w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=erc20_abi
        )
        
        allowance = token_contract.functions.allowance(
            Web3.to_checksum_address(owner_address),
            Web3.to_checksum_address(spender_address)
        ).call()
        
        return Decimal(allowance) / Decimal(10**18)
    
    except Exception as e:
        logger.error(f"Error getting token allowance: {str(e)}")
        return Decimal('0')


def approve_token(
    token_address: str,
    spender_address: str,
    amount: Decimal,
    private_key: Optional[str] = None
) -> Optional[str]:
    """
    Approve token spending.
    
    Args:
        token_address: ERC20 token contract address
        spender_address: Address to approve
        amount: Amount to approve
        private_key: Optional private key
    
    Returns:
        Transaction hash or None
    """
    try:
        w3 = get_web3_provider()
        
        erc20_abi = [
            {
                "constant": False,
                "inputs": [
                    {"name": "_spender", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            }
        ]
        
        token_contract = w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=erc20_abi
        )
        
        if not private_key:
            private_key = os.getenv('WALLET_PRIVATE_KEY')
        if not private_key:
            raise ValueError("Private key not provided")
        
        account = w3.eth.account.from_key(private_key)
        nonce = w3.eth.get_transaction_count(account.address)
        amount_wei = int(amount * Decimal(10**18))
        
        tx = token_contract.functions.approve(
            Web3.to_checksum_address(spender_address),
            amount_wei
        ).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
        })
        
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        logger.info(f"Token approval initiated: {tx_hash.hex()}")
        return tx_hash.hex()
    
    except Exception as e:
        logger.error(f"Error approving token: {str(e)}")
        return None


def estimate_gas(w3: Web3, tx: Dict[str, Any]) -> int:
    """
    Estimate gas for a transaction.
    
    Args:
        w3: Web3 instance
        tx: Transaction dictionary
    
    Returns:
        Estimated gas
    """
    try:
        return w3.eth.estimate_gas(tx)
    except Exception as e:
        logger.error(f"Error estimating gas: {str(e)}")
        return 21000  # Default gas limit

