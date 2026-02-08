#!/usr/bin/env python3
"""Test runner for noctiluca-tools."""
import unittest
import sys
import os

# Ensure tests directory is in path
sys.path.insert(0, os.path.dirname(__file__))

def run_tests():
    """Discover and run all tests."""
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"\n📊 {passed} passed, {len(result.failures)} failed, {len(result.errors)} errors")
    
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests())
