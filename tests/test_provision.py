"""Tests for provision_vps.py"""
import sys
import unittest
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import provision_vps


class TestProvisionVPS(unittest.TestCase):
    """Tests for VPS provisioning script."""
    
    def test_provision_commands_defined(self):
        """Verify provision commands string exists and has content."""
        self.assertIn("apt-get update", provision_vps.PROVISION_COMMANDS)
        self.assertIn("fail2ban", provision_vps.PROVISION_COMMANDS)
        self.assertIn("ufw", provision_vps.PROVISION_COMMANDS)
        self.assertIn("nodejs", provision_vps.PROVISION_COMMANDS)
    
    def test_check_commands_defined(self):
        """Verify check commands string exists."""
        self.assertIn("hostname", provision_vps.CHECK_COMMANDS)
        self.assertIn("Uptime", provision_vps.CHECK_COMMANDS)
        self.assertIn("fail2ban", provision_vps.CHECK_COMMANDS)
    
    def test_creates_noctiluca_user(self):
        """Verify provision creates 'noctiluca' user."""
        self.assertIn("useradd -m -s /bin/bash -G sudo noctiluca", 
                     provision_vps.PROVISION_COMMANDS)
    
    def test_ssh_hardening(self):
        """Verify SSH hardening is configured."""
        self.assertIn("PermitRootLogin no", provision_vps.PROVISION_COMMANDS)
        self.assertIn("PasswordAuthentication no", provision_vps.PROVISION_COMMANDS)
    
    def test_firewall_configured(self):
        """Verify UFW firewall is set up."""
        self.assertIn("ufw default deny incoming", provision_vps.PROVISION_COMMANDS)
        self.assertIn("ufw allow ssh", provision_vps.PROVISION_COMMANDS)


if __name__ == "__main__":
    unittest.main()
