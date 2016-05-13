
import unittest
from varapp.filters.sort import *
from varapp.variants.variants_factory import variants_collection_factory
from varapp.data_models.variants import VARIANT_FIELDS
from django.test.client import RequestFactory

class TestSort(unittest.TestCase):
    def setUp(self):
        self.variants = variants_collection_factory(db='test')

    def test_sort_from_request_ASC(self):
        """Should sort variants wrt. a specific column
        - string, int or float -, from smaller to bigger or in alphabetical order.
        Compare with manual sort.
        Frequencies could have None values, which is why we use this Sort.
        """
        for field in ['chrom','start','aaf_1kg_all']:
            request = RequestFactory().get('', {'order_by': '{},ASC'.format(field)})
            order = sort_from_request(request)
            self.assertIsInstance(order, Sort)
            self.assertEqual(order.key, field)
            self.assertEqual(order.reverse, False)
            var = self.variants.order_by(order.key, order.reverse)
            col0 = [getattr(v,field) for v in self.variants]
            col = [getattr(v,field) for v in var]
            col0_nonull = [x for x in col0 if x is not None]
            col0 = [None]*(len(col)-len(col0_nonull)) + sorted(col0_nonull)
            self.assertEqual(col0, col)

    def test_sort_from_request_DESC(self):
        """'DESC' should reverse the ordering.
        Except for Nones that are always less."""
        for field in ['chrom','start','aaf_1kg_all']:
            request = RequestFactory().get('', {'order_by': '{},DESC'.format(field)})
            order = sort_from_request(request)
            self.assertEqual(order.reverse, True)
            var = self.variants.order_by(order.key, order.reverse)
            col0 = [getattr(v,field) for v in self.variants]
            col = [getattr(v,field) for v in var]
            col0_nonull = [x for x in col0 if x is not None]
            col0 = sorted(col0_nonull, reverse=True) + [None]*(len(col)-len(col0_nonull))
            self.assertEqual(col0, col)


class TestSortableFields(unittest.TestCase):
    """Ultimately we want to be able to sort wrt. to all possible exported fields."""
    #@unittest.skip('')
    def test_sort_all(self):
        """Just check that it does not raise an error."""
        var = variants_collection_factory(db='test')
        for field in VARIANT_FIELDS:
            Sort(field, False).sort(var)


if __name__ == '__main__':
    unittest.main()
