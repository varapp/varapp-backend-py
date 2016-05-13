import unittest
from varapp.variants.variants_factory import *
from varapp.data_models.variants import Variant, VariantsCollection
from varapp.constants.tests import NVAR
import numpy as np


class TestVariantsCollectionFactory(unittest.TestCase):
    def setUp(self):
        self.db = 'test'

    def test_variants_collection_factory(self):
        varCol = variants_collection_factory(self.db)
        self.assertIsInstance(varCol, VariantsCollection)

class TestExtractVariants(unittest.TestCase):
    def setUp(self):
        self.db = 'test'
        self.BS = 75  # batch size, must be < NVAR to test properly

    def test_extract_variants_1(self):
        """Extract variants with variant_ids given by bin_ids"""
        qs = Variant.objects.using(self.db).all()
        bin_ids = np.zeros(NVAR)
        bin_ids[2:5] = 1
        var = extract_variants_from_ids_bin_array(qs, bin_ids)
        self.assertEqual([v.variant_id for v in var], list(range(3,6)))
        # Introducing the batch size as well as adding some non-contiguous variants
        bin_ids[150:153] = 1
        var = extract_variants_from_ids_bin_array(qs, bin_ids, batch_size=self.BS)
        self.assertEqual([v.variant_id for v in var], list(range(3,6)) + list(range(151,154)))

    def test_extract_variants_limit(self):
        """Extract only the first 10. *qs* is sorted by chrom/start."""
        qs = Variant.objects.using(self.db).all().order_by('chrom','start')
        bin_ids = np.zeros(NVAR)
        bin_ids[20:50] = 1
        var = extract_variants_from_ids_bin_array(qs, bin_ids, limit=10, batch_size=self.BS)
        self.assertEqual(len(var), 10)
        self.assertEqual([v.variant_id for v in var], list(range(21,31)))

    def test_extract_variants_limit_offset(self):
        """Extract only 10, skipping the first 10. *qs* is sorted by chrom/start."""
        qs = Variant.objects.using(self.db).all().order_by('variant_id')
        bin_ids = np.zeros(NVAR)
        bin_ids[20:50] = 1
        var = extract_variants_from_ids_bin_array(qs, bin_ids, limit=10, offset=10, batch_size=self.BS)
        self.assertEqual(len(var), 10)
        self.assertEqual([v.variant_id for v in var], list(range(31,41)))

    def test_extract_variants_limit_sorted(self):
        """If not sorted by variant_id (or chrom and start), the 10 variants extracted
        are in the order found in *qs*, not as in *bin_ids*."""
        qs = Variant.objects.using(self.db).all().order_by('impact')
        bin_ids = np.zeros(NVAR)
        bin_ids[20:50] = 1
        var = extract_variants_from_ids_bin_array(qs, bin_ids, limit=10, batch_size=self.BS)
        self.assertEqual(len(var), 10)
        self.assertNotEqual([v.variant_id for v in var], list(range(21,31)))

    def test_extract_variants_3(self):
        """Passing the *ordered_qs_indices* parameter list manually,
        to avoid recomputing it in the real case."""
        qs = Variant.objects.using(self.db).all().order_by('impact')
        ordered_qs_indices = list(qs.values_list('variant_id', flat=True))
        bin_ids = np.zeros(NVAR)
        bin_ids[20:50] = 1
        var = extract_variants_from_ids_bin_array(qs, bin_ids, ordered_qs_indices, limit=10, batch_size=self.BS)
        self.assertEqual(len(var), 10)
        self.assertNotEqual([v.variant_id for v in var], list(range(21,31)))
