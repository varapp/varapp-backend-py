import django
django.setup()
from django.test.client import RequestFactory

from varapp.views.views import *
from varapp.views.accounts import *
from varapp.views.bookmarks import *
from varapp.views.auth import *
from varapp.auth import set_jwt
from varapp.models.users import Users
from varapp.constants.tests import NVAR, NSAMPLES
import unittest, json, tempfile

REQUEST = RequestFactory().get('','')


#@unittest.skip('')
class TestAppControllers(unittest.TestCase):
    def test_helloworld(self):
        """The root path says hello."""
        request = RequestFactory().get('/','')
        response = index(request)
        self.assertEqual(response.content.decode(), "Hello World !\n")

    def test_get_users_info(self):
        """get_users_info() returns all available users"""
        response = get_users_info(REQUEST, db='test')
        data = json.loads(response.content.decode())
        testuser = [x for x in data if x['username']=='test'][0]
        self.assertIn('test', [d['name'] for d in testuser['databases']])
        self.assertEqual(testuser['role']['name'], 'guest')

    def test_get_dbs_info(self):
        """get_dbs_info() returns all available databases"""
        response = get_dbs_info(REQUEST, db='test')
        data = json.loads(response.content.decode())
        dbnames = [x['name'] for x in data]
        self.assertIn('test', dbnames)
        testdb = [x for x in data if x['name']=='test'][0]
        self.assertEqual(testdb['description'], 'test DB')

    def test_get_roles_info(self):
        """get_roles_info() returns all available roles"""
        response = get_roles_info(REQUEST, db='test')
        data = json.loads(response.content.decode())
        self.assertSequenceEqual(data, ['superuser','admin','head','guest'])

    def test_samples(self):
        """Samples() returns the list of all samples"""
        response = samples(REQUEST, db='test')
        data = json.loads(response.content.decode())
        self.assertTrue(len(data) > 0)
        self.assertEqual(data[0]['name'], "061399")

    def test_count(self):
        """Count() returns the total number of variants."""
        response = count(None, db='test')
        data = json.loads(response.content.decode())
        self.assertEqual(int(data), NVAR)

    def test_variants(self):
        """Variants() query variants according to the given filters and pagination."""
        N = 5
        request = RequestFactory().get('/test/variants/', {'limit':str(N), 'filter':'in_dbsnp=0'})
        response = variants(request, db='test')
        data = json.loads(response.content.decode())
        self.assertEqual(data['filters'], ['<Filter in_dbsnp=False>'])
        self.assertEqual(len(data['variants']), N)
        self.assertEqual(len(data['variants'][0]['genotypes_index']), NSAMPLES)

    def test_variants2(self):
        """Variants() query variants according to the given filters and pagination."""
        quality = Variant.objects.using('test').values_list('quality', flat=True)[0]
        request = RequestFactory().get('/test/variants/', {'filter':'quality=='+str(quality)})
        response = variants(request, db='test')
        data = json.loads(response.content.decode())
        self.assertGreaterEqual(len(data['variants']), 1)

    def test_stats(self):
        """Stats() returns statistics over the complete variants dataset.
        Just to run it ; already tested in stats_service."""
        response = stats(REQUEST, db='test')
        json.loads(response.content.decode())

    def test_get_bookmarks(self):
        user = Users.objects.get(username='test')
        response = get_bookmarks(REQUEST, db='test', user=user)
        data = json.loads(response.content.decode())
        self.assertIsInstance(data, list)

    @unittest.skip("mock it")
    def test_set_bookmark(self):
        set_bookmark(REQUEST, db='test')

    @unittest.skip("TODO")
    def test_location_find(self):
        """Location_find() returns genomic ranges from a string composed of
        ranges and gene names."""
        pass

    @unittest.skip("TODO")
    def test_location_names_autocomplete(self):
        """"""
        pass

    def test_export_annovar(self):
        """Export_variants(format='annovar') does not produce an error."""
        request = RequestFactory().get('/test/variants/export', {'format':'annovar'})
        response = export_variants(request, db='test')
        self.assertIsInstance(response, HttpResponse)
        self.assertIn('Content-Disposition', response)

    def test_export_tsv(self):
        """Export_variants(format='tsv', fields=...) does not produce an error."""
        request = RequestFactory().get('/test/variants/export',
            {'format':'annovar', 'fields':'chrom,end,hgvs_c,ensembl_gene_id,genotypes_index,source',
             'filter':'genotype=compound_het'})
        response = export_variants(request, db='test')
        self.assertIsInstance(response, HttpResponse)
        self.assertIn('Content-Disposition', response)

    def test_export_vcf(self):
        """Export_variants(format='tsv', fields=...) does not produce an error."""
        request = RequestFactory().get('/test/variants/export', {'format':'vcf'})
        response = export_variants(request, db='test')
        self.assertIsInstance(response, HttpResponse)
        self.assertIn('Content-Disposition', response)

    def test_export_report(self):
        """Export_variants(format='tsv', fields=...) does not produce an error."""
        request = RequestFactory().get('/test/variants/export', {'format':'report',
            'samples':'affected=09960', 'filter':'genotype=active'})
        response = export_variants(request, db='test')
        self.assertIsInstance(response, HttpResponse)
        self.assertIn('Content-Disposition', response)


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

