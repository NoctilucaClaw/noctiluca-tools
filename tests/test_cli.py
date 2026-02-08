"""Tests for the unified CLI."""
import subprocess
import sys
import unittest
from pathlib import Path


class TestCLI(unittest.TestCase):
    """Test the noctiluca_tools.py unified CLI."""
    
    @property
    def cli_path(self):
        return Path(__file__).parent.parent / "noctiluca_tools.py"
    
    def run_cli(self, *args):
        """Run CLI with arguments and return (stdout, stderr, returncode)."""
        result = subprocess.run(
            [sys.executable, str(self.cli_path)] + list(args),
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout, result.stderr, result.returncode
    
    def test_help(self):
        """Test --help flag."""
        stdout, stderr, code = self.run_cli("--help")
        self.assertEqual(code, 0)
        self.assertIn("Noctiluca Tools", stdout)
        self.assertIn("balance", stdout)
        self.assertIn("swap", stdout)
        self.assertIn("bridge", stdout)
        self.assertIn("vps", stdout)
    
    def test_no_args_shows_help(self):
        """Test that no arguments shows help."""
        stdout, stderr, code = self.run_cli()
        self.assertEqual(code, 0)
        self.assertIn("Noctiluca Tools", stdout)
    
    def test_swap_help(self):
        """Test swap subcommand help."""
        stdout, stderr, code = self.run_cli("swap", "--help")
        self.assertEqual(code, 0)
        self.assertIn("quote", stdout)
        self.assertIn("approve", stdout)
        self.assertIn("execute", stdout)
    
    def test_bridge_help(self):
        """Test bridge subcommand help."""
        stdout, stderr, code = self.run_cli("bridge", "--help")
        self.assertEqual(code, 0)
        self.assertIn("quote", stdout)
        self.assertIn("execute", stdout)
    
    def test_vps_help(self):
        """Test vps subcommand help."""
        stdout, stderr, code = self.run_cli("vps", "--help")
        self.assertEqual(code, 0)
        self.assertIn("register", stdout)
        self.assertIn("locations", stdout)
        self.assertIn("products", stdout)
        self.assertIn("order", stdout)


if __name__ == "__main__":
    unittest.main()
