#!/usr/bin/env python3

import unittest
from django.db.models import Q
from varapp.filters.filters import *
from varapp.filters.variant_filters import *
from varapp.filters.genotype_filters import *
from varapp.samples.samples_factory import samples_selection_factory
from varapp.constants.tests import NVAR


class UselessFilter(VariantFilter):
    """Mock a Filter class, for testing purposes. It lets all variants pass (id>-1)."""
    filter_class = 'quality'
    def __init__(self, val='', name='', op=''):
        super().__init__(val=val, name=name, op=op)
    def django_condition(self):
        return Q(**{'variant_id__gt': -1})


def _dummy(N=1, prefix=''):
    return FiltersCollection([UselessFilter(prefix+str(i), prefix+str(i), str(i)) for i in range(N)])


class TestFilter(unittest.TestCase):
    def setUp(self):
        self.f = UselessFilter(val='a', name='b', op='=')

    def test_init(self):
        self.assertEqual([self.f.val, self.f.name, self.f.op], ['a', 'b', '='])

    def test_apply0(self):
        var = self.f.apply(db='test').variants
        self.assertIsInstance(var, VariantsCollection)
        self.assertEqual(len(var), NVAR)

    def test_apply(self):
        f = QualityFilter(op='<', val='60')
        var = f.apply(db='test').variants
        self.assertGreater(len(var), 0)
        self.assertLess(len(var), NVAR)


# @unittest.skip('')
class TestFiltersCollection(unittest.TestCase):
    """Test the functionalities of a FiltersCollection, except for apply"""
    def setUp(self):
        self.fc = _dummy(5)

    def test_has(self):
        self.assertTrue(self.fc.has('4'))

    def test_len(self):
        self.assertEqual(len(self.fc), 5)

    def test_get_item(self):
        fc = _dummy(5)
        f = fc['1']
        self.assertEqual(f.val, '1')

    def test_add(self):
        fc = _dummy(5)
        newf = UselessFilter('-1', '-1', '-1')
        fc.append(newf)
        self.assertEqual(len(fc), 6)

    def test_sub(self):
        fc = _dummy(5)
        fc -= '3'
        self.assertEqual(len(fc), 4)

    def test_cache_key(self):
        fc=_dummy(3)
        key = fc.cache_key()
        self.assertNotEqual(key, '')
        fc.append(UselessFilter('x', '>='))
        key2 = fc.cache_key()
        self.assertNotEqual(key, key2)

    def test___add__(self):
        fc = _dummy(5, 'A')
        fc2 = _dummy(4, 'B')
        fcsum = fc + fc2
        self.assertIsInstance(fcsum, FiltersCollection)
        self.assertEqual(len(fcsum), 9)

    def test_extend(self):
        fc = _dummy(5, 'A')
        fc2 = _dummy(5, 'B')
        fc.extend(fc2)
        self.assertEqual(len(fc), 10)

    def test_get_filter_names(self):
        names = self.fc.get_filter_names()
        self.assertEqual(len(names), len(self.fc))

    def test_get_filters_by_class(self):
        fc = FiltersCollection([ImpactSeverityFilter('HIGH'), ImpactFilter('exon'),
            QualityFilter('0.01',op='<'), DbsnpFilter('true')])
        selection = fc.get_filters_by_class('impact')
        self.assertEqual(len(selection), 2)
        for f in selection:
            self.assertEqual(f.filter_class, 'impact')


