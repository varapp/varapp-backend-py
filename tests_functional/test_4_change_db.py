
from tests_functional.test_selenium import *


_is_setup = False

class TestSamplesSelection(SeleniumTest):
    def setUp(self):
        global _is_setup
        if not _is_setup:
            self.driver.get(self.URL)
            self.try_login(1)
            self.wait_for_ajax_end()
            self.reset_filters()
            self.wait_for_ajax_end()
            _is_setup = True

    # Helper methods

    # Actual tests

    def test_change_db(self):
        """Change database"""
        # Requires user 'test' to have access to dbs 'bil' and 'test'.
        self.change_db('test')
        n_total = int(self.waitFor('#n-total').text)
        self.assertEqual(n_total, N_TEST)
        n_filtered = int(self.waitFor('#n-filtered').text)
        self.assertEqual(n_filtered, N_TEST_ACTIVE)
        label = self.get_dbname()
        self.assertIn('test', label)

        self.change_db('bil')
        n_total = int(self.waitFor('#n-total').text)
        self.assertEqual(n_total, N_BIL)
        n_filtered = int(self.waitFor('#n-filtered').text)
        self.assertEqual(n_filtered, N_BIL_ACTIVE)
        label = self.get_dbname()
        self.assertIn('bil', label)

    def test_change_db_samples(self):
        """Change database while in /samples tab"""
        self.driver.get(self.URL+'/#/samples')
        self.change_db('test')
        n_filtered = int(self.waitFor('.variants-summary #n-variants-summary', 5).text)
        self.assertEqual(n_filtered, N_TEST_ACTIVE)

        self.change_db('bil')
        n_filtered = int(self.waitFor('.variants-summary #n-variants-summary', 5).text)
        self.assertEqual(n_filtered, N_BIL_ACTIVE)


