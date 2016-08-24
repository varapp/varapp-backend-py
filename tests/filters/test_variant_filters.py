#!/usr/bin/env python3

import unittest, sys
from varapp.data_models.variants import Variant
from varapp.filters.variant_filters import *
from varapp.filters.filters_factory import variant_filters_map
from varapp.variants.variants_factory import variants_collection_factory
from varapp.constants.tests import NVAR
from varapp.data_models.variants import VARIANT_FIELDS
import random


#@unittest.skip('')
class TestVariantFilters(unittest.TestCase):
    def setUp(self):
        self.testdb = 'test'
        self.variants = variants_collection_factory(self.testdb)
        self.N = len(self.variants)

    def assertSomethingWasFilteredOut(self, var):
        self.assertTrue(0 < len(var) < self.N, "trivial test")

    def apply_filter(self, f):
        return f.apply(db=self.testdb).variants

    def test_field_names(self):
        """Check that all filter field names are in the model,
        and that the name to call them from frontend is the same (helps maintenance)"""
        for fname,fclass in variant_filters_map.items():
            if fname in FREQUENCY_FILTER_NAMES:
                _,db,pop = fname.split('_')
                self.assertEqual(FrequencyFilter(db,pop).field_name, fname)
            else:
                self.assertEqual(fclass.field_name, fname)
            if fname != 'location':
                self.assertIn(fname, VARIANT_FIELDS)

    def test_variant_id_filter(self):
        allids = [v.variant_id for v in self.variants]
        selected_ids = [random.choice(allids) for _ in range(5)]
        f = VariantIDFilter(','.join(map(str,selected_ids)))
        var = self.apply_filter(f)
        for v in var:
            self.assertIn(v.variant_id, selected_ids)

    def test_empty_enum_filter(self):
        f = ImpactFilter('')
        try:
            filteredVar = self.apply_filter(f)
        except TypeError as ex:
            self.fail("Unhandled empty value: {}".format(str(ex)))
        self.assertEqual(f.val, {'',})
        self.assertEqual(len(filteredVar), 0)

# LOCATION FILTERS

    def test_testdb(self):
        """Just make sure that the test DB is used"""
        self.assertEqual(self.N, NVAR)

    def test_gene_exact(self):
        """Return only variants in a given gene."""
        g = "NOC2L"
        f = GeneFilter(g)
        var = self.apply_filter(f)
        self.assertEqual(var[0].gene_symbol, 'NOC2L')

    def test_gene_case_insensitive(self):
        """Return only variants in a given gene."""
        g = "nOc2L"
        f = GeneFilter(g)
        filteredVar = self.apply_filter(f)
        self.assertEqual(filteredVar[0].gene_symbol, 'NOC2L')

    def test_gene_multiple_names(self):
        """Return only variants in a given gene."""
        g = "NOC2L,SAMD11"
        f = GeneFilter(g)
        var = self.apply_filter(f)
        for x in var:
            self.assertIn(x.gene_symbol, g.split(','))

    def test_transcript(self):
        """Return only variants in a given transcript."""
        t = "EnSt00000327044"
        f = TranscriptFilter(t)
        var = self.apply_filter(f)
        self.assertSomethingWasFilteredOut(var)
        for x in var:
            self.assertEqual(x.transcript.lower(), t.lower())

    def test_location(self):
        """Return only variants in a given genomic region."""
        for loc in [('chr1',762273,762273), ('chr1',762272,762274), ('chr1',69510,721757)]:
            f = LocationFilter("{}:{}-{}".format(*loc))
            var = self.apply_filter(f)
            chroms = [v.chrom for v in var]
            starts = [v.start for v in var]
            ends   = [v.end   for v in var]
            self.assertSomethingWasFilteredOut(var)
            self.assertTrue(all(x == loc[0] for x in chroms))
            self.assertTrue(all(x >= loc[1]-1 for x in starts))
            self.assertTrue(all(x <= loc[2] for x in ends))
        for loc in [('chr1',762272,762272), ('chr1',762274,762274), ('chr1',762260,762272)]:
            f = LocationFilter("{}:{}-{}".format(*loc))
            var = self.apply_filter(f)
            self.assertEqual(len(var), 0)

    def test_location_inexistent(self):
        f = LocationFilter("ksajdhfkjasdf", db=self.testdb)
        try:
            filteredVar = self.apply_filter(f)
        except TypeError as ex:
            self.fail("Unhandled empty value: {}".format(str(ex)))
        self.assertEqual(f.val, [])
        self.assertEqual(len(filteredVar), 0)

    def test_location_more_than_300(self):
        """An error should be raised if one queries more than 300 elements."""
        query = ','.join(["NOC2L"]*301)
        f = LocationFilter(query, db=self.testdb)
        with self.assertRaises(ValueError):
            self.apply_filter(f)

