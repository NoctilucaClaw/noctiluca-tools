#!/usr/bin/env python3
"""
Across Protocol Bridge Script
Bridge USDC from Base to Polygon for VPS payment
"""

import os
import sys
import json
import requests
from web3 import Web3
from eth_account import Account

# Chain IDs
BASE_CHAIN_ID = 8453
POLYGON_CHAIN_ID = 137

# Token addresses
BASE_USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
POLYGON_USDC = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"  # Native USDC on Polygon

# RPC endpoints
BASE_RPC = "https://base.publicnode.com"

# Across API
ACROSS_API = "https://app.across.to/api"

# ERC20 ABI (minimal)
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
]


def load_wallet():
    """Load wallet from private key file"""
    key_file = os.path.expanduser("~/.noctiluca/private/evm_wallet.txt")
    with open(key_file, 'r') as f:
        content = f.read()
    
    for line in content.split('\n'):
        if line.startswith('Private Key:'):
            pk = line.split(':', 1)[1].strip()
            if not pk.startswith('0x'):
                pk = '0x' + pk
            return Account.from_key(pk)
    raise ValueError("Private key not found")


def get_balances(w3, account, usdc_contract):
    """Get ETH and USDC balances"""
    eth_balance = w3.eth.get_balance(account.address)
    usdc_balance = usdc_contract.functions.balanceOf(account.address).call()
    return eth_balance, usdc_balance


def get_quote(amount_wei, depositor):
    """Get bridge quote from Across API"""
    url = f"{ACROSS_API}/swap/approval"
    
    params = {
        "tradeType": "exactInput",
        "amount": str(amount_wei),
        "inputToken": BASE_USDC,
        "outputToken": POLYGON_USDC,
        "originChainId": BASE_CHAIN_ID,
        "destinationChainId": POLYGON_CHAIN_ID,
        "depositor": depositor,
        "recipient": depositor,
        "slippage": "auto",
    }
    
    print(f"\n📡 Getting Across quote...")
    print(f"   Amount: {amount_wei / 1e6:.2f} USDC")
    print(f"   Route: Base → Polygon")
    
    resp = requests.get(url, params=params, timeout=30)
    
    if resp.status_code != 200:
        print(f"❌ API error: {resp.status_code}")
        print(resp.text)
        return None
    
    return resp.json()


