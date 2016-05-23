#!/usr/bin/env python3

import tempfile
import unittest
import datetime
from varapp.common.manage_dbs import *
from varapp.common.utils import random_string
from varapp.models.users import VariantsDb, DbAccess
from varapp.data_models.variants import Variant
from django.conf import settings
import django.test

DB_TEST = settings.DB_TEST
TEST_DB_PATH = settings.GEMINI_DB_PATH


class TestManageDbs(django.test.TestCase):
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

    def create_temp_db(self, filename, overwrite=False):
        path = create_dummy_db(filename, path=TEST_DB_PATH, overwrite=overwrite)
        self.temp_dbs.add(path)
        return path

    #------------------------#

    def test_scan_dir_for_dbs(self):
        self.create_temp_db('aaa.db')
        found = scan_dir_for_dbs(TEST_DB_PATH)
        self.assertIn(DB_TEST, found)
        self.assertIn('aaa.db', found)
        self.assertNotIn('asdf', found)

    def test_deactivate_if_not_found_on_disk(self):
        vdb = VariantsDb.objects.create(name='xxxx', filename='xxxx.db', location=TEST_DB_PATH, is_active=1)
        deactivate_if_not_found_on_disk(vdb)
        self.assertFalse(vdb.is_active)

    def test_deactivate_if_not_found_on_disk_all(self):
        """Remove one of the sqlites manually: it should get inactivated in VariantsDb."""
        VariantsDb.objects.create(name='xxxx', filename='xxxx.db', location=TEST_DB_PATH, is_active=1)
        activate_deactivate_at_gemini_path()
        vdb = VariantsDb.objects.get(name='xxxx')
        self.assertFalse(vdb.is_active)

    def test_deactivate_if_not_found_on_disk__testdb(self):
        """Should not deactivate the test db."""
        activate_deactivate_at_gemini_path()
        testdb = VariantsDb.objects.get(filename=DB_TEST, is_active=1)
        self.assertTrue(testdb.is_active)

    def test_copy_VariantsDb_to_settings(self):
        """Should fill settings.DATABASES with all connections found in VariantsDb."""
        VariantsDb.objects.create(name='xxxx', filename='xxxx.db', location=TEST_DB_PATH, is_active=1)
        VariantsDb.objects.create(name='yyyy', filename='yyyy.db', location=TEST_DB_PATH, is_active=1)
        self.create_temp_db('xxxx.db')  # this one exists on disk, 'yyyy.db' does not.
        copy_VariantsDb_to_settings()
        self.assertIn('test', settings.DATABASES)
        self.assertIn('xxxx', settings.DATABASES)
        self.assertNotIn('yyyy', settings.DATABASES)
        self.assertIn('test', connections.databases)
        self.assertIn('xxxx', connections.databases)
        self.assertNotIn('yyyy', connections.databases)

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
        update_db(old_vdb, new_vdb)
        self.assertFalse(old_vdb.is_active)
        self.assertTrue(new_vdb.is_active)
        self.assertEqual(DbAccess.objects.filter(variants_db=old_vdb, is_active=1).count(), 0)
        self.assertEqual(DbAccess.objects.filter(variants_db=new_vdb, is_active=1).count(), 1)

    def test_update_db_cache(self):
        """The parent db's cached items should be deleted"""
        old_vdb = VariantsDb.objects.create(name='asdf', filename='asdf.db', location=TEST_DB_PATH, is_active=1)
        new_vdb = VariantsDb.objects.create(name='xxxx', filename='xxxx.db', location=TEST_DB_PATH, is_active=1)
        DbAccess.objects.create(variants_db=old_vdb, user_id=1, is_active=1)
        cache = caches['redis']
        gen_service_cache = caches['genotypes_service']
        cache.set('stats:asdf:test:1', 22)
        cache.set('gen:asdf:test:1', 22)
        gen_service_cache.set('asdf', 22)
        update_db(old_vdb, new_vdb)
        self.assertNotIn('stats:asdf:test:1', cache.keys('stats:*'))
        self.assertNotIn('gen:asdf:test:1', cache.keys('gen:*'))
        self.assertNotIn('asdf', gen_service_cache)

    def test_diff_disk_VariantsDb(self):
        """Add a new empty sqlite artificially. It should be added to settings and VariantsDb."""
        filename = 'tmp'+random_string(10)+'.db'
        self.create_temp_db(filename)
        diff_disk_VariantsDb(path=TEST_DB_PATH)
        dbs = VariantsDb.objects.values_list('filename', flat=True)
        self.assertIn(filename, dbs)

    def test_update_if_db_changed_testdb(self):
        testdb = VariantsDb.objects.get(filename=DB_TEST)
        changed = update_if_db_changed(testdb)
        self.assertFalse(changed)

    def test_update_if_db_changed(self):
        self.create_temp_db('asdf.db')
        sha1 = sha1sum(os.path.join(TEST_DB_PATH, 'asdf.db'))
        vdb = VariantsDb.objects.create(name='asdf', filename='asdf.db', location=TEST_DB_PATH, is_active=1, hash=sha1)
        changed = update_if_db_changed(vdb, warn=True)
        self.assertFalse(changed)

        # Changing the update time should not have an effect
        update_timestamp = int(time.mktime(vdb.updated_at.timetuple()))
        update_timestamp -= 10  # 10 secs before
        update_time = datetime.datetime.fromtimestamp(update_timestamp)
        vdb.updated_at = update_time   # don't vdb.save() or it updates the updated_time...
        changed = update_if_db_changed(vdb, check_time=True, warn=True)
        self.assertFalse(changed)

        # Change the hash should trigger the update
        # There might have been a save() somewhere else, so set the time back again
        vdb.hash = '1234'
        update_timestamp -= 100
        update_time = datetime.datetime.fromtimestamp(update_timestamp)
        vdb.updated_at = update_time   # don't vdb.save() or it updates the updated_time...
        changed = update_if_db_changed(vdb, check_time=True, warn=True)
        self.assertTrue(changed)

    def test_diff_disk_VariantsDb_update(self):
        """Add two sqlites with the same filename successively. The second one should
        be recognized as an update, deactivate the first one an redirect accesses."""
        filename = 'tmp'+random_string(10)+'.db'

        # Create a first new db
        self.create_temp_db(filename)
        diff_disk_VariantsDb(path=TEST_DB_PATH)
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
        diff_disk_VariantsDb(path=TEST_DB_PATH, check_time=False)
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
