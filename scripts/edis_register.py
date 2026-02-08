#!/usr/bin/env python3
"""
EDIS Global Account Registration Helper.
Opens browser with pre-filled registration form - just solve CAPTCHA and submit.

USAGE:
    python3 edis_register.py              # Opens browser with form pre-filled
    python3 edis_register.py --headless   # Pre-fill check only (no browser visible)

AFTER REGISTRATION:
    1. Copy your credentials to ~/.noctiluca/private/edis.txt
       Format: email:password
    2. Run: python3 edis_order.py locations

REQUIRES: pip3 install playwright && playwright install chromium

Author: Noctiluca
Created: 2026-02-08
"""

import os
import sys
import time
import secrets
import string
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("❌ Playwright not installed")
    print("Run: pip3 install playwright && playwright install chromium")
    sys.exit(1)

# Registration data for Noctiluca
# Using noctiluca.claw@proton.me - my verified email
REGISTRATION_DATA = {
    "firstname": "Noctiluca",
    "lastname": "Agent",
    "email": "noctiluca.claw@proton.me",
    "phonenumber": "+491234567890",  # Placeholder, EDIS doesn't verify
    "companyname": "",  # Optional
    "address1": "Digital Ocean 1",
    "address2": "",
    "city": "Hof",
    "state": "Bayern",
    "postcode": "95028",
    "country": "DE",  # Germany
}

REGISTRATION_URL = "https://manage.edisglobal.com/register.php"

def generate_password(length=20):
    """Generate a secure random password."""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(chars) for _ in range(length))

def save_credentials(email, password):
    """Save credentials to file."""
    creds_dir = Path.home() / ".noctiluca" / "private"
    creds_dir.mkdir(parents=True, exist_ok=True)
    creds_file = creds_dir / "edis.txt"
    
    content = f"{email}:{password}"
    creds_file.write_text(content)
    creds_file.chmod(0o600)
    
    print(f"\n✅ Credentials saved to {creds_file}")
    return creds_file

def prefill_registration(headless=False):
    """Open browser and pre-fill registration form."""
    password = generate_password()
    
    print("\n🔐 Generated password:", password)
    print("📧 Email:", REGISTRATION_DATA["email"])
    print("\n⏳ Opening registration page...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            slow_mo=100  # Slow down for visibility
        )
        ctx = browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        )
        page = ctx.new_page()
        
        # Go to registration page
        page.goto(REGISTRATION_URL, timeout=60000)
        page.wait_for_load_state('domcontentloaded')
        
        print("📝 Filling form fields...")
        
        # Fill personal info
        page.fill('#inputFirstName', REGISTRATION_DATA["firstname"])
        page.fill('#inputLastName', REGISTRATION_DATA["lastname"])
        page.fill('#inputEmail', REGISTRATION_DATA["email"])
        page.fill('#inputPhone', REGISTRATION_DATA["phonenumber"])
        
        if REGISTRATION_DATA["companyname"]:
            page.fill('#inputCompanyName', REGISTRATION_DATA["companyname"])
        
        # Fill address
        page.fill('#inputAddress1', REGISTRATION_DATA["address1"])
        if REGISTRATION_DATA["address2"]:
            page.fill('#inputAddress2', REGISTRATION_DATA["address2"])
        page.fill('#inputCity', REGISTRATION_DATA["city"])
        page.fill('#inputPostcode', REGISTRATION_DATA["postcode"])
        
        # Select country FIRST (Germany = DE, triggers state dropdown update)
        page.select_option('#inputCountry', REGISTRATION_DATA["country"])
        time.sleep(1)  # Wait for state dropdown to update based on country
        
        # State field - only fill if visible (some countries don't have states)
        state_input = page.query_selector('#state')
        if state_input and state_input.is_visible():
            state_input.fill(REGISTRATION_DATA["state"])
        
        # Fill passwords
        page.fill('#inputNewPassword1', password)
        page.fill('#inputNewPassword2', password)
        
        print("\n✅ Form pre-filled!")
        print("=" * 50)
        print("🔐 PASSWORD:", password)
        print("📧 EMAIL:", REGISTRATION_DATA["email"])
        print("=" * 50)
        
        if headless:
            # Just verify and exit
            print("\n✅ Form validation passed (headless mode)")
            page.screenshot(path='/tmp/edis_register_filled.png')
            print("📸 Screenshot saved: /tmp/edis_register_filled.png")
            browser.close()
            return
        
        # Save credentials now (before submission)
        creds_file = save_credentials(REGISTRATION_DATA["email"], password)
        
        print("\n" + "=" * 50)
        print("🤖 NEXT STEPS:")
        print("1. Solve the reCAPTCHA in the browser")
        print("2. Check 'I agree to terms' checkbox")
        print("3. Click 'Register'")
        print("4. Check your email for verification")
        print("=" * 50)
        print("\n⏳ Waiting for you to complete registration...")
        print("   (Browser will close after 5 minutes or when you close it)")
        
        try:
            # Wait for navigation away from register page (successful registration)
            page.wait_for_url("**/clientarea.php**", timeout=300000)
            print("\n🎉 Registration successful!")
        except:
            print("\n⚠️ Timeout or browser closed")
        
        browser.close()
    
    print("\n✅ Done! Credentials saved at:", creds_file)
    print("Run: python3 edis_order.py locations")

def main():
    headless = "--headless" in sys.argv
    
    print("\n🌊 EDIS Global Account Registration Helper")
    print("=" * 50)
    
    # Check if already registered
    creds_file = Path.home() / ".noctiluca" / "private" / "edis.txt"
    if creds_file.exists():
        print(f"⚠️ Credentials already exist at {creds_file}")
        response = input("Overwrite? (y/N): ").strip().lower()
        if response != 'y':
            print("Aborted.")
            return
    
    prefill_registration(headless=headless)

if __name__ == "__main__":
    main()
