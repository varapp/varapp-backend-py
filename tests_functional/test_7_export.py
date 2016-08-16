"""
Test exporting variants in different formats.
"""

from tests_functional.test_selenium import *

_is_setup = False

@unittest.skip('How to get rid of the created files?')
class TestExports(SeleniumTest):
    def setUp(self):
        global _is_setup
        if not _is_setup:
            self.driver.get(self.URL)
            self.try_login()
            _is_setup = True

    # Helper methods

    # Actual tests

    def test_export_annovar(self):
        """Export the selection in Annovar format"""

    def test_export_vcf(self):
        """Export the selection in VCF format"""

    def test_export_txt(self):
        """Export the selection in tabular format"""
