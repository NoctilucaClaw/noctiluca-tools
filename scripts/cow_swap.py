#!/usr/bin/env python3
"""
CoW Protocol Gasless Swap on Base
---------------------------------
Swaps WETH → USDC on Base using CoW Protocol.
After approval (one-time, costs ~0.0001 ETH), swaps are gasless.

Usage:
  python3 cow_swap.py quote           # Get quote only
  python3 cow_swap.py approve         # Approve WETH for CoW (one-time)
  python3 cow_swap.py swap [amount]   # Execute swap (amount in WETH, default: all)
  
Environment:
  EVM_PRIVATE_KEY - Private key (hex, with or without 0x prefix)
  Or reads from ~/.noctiluca/private/evm_wallet.txt
"""

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

# Base chain constants
BASE_CHAIN_ID = 8453
COW_API = "https://api.cow.fi/base/api/v1"
WETH = "0x4200000000000000000000000000000000000006"
USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
COW_VAULT = "0xC92E8bdf79f0507f65a392b0ab4667716BFE0110"

# Ordered by reliability (tested 2026-02-08)
# llamarpc returns wrong data, meowrpc doesn't support eth_call
RPC_URLS = [
    "https://base-pokt.nodies.app",
    "https://base.drpc.org", 
    "https://base-rpc.publicnode.com",
]

def rpc_call(method, params):
    """Make RPC call, trying multiple endpoints."""
    data = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (compatible; NoctilucaBot/1.0)",
    }
    last_error = None
    for rpc in RPC_URLS:
        try:
            req = urllib.request.Request(rpc,
                data=json.dumps(data).encode(),
                headers=headers)
            resp = urllib.request.urlopen(req, timeout=15)
            result = json.loads(resp.read())
            if "error" in result:
                last_error = result["error"]
                continue
            return result
        except Exception as e:
            last_error = str(e)
            continue
    raise Exception(f"All RPCs failed: {last_error}")

def get_wallet():
    """Load wallet from env or file."""
    pk = os.environ.get("EVM_PRIVATE_KEY")
    if not pk:
        keyfile = Path.home() / ".noctiluca/private/evm_wallet.txt"
        if keyfile.exists():
            content = keyfile.read_text()
            for line in content.split('\n'):
                if line.startswith('Private Key:'):
                    pk = line.split(':', 1)[1].strip()
                    break
    if not pk:
        raise ValueError("No private key found")
    
    from eth_account import Account
    if not pk.startswith('0x'):
        pk = '0x' + pk
    return Account.from_key(pk)

def get_weth_balance(address):
    """Query WETH balance on Base."""
    result = rpc_call("eth_call", [{
        "to": WETH,
        "data": f"0x70a08231000000000000000000000000{address[2:].lower()}"
    }, "latest"])
    return int(result["result"], 16)

def get_eth_balance(address):
    """Query ETH balance on Base."""
    result = rpc_call("eth_getBalance", [address, "latest"])
    return int(result["result"], 16)

def check_allowance(owner, spender):
    """Check WETH allowance for CoW vault."""
    result = rpc_call("eth_call", [{
        "to": WETH,
        "data": f"0xdd62ed3e000000000000000000000000{owner[2:].lower()}000000000000000000000000{spender[2:].lower()}"
    }, "latest"])
    return int(result["result"], 16)

def get_gas_price():
    """Get current gas price."""
    result = rpc_call("eth_gasPrice", [])
    return int(result["result"], 16)

def get_nonce(address):
    """Get transaction count/nonce."""
    result = rpc_call("eth_getTransactionCount", [address, "latest"])
    return int(result["result"], 16)

def send_raw_tx(signed_tx_hex):
    """Send raw transaction."""
    result = rpc_call("eth_sendRawTransaction", [signed_tx_hex])
    return result.get("result")

