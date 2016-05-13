
from tests_functional.test_selenium import *


_is_setup = False

class TestUserAccountPanel(SeleniumTest):
    def setUp(self):
        global _is_setup
        if not _is_setup:
            self.driver.get(self.URL+'/#/userAccount')
            self.assertEqual(self.driver.current_url, self.URL+'/#/login')
            self.try_login()
            link = self.waitFor('#user-account-link')
            link.click()
            self.assertEqual(self.driver.current_url, self.URL+'/#/userAccount')
            sleep(0.5)
            _is_setup = True
        self.driver.get(self.URL+'/#/userAccount')

    # Helper methods

    def change_value(self, field, text):
        """Change the value inside the input element *field* to *text*."""
        field.clear()
        field.send_keys(text)
        reset_button = self.select('.save-button')
        reset_button.click()
        self.toastr_success()
        self.wait_for_ajax_end()

    # Actual tests

    @unittest.skip('')
    def test_editable_field(self):
        """Change user first name"""
        # All editable fields but the password use the same component, so testing one is enough
        # It does not matter to login if we modify his first name and the test fails
        field = self.select('input#firstname')
        firstname = str(field.get_attribute('value'))

        # Change the value, then reset
        newname = PREFIX + random_string(5)
        field.clear()
        field.send_keys(newname)
        reset_button = self.select('.reset-button')
        reset_button.click()
        sleep(0.1)
        self.assertEqual(field.get_attribute('value'), firstname)

        # Change the value again, but save it
        newname = PREFIX + random_string(5)
        self.change_value(field, newname)
        self.driver.refresh()
        sleep(0.5)
        field = self.waitFor('input#firstname')
        self.assertEqual(field.get_attribute('value'), newname)

        # Restablish
        self.change_value(field, firstname)
        self.driver.refresh()
        sleep(0.5)
        field = self.waitFor('input#firstname')
        self.assertEqual(field.get_attribute('value'), firstname)

    def test_change_password(self):
        """Change the current user's password using the Change password field"""
        # If necessary to restablish user test:test manually, the password 'test'
        # hashed with salt 'abcdefghijklmnopqrs' gives 'abgOeLfPimXQo'.
        field = self.waitFor('input#password')

        # Sending a too short password should warn
        field.send_keys(random_string(3))        # too short
        self.assertExists('input#password2', 1)  # confirmation shows up
        self.assertNotExists('.save-button', 1)  # can't save yet
        warnings = self.waitForAll('.form-group.has-warning', 1)
        self.assertGreaterEqual(len(warnings), 2)  # password and confirm fields should warn (length + confirm)

        # Send a good password
        field.send_keys(Keys.BACKSPACE * 3)  # just '.clear()' will not do it, it listens to keyPress
        self.assertNotExists('input#password2', 1)
        new_pwd = PREFIX + random_string(5)
        field.send_keys(new_pwd)
        field2 = self.waitFor('input#password2', 1)
        field2.send_keys(new_pwd)  # confirm
        self.assertExists('.save-button', 1)  # ok to save now
        self.assertExists('.reset-button', 1)  # ok to save now
        self.select('.save-button').click()
        self.toastr_success()

        # Restablish to 'test'
        field.clear()
        field.send_keys('test')
        field2 = self.waitFor('input#password2', 1)
        field2.send_keys('test')
        self.waitFor('.save-button').click()
        self.toastr_success()

