#!/usr/bin/env python3

import tempfile, sqlite3
import unittest
from varapp.common.manage_dbs import *
from varapp.common.utils import random_string
from varapp.models.users import VariantsDb, DbAccess
from django.core.cache import caches
from django.conf import settings
import django.test

DB_TEST = settings.DB_TEST
TEST_DB_PATH = settings.TEST_DB_PATH


class TestManageDbsUtils(django.test.TestCase):
    def test_scan_dir_for_dbs(self):
        self.assertIn(DB_TEST, scan_dir_for_dbs(TEST_DB_PATH))

    def test_is_on_disk(self):
        self.assertTrue(is_on_disk(DB_TEST, TEST_DB_PATH))

    def test_db_name_from_filename(self):
        self.assertEqual(db_name_from_filename("asdf.db"), "asdf")
        self.assertEqual(db_name_from_filename("asdf.db", "xxx"), "xxx")
        self.assertEqual(db_name_from_filename("aaa/asdf.db"), "asdf")

    def test_vdb_full_path(self):
        vdb = VariantsDb.objects.get(name='test', filename=DB_TEST, is_active=1)
        vdb_path = vdb_full_path(vdb)
        test_path = os.path.join(TEST_DB_PATH, DB_TEST)
        self.assertTrue(os.path.samefile(vdb_path, test_path))

    def test_add_db_to_settings__and_remove(self):
        self.assertNotIn('asdf', settings.DATABASES)
        add_db_to_settings('asdf', 'asdf.db', 'dir')
        self.assertIn('asdf', settings.DATABASES)
        self.assertIn('asdf', connections.databases)
        self.assertEqual(settings.DATABASES.get('asdf')['NAME'], 'dir/asdf.db')
        remove_db_from_settings('asdf')
        self.assertNotIn('asdf', settings.DATABASES)
        self.assertNotIn('asdf', connections.databases)

    def test_remove_db_from_cache(self):
        cache = caches['redis']
        gen_service_cache = caches['genotypes_service']
        cache.set('stats:xx:test:1', 22)
        cache.set('gen:xx:test:1', 22)
        gen_service_cache.set('xx', 22)
        remove_db_from_cache('xx')
        self.assertNotIn('xx', cache.keys('stats:*'))
        self.assertNotIn('xx', cache.keys('gen:*'))
        self.assertNotIn('xx', gen_service_cache)

    def test_remove_db(self):
        cache = caches['redis']
        vdb = VariantsDb.objects.create(name='fff', filename='fff.db', location=TEST_DB_PATH, is_active=1)
        cache.set('stats:fff:test:2', 33)
        settings.DATABASES[vdb.name] = 33
        connections.databases[vdb.name] = 33
        remove_db(vdb)
        self.assertNotIn('fff', settings.DATABASES)
        self.assertNotIn('fff', connections.databases)
        self.assertEqual(len(cache.keys('stats:fff:test:*')), 0)

    def test_is_demo_db(self):
        vdb = VariantsDb.objects.get(filename=DB_TEST, is_active=1)
        self.assertTrue(is_demo_db(vdb))
        vdb.location = os.path.join(vdb.location, '../') # exists
        self.assertFalse(is_demo_db(vdb))
        vdb.location = '/dir'  # does not exist
        self.assertFalse(is_demo_db(vdb))
        vdb2 = VariantsDb(name='asdf')
        self.assertFalse(is_demo_db(vdb2))

    def test_is_demo_db_path(self):
        dbpath = os.path.join(TEST_DB_PATH, DB_TEST)
        self.assertTrue(is_demo_db_path(dbpath))
        self.assertFalse(is_demo_db_path(dbpath+'/..')) # exists
        self.assertFalse(is_demo_db_path(dbpath+'/../x')) # does not exist

    @unittest.skip("How to test that? Both ctime and timestamp are rounded to the second")
    def test_is_newer(self):
        """Create a file, then a VariantsDb, and compare timestamps."""


class TestManageDbsStartup(django.test.TestCase):
    """Test stuff that happens when the app starts -
       comparing the state of the db with what is on disk."""
    def test_deactivate_if_not_found_on_disk(self):
        """Remove one of the sqlites manually: it should get inactivated in VariantsDb."""
        VariantsDb.objects.create(name='xxxx', filename='xxxx.db', location=TEST_DB_PATH, is_active=1)
        deactivate_if_not_found_on_disk()
        vdb = VariantsDb.objects.get(name='xxxx')
        self.assertFalse(vdb.is_active)

    def test_deactivate_if_not_found_on_disk__testdb(self):
        """Should not deactivate the test db."""
        deactivate_if_not_found_on_disk()
        testdb = VariantsDb.objects.get(filename=DB_TEST, is_active=1)
        self.assertTrue(testdb.is_active)

    def test_copy_VariantsDb_to_settings(self):
        """Should fill settings.DATABASES with all connections found in VariantsDb."""
        VariantsDb.objects.create(name='xxxx', filename='xxxx.db', location=TEST_DB_PATH, is_active=1)
        VariantsDb.objects.create(name='yyyy', filename='yyyy.db', location=TEST_DB_PATH, is_active=1)
        copy_VariantsDb_to_settings()
        self.assertIn('test', settings.DATABASES)
        self.assertIn('xxxx', settings.DATABASES)
        self.assertIn('yyyy', settings.DATABASES)
        self.assertIn('test', connections.databases)
        self.assertIn('xxxx', connections.databases)
        self.assertIn('yyyy', connections.databases)


