#!/usr/bin/env python3

import unittest
from django.test.client import RequestFactory
from varapp.models.gemini import Variants
from varapp.variants.variants_factory import variants_collection_factory
from varapp.filters.pagination import Pagination, pagination_from_request


#@unittest.skip('')
class TestPagination(unittest.TestCase):
    def setUp(self):
        self.rf = RequestFactory()
        self.variants_django = Variants.objects.using('test').all()
        self.variants = variants_collection_factory(db='test')

    #@unittest.skip('')
    def test_limit(self):
        """Limiting to N results should return N elements."""
        N = 10
        var = list(Pagination(limit=N).limit(self.variants_django))
        self.assertEqual(len(var), N)
        var = list(Pagination(limit=N).limit(self.variants))
        self.assertEqual(len(var), N)

    #@unittest.skip('')
    def test_offset(self):
        """Skipping the first N from M+N results should return M elements."""
        N = 10; M = 30
        var = list(Pagination(offset=N).offset(self.variants[:(N+M)]))
        self.assertEqual(len(var), M)

    #@unittest.skip('')
    def test_paginate(self):
        """Offsetting by N, then taking the first M should return M elements,
        the first of which should be the Nth of the original list."""
        N = 10; M = 30
        pagination = Pagination(limit=M, offset=N)
        var = pagination.paginate(self.variants)
        self.assertEqual(len(var), M)
        self.assertEqual(var[0].variant_id, self.variants[N].variant_id)

        var = list(pagination.paginate(self.variants))
        self.assertEqual(len(var), M)
        self.assertEqual(var[0].variant_id, self.variants[N].variant_id)


    def test_pagination_from_request_fullparams(self):
        """Both lim+offset are passed"""
        request = self.rf.get('/', {'limit':'10', 'offset':30})
        pagination = pagination_from_request(request)
        self.assertEqual(pagination.off, 30)
        self.assertEqual(pagination.lim, 10)

    def test_pagination_from_request_limit(self):
        """Default offset shall be 0"""
        request = self.rf.get('/', {'limit':'10'})
        pagination = pagination_from_request(request)
        self.assertEqual(pagination.off, 0)

    def test_pagination_from_request_offset(self):
        """If no limit argument is passed, lim shall be set to None"""
        request = self.rf.get('/', {'offset':'30'})
        pagination = pagination_from_request(request)
        self.assertEqual(pagination.lim, None)
        self.assertEqual(pagination.off, 30)

    #@unittest.skip('')
    def test_pagination_from_request(self):
        """Offsetting by N, then taking the first M should return M elements,
        the first of which should be the Nth of the original list."""
        N = 10; M = 30
        request = self.rf.get('', {'offset':str(N), 'limit':str(M)})
        pagination = pagination_from_request(request)
        var = list(pagination.paginate(self.variants))
        self.assertEqual(len(var), M)
        self.assertEqual(var[0].variant_id, self.variants[N].variant_id)


if __name__ == '__main__':
    unittest.main()