# QUALITY FILTERS

    def test_quality_eq(self):
        """Return only qualities equal to that value."""
        quality = Variant.objects.using(self.testdb).values_list('quality', flat=True)[0]
        for op in ['=','==']:
            f = QualityFilter(str(quality), op=op)
            self.assertEqual(f.val, float(quality))
            var = self.apply_filter(f)
            self.assertSomethingWasFilteredOut(var)
            for x in var:
                self.assertEqual(x.quality, quality)

    def test_quality_ge(self):
        """Return only qualities superior/inferior to the given threshold."""
        quality = 1000
        f = QualityFilter(str(quality), op='>=')
        self.assertEqual(f.val, float(quality))
        var = self.apply_filter(f)
        self.assertSomethingWasFilteredOut(var)
        for x in var:
            self.assertGreaterEqual(x.quality, quality)

    def test_quality_lt(self):
        """Return only qualities superior/inferior to the given threshold."""
        quality = 1000
        f = QualityFilter(str(quality), op='<')
        var = self.apply_filter(f)
        self.assertSomethingWasFilteredOut(var)
        for x in var:
            self.assertLessEqual(x.quality, quality)

    def test_passfilter(self):
        """Return only variants having passed the quality filters."""
        f = PassFilter('PASS')
        var = self.apply_filter(f)
        self.assertSomethingWasFilteredOut(var)
        for x in var:
            self.assertEqual(x.pass_filter, None)

        filter_names = "PASS,VQSRTrancheSNP99.00to99.90,VQSRTrancheSNP90.00to99.00" \
                       + "VQSRTrancheINDEL99.00to99.90,VQSRTrancheINDEL90.00to99.00,aaa"
        f = PassFilter(filter_names)
        var = self.apply_filter(f)
        self.assertSomethingWasFilteredOut(var)
        for x in var:
            self.assertIn(x.pass_filter, f.parse_arg(filter_names))

    def test_qual_depth(self):
        """Return only qual_depth inferior to the given threshold."""
        qual_depth = 10
        f = QualDepthFilter(str(qual_depth), op='<')
        var = self.apply_filter(f)
        self.assertSomethingWasFilteredOut(var)
        for x in var:
            self.assertLess(x.qual_depth, qual_depth)

    def test_fisher_strand_bias(self):
        """Return only Fisher strand bias superior to the given threshold."""
        bias = 10
        f = StrandBiasFilter(str(bias), op='>')
        var = self.apply_filter(f)
        self.assertSomethingWasFilteredOut(var)
        for x in var:
            self.assertGreater(x.fisher_strand_bias, bias)

    def test_rms_map_qual(self):
        """Return only RMS mapping quality superior to the given threshold."""
        qual = 50
        f = RmsMapQualFilter(str(qual), op='>=')
        var = self.apply_filter(f)
        self.assertSomethingWasFilteredOut(var)
        for x in var:
            self.assertGreaterEqual(x.rms_map_qual, qual)

    def test_base_qual_rank_sum(self):
        """Return only base_qual_rank_sum superior to the given threshold."""
        qual = 1
        f = BaseQualRankSumFilter(str(qual), op='>=')
        var = self.apply_filter(f)
        self.assertSomethingWasFilteredOut(var)
        for x in var:
            self.assertGreaterEqual(x.base_qual_rank_sum, qual)

    def test_map_qual_rank_sum(self):
        """Return only mq_rank_sum superior to the given threshold."""
        qual = 1
        f = MapQualRankSumFilter(str(qual), op='>=')
        var = self.apply_filter(f)
        self.assertSomethingWasFilteredOut(var)
        for x in var:
            self.assertGreaterEqual(x.map_qual_rank_sum, qual)

    def test_read_pos_rank_sum(self):
        """Return only read_pos_rank_sum superior to the given threshold."""
        qual = 1
        f = ReadPosRankSumFilter(str(qual), op='>=')
        var = self.apply_filter(f)
        self.assertSomethingWasFilteredOut(var)
        for x in var:
            self.assertGreaterEqual(x.read_pos_rank_sum, qual)


