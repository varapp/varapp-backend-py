import django
django.setup()
from django.test.client import RequestFactory

from varapp.views.main_views import *
from varapp.views.accounts_views import *
from varapp.views.bookmarks_views import *
from varapp.models.users import Users
from varapp.constants.tests import NVAR, NSAMPLES
import unittest, json

REQUEST = RequestFactory().get('','')


class TestMainViews(unittest.TestCase):
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
