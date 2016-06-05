import django
django.setup()
from django.test.client import RequestFactory

from varapp.views.auth_views import *
from varapp.auth.auth import set_jwt
import unittest

REQUEST = RequestFactory().get('','')


class TestAccounts(unittest.TestCase):
    def test_authenticate(self):
        """Try to login. This view is protected, hence the jwt set up."""
        credentials = 'JWT ' + set_jwt({'username':'test', 'code':'test', 'databases':['test']}, 'abcdefghijklmnopqrs')
        request = RequestFactory().post('/', {'username':'test', 'password':'test'})
        request.META['HTTP_AUTHORIZATION'] = credentials
        response = authenticate(request, db='test')
        self.assertIsInstance(response, JsonResponse)
        self.assertIn(b'id_token', response.content)

    def test_renew_token(self):
        pass

    def test_protected(self):
        pass