class TestManageDbsDynamic(django.test.TestCase):
    """Test stuff that happens when all dbs are queried -
       comparing the state of the db with what is on disk."""
    def setUp(self):
        self.temp_dbs = set()

    def tearDown(self):
        for db in self.temp_dbs:
            if os.path.exists(db):
                os.remove(db)
            name = db_name_from_filename(db)
            if name in settings.DATABASES:
                settings.DATABASES.pop(name)
            if name in connections.databases:
                connections.databases.pop(name)

    def create_temp_db(self, name, overwrite=False):
        """Create a minimal testing sqlite with a random table name"""
        path = os.path.join(TEST_DB_PATH, name)
        if overwrite:
            if os.path.exists(path):
                os.remove(path)
        conn = sqlite3.connect(path)
        c = conn.cursor()
        tablename = random_string(10)
        c.execute("create table '{}' (id int)".format(tablename))
        self.temp_dbs.add(path)
        return path

    # Actual tests

    def test_add_new_db(self):
        """The new sqlite connection should be added to both settings and VariantsDb"""
        with tempfile.NamedTemporaryFile(dir=TEST_DB_PATH) as target:
            path = target.name
            self.temp_dbs.add(path)
            add_new_db(path, sha='asdf')
            name = db_name_from_filename(path)
            vdb = VariantsDb.objects.filter(filename=os.path.basename(path))
            self.assertEqual(vdb.count(), 1)
            self.assertEqual(vdb[0].hash, 'asdf')
            self.assertTrue(vdb[0].is_active)
            self.assertIn(name, settings.DATABASES)
            self.assertIn(name, connections.databases)

    def test_update_db(self):
        """The parent db should be deactivated, and an access transmitted to the new one"""
        old_vdb = VariantsDb.objects.create(name='asdf', filename='asdf.db', location=TEST_DB_PATH, is_active=1)
        new_vdb = VariantsDb.objects.create(name='xxxx', filename='xxxx.db', location=TEST_DB_PATH, is_active=1)
        DbAccess.objects.create(variants_db=old_vdb, user_id=1, is_active=1)
        update_db(new_vdb, old_vdb)
        self.assertFalse(old_vdb.is_active)
        self.assertTrue(new_vdb.is_active)
        self.assertEqual(DbAccess.objects.filter(variants_db=old_vdb, is_active=1).count(), 0)
        self.assertEqual(DbAccess.objects.filter(variants_db=new_vdb, is_active=1).count(), 1)

    def test_diff_disk_VariantsDb(self):
        """Add a new empty sqlite artificially. It should be added to settings and VariantsDb."""
        filename = 'tmp'+random_string(10)+'.db'
        self.create_temp_db(filename)
        diff_disk_VariantsDb(path=TEST_DB_PATH, check_hash=False)
        dbs = VariantsDb.objects.values_list('filename', flat=True)
        self.assertIn(filename, dbs)

    def test_diff_disk_VariantsDb__update(self):
        """Add two sqlites with the same filename successively. The second one should
        be recognized as an update, deactivate the first one an redirect accesses."""
        filename = 'tmp'+random_string(10)+'.db'

        # Create a first new db
        self.create_temp_db(filename)
        diff_disk_VariantsDb(path=TEST_DB_PATH, check_hash=True)
        # There exists one and only one
        old_vdbs = VariantsDb.objects.filter(filename=filename)
        self.assertEqual(old_vdbs.count(), 1)
        old_vdb = old_vdbs[0]
        # Hash is calculated
        self.assertIsNot(old_vdb.hash, None)
        old_sha = old_vdb.hash
        old_pk = old_vdb.id
        # Set access to test user
        DbAccess.objects.create(variants_db=old_vdb, user_id=1)

        # Create a second one with the same name but different content
        self.create_temp_db(filename)
        diff_disk_VariantsDb(path=TEST_DB_PATH, check_hash=True, check_time=False)
        vdbs = VariantsDb.objects.filter(filename=filename)
        self.assertEqual(vdbs.count(), 2)

        # The older one is still here but inactive
        vdbs = VariantsDb.objects.filter(filename=filename)
        self.assertEqual(vdbs.count(), 2)
        vdbs = VariantsDb.objects.filter(filename=filename, is_active=1)
        self.assertEqual(vdbs.count(), 1)

        # Only the new one is active, and it has a new hash
        vdb = vdbs[0]
        self.assertNotEqual(vdb.pk, old_pk)
        self.assertNotEqual(vdb.hash, old_sha)

        # Accesses have changed hands
        old_accesses = DbAccess.objects.filter(variants_db=old_vdb)
        self.assertEqual(old_accesses.count(), 1)
        old_accesses = DbAccess.objects.filter(variants_db=old_vdb, is_active=1)
        self.assertEqual(old_accesses.count(), 0)
        accesses = DbAccess.objects.filter(variants_db=vdb, is_active=1)
        self.assertEqual(accesses.count(), 1)


if __name__ == '__main__':
    unittest.main()
