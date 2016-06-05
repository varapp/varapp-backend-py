
from tests_functional.test_selenium import *
import re


class TestLogin(SeleniumTest):
    def setUp(self):
        self.driver.get(self.URL+'/#/login')
        self.new_username = PREFIX + random_string(10)
        self.new_email = random_string(10)+'@test.com'

    def tearDown(self):
        self.try_logout()

    def test_1_enter(self):
        """I see a header, a login form and a footer when I enter the website"""
        self.assertIn('Varapp', self.driver.title)
        self.assertExists('#header')
        self.assertExists('#footer')
        self.assertExists('#app-container')
        self.assertExists('#app')
        self.assertExists('#login')

    def test_2_login(self):
        """Simulate a user logging in with 'test/test' """
        self.assertExists('#login')
        self.try_login()
        self.assertExists('#variants', 5)
        self.assertExists('#samples-summary', 5)
        self.assertExists('#filters', 5)
        self.assertExists('#lookup-panel', 5)
        self.driver.get(self.URL+'/#/login')

    def test_3_register_new_user(self):
        """Simulate a new user signing up"""
        self.assertExists('#signup-link', 10)
        signup_link = self.driver.find_element_by_id('signup-link')
        signup_link.click()
        self.assertExists('#signup-form', 2)
        self.assertEqual(self.driver.current_url, self.URL+"/#/signup")
        username_input = self.driver.find_element_by_name('username')
        firstname_input = self.driver.find_element_by_name('firstname')
        lastname_input = self.driver.find_element_by_name('lastname')
        email_input = self.driver.find_element_by_name('email')
        phone_input = self.driver.find_element_by_name('phone')
        password_input = self.driver.find_element_by_name('password')
        confirm_input = self.driver.find_element_by_name('password2')
        submit_button = self.driver.find_element_by_class_name('submit-button')
        username_input.send_keys(self.new_username)
        firstname_input.send_keys(PREFIX + 'new_firstname')
        lastname_input.send_keys(PREFIX + 'new_lastname')
        email_input.send_keys(self.new_email)
        phone_input.send_keys('000000')
        password_input.send_keys(PREFIX + 'new_password')
        confirm_input.send_keys(PREFIX + 'new_password')
        self.wait(EC.element_to_be_clickable((By.CLASS_NAME, 'submit-button')), 1)
        submit_button.click()
        #self.js_click(submit_button)
        self.assertExists('#account-will-be-created-panel', 2)
        self.assertIn(self.driver.current_url.split('?')[0], self.URL+"/#/accountWillBeCreated")
        self.assertIn('?email={}'.format(self.new_email.replace('@','%40')), self.driver.current_url)  # email is passed as param
        panel_title = self.driver.find_element_by_class_name('panel-title')
        self.assertEqual(panel_title.text, 'New account pending validation')
        self.driver.get(self.URL+'/#/login')

    def test_4_ask_for_password_reset(self):
        """Simulate a user asking for a password reset"""
        # (It just sends a confirmation email, the password remains untouched)
        self.assertExists('#forget-password-link', 5)
        reset_link = self.driver.find_element_by_id('forget-password-link')
        reset_link.click()
        self.assertExists('#forget-password-form', 2)
        self.assertEqual(self.driver.current_url, self.URL+"/#/forgetPassword")
        username_input = self.driver.find_element_by_name('username')
        email_input = self.driver.find_element_by_name('email')
        submit_button = self.driver.find_element_by_class_name('submit-button')
        username_input.send_keys('test')
        email_input.send_keys('test@test.com')
        submit_button.click()
        self.assertExists('#password-change-request-panel', 2)
        self.assertEqual(self.driver.current_url.split('?')[0], self.URL+"/#/passwordChangeRequested")
        self.assertIn('?email=test%40test.com', self.driver.current_url)  # email is passed as param
        panel_title = self.driver.find_element_by_class_name('panel-title')
        self.assertEqual(panel_title.text, 'Password change request sent')
        self.driver.get(self.URL+'/#/login')