# FREQUENCY FILTERS

    def test_in_dbsnp(self):
        """In_dbsnp=0 filter returns only what is not in dbSNP."""
        f = DbsnpFilter('0')
        var = self.apply_filter(f)
        self.assertSomethingWasFilteredOut(var)
        self.assertTrue(all(x.in_dbsnp is False for x in var))

        f = DbsnpFilter('1')
        var = self.apply_filter(f)
        self.assertSomethingWasFilteredOut(var)
        for x in var:
            self.assertTrue(x.in_dbsnp)

    def test_in_1kg(self):
        """In_1kg=0 filter returns only what is not in 1000 Genomes."""
        f = ThousandGenomesFilter('0')
        var = self.apply_filter(f)
        self.assertSomethingWasFilteredOut(var)
        for x in var:
            self.assertFalse(x.in_1kg)

    def test_in_esp(self):
        """In_esp=0 filter returns only what is not in ESP."""
        f = ESPFilter('0')
        var = self.apply_filter(f)
        self.assertSomethingWasFilteredOut(var)
        for x in var:
            self.assertFalse(x.in_esp)

    def test_frequency_1kg_all_01(self):
        """Returns only rare variants - based on 1000 Genomes."""
        freq = 0.01
        f = FrequencyFilter('1kg','all')(freq, '', '<=')
        var = self.apply_filter(f)
        v1kg = list(var)
        self.assertSomethingWasFilteredOut(v1kg)
        self.assertTrue(any([x.aaf_1kg_all is not None for x in v1kg]))
        self.assertTrue(all((x.aaf_1kg_all or 0) <= freq for x in v1kg))

    def test_frequency_1kg_all_NoneValue(self):
        """None frequency values in Gemini are to be considered as zero (rare)."""
        f = FrequencyFilter('1kg','all')(0, '', '<=')
        nonevals = [v for v in self.variants if v.aaf_1kg_all is None]
        if len(nonevals) > 0:
            var = self.apply_filter(f)
            self.assertGreater(len(var), 0)
            self.assertTrue(all([(x.aaf_1kg_all is None) or (x.aaf_1kg_all <= 0) for x in var]))
            # And *nonevals* are the same as *var*, except from real 0 values:
            noneids = {v.variant_id for v in nonevals}
            zerofreqids = {v.variant_id for v in var}
            self.assertTrue(noneids.issubset(zerofreqids))

    def test_frequency_esp_all_04(self):
        """Returns only rare variants - based on ESP."""
        freq = 0.4
        f = FrequencyFilter('esp','all')(freq, '', '>')
        var = self.apply_filter(f)
        vesp = list(var)
        self.assertSomethingWasFilteredOut(vesp)
        self.assertTrue(any([x.aaf_esp_all is not None for x in vesp]))
        self.assertTrue(all((x.aaf_esp_all or sys.maxsize) > freq for x in vesp))

        # Check that passing the two filters takes both into account
        v1kg = list(FrequencyFilter('1kg','all')(0.01, '', '<=').apply(db=self.testdb).variants)
        self.assertNotEqual(set([x.variant_id for x in v1kg]), set([x.variant_id for x in vesp]))

    def test_frequency_exac_all(self):
        """Returns only rare variants - based on ESP."""
        freq = 0.4
        f = FrequencyFilter('exac','all')(freq, '', '>')
        var = self.apply_filter(f)
        vexac = list(var)
        self.assertSomethingWasFilteredOut(vexac)
        self.assertTrue(any([x.aaf_exac_all is not None for x in vexac]))
        self.assertTrue(all((x.aaf_exac_all or sys.maxsize) > freq for x in vexac))

    def test_frequency_max_all(self):
        """Returns only rare variants - based on ESP."""
        freq = 0.3
        f = FrequencyFilter('max','all')(freq, '', '>')
        var = self.apply_filter(f)
        vmax = list(var)
        self.assertSomethingWasFilteredOut(vmax)
        self.assertTrue(any([x.aaf_max_all is not None for x in vmax]))
        self.assertTrue(all((x.aaf_max_all or sys.maxsize) > freq for x in vmax))

