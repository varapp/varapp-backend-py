"""
Test the view of the alignemnts in IGV.js.
"""
from tests_functional.test_selenium import *
from selenium.webdriver import ActionChains
import urllib.request, ssl


_is_setup = False

class TestFilters(SeleniumTest):
    def setUp(self):
        global _is_setup
        if not _is_setup:
            self.main_page()
            self.try_login()
            self.change_db('test')
            _is_setup = True

    def test_0_bamserver_is_up(self):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        ssl_context.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request('https://varapp-dev.vital-it.ch/bamserver', method='HEAD')
        response = urllib.request.urlopen(req, context=ssl_context)
        self.assertEqual(response.code, 200)

    def test_1_view_alignment(self):
        actions = ActionChains(self.driver)
        rows = self.waitForAll('.public_fixedDataTable_bodyRow .public_fixedDataTableCell_cellContent')
        actions.double_click(rows[0]).perform()
        self.waitFor('.igv-modal', 3)
