"""
Functional e2e tests using Selenium WebDrivers.
Be careful to have the test runner using only 1 process,
otherwise the tests will have concurrent actions.
"""

import unittest
import pytest
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from time import sleep

PREFIX = '_functest_'

N_TEST = 308
N_TEST_ACTIVE = 185
N_BIL = 266
N_BIL_ACTIVE = 34

def random_string(N=20):
    import random, string
    return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(N))


@pytest.mark.usefixtures("url")     # can access self.URL from inside a test class
class SeleniumTest(unittest.TestCase):
    """TestCase subclass with common methods and webdriver config"""

    @classmethod
    def setUpClass(cls):
        cls.display = Display(visible=0, size=(1600, 1200))
        cls.display.start()
        cls.driver = webdriver.Firefox()
        #cls.driver = webdriver.Chrome()   # requires chromedriver in path and pip installed
        #cls.driver = webdriver.PhantomJS()

    @classmethod
    def tearDownClass(cls):
        cls.driver.close()
        cls.driver.quit()
        cls.display.stop()

    # Helper methods

    def remove_footer(self):
        self.driver.execute_script("$('#footer').remove();")

    def main_page(self):
        self.driver.get(self.URL)
        self.remove_footer()

    def open_devtools(self):
        self.driver.find_element_by_tag_name('body').send_keys(Keys.LEFT_ALT + Keys.COMMAND + 'i')

    def select(self, selector):
        return self.driver.find_element_by_css_selector(selector)

    def selectAll(self, selector):
        return self.driver.find_elements_by_css_selector(selector)

    def wait(self, for_what, until=10):
        return WebDriverWait(self.driver, until).until(for_what)

    def waitFor(self, selector, until=10):
        """Wait until this element is found in the DOM within *until* seconds. Return the element."""
        return self.wait(EC.presence_of_element_located((By.CSS_SELECTOR, selector)), until=until)

    def waitForAll(self, selector, until=10):
        """Wait until this element is found in the DOM within *until* seconds. Return the list of elements."""
        return self.wait(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)), until=until)

    def exists(self, selector, until=0):
        """Return a boolean: does this element exist (visible within *until* seconds)"""
        if until > 0:
            try:
                self.waitFor(selector, until)
                return True
            except TimeoutException:
                return False
        else:
            try:
                if EC.presence_of_element_located((By.CSS_SELECTOR, selector))(self.driver):
                    return True
            except NoSuchElementException:
                return False

    def disappeared(self, selector, until=0):
        """Return a boolean: did this element disappear (invisible before *until* seconds)"""
        cond = EC.invisibility_of_element_located((By.CSS_SELECTOR, selector))
        if until > 0:
            try:
                self.wait(cond, until)
                return True
            except TimeoutException:
                return False
        else:
            return cond(self.driver)

    def assertExists(self, selector, until=0):
        """Assert that the given element exists within *until* seconds"""
        if self.exists(selector, until):
            return True
        else:
            self.fail("No such element: '{}'".format(selector))

    def assertNotExists(self, selector, until=0):
        """Assert that the given element disappeared before *until* seconds"""
        if self.disappeared(selector, until):
            return True
        else:
            self.fail("Element '{}' is still visible".format(selector))

    def wait_for_ajax_end(self):
        """Wait for all connections to a server to close.
           Thanks to https://blog.mozilla.org/webqa/2012/07/12/how-to-webdriverwait/ """
        self.wait(lambda s: s.execute_script("return jQuery.active == 0"))
        sleep(0.5)  # doesn't hurt

    def remove_style(self, elt):
        """In case it prevents an element from being clickable"""
        self.driver.execute_script("arguments[0].setAttribute('style', '')", elt)

    def highlight(self, elt):
        """To help debugging, add a visible border to the element"""
        self.driver.execute_script("arguments[0].setAttribute(arguments[1], arguments[2])",
            elt, "style", "border: 2px solid red; color: red; font-weight: bold;")
        sleep(1)

    def robust_click(self, elt):
        """Click on the element, for the click() method is bugged half of the time"""
        self.driver.execute_script("arguments[0].scrollIntoView(true);", elt)
        action = ActionChains(self.driver)
        action.move_to_element(elt).click().perform()

    def js_click(self, elt):
        """Click on an element using javascript, because the selenium method sucks."""
        self.driver.execute_script("arguments[0].click();", elt)

    # Login-logout

    def try_login(self, until=1):
        """Fill in the login form and submit. If the login panel is
            not found, chack that we are already logged in."""
        if self.exists('#login', until):
            self.wait(EC.presence_of_element_located((By.NAME, 'username')), 2)
            username_input = self.driver.find_element_by_name('username')
            password_input = self.driver.find_element_by_name('password')
            submit_button = self.driver.find_element_by_class_name('submit-button')
            username_input.clear()
            password_input.clear()
            username_input.send_keys('test')
            password_input.send_keys('test')
            submit_button.click()
            return 1
        else:
            return 0

    def try_logout(self):
        """Follow the logout link from the header"""
        if self.exists('#header-logout-link', 3):
            logout_link = self.driver.find_element_by_id('header-logout-link')
            logout_link.click()
            return 1
        else:
            return 0

    # Common actions

    def confirm(self):
        """Wait for the Confirm modal to pop up, then click the Ok button"""
        ok = self.waitFor('.confirm-ok-button')
        ok.click()

    def wait_for_stats_and_vars(self):
        self.wait_for_ajax_end()  # global stats
        sleep(0.1)
        self.wait_for_ajax_end()  # variants

    def reset_filters(self):
        """Click the Reset filters button"""
        reset = self.waitFor('#reset-button')
        reset.click()
        self.wait_for_ajax_end()

    def get_dbname(self):
        """Return the name of the current database"""
        dbname = self.waitFor('#select-database span:first-child').text
        return dbname

    def get_current_scenario(self):
        """Return the name of the selected genotypes scenario"""
        #option = self.select('.genotypes-filter-input input[type="radio"]:checked')
        option = self.select('.genotypes-filter-input input.checked')
        return option.get_attribute('value')

    def change_db(self, dbname, check=False):
        """Use the dropdown menu to select a database.
           If *check* is True, return immediately if *dbname* is already the current db."""
        if check and dbname == self.get_dbname():
            return
        select = self.waitFor('button#select-database')
        select.click()
        items = self.waitForAll('.dropdown-menu li a')
        item = None
        for i,item in enumerate(items):
            if item.text == dbname:
                break
        item.click()
        self.wait_for_stats_and_vars()

    def choose_genotypes_scenario(self, scenario):
        option = self.waitFor('div.genotypes-filter-input input[value="{}"]'.format(scenario))
        option.click()
        self.wait_for_ajax_end()

    def toastr_success(self):
        """Detect the presence of a success toastr popup"""
        self.assertExists('.toast-success', 1)

    def toastr_error(self):
        """Detect the presence of an error toastr popup"""
        self.assertExists('.toast-error', 1)
