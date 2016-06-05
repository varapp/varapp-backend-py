import django
django.setup()
from django.test.client import RequestFactory
import django.test

from varapp.views.accounts_views import *
from varapp.models.users import Users
from varapp.common.manage_dbs import *
import unittest, tempfile, json

from django.conf import settings
EMPTY_REQUEST = RequestFactory().get('','')
TEST_DB_PATH = settings.GEMINI_DB_PATH


class TestAccounts(django.test.TestCase):
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

    #---------------------------------------#

    def test_get_roles_info(self):
        response = get_roles_info(EMPTY_REQUEST)
        content = json.loads(response.content.decode())
        self.assertGreaterEqual(len(content), 4)
        self.assertIn('superuser', content)

    def test_get_users_info(self):
        response = get_users_info(EMPTY_REQUEST)
        content = json.loads(response.content.decode())
        self.assertGreaterEqual(len(content), 1)
        self.assertIn('test', [x['username'] for x in content])

    def test_get_dbs_info(self):
        """Important entry point: called when the Admin page is accessed.
        What happens then a db gets added or removed before the view is called."""
        response = get_dbs_info(EMPTY_REQUEST)
        content = json.loads(response.content.decode())
        self.assertGreaterEqual(len(content), 1)
        self.assertIn('test', [x['name'] for x in content])

    def test_get_dbs_info__add_remove(self):
        # Create a new one
        response = get_dbs_info(EMPTY_REQUEST)
        content = json.loads(response.content.decode())
        ndbs = len(content)

        path = self.create_temp_db('asdf.db')
        response = get_dbs_info(EMPTY_REQUEST)
        content = json.loads(response.content.decode())
        self.assertGreaterEqual(len(content), 2)
        self.assertIn('asdf', [x['name'] for x in content])

        os.remove(path)
        response = get_dbs_info(EMPTY_REQUEST)
        content = json.loads(response.content.decode())
        self.assertEqual(len(content), ndbs)

    @unittest.skip('mock it')
    def test_signup(self):
        request = RequestFactory().post('/test/signup',
                                        {'username':'temp', 'password':'temp', 'email':'temp@test',
                                         'firstname':'', 'lastname':'', 'phone': ''})
        with tempfile.TemporaryFile(mode='a+') as target:
            signup(request, email_to_file=target)
            target.seek(0)
            content = target.readlines()
        self.assertTrue("Your account 'temp' has been created" in ' '.join(content))

    @unittest.skip('mock it (it changes the validation_code)')
    def test_reset_password_request(self):
        """Send a request to reset password"""
        request = RequestFactory().post('/test/resetPassword',
                                        {'username':'test', 'email':'julien.delafontaine@isb-sib.ch'})
        with tempfile.TemporaryFile(mode='a+') as target:
            reset_password_request(request, email_to_file=target)
            target.seek(0)
            content = target.readlines()
        self.assertTrue('You asked for a new password' in ' '.join(content))

    @unittest.skip('mock it')
    def test_change_password(self):
        """Send a request to validate password change"""
        request = RequestFactory().get('/test/changePassword',
                                       {'username':'temp', 'email':'temp@test'})

        # Reset it first to a random one
        with tempfile.TemporaryFile(mode='a+') as target:
            change_password(request, email_to_file=target)
            target.seek(0)
            content = target.readlines()
        self.assertTrue('Your varapp password has been reset' in ' '.join(content))

        # Put it back
        with tempfile.TemporaryFile(mode='a+') as target:
            change_password(request, new_password='temp', email_to_file=target)
        self.assertEqual(Users.objects.get(username='temp').password, 'K6NESq3C4r5zA')

    def test_change_attribute(self):
        pass

    def test_user_activation(self):
        pass

    @unittest.skip('mock it')
    def test_delete_user(self):
        code = Users.objects.get(username='temp')
        request = RequestFactory().get('/test/deleteUser',
                                       {'username':'temp', 'code':code})
        self.assertEqual(Users.objects.filter(username='temp'), [])

    def test_attribute_db(self):
        pass


if __name__ == '__main__':
    unittest.main()

