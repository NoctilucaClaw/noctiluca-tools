#!/usr/bin/env python3
"""
Noctiluca Tools - Unified CLI
=============================

A collection of tools for AI agent infrastructure independence.

Commands:
  swap      - Gasless token swaps via CoW Protocol (Base)
  bridge    - Cross-chain bridging via Across Protocol
  vps       - EDIS Global VPS management

Usage:
  ./noctiluca_tools.py swap quote
  ./noctiluca_tools.py swap approve
  ./noctiluca_tools.py swap execute [amount]
  ./noctiluca_tools.py bridge quote <amount>
  ./noctiluca_tools.py bridge execute <amount>
  ./noctiluca_tools.py vps register
  ./noctiluca_tools.py vps order [--location ID] [--product ID]
  ./noctiluca_tools.py vps locations
  ./noctiluca_tools.py vps products
  ./noctiluca_tools.py balance

Run with --help for more details.
"""

import argparse
import importlib.util
import os
import sys
from pathlib import Path

# Get scripts directory relative to this file
SCRIPTS_DIR = Path(__file__).parent / "scripts"


def load_script(name: str):
    """Dynamically load a script module."""
    script_path = SCRIPTS_DIR / f"{name}.py"
    if not script_path.exists():
        print(f"Error: Script not found: {script_path}", file=sys.stderr)
        sys.exit(1)
    
    spec = importlib.util.spec_from_file_location(name, script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cmd_swap(args):
    """Handle swap subcommand."""
    # Temporarily modify sys.argv for the script
    original_argv = sys.argv
    
    if args.action == "quote":
        sys.argv = ["cow_swap.py", "quote"]
    elif args.action == "approve":
        sys.argv = ["cow_swap.py", "approve"]
    elif args.action == "execute":
        if args.amount:
            sys.argv = ["cow_swap.py", "swap", args.amount]
        else:
            sys.argv = ["cow_swap.py", "swap"]
    else:
        print(f"Unknown swap action: {args.action}")
        print("Use: swap quote|approve|execute [amount]")
        sys.exit(1)
    
    try:
        module = load_script("cow_swap")
        if hasattr(module, "main"):
            module.main()
    finally:
        sys.argv = original_argv


def cmd_bridge(args):
    """Handle bridge subcommand."""
    original_argv = sys.argv
    
    if args.action == "quote":
        if not args.amount:
            print("Error: amount required for quote")
            sys.exit(1)
        sys.argv = ["across_bridge.py", "quote", args.amount]
    elif args.action == "execute":
        if not args.amount:
            print("Error: amount required for bridge")
            sys.exit(1)
        sys.argv = ["across_bridge.py", "bridge", args.amount]
    else:
        print(f"Unknown bridge action: {args.action}")
        print("Use: bridge quote|execute <amount>")
        sys.exit(1)
    
    try:
        module = load_script("across_bridge")
        if hasattr(module, "main"):
            module.main()
    finally:
        sys.argv = original_argv


def cmd_vps(args):
    """Handle VPS subcommand."""
    original_argv = sys.argv
    
    try:
        if args.action == "register":
            sys.argv = ["edis_register.py"]
            module = load_script("edis_register")
            if hasattr(module, "main"):
                module.main()
        elif args.action == "locations":
            sys.argv = ["edis_order.py", "locations"]
            module = load_script("edis_order")
            if hasattr(module, "main"):
                module.main()
        elif args.action == "products":
            sys.argv = ["edis_order.py", "products"]
            module = load_script("edis_order")
            if hasattr(module, "main"):
                module.main()
        elif args.action == "order":
            cmd = ["edis_order.py", "order"]
            if args.location:
                cmd.extend(["--location", args.location])
            if args.product:
                cmd.extend(["--product", args.product])
            sys.argv = cmd
            module = load_script("edis_order")
            if hasattr(module, "main"):
                module.main()
        else:
            print(f"Unknown VPS action: {args.action}")
            print("Use: vps register|locations|products|order")
            sys.exit(1)
    finally:
        sys.argv = original_argv


def cmd_balance(args):
    """Check wallet balances across networks."""
    import json
    import urllib.request
    
    # Load wallet
    wallet_file = Path.home() / ".noctiluca" / "private" / "evm_wallet.txt"
    if not wallet_file.exists():
        print("Error: No wallet found at ~/.noctiluca/private/evm_wallet.txt")
        sys.exit(1)
    
    address = None
    for line in wallet_file.read_text().strip().split("\n"):
        if line.startswith("Address:"):
            address = line.split(":")[1].strip()
            break
    
    if not address:
        print("Error: Could not parse wallet address")
        sys.exit(1)
    
    print(f"Wallet: {address}\n")
    
    # Define networks and tokens
    # Using publicnode RPCs - most reliable for anonymous access
    networks = {
        "Base": {
            "rpc": "https://base-rpc.publicnode.com",
            "tokens": {
                "ETH": None,  # Native
                "WETH": "0x4200000000000000000000000000000000000006",
                "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            }
        },
        "Polygon": {
            "rpc": "https://polygon-bor-rpc.publicnode.com",
            "tokens": {
                "MATIC": None,  # Native
                "USDC": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
            }
        }
    }
    
    def get_balance(rpc, address, token=None, decimals=18):
        """Get balance via RPC."""
        try:
            if token is None:
                # Native balance
                data = {
                    "jsonrpc": "2.0",
                    "method": "eth_getBalance",
                    "params": [address, "latest"],
                    "id": 1
                }
            else:
                # ERC20 balance
                call_data = "0x70a08231" + address[2:].lower().zfill(64)
                data = {
                    "jsonrpc": "2.0",
                    "method": "eth_call",
                    "params": [{"to": token, "data": call_data}, "latest"],
                    "id": 1
                }
            
            req = urllib.request.Request(
                rpc,
                data=json.dumps(data).encode(),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json",
                }
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.load(resp)
                if "result" in result:
                    raw = int(result["result"], 16)
                    return raw / (10 ** decimals)
        except Exception as e:
            return None
        return None
    
    # Check all balances
    for network_name, config in networks.items():
        print(f"=== {network_name} ===")
        for token_name, token_addr in config["tokens"].items():
            # USDC has 6 decimals
            decimals = 6 if "USDC" in token_name else 18
            balance = get_balance(config["rpc"], address, token_addr, decimals)
            if balance is not None:
                if balance > 0.0001 or "USDC" in token_name:
                    print(f"  {token_name}: {balance:.6f}")
                else:
                    print(f"  {token_name}: {balance:.10f}")
            else:
                print(f"  {token_name}: (error)")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Noctiluca Tools - AI Agent Infrastructure CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s balance                    Check wallet balances
  %(prog)s swap quote                 Get WETH→USDC swap quote
  %(prog)s swap approve               Approve WETH for trading (one-time)
  %(prog)s swap execute               Swap all WETH to USDC
  %(prog)s bridge quote 50            Get quote for bridging 50 USDC
  %(prog)s bridge execute 50          Bridge 50 USDC Base→Polygon
  %(prog)s vps locations              List EDIS Global locations
  %(prog)s vps order                  Order a VPS

More info: https://github.com/NoctilucaClaw/noctiluca-tools
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Balance command
    balance_parser = subparsers.add_parser("balance", help="Check wallet balances")
    balance_parser.set_defaults(func=cmd_balance)
    
    # Swap command
    swap_parser = subparsers.add_parser("swap", help="Token swaps via CoW Protocol")
    swap_parser.add_argument("action", choices=["quote", "approve", "execute"],
                            help="Action to perform")
    swap_parser.add_argument("amount", nargs="?", help="Amount in WETH (default: all)")
    swap_parser.set_defaults(func=cmd_swap)
    
    # Bridge command
    bridge_parser = subparsers.add_parser("bridge", help="Cross-chain bridging")
    bridge_parser.add_argument("action", choices=["quote", "execute"],
                              help="Action to perform")
    bridge_parser.add_argument("amount", nargs="?", help="Amount in USDC")
    bridge_parser.set_defaults(func=cmd_bridge)
    
    # VPS command
    vps_parser = subparsers.add_parser("vps", help="EDIS Global VPS management")
    vps_parser.add_argument("action", 
                           choices=["register", "locations", "products", "order"],
                           help="Action to perform")
    vps_parser.add_argument("--location", help="Location ID for order")
    vps_parser.add_argument("--product", help="Product ID for order")
    vps_parser.set_defaults(func=cmd_vps)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    args.func(args)


if __name__ == "__main__":
    main()
