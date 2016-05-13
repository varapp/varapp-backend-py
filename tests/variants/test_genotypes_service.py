#!/usr/bin/env python3

import unittest
import numpy as np
from random import randint
from varapp.data_models.variants import Variant
from varapp.samples.samples_factory import samples_selection_factory
from varapp.variants.variants_factory import variants_collection_factory
from varapp.variants.genotypes_service import *

class GenotypesCache(unittest.TestCase):
    def setUp(self):
        self.var = variants_collection_factory(db='test')
        self.ss = samples_selection_factory(db='test')

    def test_extract_genotypes(self):
        gts = extract_genotypes(db='test')
        self.assertIsInstance(gts, np.ndarray)
        self.assertEqual(len(gts), len(self.var))
        self.assertEqual(len(gts[0]), len(self.ss))
        for i,v in enumerate(self.var):
            self.assertEqual(i, v.pk - 1)

    def test_genotypes_service(self):
        gs = genotypes_service('test')
        self.assertIsInstance(gs, GenotypesService)

    def test_genotypes_property(self):
        gs = GenotypesService('test')
        self.assertIsInstance(gs.genotypes, np.ndarray)
        gts = extract_genotypes(db='test')
        self.assertTrue(hasattr(gs,'db'))
        self.assertTrue(hasattr(gs,'_gt_types_bit'))
        for i,x in enumerate(gs.genotypes[:10]):
            self.assertListEqual(list(x), [variant_build_gt_type_bit(x) for x in gts[i]])

    def test_get_chrX(self):
        gs = GenotypesService('test')
        x = gs.chrX
        self.assertEqual(len(x), Variant.objects.filter(chrom='chrX').count())

    def test_init(self):
        gs = GenotypesService('test')
        self.assertIsNot(gs._gt_types_bit, None)


if __name__ == '__main__':
    unittest.main()
