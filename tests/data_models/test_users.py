#!/usr/bin/env python3

import unittest
import django.test
from varapp.data_models.users import *
from varapp.models.users import *
from django.conf import settings

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


class TestFactories(django.test.TestCase):
    def test_role_factory(self):
        R = Roles(rank=6)
        r = role_factory(R)
        self.assertIsInstance(r, Role)
        self.assertEqual(r.rank, R.rank)

    def test_person_factory(self):
        P = People(firstname='asdf')
        p = person_factory(P)
        self.assertIsInstance(p, Person)
        self.assertEqual(p.firstname, P.firstname)

    def test_database_factory(self):
        D = VariantsDb.objects.get(filename=settings.DB_TEST)
        d = database_factory(D)
        self.assertIsInstance(d, Database)
        self.assertEqual(d.name, D.name)
        self.assertGreaterEqual(len(d.users), 1)

    def test_user_factory(self):
        R = Roles.objects.create(rank=6)
        P = People.objects.create(firstname='asdf')
        U = Users.objects.create(username='adsf', role=R, person=P, is_active=1)
        D = VariantsDb.objects.get(filename=settings.DB_TEST)
        u = user_factory(U)
        self.assertIsInstance(u, User)
        self.assertEqual(u.username, U.username)
        self.assertGreaterEqual(len(u.databases), 0)

        # Add access to test db - it should reflect in User.databases
        DbAccess.objects.create(user=U, variants_db=D, is_active=1)
        u = user_factory(U)
        self.assertGreaterEqual(len(u.databases), 1)

        # Make the db inactive - it should get ignored again
        D.is_active = 0
        D.save()
        u = user_factory(U)
        self.assertGreaterEqual(len(u.databases), 0)


class TestLists(unittest.TestCase):
    def test_users_list_from_users_db(self):
        L = users_list_from_users_db()
        self.assertGreaterEqual(len(L), 1)
        self.assertIsInstance(L[0], User)

    def test_roles_list_from_users_db(self):
        L = roles_list_from_users_db()
        self.assertGreaterEqual(len(L), 1)
        self.assertIsInstance(L[0], Role)

    def test_persons_list_from_db(self):
        L = persons_list_from_db()
        self.assertGreaterEqual(len(L), 1)
        self.assertIsInstance(L[0], Person)

    def test_databases_list_from_users_db(self):
        L = databases_list_from_users_db()
        self.assertGreaterEqual(len(L), 1)
        self.assertIsInstance(L[0], Database)
        self.assertEqual(L[0].filename, settings.DB_TEST)



if __name__ == '__main__':
    unittest.main()

