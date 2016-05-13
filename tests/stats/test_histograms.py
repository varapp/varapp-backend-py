import unittest
from varapp.stats.histograms import *

class TestDiscreteCounts(unittest.TestCase):
    def test_DiscreteCounts_strings(self):
        h = DiscreteCounts({'a': 3, 'b': 1, 'c': 1})
        self.assertEqual(h.counts, {'a': 3, 'b': 1, 'c': 1})

    def test_DiscreteHistogram_boolean(self):
        h = DiscreteCounts({True: 3, False: 1})
        self.assertEqual(h.counts, {True: 3, False: 1})

    def test_DiscreteHistogram_boolean_with_null(self):
        h = DiscreteCounts({True: 3, False: 1, None:2})
        self.assertEqual(h.counts, {True: 3, False: 1, None:2})

    def test_DiscreteHistogram_getter(self):
        h = DiscreteCounts({'a': 3, 'b': 1, 'c': 1})
        self.assertEqual(h.counts['a'], 3)
        self.assertEqual(h['a'], 3)


#@unittest.skip('')
class TestStatsContinuous(unittest.TestCase):
    """Test the quantile_balanced() function."""
    def test_StatsContinuous(self):
        histo = StatsContinuous({'min':1, 'max':8})
        self.assertEqual(histo.min, 1)
        self.assertEqual(histo.max, 8)

    def test_StatsContinuousFrequency(self):
        histo = StatsFrequency()
        self.assertEqual(histo.min, 0)
        self.assertEqual(histo.max, 1)

    def test_quantile_balanced_qual_values(self):
        """Real quality values from test db."""
        vals = [10.04, 10.08, 10.09, 10.12, 10.14, 45.67, 47.21, 67.65, 237.88, 350.11, 520.0, 1000.01, 1000.01,
            1000.01, 1000.02, 1000.07, 1554.35, 1601.92, 1681.17, 1762.22, 1944.93, 1976.16, 2246.69, 2621.69,
            2778.73, 3699.33, 7339.64, 7805.13, 8924.67, 10436.5, 12002.42, 12192.58, 12475.87, 12501.57,
            13873.05, 14970.39, 15206.21, 16322.76, 16493.0, 19870.59, 21530.7, 22786.52, 25303.33, 28473.69,
            28684.75, 52001.93, 86811.8, 92070.36, 128116.33, 129130.24, 132986.33, 150093.54, 181994.69]
        histo = StatsContinuous({'min':min(vals), 'max':max(vals)})
        self.assertEqual(histo.min, 10.04)
        self.assertEqual(histo.max, 181994.69)

    def test_quantile_balanced_empty(self):
        histo = StatsContinuous({})
        self.assertEqual(histo.min, 0)
        self.assertEqual(histo.max, 0)


if __name__ == '__main__':
    unittest.main()

