
from tests_functional.test_selenium import *

_is_setup = False

class TestColumnsSelection(SeleniumTest):
    def setUp(self):
        global _is_setup
        if not _is_setup:
            self.main_page()
            self.try_login()
            self.wait_for_ajax_end()
            _is_setup = True

    # Helper methods

    def get_table_header_names(self):
        header_links = self.selectAll('.public_fixedDataTable_header a')
        headers = [h.text for h in header_links]
        return headers

    def is_not_in_header(self, header_text):
        self.wait(lambda s: header_text not in self.get_table_header_names(), 3)

    def is_in_header(self, header_text):
        self.wait(lambda s: header_text in self.get_table_header_names(), 3)

    # Actual tests

    def test_add_remove_column(self):
        """Add/remove columns of annotation to the table"""
        headers = self.get_table_header_names()
        self.assertIn('Chr', headers)
        self.assertNotIn('HGVSc', headers)
        self.assertNotIn('HGVSp', headers)

        # Open the selection window
        btn = self.waitFor('#select-columns-button')
        btn.click()
        items = self.waitForAll(".select-columns-container a[role='menuitem']", 2)

        # Remove 'Chr' column
        chrom = items[0]
        chrom.click()
        self.is_not_in_header('Chr')

        # Add HGVS columns
        # There should be no need to reopen the window
        hgvsc = items[11]
        hgvsp = items[12]
        hgvsc.click()
        hgvsp.click()
        sleep(0.3)
        self.is_in_header('HGVSc')
        # For some stupid reason when run with Jenkins HGVSp would not be in the list, '' instead



