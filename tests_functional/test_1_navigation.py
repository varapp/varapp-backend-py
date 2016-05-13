
from tests_functional.test_selenium import *


class TestNavigation(SeleniumTest):

    def test_navigation(self):
        """Go through the different pages and links"""
        self.driver.get(self.URL)
        self.try_login()

        # Go to samples selection
        samples_summary = self.waitFor('#samples-summary', 5)
        samples_summary.click()
        self.assertEqual(self.driver.current_url, self.URL+'/#/samples')
        self.assertExists('#samples-selection', 5)

        # Return to variants
        variants_summary = self.waitFor('#variants-summary', 5)
        variants_summary.click()
        self.assertExists('#variants', 5)

        # Go to UserAccount panel
        user_account = self.waitFor('#user-account-link', 5)
        user_account.click()
        self.assertExists('#user-account-panel', 5)

        # Go back using the 'Back button'
        back_button = self.select('.back-button')
        back_button.click()
        self.assertExists('#variants', 5)

        ## Need to be admin
        ## Go to Admin panel
        #user_account = self.waitFor('admin-link', 5)
        #user_account.click()
        #self.assertExists('#admin-panel', 5)

        ## Go back using the 'Back button'
        #back_button = self.driver.find_element_by_class_name('back-button')
        #back_button.click()
        #self.assertExists('#variants', 5)

        # Try the link in the page title
        link_to_varapp = self.select('.link-to-varapp')
        link_to_varapp.click()
        self.assertExists('#variants', 5)

    def test_docs_are_available(self):
        """Docs should be available - even without logging in"""
        self.driver.get('http://varapp-demo.vital-it.ch/docs')
        self.assertIn("Varapp", self.driver.title)
        self.assertIn("documentation", self.driver.title)

