
from tests_functional.test_selenium import *
from selenium.webdriver import ActionChains


_is_setup = False

class TestFilters(SeleniumTest):
    def setUp(self):
        global _is_setup
        if not _is_setup:
            self.main_page()
            self.try_login()
            self.waitFor('#filters')
            self.change_db('test')
            _is_setup = True
        self.wait_for_global_stats()
        self.reset_filters()

    # Helper methods

    def get_n_variants(self):
        """Return the number of filtered variants"""
        nvariants = self.waitFor('#n-filtered')
        n_filtered = int(nvariants.text)
        return n_filtered

    def wait_for_global_stats(self):
        """Wait until loading global stats is finished. It should display the number of variants"""
        self.wait_for_ajax_end()
        self.waitFor('#n-total')

    def move_slider(self, slider, offset=0.0):
        """Click somewhere in an horizontal slider. The position is given in fraction
           of its width: *offset* from 0 to 1."""
        width = slider.size['width']
        action_chains = ActionChains(self.driver)
        # Move to the middle of the slider (default), then to its leftmost point
        action_chains.move_to_element(slider).move_by_offset(-width/2.0, 0)
        # Double-click twice to know where the cursor is.
        #action_chains.context_click().context_click()
        # Need to perform() because it seems to bug with move_by_offset otherwise
        action_chains.perform()
        # Offset to the right
        action_chains.move_by_offset(width * offset, 0)
        # Double-click twice to know where the cursor is
        #action_chains.context_click().context_click()
        action_chains.click().perform()

    def open_filters_group(self, group):
        """Open the collapsible panel for that filters group. Group names start with a capital letter."""
        header = self.select('#filter-group-collapse-heading-' + group)
        body = self.select('#filter-group-collapse-' + group)
        # Check if it is already open, otherwise it would just close it
        if 'in' not in body.get_attribute('class').split():
            self.wait(EC.element_to_be_clickable((By.ID, 'filter-group-collapse-heading-' + group)))
            header.click()
            self.waitFor('#filter-group-collapse-' + group)

    def close_filters_group(self, group):
        """Close the collapsible panel for that filters group. Group names start with a capital letter."""
        header = self.select('#filter-group-collapse-heading-' + group)
        body = self.select('#filter-group-collapse-' + group)
        # Check if it is already open, otherwise it would just close it
        if 'in' in body.get_attribute('class').split():
            self.wait(EC.element_to_be_clickable((By.ID, 'filter-group-collapse-heading-' + group)))
            header.click()
            self.waitFor('#filter-group-collapse-' + group)

    def checkbox_check(self, value):
        """Click an individual enum checkbox"""
        box = self.waitFor('.enum-filter-input input[value="{}"]'.format(value))
        self.js_click(box)
        #box.click()
        self.wait_for_ajax_end()

    def checkbox_all_check(self, value):
        """Click a 'select/deselect all' checkbox"""
        box = self.waitFor('.enum-filter-{} input'.format(value))
        box.click()
        self.wait_for_ajax_end()

    def search_location(self, loc):
        """Search for a location string *loc* in the Location filter"""
        locbar = self.waitFor('input.location-search')
        locbar.send_keys(loc)
        locbar.send_keys(Keys.ENTER)
        self.wait_for_ajax_end()

    # Actual tests

    def test_1_genotypes_filter(self):
        """Change the genotypes scenario"""
        n_filtered = self.get_n_variants()
        # Test that all kinds of scenarios are displayed
        self.waitFor('div.genotypes-filter-input', 5)
        scenarios = self.selectAll(
            'div.genotypes-filter div.genotypes-filter-choices div.genotypes-filter-input input')
        scenario_names = {s.get_attribute('name') for s in scenarios}
        self.assertEqual(scenario_names, {'active','dominant','recessive','de_novo','compound_het','x_linked'})
        self.assertEqual(scenarios[0].get_attribute('name'), 'active')
        self.assertEqual(scenarios[0].get_attribute('checked'), 'true')

        # Choose another scenario
        self.choose_genotypes_scenario('dominant')
        self.assertEqual(scenarios[1].get_attribute('checked'), 'true')
        n_filtered_dominant = self.get_n_variants()
        self.assertNotEqual(n_filtered, n_filtered_dominant)

    def test_2_true_false_any_filter(self):
        """Apply a true/false/any filter, such as 'in dbsnp' """
        n_filtered = self.get_n_variants()
        self.open_filters_group('Frequency')
        # Option 'any' should be selected by default, among 3 options
        in_dbsnp = self.waitFor('#one-filter-in_dbsnp', 1)
        options = in_dbsnp.find_elements_by_css_selector('.one-choice input')
        self.assertEqual(len(options), 3)
        self.assertEqual(options[2].get_attribute('checked'), 'true')

        # Change to true ('yes') - as soon as it is clickable
        yes = in_dbsnp.find_element_by_css_selector('.one-choice input[value="true"]')
        yes.click()
        self.wait_for_ajax_end()
        n_filtered_in_dbsnp = self.get_n_variants()
        self.assertNotEqual(n_filtered, n_filtered_in_dbsnp, "Expected to fail with chromedriver")
        self.assertEqual(yes.get_attribute('checked'), 'true')

    def test_3_frequency_filter(self):
        """Test the sliders that have ticks"""
        """
        In particular:
        - default value that resets the filter
        - using a custom text value should replace one of the ticks with the new value
        """
        div = '#one-filter-aaf_1kg_all '

        def get_slider_value(nbreak):
            ticks = self.waitForAll(div+'.ticks', 0.5)
            return ticks[int(nbreak)].text

        def switch():
            sw = self.waitFor(div+'.switch-input-mode')
            self.js_click(sw)

        n_filtered = self.get_n_variants()
        # Open the collapsible panel
        self.open_filters_group('Frequency')
        slider = self.waitFor(div+'input', 2)
        self.assertEqual(slider.get_attribute('value'), '4')
        self.assertEqual(get_slider_value('4'), '1')

        # Click in the middle of the slider (default click())
        self.wait(EC.element_to_be_clickable((By.CSS_SELECTOR, div+'input')))
        self.move_slider(slider, 0.5)
        self.wait_for_ajax_end()
        sleep(0.1)
        self.assertEqual(slider.get_attribute('value'), '2')
        self.assertEqual(get_slider_value('2'), '1%')
        n_filtered_freq = self.get_n_variants()
        self.assertLess(n_filtered_freq, n_filtered)
        # Summary item appears
        summary = self.select('.filter-group-summary')
        summary_items = summary.find_elements_by_tag_name('li')
        self.assertGreater(len(summary_items), 0)

        # Click to the end of the slider again - reset filter
        self.wait(EC.element_to_be_clickable((By.CSS_SELECTOR, div+'input')))
        self.move_slider(slider, 0.98)
        self.wait_for_ajax_end()
        sleep(0.1)
        self.assertEqual(slider.get_attribute('value'), '4')
        n_filtered_freq = self.get_n_variants()
        self.assertEqual(n_filtered, n_filtered_freq)

        # Slider/text input switch
        slider = self.waitFor(div+'input', 2)
        slider_value = get_slider_value(slider.get_attribute('value'))
        switch()
        text_input = self.waitFor(div+'input[type="text"]')
        self.assertEqual(text_input.get_attribute('value'), slider_value)
        switch()
        self.assertExists(div+'input[type="range"]')

        # Summary item disappears. Close the panel to be sure it is visible
        self.close_filters_group('Frequency')
        self.wait(EC.invisibility_of_element_located((By.CSS_SELECTOR, '.filter-group-summary')), 5)

    def test_4_continuous_filter(self):
        """Test the continuous sliders"""
        """
        In particular:
        - default value that resets the filter
        - using a custom filter should place the cursor at the new value
        """
        div = '#one-filter-quality '

        def get_slider_value():
            sleep(0.1)
            return self.waitFor('.continuous-value-text', 0.5).text

        def switch():
            sw = self.waitFor(div+'.switch-input-mode')
            self.js_click(sw)

        n_filtered = self.get_n_variants()
        self.open_filters_group('Quality')
        slider = self.waitFor(div+'input[type="range"]', 2)
        minbreak = int(slider.get_attribute('value'))  # break 1-100, not the actual value
        minval = float(get_slider_value())

        # Click in the middle of the slider (default click())
        self.wait(EC.element_to_be_clickable((By.CSS_SELECTOR, div+'input')))
        self.move_slider(slider, 0.2)
        self.wait_for_ajax_end()
        self.assertGreater(int(slider.get_attribute('value')), minbreak)
        self.assertGreater(float(get_slider_value()), minval)
        n_filtered_cont = self.get_n_variants()
        self.assertLess(n_filtered_cont, n_filtered)

        # Slider/text input switch
        slider_value = get_slider_value()
        switch()
        text_input = self.waitFor(div+'input[type="text"]')
        self.assertEqual(text_input.get_attribute('value'), slider_value)
        switch()
        self.assertExists(div+'input[type="range"]')

    def test_5_enum_filter(self):
        """Test the enum filters (checkboxes), particularly Impact filters"""
        self.open_filters_group('Impact')

        # There are 3 classes of severity
        severities = self.waitForAll('.enum-filter-Impact .enum-filter-name')
        self.assertEqual(len(severities), 3)

        # Select "frameshift" (HIGH), "splice acceptor" (HIGH), "missense" (MED).
        # The result should be their union.
        n_frameshift = int(self.waitFor('.enum-filter-choices-frameshift_variant .badge').text)
        n_splice_acceptor = int(self.waitFor('.enum-filter-choices-splice_acceptor_variant .badge').text)
        n_missense = int(self.waitFor('.enum-filter-choices-missense_variant .badge').text)
        self.checkbox_check('frameshift_variant')
        self.assertEqual(self.get_n_variants(), n_frameshift)
        self.checkbox_check('splice_acceptor_variant')
        self.assertEqual(self.get_n_variants(), n_frameshift + n_splice_acceptor)
        self.checkbox_check('missense_variant')
        self.assertEqual(self.get_n_variants(), n_frameshift + n_splice_acceptor + n_missense)

        # The "deselect all" button from HIGH should remove only HIGH selectors
        self.checkbox_all_check('HIGH')
        self.assertEqual(self.get_n_variants(), n_missense)
        # Clicking again should add the whole HIGH category
        self.checkbox_all_check('HIGH')
        self.assertGreater(self.get_n_variants(), n_frameshift + n_splice_acceptor + n_missense)

    def test_6_location_filter_gene(self):
        """Search for a gene name in Location filter"""
        self.assertExists('.glyphicon-search')
        self.search_location('HUNK')
        n_filtered_gene = self.get_n_variants()
        self.assertEqual(n_filtered_gene, 8)

    def test_6_location_filter_region(self):
        """Search for a region in Location filter"""
        self.search_location('chr21:33000000-34000000')  # HUNK
        n_filtered_gene = self.get_n_variants()
        self.assertEqual(n_filtered_gene, 8)

    def test_6_location_filter_mix(self):
        """Search for a region and a gene name in Location filter"""
        self.search_location('HUNK, chrX:0-1000000, ZAN')
        n_filtered_gene = self.get_n_variants()
        self.assertEqual(n_filtered_gene, 10)