class TestApplyFiltersCollection(unittest.TestCase):
    """Test FiltersCollection.apply()"""
    def setUp(self):
        self.ss = samples_selection_factory(db='test',
            groups = {'affected': ['09818','09819'], 'not_affected':['09960','09961']})
        self.qfilter = QualityFilter(op='>=', val='50')
        self.dominant = GenotypesFilterDominant(self.ss)

    def test_apply(self):
        fc = FiltersCollection([self.qfilter])
        result = fc.apply(db='test')
        self.assertIsInstance(result, FilterResult)
        var = result.variants
        self.assertIsInstance(var, VariantsCollection)
        self.assertEqual(result.n_filtered, len(var))
        self.assertEqual(set(result.ids), set(v.variant_id for v in var))
        self.assertTrue(0 < len(var) < NVAR)

    def test_apply_with_limit(self):
        limit = offset = 2
        fc = FiltersCollection([self.qfilter])
        result = fc.apply(db='test', offset=offset, limit=limit)
        self.assertIsInstance(result, FilterResult)
        var = result.variants
        self.assertIsInstance(var, VariantsCollection)
        self.assertEqual(len(var), limit)
        self.assertGreater(result.n_filtered, limit, "If equal the test is useless")
        self.assertNotEqual(set(result.ids), set(v.variant_id for v in var))

    def test_apply_sorted(self):
        fc = FiltersCollection([self.qfilter])

        var = fc.apply(db='test', sort_by='quality').variants
        self.assertIsInstance(var, VariantsCollection)
        self.assertTrue(0 < len(var) < NVAR)
        is_sorted_by_start = all(var[i].start <= var[i+1].start for i in range(len(var)-1))
        self.assertFalse(is_sorted_by_start)
        is_sorted_by_quality = all(var[i].quality <= var[i+1].quality for i in range(len(var)-1))
        self.assertTrue(is_sorted_by_quality)

        var = fc.apply(db='test', sort_by='quality', reverse=True).variants
        self.assertIsInstance(var, VariantsCollection)
        self.assertTrue(0 < len(var) < NVAR)
        is_sorted_by_quality = all(var[i].quality < var[i+1].quality for i in range(len(var)-1))
        self.assertFalse(is_sorted_by_quality)
        is_sorted_by_quality_reverse = all(var[i].quality >= var[i+1].quality for i in range(len(var)-1))
        self.assertTrue(is_sorted_by_quality_reverse)

    def test_apply_sorted_with_limit(self):
        fc = FiltersCollection([self.qfilter])
        r1 = fc.apply(db='test')
        r2 = fc.apply(db='test', limit=2, offset=2)
        self.assertTrue(all([x==y for x,y in zip(r1.ids,r2.ids)]), "the whole list of ids is the same")
        self.assertEqual(set(r1.ids) | set(r2.ids), set(r2.ids), "r1 embeds r2")
        self.assertEqual(r2.variants.ids, r1.variants.ids[2:4], "the subset is the right one")
        r3 = fc.apply(db='test', sort_by='quality')
        self.assertTrue(any([x!=y for x,y in zip(r1.ids,r3.ids)]), "the ordering changed")
        r4 = fc.apply(db='test', sort_by='quality', limit=2, offset=2)
        self.assertNotEqual(r2.variants.ids, r4.variants.ids, "the ordering changed before subsetting")
        self.assertEqual(r4.variants.ids, r3.variants.ids[2:4], "the subset is the right one")

    def test_apply_with_only_genotype_filter(self):
        fc = FiltersCollection([self.dominant])
        result = fc.apply(db='test')
        self.assertIsInstance(result, FilterResult)
        var = result.variants
        self.assertEqual(var.db, 'test')
        self.assertIsInstance(var, VariantsCollection)
        self.assertEqual(result.n_filtered, len(var))
        self.assertEqual(set(result.ids), set(v.variant_id for v in var))
        self.assertTrue(0 < len(var) < NVAR)
        # Applying the filter directly yields the same result
        var0 = self.dominant.apply(db='test').variants
        self.assertEqual(len(var), len(var0))

    def test_apply_with_genotype_filter(self):
        """Check that filtering on quality only yields less variants
        than filtering on quality, then on genotype."""
        fc = FiltersCollection([self.qfilter, self.dominant])
        result = fc.apply(db='test')
        self.assertIsInstance(result, FilterResult)
        var = result.variants
        self.assertEqual(var.db, 'test')
        self.assertIsInstance(var, VariantsCollection)
        self.assertEqual(result.n_filtered, len(var))
        self.assertEqual(set(result.ids), set(v.variant_id for v in var))
        self.assertTrue(0 < len(var) < NVAR)
        # Applying the filter directly yields the same result
        var0 = self.qfilter.apply(db='test').variants
        self.assertLess(len(var), len(var0))

    def test_apply_with_gf_and_biglimit(self):
        """Should return all filtered variants, as the limit is very high"""
        limit = NVAR
        fc = FiltersCollection([self.qfilter, self.dominant])
        var = fc.apply(db='test', limit=limit).variants
        self.assertIsInstance(var, VariantsCollection)
        self.assertTrue(0 < len(var) <= limit)
        self.assertEqual(len(var), 4)  # 3 + one that is 'unknown/unknown' in most samples

    def test_apply_with_gf_and_limit(self):
        """Should return at most *limit* variants, but all filtered ids"""
        limit = 2
        fc = FiltersCollection([self.qfilter, self.dominant])
        res = fc.apply(db='test', limit=limit)
        var = res.variants
        self.assertIsInstance(var, VariantsCollection)
        self.assertEqual(len(var), limit)
        self.assertEqual(res.n_filtered, len(res.ids), "If equal the test is useless")
        self.assertNotEqual(res.n_filtered, len(var))

    def test_apply_with_gf_and_limit_and_offset(self):
        """Should return at most *limit* variants, skipping the first *offset*."""
        limit = 2
        offset = 1
        fc = FiltersCollection([self.qfilter, self.dominant])
        res = fc.apply(db='test', limit=limit, offset=offset)
        var = res.variants
        self.assertIsInstance(var, VariantsCollection)
        self.assertEqual(len(var), 2)
        self.assertEqual(res.n_filtered, len(res.ids))
        self.assertNotEqual(res.n_filtered, len(var), "If equal the test is useless")

    def test_nvariants_accurate(self):
        """Check that the number of variants returned corresponds to what is in the db.
        In this case, filtering by only frequencies in the db should bring more variants than
        filtering by frequencies and by Active genotypes."""
        qs = Variant.objects.using('test')
        freq_filtered = qs.filter(Q(aaf_1kg_all__lte=0.01) | Q(aaf_1kg_all__isnull=True)) \
                          .filter(Q(aaf_esp_all__lte=0.01) | Q(aaf_esp_all__isnull=True))
        ff1 = FrequencyFilter('1kg','all')(0.01, op='<=')
        ff2 = FrequencyFilter('esp','all')(0.01, op='<=')

        fc = FiltersCollection([ff1,ff2])
        res = fc.apply(initqs=qs, db='test')
        self.assertEqual(res.n_filtered, freq_filtered.count())

        gf = GenotypesFilterActive(self.ss)
        fc = FiltersCollection([ff1,ff2,gf])
        res = fc.apply(initqs=qs, db='test')
        self.assertLessEqual(res.n_filtered, freq_filtered.count())


