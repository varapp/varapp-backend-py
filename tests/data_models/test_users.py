#!/usr/bin/env python3

import unittest

from django.test.client import RequestFactory

from varapp.data_models.users import *

class TestUser(unittest.TestCase):
    def test_user_constructor(self):
        s = User('A', 'a@a', 'code', '', 1, Person(firstname='A'), Role('guest'))
        self.assertEqual(s.username, 'A')
        self.assertEqual(s.person.firstname, 'A')
        self.assertEqual(s.role.name, 'guest')

    def test_expose(self):
        u = User('A', 'a@a', 'code', '', 1, Person(firstname='A'), Role('guest'))
        self.assertIsInstance(u.expose(), dict)
        self.assertEqual(u.expose()['username'], 'A')


class TestDatabase(unittest.TestCase):
    def test_database_constructor(self):
        d = Database('db', 'path', 'filename', 'sha1', 'desc', 1, 'size', ['A','B'])
        self.assertEqual(d.name, 'db')
        self.assertEqual(d.users[1], 'B')

    def test_expose(self):
        d = Database('db', 'path', 'filename', 'sha1', 'desc', 1, 'size', ['A','B'])
        self.assertIsInstance(d.expose(), dict)
        self.assertEqual(d.expose()['users'][0], 'A')


if __name__ == '__main__':
    unittest.main()

