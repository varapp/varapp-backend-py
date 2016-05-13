
import unittest
from django.test.client import RequestFactory
from varapp.filters.filters import FiltersCollection
from varapp.filters.variant_filters import *
from varapp.filters.filters_factory import variant_filters_from_request, variant_filters_collection_factory


class TestFiltersFactory(unittest.TestCase):
    def test_variant_filters_from_request(self):
        filters = [('filter', 'in_dbsnp'),
                   ('filter', 'quality<=1000'),
                   ('filter', 'aaf_1kg_all<=0.5'),
                   ('filter', 'aaf_max_all>0.4'),
                  ]
        expected = [DbsnpFilter(name='in_dbsnp', op='=', val='1'),
                    QualityFilter(name='quality', op='<=', val='1000'),
                    ContinuousFilter(name='aaf_1kg_all', op='<=', val='0.5'),
                    ContinuousFilter(name='aaf_max_all', op='>', val='0.4'),
                   ]
        request = RequestFactory().get('', filters)
        fc = variant_filters_from_request(request, db='test')
        self.assertIsInstance(fc, FiltersCollection)
        self.assertTrue(len(fc) == len(filters))

        def check(ff, expect):
            self.assertEqual(ff.val, expect.val)
            self.assertEqual(ff.name, expect.name)
            self.assertEqual(ff.op, expect.op)

        for f in expected:
            check(fc[f.name], f)

    def test_size(self):
        """The created FilterCollection has the correct number of filters."""
        filters = [('in_dbsnp', None, None),
                   ('quality', '<=', '1000'),
                   ('is_exonic', '=', 'true')
                   ]
        filterColl = variant_filters_collection_factory(filters)
        self.assertEqual(len(filterColl), 3)

    def test_has(self):
        """The created FilterCollection has the correct elements."""
        filters = [('in_dbsnp', None, None),
                   ('quality', '<=', '1000'),
                   ('is_exonic', '=', 'true')
                   ]
        filterColl = variant_filters_collection_factory(filters)
        self.assertTrue(filterColl.has('is_exonic'))
        self.assertFalse(filterColl.has('paf le chien'))



if __name__ == '__main__':
    unittest.main()