def wait_for_tx(tx_hash, timeout=60):
    """Wait for transaction to be mined."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            result = rpc_call("eth_getTransactionReceipt", [tx_hash])
            if result.get("result"):
                return result["result"]
        except:
            pass
        time.sleep(2)
    raise Exception("Transaction not mined within timeout")

def get_quote(sell_amount_wei, from_address):
    """Get CoW Protocol quote for WETH→USDC swap."""
    payload = {
        "sellToken": WETH,
        "buyToken": USDC,
        "sellAmountBeforeFee": str(sell_amount_wei),
        "from": from_address,
        "receiver": from_address,
        "kind": "sell",
        "signingScheme": "eip712"
    }
    
    req = urllib.request.Request(
        f"{COW_API}/quote",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read())

def cmd_quote():
    """Get a quote."""
    wallet = get_wallet()
    balance = get_weth_balance(wallet.address)
    eth_balance = get_eth_balance(wallet.address)
    allowance = check_allowance(wallet.address, COW_VAULT)
    
    print(f"Wallet: {wallet.address}")
    print(f"ETH Balance: {eth_balance/1e18:.6f} ETH")
    print(f"WETH Balance: {balance/1e18:.5f} WETH")
    print(f"CoW Allowance: {allowance/1e18:.5f} WETH")
    print()
    
    if balance == 0:
        print("❌ No WETH to swap")
        return
    
    quote = get_quote(balance, wallet.address)
    q = quote['quote']
    sell = int(q['sellAmount'])/1e18
    fee = int(q['feeAmount'])/1e18
    buy = int(q['buyAmount'])/1e6
    
    print(f"Quote (CoW Protocol on Base):")
    print(f"  Sell: {sell:.5f} WETH")
    print(f"  Fee:  {fee:.7f} WETH (deducted from sell)")
    print(f"  Get:  {buy:.2f} USDC")
    print(f"  Rate: ~${buy/sell:.2f}/WETH")
    print()
    
    if allowance >= balance:
        print("✅ Already approved! Ready to swap.")
        print(f"   Run: python3 {sys.argv[0]} swap")
    else:
        print("⚠️  Need approval first (one-time, costs ~0.0001 ETH)")
        print(f"   Run: python3 {sys.argv[0]} approve")

def cmd_approve():
    """Approve WETH for CoW Protocol."""
    from eth_account import Account
    
    wallet = get_wallet()
    eth_balance = get_eth_balance(wallet.address)
    allowance = check_allowance(wallet.address, COW_VAULT)
    
    print(f"Wallet: {wallet.address}")
    print(f"ETH Balance: {eth_balance/1e18:.6f} ETH")
    print(f"Current Allowance: {allowance/1e18:.5f} WETH")
    print()
    
    if allowance > 0:
        print("✅ Already approved!")
        return
    
    # Build approval transaction
    # approve(spender, amount) - max approval
    data = f"0x095ea7b3000000000000000000000000{COW_VAULT[2:].lower()}{'f'*64}"
    
    gas_price = get_gas_price()
    # Add 20% buffer
    gas_price = int(gas_price * 1.2)
    
    nonce = get_nonce(wallet.address)
    
    # Estimate gas
    gas_estimate = 50000  # Standard ERC20 approve
    
    tx_cost = gas_estimate * gas_price
    print(f"Estimated cost: {tx_cost/1e18:.8f} ETH ({gas_price/1e9:.4f} Gwei)")
    
    if eth_balance < tx_cost:
        print(f"❌ Insufficient ETH for gas. Need {tx_cost/1e18:.8f}, have {eth_balance/1e18:.8f}")
        return
    
    # Build transaction
    tx = {
        "chainId": BASE_CHAIN_ID,
        "nonce": nonce,
        "to": WETH,
        "value": 0,
        "gas": gas_estimate,
        "maxFeePerGas": gas_price * 2,
        "maxPriorityFeePerGas": gas_price,
        "data": bytes.fromhex(data[2:]),
    }
    
    print("Signing and sending approval transaction...")
    signed = Account.sign_transaction(tx, wallet.key)
    tx_hash = send_raw_tx(signed.raw_transaction.hex())
    
    if not tx_hash:
        print("❌ Failed to send transaction")
        return
    
    print(f"Tx sent: {tx_hash}")
    print("Waiting for confirmation...")
    
    receipt = wait_for_tx(tx_hash)
    
    if receipt["status"] == "0x1":
        print(f"✅ Approval confirmed!")
        print(f"   Block: {int(receipt['blockNumber'], 16)}")
        print(f"   Gas used: {int(receipt['gasUsed'], 16)}")
        new_allowance = check_allowance(wallet.address, COW_VAULT)
        print(f"   New allowance: {new_allowance/1e18:.5f} WETH (max)")
        print()
        print(f"Now run: python3 {sys.argv[0]} swap")
    else:
        print(f"❌ Transaction failed!")

def cmd_swap(amount=None):
    """Execute the swap."""
    from eth_account import Account
    from eth_account.messages import encode_typed_data
    
    wallet = get_wallet()
    balance = get_weth_balance(wallet.address)
    allowance = check_allowance(wallet.address, COW_VAULT)
    
    sell_wei = int(amount * 1e18) if amount else balance
    
    print(f"Wallet: {wallet.address}")
    print(f"Swapping: {sell_wei/1e18:.5f} WETH → USDC")
    print()
    
    if allowance < sell_wei:
        print(f"❌ Insufficient allowance. Run: python3 {sys.argv[0]} approve")
        return
    
    # Get fresh quote
    quote_resp = get_quote(sell_wei, wallet.address)
    quote = quote_resp['quote']
    
    buy_amount = int(quote['buyAmount'])
    valid_to = quote['validTo']
    sell_amount = int(quote['sellAmount'])
    # Note: CoW Protocol on Base uses feeAmount=0 in orders
    # The fee is already deducted from sellAmount vs sellAmountBeforeFee
    fee_amount = 0
    
    print(f"Quote:")
    print(f"  Sell: {sell_amount/1e18:.5f} WETH")
    print(f"  Get:  {buy_amount/1e6:.2f} USDC")
    print()
    
    # Build EIP-712 order for signing
    order_struct = {
        "sellToken": WETH,
        "buyToken": USDC,
        "receiver": wallet.address,
        "sellAmount": sell_amount,
        "buyAmount": buy_amount,
        "validTo": valid_to,
        "appData": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "feeAmount": fee_amount,  # Must be 0 on Base
        "kind": "sell",
        "partiallyFillable": False,
        "sellTokenBalance": "erc20",
        "buyTokenBalance": "erc20",
    }
    
    # EIP-712 domain
    domain = {
        "name": "Gnosis Protocol",
        "version": "v2", 
        "chainId": BASE_CHAIN_ID,
        "verifyingContract": "0x9008D19f58AAbD9eD0D60971565AA8510560ab41"
    }
    
    # Type definitions
    types = {
        "Order": [
            {"name": "sellToken", "type": "address"},
            {"name": "buyToken", "type": "address"},
            {"name": "receiver", "type": "address"},
            {"name": "sellAmount", "type": "uint256"},
            {"name": "buyAmount", "type": "uint256"},
            {"name": "validTo", "type": "uint32"},
            {"name": "appData", "type": "bytes32"},
            {"name": "feeAmount", "type": "uint256"},
            {"name": "kind", "type": "string"},
            {"name": "partiallyFillable", "type": "bool"},
            {"name": "sellTokenBalance", "type": "string"},
            {"name": "buyTokenBalance", "type": "string"},
        ]
    }
    
    # Sign
    typed_data = {
        "types": types,
        "primaryType": "Order",
        "domain": domain,
        "message": order_struct
    }
    
    print("Signing order...")
    signable = encode_typed_data(full_message=typed_data)
    signed = Account.sign_message(signable, wallet.key)
    signature = signed.signature.hex()
    if not signature.startswith('0x'):
        signature = '0x' + signature
    
    # Submit order to CoW API
    order_payload = {
        "sellToken": order_struct["sellToken"],
        "buyToken": order_struct["buyToken"],
        "receiver": order_struct["receiver"],
        "sellAmount": str(order_struct["sellAmount"]),
        "buyAmount": str(order_struct["buyAmount"]),
        "validTo": order_struct["validTo"],
        "appData": order_struct["appData"],
        "feeAmount": str(order_struct["feeAmount"]),
        "kind": order_struct["kind"],
        "partiallyFillable": order_struct["partiallyFillable"],
        "sellTokenBalance": order_struct["sellTokenBalance"],
        "buyTokenBalance": order_struct["buyTokenBalance"],
        "signingScheme": "eip712",
        "signature": signature,
        "from": wallet.address,
    }
    
    print("Submitting order to CoW Protocol...")
    
    req = urllib.request.Request(
        f"{COW_API}/orders",
        data=json.dumps(order_payload).encode(),
        headers={"Content-Type": "application/json"}
    )
    
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        order_uid = json.loads(resp.read())
        print(f"✅ Order submitted!")
        print(f"   Order ID: {order_uid}")
        print(f"   Track: https://explorer.cow.fi/base/orders/{order_uid}")
        print()
        print("Order will be filled by solvers (usually within minutes).")
        print("USDC will appear in your wallet after filling.")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"❌ Order submission failed: {e.code}")
        print(f"   {error_body}")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    action = sys.argv[1].lower()
    
    if action == "quote":
        cmd_quote()
    elif action == "approve":
        cmd_approve()
    elif action == "swap":
        amount = float(sys.argv[2]) if len(sys.argv) > 2 else None
        cmd_swap(amount)
    else:
        print(f"Unknown action: {action}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
