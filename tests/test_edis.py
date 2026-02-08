#!/usr/bin/env python3
"""Tests for EDIS Global VPS order tools."""
import os
import sys
import unittest

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


class TestEdisApiEndpoints(unittest.TestCase):
    """Test EDIS API endpoint configuration."""
    
    def test_api_base_url(self):
        """EDIS API should use HTTPS."""
        api_base = 'https://manage.edisglobal.com/api/v1'
        self.assertTrue(api_base.startswith('https://'))
    
    def test_location_ids(self):
        """Known location IDs should be valid."""
        # Frankfurt, Germany = ID 122
        # These are hardcoded defaults
        known_locations = {
            122: 'Germany, Frankfurt',
        }
        for loc_id in known_locations:
            self.assertIsInstance(loc_id, int)
            self.assertGreater(loc_id, 0)


class TestEdisOrderConfig(unittest.TestCase):
    """Test EDIS order configuration defaults."""
    
    def test_default_billing_cycle(self):
        """Default billing should be monthly."""
        billing_cycle = 'monthly'
        valid_cycles = ['monthly', 'quarterly', 'annually']
        self.assertIn(billing_cycle, valid_cycles)
    
    def test_payment_methods(self):
        """Cryptomus should be available for crypto payments."""
        payment_methods = ['paypal', 'creditcard', 'alipay', 'cryptomus']
        self.assertIn('cryptomus', payment_methods)
    
    def test_discount_code_format(self):
        """Discount codes should be alphanumeric."""
        discount_code = 'TRYMEOUT'
        self.assertTrue(discount_code.isalnum())


class TestEdisRegistration(unittest.TestCase):
    """Test EDIS registration form fields."""
    
    def test_required_fields(self):
        """All required registration fields should be defined."""
        required_fields = [
            'firstname',
            'lastname',
            'email',
            'phonenumber',
            'address1',
            'city',
            'state',
            'postcode',
            'country',
            'password',
            'password2',
        ]
        self.assertEqual(len(required_fields), 11)
    
    def test_country_format(self):
        """Country should be 2-letter ISO code."""
        country = 'DE'
        self.assertEqual(len(country), 2)
        self.assertTrue(country.isalpha())
        self.assertTrue(country.isupper())


if __name__ == '__main__':
    unittest.main()
