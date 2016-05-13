import unittest
from varapp.models.gemini import Variants
from varapp.stats.variant_stats import VariantStats
from varapp.stats.histograms import StatsContinuous, DiscreteCounts, StatsFrequency
from varapp.variants.variants_factory import variants_collection_factory
from varapp.samples.samples_factory import samples_selection_factory
from varapp.filters.filters_factory import variant_filters_collection_factory
from varapp.constants.filters import *


@unittest.skip('')
class TestVariantsStats(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()