def execute_bridge(w3, account, quote_data):
    """Execute bridge transactions"""
    
    # Check if approval is needed
    approval_txns = quote_data.get("approvalTxns", [])
    bridge_txn = quote_data.get("swapTx")
    
    print(f"\n📋 Transaction plan:")
    print(f"   Approval TXs: {len(approval_txns)}")
    print(f"   Bridge TX: {'Yes' if bridge_txn else 'No'}")
    
    # Get current nonce
    nonce = w3.eth.get_transaction_count(account.address)
    
    # Execute approval transactions first
    for i, approval in enumerate(approval_txns):
        print(f"\n🔐 Executing approval {i+1}/{len(approval_txns)}...")
        
        tx = {
            'to': Web3.to_checksum_address(approval['to']),
            'data': approval['data'],
            'value': int(approval.get('value', 0)),
            'gas': 100000,
            'maxFeePerGas': w3.eth.gas_price * 2,
            'maxPriorityFeePerGas': w3.to_wei(0.001, 'gwei'),
            'nonce': nonce,
            'chainId': BASE_CHAIN_ID,
        }
        
        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        print(f"   TX: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        if receipt['status'] != 1:
            print(f"❌ Approval failed!")
            return False
        print(f"   ✅ Confirmed in block {receipt['blockNumber']}")
        nonce += 1
    
    # Execute bridge transaction
    if bridge_txn:
        print(f"\n🌉 Executing bridge transaction...")
        
        tx = {
            'to': Web3.to_checksum_address(bridge_txn['to']),
            'data': bridge_txn['data'],
            'value': int(bridge_txn.get('value', 0)),
            'gas': 300000,
            'maxFeePerGas': w3.eth.gas_price * 2,
            'maxPriorityFeePerGas': w3.to_wei(0.001, 'gwei'),
            'nonce': nonce,
            'chainId': BASE_CHAIN_ID,
        }
        
        # Estimate gas
        try:
            estimated_gas = w3.eth.estimate_gas(tx)
            tx['gas'] = int(estimated_gas * 1.2)
            print(f"   Estimated gas: {estimated_gas}")
        except Exception as e:
            print(f"   Gas estimation failed, using default: {e}")
        
        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        print(f"   TX: {tx_hash.hex()}")
        print(f"   BaseScan: https://basescan.org/tx/{tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        if receipt['status'] != 1:
            print(f"❌ Bridge failed!")
            return False
        
        print(f"   ✅ Deposit confirmed in block {receipt['blockNumber']}")
        print(f"\n🎉 Bridge initiated! Funds should arrive on Polygon in ~3 seconds.")
        return True
    
    return False


def main():
    print("=" * 60)
    print("🌉 Across Protocol Bridge: Base USDC → Polygon USDC")
    print("=" * 60)
    
    if "--help" in sys.argv or "-h" in sys.argv:
        print("\nUsage: python3 across_bridge.py [OPTIONS]")
        print("\nOptions:")
        print("  --execute, -x    Execute the bridge (required to actually bridge)")
        print("  --help, -h       Show this help message")
        print("\nWithout --execute, shows quote only (dry run).")
        sys.exit(0)
    
    # Load wallet
    account = load_wallet()
    print(f"\n💳 Wallet: {account.address}")
    
    # Connect to Base
    w3 = Web3(Web3.HTTPProvider(BASE_RPC))
    if not w3.is_connected():
        print("❌ Failed to connect to Base RPC")
        sys.exit(1)
    print(f"✅ Connected to Base (Chain ID: {w3.eth.chain_id})")
    
    # Get USDC contract
    usdc = w3.eth.contract(address=Web3.to_checksum_address(BASE_USDC), abi=ERC20_ABI)
    
    # Get balances
    eth_balance, usdc_balance = get_balances(w3, account, usdc)
    print(f"\n💰 Balances:")
    print(f"   ETH: {eth_balance / 1e18:.6f}")
    print(f"   USDC: {usdc_balance / 1e6:.2f}")
    
    if usdc_balance == 0:
        print("\n❌ No USDC to bridge!")
        sys.exit(1)
    
    if eth_balance < w3.to_wei(0.0001, 'ether'):
        print("\n❌ Not enough ETH for gas!")
        sys.exit(1)
    
    # Bridge amount (leave some dust for safety)
    bridge_amount = usdc_balance - 1000  # Leave 0.001 USDC
    print(f"\n🎯 Bridging {bridge_amount / 1e6:.2f} USDC to Polygon")
    
    # Get quote
    quote = get_quote(bridge_amount, account.address)
    if not quote:
        print("❌ Failed to get quote")
        sys.exit(1)
    
    # Show expected output
    if 'expectedOutput' in quote:
        expected = int(quote['expectedOutput'])
        print(f"\n📊 Expected output: {expected / 1e6:.2f} USDC on Polygon")
        fee = (bridge_amount - expected) / 1e6
        print(f"   Bridge fee: ~${fee:.4f}")
    
    # Check for auto-execute flag
    auto_execute = "--execute" in sys.argv or "-x" in sys.argv
    
    if not auto_execute:
        print("\n" + "=" * 60)
        print("Run with --execute or -x flag to execute the bridge")
        print("Example: python3 across_bridge.py --execute")
        sys.exit(0)
    
    # Execute
    success = execute_bridge(w3, account, quote)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Bridge complete!")
        print(f"Check Polygon for your USDC:")
        print(f"https://polygonscan.com/address/{account.address}")
    else:
        print("\n❌ Bridge failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
