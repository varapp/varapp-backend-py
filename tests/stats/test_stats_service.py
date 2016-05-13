import unittest
from varapp.stats.stats_service import stats_service, GlobalStatsService
from varapp.stats.variant_stats import VariantStats
from varapp.variants.variants_factory import variants_collection_factory
from varapp.data_models.variants import Variant
from varapp.constants.filters import *
import numpy as np


class TestStatsService(unittest.TestCase):
    def setUp(self):
        self.qs = Variant.objects.using('test')
        self.variants = variants_collection_factory(db='test')
        self.N = len(self.variants)

    def test_stats_service(self):
        """stats_service(db) creates a GlobalStatsService"""
        sts = stats_service(db='test')
        self.assertIsInstance(sts, GlobalStatsService)

    def test_GLobalStatsService(self):
        """Check attributes"""
        VS = GlobalStatsService('test')
        self.assertTrue(hasattr(VS, 'db'))

    def test_init_discrete_filter_masks(self):
        """Init discrete filter masks"""
        VS = GlobalStatsService('test')
        self.assertTrue(VS._masks_ready)

    def test_global_stats(self):
        """GLobalStatsService.global_stats() returns a VariantStats object with info
           on all discrete and numeric fields."""
        VS = GlobalStatsService('test')
        stats = VS.get_global_stats()
        self.assertIsInstance(stats, VariantStats)
        for f in DISCRETE_FILTER_NAMES:
            self.assertIn(f, stats.stats)
            for val,cnt in stats.stats[f].counts.items():
                val == 'pairs' or self.assertIsInstance(cnt, int)
        for f in NUMERIC_FILTER_NAMES:
            self.assertIn(f, stats.stats)
            self.assertIsInstance(stats.stats[f].max, float)
            self.assertIsInstance(stats.stats[f].min, float)

    def test_global_stats_accurate(self):
        VS = GlobalStatsService('test')
        globstats = VS.get_global_stats().stats
        qs = self.qs
        self.assertEqual(globstats['pass_filter'][None], qs.filter(pass_filter__isnull=True).count())
        #self.assertEqual(globstats['impact_severity']['MED'], qs.filter(impact_severity='MED').count())
        self.assertEqual(globstats['impact']['intron_variant'], qs.filter(impact='intron_variant').count())
        self.assertEqual(globstats['quality'].max, max(qs.values_list('quality',flat=True)))
        self.assertEqual(globstats['cadd_raw'].min, min(qs.filter(cadd_raw__isnull=False).values_list('cadd_raw',flat=True)))
        self.assertEqual((globstats['aaf_1kg_all'].min, globstats['aaf_1kg_all'].max), (0,1))

    def test_make_stats(self):
        VS = GlobalStatsService('test')
        qs = self.qs
        freq_filtered = qs.filter(aaf_1kg_all__lte=0.01).filter(aaf_esp_all__lte=0.01).filter(aaf_exac_all__lte=0.01)
        ids = list(freq_filtered.values_list('variant_id',flat=True))
        stats = VS.make_stats(ids)
        self.assertEqual(stats.total_count, freq_filtered.count())
        self.assertEqual(stats.stats['in_dbsnp'].counts[True], freq_filtered.filter(in_dbsnp=True).count())
        self.assertEqual(stats.stats['in_dbsnp'].counts[False], freq_filtered.filter(in_dbsnp=False).count())

    def test_init_impacts(self):
        VS = GlobalStatsService('test')
        impacts = VS.get_global_stats().stats['impact']['pairs']
        self.assertEqual(set(impacts), {'HIGH','MED','LOW'})

    def test_cache_mask(self):
        VS = GlobalStatsService('test')
        mask = VS.get_mask('impact', 'intron_variant')
        self.assertIsInstance(mask, np.ndarray)
        VS.save_mask(mask, 'impact','intron_variant')
        remask = VS.get_mask('impact', 'intron_variant')
        self.assertEqual(np.sum(mask - remask), 0)


if __name__ == '__main__':
    unittest.main()
