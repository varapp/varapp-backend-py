
from tests_functional.test_selenium import *



_is_setup = False

class TestSamplesSelection(SeleniumTest):
    def setUp(self):
        global _is_setup
        if not _is_setup:
            self.main_page()
            self.try_login(1)
            self.reset_filters()
            self.change_db('test')
            self.driver.get(self.URL+'/#/samples')
            _is_setup = True
        self.reset_samples()
        self.waitFor('#samples-table')
        self.stats0 = self.fetch_stats()

    # Helper methods

    def fetch_stats(self):
        """Get #variants, #samples selected, #affected, #not affected reading inside stat badges."""
        n_filtered = self.waitFor('#n-variants-summary', 3).text
        self.waitFor('.samples-summary')
        s_total = self.waitFor('#n-samples', 1).text
        s_affected = self.waitFor('#n-affected', 1).text
        s_not_affected = self.waitFor('#n-not-affected', 1).text
        sleep(0.6)
        nrows = len(self.selectAll('.fixedDataTableRowLayout_rowWrapper')) - 1
        stats = {'nrows': nrows, 'n_total': int(n_filtered), 's_total': int(s_total),
                 'affected': int(s_affected), 'not_affected': int(s_not_affected)}
        return stats

    def reset_samples(self):
        """Click the Restore samples button, and confirm"""
        self.select('#restore-samples-button').click()
        self.confirm()
        self.wait_for_ajax_end()
        # Reset the filter buttons
        not_affected_filter = self.select('#filter-not-affected-btn')
        affected_filter = self.select('#filter-affected-btn')
        bar = self.select('#samples-search-bar')
        bar.send_keys(Keys.DELETE)
        if 'active' in not_affected_filter.get_attribute('class'):
            not_affected_filter.click()
        if 'active' in affected_filter.get_attribute('class'):
            affected_filter.click()

    # Actual tests

    def test_0_select_all_samples(self):
        """Test the select all samples button"""
        check_all = self.select('#check-all-samples-btn')
        check_all.click()
        self.wait_for_ajax_end()
        unchecked = self.selectAll('.add-family-button.checkbox-unchecked')
        checked = self.selectAll('.add-family-button.checkbox-checked')
        self.assertEqual(len(checked), 0)  # all unchecked
        self.assertNotEqual(len(unchecked), 0)
        total = len(unchecked)  # total n of samples
        check_all.click()
        self.wait_for_ajax_end()
        unchecked = self.selectAll('.add-family-button.checkbox-unchecked')
        checked = self.selectAll('.add-family-button.checkbox-checked')
        self.assertEqual(len(unchecked), 0)
        self.assertEqual(len(checked), total)

    def test_1_select_family(self):
        """Test the add/remove family buttons"""
        # Click on one of the unchecked add family buttons
        unchecked_family_buttons = self.waitForAll('button.add-family-button.checkbox-unchecked')
        first_unchecked = unchecked_family_buttons[0]
        #self.wait(lambda s:first_unchecked.is_displayed())
        self.robust_click(first_unchecked)
        #first_unchecked.click()
        self.wait_for_ajax_end()
        stats1 = self.fetch_stats()
        self.assertGreater(stats1['n_total'], self.stats0['n_total'])

        # Click on one of the already checked add family buttons
        checked_family_buttons = self.waitForAll('button.add-family-button.checkbox-checked')
        first_checked = checked_family_buttons[0]
        first_checked.click()
        self.wait_for_ajax_end()
        stats2 = self.fetch_stats()
        self.assertLess(stats2['n_total'], stats1['n_total'])

    def test_2_select_sample(self):
        """Test the add/remove sample buttons"""
        # Click on one of the unchecked add sample buttons
        unchecked_sample_buttons = self.waitForAll('button.add-sample-button.checkbox-unchecked')
        first_unchecked = unchecked_sample_buttons[0]
        #self.wait(lambda s:first_unchecked.is_displayed())
        self.robust_click(first_unchecked)
        #first_unchecked.click()
        self.wait_for_ajax_end()
        stats1 = self.fetch_stats()
        self.assertEqual(stats1['s_total'], self.stats0['s_total'] + 1)

        # Click on one of the already checked add sample buttons
        checked_sample_buttons = self.waitForAll('button.add-sample-button.checkbox-checked')
        first_checked = checked_sample_buttons[0]
        first_checked.click()
        self.wait_for_ajax_end()
        stats2 = self.fetch_stats()
        self.assertEqual(stats2['s_total'], stats1['s_total'] - 1)

    def test_3_switch_affected(self):
        """Test the buttons to switch the phenotype"""
        # Switch affected to not affected
        switches = self.selectAll('.affected-switch-button')
        switches[0].click()
        stats1 = self.fetch_stats()
        self.assertEqual(stats1['not_affected'], self.stats0['not_affected'] + 1)
        self.assertEqual(stats1['affected'], self.stats0['not_affected'] - 1)

        # Switch not affected to affected
        switches = self.selectAll('.affected-switch-button')
        switches[5].click()
        stats2 = self.fetch_stats()
        self.assertEqual(stats2['not_affected'], stats1['not_affected'] - 1)
        self.assertEqual(stats2['affected'], stats1['affected'] + 1)

    def test_4_filter_affected(self):
        """Test the buttons to filter by phenotype"""
        # Filter not affected
        not_affected_filter = self.select('#filter-not-affected-btn')
        not_affected_filter.click()
        sleep(0.3)
        affected_switches = self.selectAll('.affected-switch-button .sample_group_affected')
        self.assertEqual(len(affected_switches), 0)

        # Filter affected
        not_affected_filter = self.select('#filter-affected-btn')
        not_affected_filter.click()
        sleep(0.3)
        not_affected_switches = self.selectAll('.affected-switch-button .sample_group_not_affected')
        self.assertEqual(len(not_affected_switches), 0)

    def test_5_search_bar(self):
        """Test the search bar to filter samples by name"""
        bar = self.select('#samples-search-bar')
        bar.send_keys(Keys.DELETE)
        bar.send_keys('09')
        stats = self.fetch_stats()
        self.assertEqual(stats['nrows'], 4)
        bar.send_keys('8')
        stats = self.fetch_stats()
        self.assertEqual(stats['nrows'], 2)
        bar.send_keys('18')
        stats = self.fetch_stats()
        self.assertEqual(stats['nrows'], 1)


