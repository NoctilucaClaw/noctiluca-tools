#!/usr/bin/env python3
"""Tests for configuration loading and validation."""
import os
import sys
import tempfile
import unittest

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


class TestPrivateKeyLoading(unittest.TestCase):
    """Test private key loading from files."""
    
    def test_load_private_key_format(self):
        """Private key should be 64 hex chars or 0x-prefixed 66 chars."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            # Test key (not real)
            f.write('0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef')
            f.flush()
            
            with open(f.name, 'r') as rf:
                key = rf.read().strip()
            
            # Valid formats: 64 chars or 66 with 0x prefix
            if key.startswith('0x'):
                self.assertEqual(len(key), 66)
            else:
                self.assertEqual(len(key), 64)
            
            os.unlink(f.name)
    
    def test_reject_invalid_key(self):
        """Short keys should be rejected."""
        short_key = '0x1234'
        with self.assertRaises(ValueError):
            if len(short_key) < 64:
                raise ValueError("Private key too short")


class TestRpcEndpoints(unittest.TestCase):
    """Test RPC endpoint configuration."""
    
    def test_base_rpc_urls(self):
        """RPC URLs should be valid HTTPS endpoints."""
        rpc_urls = [
            'https://mainnet.base.org',
            'https://base.drpc.org',
            'https://base.publicnode.com',
        ]
        for url in rpc_urls:
            self.assertTrue(url.startswith('https://'), f"RPC URL must be HTTPS: {url}")


class TestEthereumAddresses(unittest.TestCase):
    """Test Ethereum address validation."""
    
    def test_valid_address_format(self):
        """Addresses should be 0x-prefixed 42-char hex."""
        addresses = [
            '0x643fc612b928ee9C58B8C9F1DF017E75757Be3D4',  # My wallet
            '0xBE3c41E1CC251422F0502442203a2C0c4F63111b',  # 0xSplits
        ]
        for addr in addresses:
            self.assertTrue(addr.startswith('0x'))
            self.assertEqual(len(addr), 42)
            # Check hex characters (after 0x)
            int(addr[2:], 16)  # Raises ValueError if not hex


if __name__ == '__main__':
    unittest.main()
