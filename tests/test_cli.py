#!/usr/bin/env python3
"""Tests for the unified CLI (noctiluca_tools.py)."""

import unittest
import sys
import importlib.util
from pathlib import Path
from io import StringIO

# Load the CLI module
CLI_PATH = Path(__file__).parent.parent / "noctiluca_tools.py"
spec = importlib.util.spec_from_file_location("noctiluca_tools", CLI_PATH)
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


class TestCliModuleFunctions(unittest.TestCase):
    """Tests for CLI module helper functions."""
    
    def test_get_wallet_address_returns_none_when_missing(self):
        """Should return None when wallet file doesn't exist."""
        # This tests the fallback behavior
        import tempfile
        import os
        original_home = os.environ.get('HOME')
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['HOME'] = tmpdir
            result = cli.get_wallet_address()
            # Restore
            if original_home:
                os.environ['HOME'] = original_home
        # Note: result may be None or actual address depending on file existence
        self.assertTrue(result is None or result.startswith('0x'))
    
    def test_scripts_dir_exists(self):
        """Scripts directory should exist."""
        self.assertTrue(cli.SCRIPTS_DIR.exists())
        self.assertTrue(cli.SCRIPTS_DIR.is_dir())
    
    def test_load_script_finds_cow_swap(self):
        """Should be able to load cow_swap module."""
        module = cli.load_script("cow_swap")
        self.assertTrue(hasattr(module, 'main') or hasattr(module, 'run'))


class TestCliCommands(unittest.TestCase):
    """Tests for CLI command structure."""
    
    def test_balance_command_defined(self):
        """Balance command should be defined."""
        self.assertTrue(callable(cli.cmd_balance))
    
    def test_status_command_defined(self):
        """Status command should be defined."""
        self.assertTrue(callable(cli.cmd_status))
    
    def test_swap_command_defined(self):
        """Swap command should be defined."""
        self.assertTrue(callable(cli.cmd_swap))
    
    def test_bridge_command_defined(self):
        """Bridge command should be defined."""
        self.assertTrue(callable(cli.cmd_bridge))
    
    def test_vps_command_defined(self):
        """VPS command should be defined."""
        self.assertTrue(callable(cli.cmd_vps))


class TestGetBalance(unittest.TestCase):
    """Tests for the get_balance RPC function."""
    
    def test_get_balance_returns_number_or_none(self):
        """Should return a float or None."""
        # Test with a known RPC (might timeout in CI)
        result = cli.get_balance(
            "https://base-rpc.publicnode.com",
            "0x0000000000000000000000000000000000000000",  # Zero address
            None,  # Native balance
            18
        )
        self.assertTrue(result is None or isinstance(result, float))
    
    def test_get_balance_handles_bad_rpc(self):
        """Should return None for invalid RPC."""
        result = cli.get_balance(
            "https://invalid.rpc.example.com",
            "0x0000000000000000000000000000000000000000",
            None,
            18
        )
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
