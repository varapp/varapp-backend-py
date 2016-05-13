#!/usr/bin/env python3

import unittest
from varapp.samples.samples_factory import *
from varapp.variants.variants_factory import variants_collection_factory
from varapp.variants.genotypes_service import extract_genotypes
from varapp.constants.tests import S09818,S09819,S09960,S09961, NSAMPLES, TESTDB


class TestSamplesSelection(unittest.TestCase):
    def setUp(self):
        self.variants = variants_collection_factory(db=TESTDB)
        self.groups = {'group1': ['09818'], 'group2': ['09819'],
                       'group3': ['09960','09961']}
        self.samples = samples_selection_factory(db=TESTDB, groups=self.groups)
        genotypes = extract_genotypes(db=TESTDB)
        self.genotypes = genotypes[0]

    def test_dont_mutate(self):
        samples = samples_list_from_db(db=TESTDB)
        for s in samples:
            if s.name == '09818':
                self.assertFalse(s.active)
        ss = SamplesSelection(samples, groups={'a': ['09818']})
        for s in ss.samples:
            if s.name == '09818':
                self.assertTrue(s.active)

    def test_define_groups(self):
        samples = samples_list_from_db(db=TESTDB)
        groups = {'affected': ['09818','09819']}
        ss = SamplesSelection(samples, groups)
        for s in ss.samples:
            if s.name in groups['affected']:
                self.assertTrue(s.active)
                self.assertEqual(s.group, 'affected')
            else:
                self.assertFalse(s.active)
                self.assertIs(s.group, None)

    def test_properties(self):
        self.assertIsInstance(self.samples, SamplesSelection)
        self.assertEqual(self.samples.ids, list(range(1,NSAMPLES+1)))
        self.assertEqual(self.samples.names, ['061399', '061400', '09818', '09819', '09960', '09961',
            '101563', '101564', '101565', '101591', '10254', '10255', '13768'])

    def test_len(self):
        self.assertEqual(len(self.samples), 13)

    def test_getitem(self):
        """Get by index, slice, or enumeration."""
        s = self.samples[S09819]
        self.assertIsInstance(s, Sample)
        self.assertEqual(s.name, "09819")

    def test_get(self):
        """Get by name"""
        ss = self.samples.get('09819')
        self.assertEqual(ss.sample_id-1, S09819)

    def test_get_list(self):
        ss = self.samples.get_list(['09818','09819','09960'])
        ids = [x.sample_id-1 for x in ss]
        self.assertEqual(ids, [S09818,S09819,S09960])

    def test_get_group(self):
        group = self.samples.get_group("group3")
        self.assertIsInstance(group, list)
        self.assertEqual(len(group), 2)

    def test_idx_of(self):
        self.assertEqual(self.samples.idx_of('09960'), S09960)

    def test_idxs_of(self):
        self.assertEqual(self.samples.idxs_of(['09960','09961']), [S09960,S09961])

    def test_sort(self):
        ss = self.samples.sort('sample_id')
        self.assertEqual(self.samples.ids, ss.ids)
        ss = self.samples.sort('sample_id', reverse=True)
        self.assertEqual(list(reversed(self.samples.ids)), ss.ids)

    def test_mother_of(self):
        s = self.samples[S09818]
        mother = self.samples.mother_of(s)
        self.assertEqual(mother.name, '09960')

    def test_father_of(self):
        s = self.samples[S09818]
        mother = self.samples.father_of(s)
        self.assertEqual(mother.name, '09961')

    def test_children_of(self):
        s = self.samples.get('09960')
        children = self.samples.children_of(s)
        self.assertEqual(len(children), 2)
        self.assertEqual([x.name for x in children], ['09818','09819'])

    def test_idxs_of_group(self):
        self.assertEqual(self.samples.idxs_of_group('group3'), [S09960,S09961])

    #@unittest.skip('')
    def test_select_x_active(self):
        """Select without specifying a group: should get every active sample
        Not all samples are grouped: those not grouped are inactive.
        """
        groups = {'group1': ['09818'], 'group3': ['09819','09960']}
        ss = SamplesSelection(self.samples, groups)
        selected = ss.select_x_active(self.genotypes)  # no group_name
        self.assertEqual(len(selected), 3)

    def test_fetch_ped_info_groups(self):
        """Once grouped according to the 'phenotype' PED info,
        there should be groups '1' and '2', and nothing without a group."""
        samples = samples_selection_factory(db=TESTDB)
        groups = fetch_ped_info_groups(samples)
        self.assertEqual(len(groups), 2)
        self.assertEqual(sum(len(v) for k,v in groups.items()), len(samples))

    def test_cache_key(self):
        samples = samples_selection_factory(db=TESTDB)

        ss1 = SamplesSelection(samples, {'affected': ['09818','09819']})
        key1 = ss1.cache_key()
        self.assertNotEqual(key1, '')

        ss2 = SamplesSelection(samples, {'affected': ['09818']})
        key2 = ss2.cache_key()
        self.assertNotEqual(key1, key2)

        ss3 = SamplesSelection(samples, {'affected': ['09818','09819'], 'not_affected': ['09960']})
        key3 = ss3.cache_key()
        self.assertNotEqual(key1, key3)

        ss4 = SamplesSelection(samples, {'not_affected': ['09818','09819']})
        key4 = ss4.cache_key()
        self.assertNotEqual(key1, key4)

        ss5 = SamplesSelection(samples, {'affected': ['09819']})
        key5 = ss5.cache_key()
        self.assertNotEqual(key1, key5)

        self.assertEqual(len({key1, key2, key3, key4, key5}), 5)  # all unique

    def test_expose(self):
        self.assertIsInstance(self.samples.expose(), list)
        self.assertIsInstance(self.samples.expose()[0], dict)


if __name__ == '__main__':
    unittest.main()

