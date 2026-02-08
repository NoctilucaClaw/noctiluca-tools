#!/usr/bin/env python3
"""
VPS Provisioning Script.
Sets up a fresh VPS with essential tools and security hardening.

USAGE:
    python3 provision_vps.py <host> [--user root] [--key ~/.ssh/id_rsa]
    python3 provision_vps.py setup-keys <host>   # Copy SSH key to VPS
    python3 provision_vps.py check <host>        # Check VPS status

WHAT IT DOES:
    1. Updates system packages
    2. Installs essential tools (git, curl, wget, htop, tmux, fail2ban)
    3. Creates 'noctiluca' user with sudo access
    4. Configures SSH hardening (disable root login, password auth)
    5. Sets up UFW firewall (SSH only by default)
    6. Installs Node.js LTS (for OpenClaw)
    7. Installs Python 3 with pip

Author: Noctiluca
Created: 2026-02-08
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Commands to run on fresh VPS
PROVISION_COMMANDS = """
set -e

echo "=== 1. System Update ==="
apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y

echo "=== 2. Essential Packages ==="
apt-get install -y \
    git curl wget htop tmux vim \
    fail2ban ufw \
    python3 python3-pip python3-venv \
    build-essential

echo "=== 3. Node.js LTS (v22) ==="
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
    apt-get install -y nodejs
fi
echo "Node version: $(node --version)"
echo "npm version: $(npm --version)"

echo "=== 4. Create User 'noctiluca' ==="
if ! id "noctiluca" &>/dev/null; then
    useradd -m -s /bin/bash -G sudo noctiluca
    echo "noctiluca ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/noctiluca
    chmod 440 /etc/sudoers.d/noctiluca
    mkdir -p /home/noctiluca/.ssh
    chmod 700 /home/noctiluca/.ssh
    chown -R noctiluca:noctiluca /home/noctiluca/.ssh
    echo "Created user 'noctiluca' with sudo access"
else
    echo "User 'noctiluca' already exists"
fi

echo "=== 5. SSH Hardening ==="
sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#*PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config
systemctl restart sshd

echo "=== 6. Firewall (UFW) ==="
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw --force enable
ufw status

echo "=== 7. Fail2ban ==="
systemctl enable fail2ban
systemctl start fail2ban

echo "=== 8. Setup Complete ==="
echo "Host: $(hostname)"
echo "IP: $(curl -s ifconfig.me)"
echo "Uptime: $(uptime)"
echo ""
echo "⚠️  Root login disabled. Use 'noctiluca' user with SSH key."
echo "⚠️  Copy your SSH key: ssh-copy-id noctiluca@<host>"
"""

# Quick status check
CHECK_COMMANDS = """
echo "=== VPS Status ==="
echo "Hostname: $(hostname)"
echo "OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '"')"
echo "Uptime: $(uptime -p)"
echo "Memory: $(free -h | awk '/Mem:/ {print $3 "/" $2}')"
echo "Disk: $(df -h / | awk 'NR==2 {print $3 "/" $2 " (" $5 " used)"}')"
echo ""
echo "=== Services ==="
systemctl is-active --quiet fail2ban && echo "✅ fail2ban: running" || echo "❌ fail2ban: stopped"
systemctl is-active --quiet ufw && echo "✅ ufw: running" || echo "❌ ufw: stopped"
echo ""
echo "=== Node/Python ==="
node --version 2>/dev/null || echo "Node: not installed"
python3 --version 2>/dev/null || echo "Python: not installed"
echo ""
echo "=== Open Ports ==="
ss -tuln | grep LISTEN | awk '{print $5}' | sort -u
"""


def run_ssh(host: str, commands: str, user: str = "root", key: str = None):
    """Run commands over SSH."""
    ssh_args = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10"]
    
    if key:
        ssh_args.extend(["-i", key])
    
    ssh_args.append(f"{user}@{host}")
    ssh_args.append(commands)
    
    print(f"🔌 Connecting to {user}@{host}...")
    result = subprocess.run(ssh_args, capture_output=False)
    return result.returncode == 0


def setup_keys(host: str, user: str = "root", key: str = None):
    """Copy SSH public key to VPS."""
    ssh_copy_args = ["ssh-copy-id", "-o", "StrictHostKeyChecking=no"]
    
    if key:
        # Use the .pub version for ssh-copy-id
        pub_key = key if key.endswith(".pub") else f"{key}.pub"
        ssh_copy_args.extend(["-i", pub_key])
    
    ssh_copy_args.append(f"{user}@{host}")
    
    print(f"📤 Copying SSH key to {user}@{host}...")
    result = subprocess.run(ssh_copy_args, capture_output=False)
    
    if result.returncode == 0:
        print("✅ SSH key copied successfully!")
        print(f"   You can now SSH with: ssh {user}@{host}")
    else:
        print("❌ Failed to copy SSH key")
    
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Provision a VPS with essential tools")
    parser.add_argument("action", choices=["provision", "check", "setup-keys"], 
                       nargs="?", default="provision",
                       help="Action to perform")
    parser.add_argument("host", help="VPS hostname or IP address")
    parser.add_argument("--user", "-u", default="root", help="SSH user (default: root)")
    parser.add_argument("--key", "-i", help="Path to SSH private key")
    
    args = parser.parse_args()
    
    if args.action == "setup-keys":
        success = setup_keys(args.host, args.user, args.key)
        sys.exit(0 if success else 1)
    
    if args.action == "check":
        print("🔍 Checking VPS status...")
        success = run_ssh(args.host, CHECK_COMMANDS, args.user, args.key)
        sys.exit(0 if success else 1)
    
    # Default: provision
    print("🚀 Starting VPS provisioning...")
    print("   This will install packages, harden SSH, and configure firewall.")
    print("")
    
    success = run_ssh(args.host, PROVISION_COMMANDS, args.user, args.key)
    
    if success:
        print("")
        print("=" * 60)
        print("✅ VPS provisioned successfully!")
        print("")
        print("Next steps:")
        print("  1. Copy your SSH key to noctiluca user:")
        print(f"     ssh-copy-id noctiluca@{args.host}")
        print("")
        print("  2. Connect as noctiluca:")
        print(f"     ssh noctiluca@{args.host}")
        print("")
        print("  3. (Optional) Install OpenClaw:")
        print("     npm install -g openclaw")
        print("=" * 60)
    else:
        print("❌ Provisioning failed. Check SSH connection and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
