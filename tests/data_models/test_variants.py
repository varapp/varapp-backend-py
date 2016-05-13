import unittest
from varapp.data_models.variants import *
from varapp.variants.variants_factory import variants_collection_factory
from varapp.samples.samples_factory import samples_selection_factory
from varapp.constants.tests import NVAR


class TestVariant(unittest.TestCase):
    def test_init(self):
        v = Variant(chrom="chr1", start=12)
        self.assertEqual(v.chrom, "chr1")
        self.assertEqual(v.start, 12)

    def test_expose_variant(self):
        v = Variant(chrom="chr1", start=12, pass_filter=None)
        exp = expose_variant(v)
        self.assertEqual(exp['chrom'], v.chrom)
        self.assertEqual(exp['start'], v.start+1)
        self.assertEqual(exp['pass_filter'], 'PASS')

    def test_annotate_variants(self):
        v = Variant(chrom="chr1", start=12, transcript='ENST00000430354')
        variants = [expose_variant(v)]
        variants = annotate_variants(variants, db='test')
        exp = variants[0]
        self.assertEqual(exp['ensembl_transcript_id'], 'ENST00000430354')
        self.assertEqual(exp['ensembl_gene_id'], 'ENSG00000142149')
        self.assertEqual(exp['entrez_gene_id'], '30811')

    @unittest.skip("One would need to add a genotypes blob tot his variant")
    def test_add_genotypes_selection(self):
        v = Variant(chrom="chr1", start=12, transcript='ENST00000430354')
        ss = samples_selection_factory('test', groups={})
        exp = expose_variant(v)
        exp = add_genotypes_selection(exp, ss)


class TestVariantsCollection(unittest.TestCase):
    def setUp(self):
        self.varCol = variants_collection_factory('test')
        self.simpleVariants = VariantsCollection([
            Variant(ref=x[0], quality=x[1], chrom=x[2], start=x[3])
            for x in ([
                ('A', 100.3, 'chr1', 100), ('B', 10.4, 'chr1', 99), ('C', 9.2, 'chr2', 20),
                ('D', 200, 'chr12', 1000), ('E', 1, 'chr1', 2000),
            ])
        ])

    def test_len(self):
        self.assertEqual(len(self.varCol), NVAR)

    def test_getitem(self):
        v = self.varCol[3]
        self.assertIsInstance(v, Variant)

    def test_add(self):
        s = self.simpleVariants + self.simpleVariants
        self.assertIsInstance(s, VariantsCollection)
        self.assertEqual(len(s), 2*len(self.simpleVariants))

    def test_sub(self):
        s = self.simpleVariants.sub(1,3)
        self.assertIsInstance(s, VariantsCollection)
        self.assertEqual(len(s), 2)

    def test_ids(self):
        self.assertEqual(self.varCol.ids, [v.variant_id for v in self.varCol.list])

    def _check_variant_ids(self, variants, ids):
        self.assertEqual([v.ref for v in variants], list(ids))

    def test_check_variants_ids(self):
        """Just check that the check methods checks."""
        self._check_variant_ids(self.simpleVariants, 'ABCDE')

    def test_order_by_quality(self):
        self._check_variant_ids(self.simpleVariants.order_by('quality'), 'ECBAD')

    def test_order_by_quality_reverse(self):
        self._check_variant_ids(self.simpleVariants.order_by('quality', reverse=True), 'DABCE')


if __name__ == '__main__':
    unittest.main()

