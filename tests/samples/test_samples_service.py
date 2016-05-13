#!/usr/bin/env python3

import unittest
from django.test.client import RequestFactory
from varapp.data_models.samples import Sample, SamplesSelection
from varapp.models.gemini import Samples
from varapp.samples.samples_service import samples_service
from varapp.samples.samples_factory import *
from varapp.constants.tests import NSAMPLES
from varapp.samples.samples_service import samples_selection_from_request

class TestSample(unittest.TestCase):
    def test_sample(self):
        s = Sample('A', sample_id=0)
        self.assertEqual(s.sample_id, 0)
        self.assertEqual(s.name, 'A')

    def test_expose(self):
        s = Sample('A', sample_id=0)
        self.assertIsInstance(s.expose(), dict)
        self.assertEqual(s.expose()['name'], 'A')


class TestSamplesSelectionFactory(unittest.TestCase):
    def test_sample_factory(self):
        """Convert one Django `Samples` object to a `Sample`."""
        django_s = Samples.objects.using('test').all()[0]
        model_s = sample_factory(django_s)
        self.assertIsInstance(model_s, Sample)

    def test_samples_list_from_db(self):
        samples = samples_list_from_db(db='test')
        self.assertIsInstance(samples, list)
        self.assertIsInstance(samples[0], Sample)

    def test_samples_selection_factory(self):
        """Create a `SamplesSelection` from the database content."""
        ss = samples_selection_factory(db='test')
        self.assertIsInstance(ss, SamplesSelection)
        self.assertEqual(list.__len__(ss.samples), NSAMPLES)

    def test_samples_selection_from_samples_list(self):
        """Create a SamplesSelection from a list of `Sample`s."""
        samples = [Sample('a'), Sample('b')]
        ss = SamplesSelection(samples)
        self.assertEqual(len(ss.samples), 2)

    def test_samples_selection_from_request(self):
        """Create a SamplesSelection from groups dessribed in URL."""
        request = RequestFactory().get('', [('samples','group1=09818'),
                                            ('samples','group2=09819'), ('samples','group3=09960,09961')])
        ss = samples_selection_from_request(request, db='test')
        self.assertIsInstance(ss, SamplesSelection)

    def test_samples_service(self):
        """Create a cache service for a SamplesSelection."""
        ss = samples_service('test').all()
        self.assertIsInstance(ss, SamplesSelection)
        self.assertEqual(len(ss.samples), NSAMPLES)


if __name__ == '__main__':
    unittest.main()
