import django
django.setup()
from django.test.client import RequestFactory

from varapp.views.accounts_views import *
from varapp.views.auth_views import *
from varapp.auth.auth import set_jwt
from varapp.models.users import Users
import unittest, tempfile

REQUEST = RequestFactory().get('','')


class TestAccounts(unittest.TestCase):
    """This suite creates a test user 'temp', acts on it, then removes it."""
    def test_authenticate(self):
        """Try to login. This view is protected, hence the jwt set up."""
        credentials = 'JWT ' + set_jwt({'username':'test', 'code':'test', 'databases':['test']}, 'abcdefghijklmnopqrs')
        request = RequestFactory().post('/', {'username':'test', 'password':'test'})
        request.META['HTTP_AUTHORIZATION'] = credentials
        response = authenticate(request, db='test')
        self.assertIsInstance(response, JsonResponse)
        self.assertIn(b'id_token', response.content)

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
    def test_signup(self):
        request = RequestFactory().post('/test/signup',
                                        {'username':'temp', 'password':'temp', 'email':'temp@test',
                                         'firstname':'', 'lastname':'', 'phone': ''})
        with tempfile.TemporaryFile(mode='a+') as target:
            signup(request, email_to_file=target)
            target.seek(0)
            content = target.readlines()
        self.assertTrue("Your account 'temp' has been created" in ' '.join(content))

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

    @unittest.skip('mock it')
    def test_delete_user(self):
        code = Users.objects.get(username='temp')
        request = RequestFactory().get('/test/deleteUser',
                                       {'username':'temp', 'code':code})
        self.assertEqual(Users.objects.filter(username='temp'), [])


if __name__ == '__main__':
    unittest.main()