class TestApplyFiltersCollectionCompound(unittest.TestCase):
    """Test FiltersCollection.apply() when the genotypes filter is a compound het"""
    def setUp(self):
        self.ss = samples_selection_factory(db='test',
            groups = {'affected': ['09818','09819'], 'not_affected':['09960','09961']})
        self.qfilter = QualityFilter(op='>=', val='50')
        self.compound = GenotypesFilterCompoundHeterozygous(self.ss)

    def test_apply_with_compound(self):
        fc = FiltersCollection([self.compound])
        var = fc.apply(db='test').variants
        self.assertEqual(var.db, 'test')
        self.assertIsInstance(var, VariantsCollection)
        self.assertTrue(0 < len(var) < NVAR)
        self.assertTrue(hasattr(var[0], 'source'))
        self.assertIn(var[0].source, ['maternal','paternal'])

    def test_apply_sorted_with_compound(self):
        """To filter compound hets, one need to reorder by gene first,
        so the sorting has to be done afterwards. Check that it works."""
        fc = FiltersCollection([self.qfilter, self.compound])
        var = fc.apply(db='test', sort_by='quality').variants
        self.assertIsInstance(var, VariantsCollection)
        self.assertTrue(0 < len(var) < NVAR)
        is_sorted_by_quality = all(var[i].quality <= var[i+1].quality for i in range(len(var)-1))
        self.assertTrue(is_sorted_by_quality)

    def test_apply_with_limit_compound1(self):
        """Should return all filtered variants, as the limit is very high"""
        limit = NVAR
        fc = FiltersCollection([self.qfilter, self.compound])
        var = fc.apply(db='test', limit=limit).variants
        self.assertIsInstance(var, VariantsCollection)
        self.assertTrue(0 < len(var) <= limit)

    def test_apply_with_limit_compound2(self):
        """Should return at most *limit* variants"""
        limit = 2
        fc = FiltersCollection([self.qfilter, self.compound])
        var = fc.apply(db='test', limit=limit).variants
        self.assertIsInstance(var, VariantsCollection)
        self.assertEqual(len(var), limit)

    def test_apply_with_limit_and_offset_compound(self):
        """Should return at most *limit* variants, skipping the first *offset*."""
        limit = 2
        offset = 1
        fc = FiltersCollection([self.qfilter, self.compound])
        var = fc.apply(db='test', limit=limit, offset=offset).variants
        self.assertIsInstance(var, VariantsCollection)
        self.assertEqual(len(var), limit)

    def test_remove_singletons(self):
        """If singletons were not removed, this request would return a list of only paternal variants."""
        qualdfilter = QualDepthFilter(14, op='>=')
        fc = FiltersCollection([qualdfilter, self.compound])
        res = fc.apply(db='test')
        self.assertEqual(len(res.ids), 0)




if __name__ == '__main__':
    unittest.main()
