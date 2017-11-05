# -*- coding: utf-8 -*-

from context import monitoring
# import context.website_monitoring

import unittest

# DRAFT

class NoDataWebsiteTest(unittest.TestCase):
    """No data test case."""

    def setUp(self):
        self.website_handler = monitoring.WebsiteHandler('EmptyTest', 'http://test.com', 5, None)

    def test_get_grid_from_empty_website_true(self):
        self.assertEqual(self.website_handler.get_info_for_grid(True), ['EmptyTest', 5] + 8 * [None])

    def test_get_grid_from_empty_website_false(self):
        self.assertEqual(self.website_handler.get_info_for_grid(False), ['EmptyTest', 5] + 8 * [None])

    def test_nan_values_availability(self):
        self.assertEqual(self.website_handler.availability_to_string(float('nan')), 'No data')

    def test_nan_values_elapsed(self):
        self.assertEqual(self.website_handler.elapsed_to_string(float('nan')), 'No data')

    def test_has_no_data(self):
        self.assertEqual(self.website_handler.has_no_data(), True)

if __name__ == '__main__':
    unittest.main()
