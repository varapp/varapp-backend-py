
from tests_functional.test_selenium import *

_is_setup = False

class TestBookmarks(SeleniumTest):
    def setUp(self):
        global _is_setup
        if not _is_setup:
            self.driver.get(self.URL)
            self.try_login(1)
            self.change_db('test')
            self.reset_filters()
            _is_setup = True

    # Helper methods

    def save_bookmark(self, name):
        button = self.select('button#save-bookmark-button')
        button.click()
        input_field = self.waitFor('.dropdown-menu input[type="text"]', 1)
        save = self.waitFor('.dropdown-menu button', 1)
        input_field.send_keys(name)
        save.click()

    def open_bookmarks_list(self):
        button = self.select('button#load-bookmark-button')
        button.click()
        try:
            menuitems = self.waitForAll('#bookmark-buttons ul.dropdown-menu a', 1)
        except TimeoutException:
            menuitems = []
        return menuitems

    def find_bookmark(self, name):
        menuitems = self.open_bookmarks_list()
        for item in menuitems:
            innertext = item.find_element_by_css_selector('.bookmark-desc').text
            if name in innertext:
                return item
        return None

    def delete_bookmark(self, name):
        menuitems = self.open_bookmarks_list()
        for item in menuitems:
            innertext = item.find_element_by_css_selector('.bookmark-desc').text
            delete_button = item.find_element_by_css_selector('.remove-bookmark-button')
            if name in innertext:
                self.js_click(delete_button)
                self.confirm()
                break

    # Actual tests

    def test_1_create_bookmark(self):
        """Create a bookmark for recessive variants, reset, then retrieve it"""
        # Create
        scenario = 'recessive'
        name = PREFIX+'-'+scenario+'+'+random_string(5)
        self.choose_genotypes_scenario(scenario)
        self.save_bookmark(name)

        # Go to bookmark
        self.reset_filters()
        self.assertEqual(self.get_current_scenario(), 'active')
        item = self.find_bookmark(name)
        if not item:
            self.fail("No bookmarks available")
        item.click()
        self.wait_for_ajax_end()  # load bookmark query from db
        #self.wait(lambda s: s.find_element_by_css_selector(
        #    '.genotypes-filter-input input[value="{}"]'.format(scenario)).get_attribute('checked'))
        self.assertEqual(self.get_current_scenario(), scenario)

        # Remove it
        self.delete_bookmark(name)
        self.wait_for_ajax_end()
        item = self.find_bookmark(name)
        self.assertIsNone(item)
