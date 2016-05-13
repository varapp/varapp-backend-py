#!/usr/bin/env python3

import unittest
from varapp.common.utils import *

HERE = os.path.abspath(__file__)


class TestUtils(unittest.TestCase):
    def test_normpath(self):
        self.assertTrue(normpath("~/a").startswith('/'))
        self.assertEqual(normpath(HERE), HERE)
        self.assertEqual(normpath("/a/b/../c/d"), "/a/c/d")


if __name__ == '__main__':
    unittest.main()
