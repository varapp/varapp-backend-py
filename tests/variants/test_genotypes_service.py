#!/usr/bin/env python3

import unittest
import numpy as np
from random import randint
from varapp.data_models.variants import Variant
from varapp.samples.samples_factory import samples_selection_factory
from varapp.variants.variants_factory import variants_collection_factory
from varapp.variants.genotypes_service import *
from varapp.constants.tests import NSAMPLES, NVAR

class TestGenotypesService(unittest.TestCase):
    def setUp(self):
        self.var = variants_collection_factory(db='test')
        self.ss = samples_selection_factory(db='test')

    def test_variant_build_gt_type_bit(self):
        """variant_build_gt_type_bit transforms gt_types to powers of 2"""
        for gt in [1,2,3,4,5]:
            self.assertTrue(variant_build_gt_type_bit(gt) % 2 == 0)

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
        self.assertEqual(gs.N, NVAR)
        self.assertEqual(gs.S, NSAMPLES)
        self.assertIsInstance(gs.genotypes, np.ndarray)
        self.assertTrue(hasattr(gs,'db'))
        self.assertTrue(hasattr(gs,'_gt_types_bit'))
        gts = extract_genotypes(db='test')
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