# IMPACT FILTERS

    def test_type(self):
        f = TypeFilter('snp')
        var = self.apply_filter(f)
        self.assertSomethingWasFilteredOut(var)
        self.assertTrue(all(x.type == 'snp' for x in var))

    def test_is_exonic(self):
        f = IsExonicFilter('1')
        var = self.apply_filter(f)
        self.assertSomethingWasFilteredOut(var)
        self.assertTrue(all(x.is_exonic is True for x in var))
        for x in var:
            self.assertTrue(x.is_exonic)

    def test_is_coding(self):
        f = IsCodingFilter('1')
        var = self.apply_filter(f)
        self.assertSomethingWasFilteredOut(var)
        for x in var:
            self.assertTrue(x.is_coding)

    def test_impact(self):
        impact = '3_prime_UTR_variant'
        f = ImpactFilter(impact)
        var = self.apply_filter(f)
        self.assertSomethingWasFilteredOut(var)
        for x in var:
            self.assertEqual(x.impact, impact)

    def test_impact_severity(self):
        impact = 'HiGh'
        f = ImpactSeverityFilter(impact)
        var = self.apply_filter(f)
        self.assertSomethingWasFilteredOut(var)
        for x in var:
            self.assertEqual(x.impact_severity, impact.upper())

# PATHOGENICITY FILTERS

    def test_cadd_raw(self):
        """Also check that None values are still here after filtering"""
        score = -1.0
        f = CaddRawFilter(str(score), op='<=')
        var = self.apply_filter(f)
        self.assertSomethingWasFilteredOut(var)
        nulls_included = False
        for x in var:
            if x.cadd_raw is None:
                nulls_included = True
            else:
                self.assertLessEqual(x.cadd_raw, score)
        self.assertTrue(nulls_included)

    def test_cadd_scaled(self):
        """Also check that None values are still here after filtering"""
        score = 2.0
        f = CaddRawFilter(str(score), op='>')
        var = self.apply_filter(f)
        self.assertSomethingWasFilteredOut(var)
        nulls_included = False
        for x in var:
            if x.cadd_scaled is None:
                nulls_included = True
            else:
                self.assertGreater(x.cadd_scaled, score)
        self.assertTrue(nulls_included)

    def test_gerp_score(self):
        """Also check that None values are still here after filtering"""
        score = 0.5
        f = GERPScoreFilter(str(score), op='>')
        var = self.apply_filter(f)
        self.assertSomethingWasFilteredOut(var)
        nulls_included = False
        for x in var:
            if x.gerp_bp_score is None:
                nulls_included = True
            else:
                self.assertGreater(x.gerp_bp_score, score)
        #self.assertTrue(nulls_included)  # No NULL value in dataset

    @unittest.skip('deactivated for now')
    def test_gerp_pval(self):
        """Also check that None values are filtered out (replaced by 1)"""
        score = 0.5
        f = GERPPvalueFilter(str(score), op='>')
        var = self.apply_filter(f)
        self.assertSomethingWasFilteredOut(var)
        nulls_included = False
        for x in var:
            if x.gerp_element_pval is None:
                nulls_included = True
            else:
                self.assertGreater(x.gerp_element_pval, score)
        self.assertFalse(nulls_included)

    def test_polyphen_score(self):
        """Also check that None values are filtered out (ContinuousFilterNoneLower)"""
        score = 0.5
        f = PolyphenScoreFilter(str(score), op='>')
        var = self.apply_filter(f)
        self.assertSomethingWasFilteredOut(var)
        nulls_included = False
        for x in var:
            if x.polyphen_score is None:
                nulls_included = True
            else:
                self.assertGreater(x.polyphen_score, score)
        self.assertFalse(nulls_included)

    def test_sift_score(self):
        """Also check that None values are filtered out (ContinuousFilterNoneHigher)"""
        score = 0.5
        f = SiftScoreFilter(str(score), op='<')
        var = self.apply_filter(f)
        self.assertSomethingWasFilteredOut(var)
        nulls_included = False
        for x in var:
            if x.sift_score is None:
                nulls_included = True
            else:
                self.assertLess(x.sift_score, score)
        self.assertFalse(nulls_included)

    def test_polyphen_pred(self):
        for term in ['benign','possibly_damaging']:
            f = PolyphenPredFilter(term)
            var = self.apply_filter(f)
            self.assertSomethingWasFilteredOut(var)
            for x in var:
                self.assertEqual(x.polyphen_pred, term)

    def test_sift_pred(self):
        for term in ['tolerated','deleterious']:
            f = SiftPredFilter(term)
            var = self.apply_filter(f)
            self.assertSomethingWasFilteredOut(var)
            for x in var:
                self.assertEqual(x.sift_pred, term)


if __name__ == '__main__':
    unittest.main()


