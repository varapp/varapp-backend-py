#!/usr/bin/env python3

import unittest
import varapp
from varapp.apps import VarappConfig
from django.db import connections
import django.test

class TestStartup(django.test.TestCase):
    """What happens when the app starts"""
    def test_normal(self):
        conf = VarappConfig('varapp', varapp)
        return_code = conf.ready()
        self.assertEqual(return_code, 0)

    def test_no_tables_in_users_db(self):
        c = connections['default'].cursor()
        c.execute("PRAGMA writable_schema = 1")
        c.execute("delete from sqlite_master where type='table'")
        c.execute("PRAGMA writable_schema = 0")
        conf = VarappConfig('varapp', varapp)
        return_code = conf.ready()
        self.assertEqual(return_code, 1)

    @unittest.skip('')
    def test_no_redis(self):
        pass
