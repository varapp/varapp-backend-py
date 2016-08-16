"""
Test the lookup window - the closer view to gene info, genotypes etc.
"""

from tests_functional.test_selenium import *


_is_setup = False

class TestLookup(SeleniumTest):
    def setUp(self):
        global _is_setup
        if not _is_setup:
            self.main_page()
            self.try_login()
            self.waitFor('#variants')
            _is_setup = True

    def test_0_lookup_gene_name(self):
        """Open the lookup for gene names, showing additional gene annotation with external links"""
        gene_links = self.waitForAll(".lookup-link")
        self.assertGreater(len(gene_links), 0)
        gene_links[0].click()
        self.assertExists("#lookup-panel", 1)
        rows = self.selectAll("#lookup-panel td.lookup")
        self.assertGreater(len(rows[0].text), 0)
        self.assertEqual(rows[1].text[:4], 'ENSG')
        self.assertTrue(rows[2].text.isnumeric())
        self.assertEqual(rows[3].text, 'Search...')
        desc = self.select(".lookup-description").text

        # Choose another gene
        gene_links[1].click()
        desc2 = self.select(".lookup-description").text
        self.assertNotEqual(desc2, desc)

    def test_1_lookup_genotypes(self):
        """Open the lookup for genotypes, showing the family information"""
        genotypes = self.waitForAll(".genotypes-container")
        self.assertGreater(len(genotypes), 0)
        genotypes[0].click()
        self.assertExists("#lookup-panel", 1)
        self.assertExists(".lookup-sample-name")
        self.assertExists(".lookup-genotype")
        self.assertExists(".lookup-parents")

    def test_3_close(self):
        """Close the lookup panel"""
        close = self.select("#lookup-panel .close-icon")
        close.click()
        self.assertNotExists("#lookup-panel", 1)

