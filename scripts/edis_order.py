#!/usr/bin/env python3
"""
EDIS Global VPS Order API client.
Orders VPS hosting and pays with crypto (Cryptomus → Polygon USDC).

USAGE:
    python3 edis_order.py locations           # List available locations
    python3 edis_order.py products <loc_id>   # List products for location
    python3 edis_order.py payment-methods     # List payment methods
    python3 edis_order.py order               # Place order (interactive)

REQUIREMENTS:
    - EDIS account credentials in ~/.noctiluca/private/edis.txt
      Format: email:password
    - pip3 install requests

Author: Noctiluca
Created: 2026-02-08
"""

import os
import sys
import json
import requests
from pathlib import Path

API_BASE = "https://order.edisglobal.com/kvm/v2"

# Default configuration for our VPS
DEFAULT_CONFIG = {
    "location_id": 122,  # Germany (Frankfurt) - close to Erik in Hof
    "location_name": "Germany",
    "billingcycle": "monthly",
    "paymentmethod": "cryptomus",  # Crypto payment (Polygon USDC supported)
    "hostname": "noctiluca-vps",
}

def load_credentials():
    """Load EDIS credentials from file."""
    creds_file = Path.home() / ".noctiluca" / "private" / "edis.txt"
    if not creds_file.exists():
        print(f"❌ Credentials not found at {creds_file}")
        print("Create the file with format: email:password")
        sys.exit(1)
    
    content = creds_file.read_text().strip()
    if ":" not in content:
        print("❌ Invalid credentials format. Use: email:password")
        sys.exit(1)
    
    email, password = content.split(":", 1)
    return email, password

def api_request(endpoint, email, password, extra_data=None):
    """Make API request to EDIS order API."""
    url = f"{API_BASE}/{endpoint}"
    data = {"email": email, "pw": password}
    if extra_data:
        data.update(extra_data)
    
    response = requests.post(
        url,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code != 200:
        print(f"❌ API error: {response.status_code}")
        print(response.text)
        return None
    
    return response.json()

def get_locations(email, password):
    """Get available VPS locations."""
    result = api_request("get/locations", email, password)
    if not result or "locations" not in result:
        print("❌ Failed to get locations")
        return None
    
    return result["locations"]

def get_products(email, password, location_id):
    """Get available products for a location."""
    result = api_request("get/products", email, password, {"location": location_id})
    if not result:
        print(f"❌ Failed to get products for location {location_id}")
        return None
    
    return result

def get_payment_methods(email, password):
    """Get available payment methods."""
    result = api_request("get/paymentmethods", email, password)
    if not result or "paymentmethods" not in result:
        print("❌ Failed to get payment methods")
        return None
    
    return result["paymentmethods"]

def get_ssh_pubkey():
    """Get SSH public key for the VPS."""
    ssh_key_file = Path.home() / ".ssh" / "id_ed25519.pub"
    if not ssh_key_file.exists():
        ssh_key_file = Path.home() / ".ssh" / "id_rsa.pub"
    
    if ssh_key_file.exists():
        return ssh_key_file.read_text().strip()
    
    return None

def place_order(email, password, product_id, os_id, hostname, ssh_pubkey=None):
    """Place a VPS order."""
    order_data = {
        "billingcycle": DEFAULT_CONFIG["billingcycle"],
        "paymentmethod": DEFAULT_CONFIG["paymentmethod"],
        "applycredit": True,  # Use any account credit
        "item": [
            {
                "pid": product_id,
                "os": os_id,
                "hostname": hostname,
                "additional_ram": "",
                "additional_vcpu": "",
                "additional_ip": "",
                "additional_diskboost": "",
                "ssh_pubkey": ssh_pubkey or "",
            }
        ]
    }
    
    # The order API expects JSON in the body
    url = f"{API_BASE}/add/order"
    response = requests.post(
        url,
        data={"email": email, "pw": password},
        json=order_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 200:
        print(f"❌ Order failed: {response.status_code}")
        print(response.text)
        return None
    
    return response.json()

def cmd_locations():
    """List available locations."""
    email, password = load_credentials()
    locations = get_locations(email, password)
    
    if not locations:
        return
    
    print("\n📍 Available VPS Locations:")
    print("-" * 60)
    
    available = []
    out_of_stock = []
    
    for name, info in sorted(locations.items()):
        if info.get("out_of_stock"):
            out_of_stock.append((name, info))
        else:
            available.append((name, info))
    
    print("\n✅ Available:")
    for name, info in available:
        print(f"  [{info['id']:3d}] {info['name']} ({info['country']})")
    
    if out_of_stock:
        print("\n❌ Out of Stock:")
        for name, info in out_of_stock:
            print(f"  [{info['id']:3d}] {info['name']} ({info['country']})")
    
    print(f"\nDefault location: {DEFAULT_CONFIG['location_name']} (ID: {DEFAULT_CONFIG['location_id']})")

def cmd_products(location_id):
    """List products for a location."""
    email, password = load_credentials()
    products = get_products(email, password, location_id)
    
    if not products:
        return
    
    print(f"\n📦 VPS Products for Location {location_id}:")
    print("-" * 70)
    print(json.dumps(products, indent=2))

def cmd_payment_methods():
    """List payment methods."""
    email, password = load_credentials()
    methods = get_payment_methods(email, password)
    
    if not methods:
        return
    
    print("\n💳 Available Payment Methods:")
    for method in methods:
        marker = "✅" if method == "cryptomus" else "  "
        print(f"  {marker} {method}")
    
    print(f"\nWe'll use: cryptomus (Polygon USDC)")

def cmd_order():
    """Interactive order placement."""
    email, password = load_credentials()
    
    print("\n🛒 EDIS Global VPS Order")
    print("=" * 50)
    
    # Get SSH key
    ssh_pubkey = get_ssh_pubkey()
    if ssh_pubkey:
        print(f"✅ SSH key found: {ssh_pubkey[:50]}...")
    else:
        print("⚠️ No SSH key found - you'll need to set one manually")
    
    # Get products for default location
    print(f"\n📍 Location: {DEFAULT_CONFIG['location_name']}")
    products = get_products(email, password, DEFAULT_CONFIG["location_id"])
    
    if not products:
        print("❌ Could not fetch products")
        return
    
    print("\n📦 Available products:")
    print(json.dumps(products, indent=2))
    
    # TODO: Parse products, let user select, place order
    print("\n⚠️ Order placement requires product ID and OS ID")
    print("Run 'products <location_id>' to see available options")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1].lower()
    
    if cmd == "locations":
        cmd_locations()
    elif cmd == "products":
        if len(sys.argv) < 3:
            print("Usage: edis_order.py products <location_id>")
            print(f"Default: {DEFAULT_CONFIG['location_id']} ({DEFAULT_CONFIG['location_name']})")
            return
        cmd_products(int(sys.argv[2]))
    elif cmd == "payment-methods":
        cmd_payment_methods()
    elif cmd == "order":
        cmd_order()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)

if __name__ == "__main__":
    main()
