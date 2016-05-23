import unittest
import tempfile
from varapp.constants.tests import TESTDB
from varapp.export import export
from varapp.samples.samples_factory import samples_list_from_db, samples_selection_factory
from varapp.variants.variants_factory import variants_collection_factory


#@unittest.skip('')
class TestExportUtils(unittest.TestCase):
    def setUp(self):
        self.ss = samples_selection_factory(TESTDB, groups='ped')
        self.variants = variants_collection_factory(TESTDB)
        self.N = len(self.variants)

    def test_fetch_resources(self):
        resources = export.fetch_resources(TESTDB)
        self.assertIsInstance(resources, list)
        for x in resources:
            self.assertEqual(len(x), 2)
            #print(x)

    def test_fetch_vcf_header(self):
        header = export.fetch_vcf_header(TESTDB)
        self.assertIsInstance(header, list)
        self.assertEqual(header[-1][:6], '#CHROM')
        #for x in header:
        #    print(x)
        #raise

    def test_export_report(self):
        with tempfile.TemporaryFile(mode='a+') as target:
            params = {'samples': ['affected=09818,09819', 'not_affected=09960,09961'],
                      'order_by': ['ref,DESC'],
                      'limit': ['400'],
                      'offset': ['1'],
                      'filter': ['impact=inframe_insertion,frameshift_variant',
                                 'genotype=compound_het', 'quality>=100']}
            export.export_report([1,2,3,4], target, TESTDB, params)
            target.seek(0)
            report = target.readlines()
            self.assertEqual(len([l for l in report if l.startswith('------')]), 4)
            #for x in report:
            #    print(x.strip('\n'))
            target.seek(0)
            #raise

    def test_export_vcf(self):
        """There should be as many non-comment lines in the exported file as there are variants,
        and each line has 9 mandatory fields + one field per sample.
        """
        with tempfile.TemporaryFile(mode='a+') as target:
            export.export_vcf(self.variants, target, self.ss)
            target.seek(0)
            lines = target.readlines()
            header = [x for x in lines if x[0] == '#'][-1]
            info = [x for x in lines if x[0] != '#']
            self.assertEqual(len(info), self.N)
            target.seek(0)
            self.assertEqual(len(header.split('\t')), 9 + len(self.ss.samples))
            for i in range(1, min(3,self.N)):
                self.assertEqual(len(info[i].split('\t')), 9 + len(self.ss.samples))

    def test_export_tsv(self):
        """There should be as many lines (+1: header) in the exported file as there are variants,
        and each line has as many fields as requested by the *fields* parameter.
        """
        with tempfile.TemporaryFile(mode='a+') as target:
            fields = ['chrom','end','aaf_1kg_all']
            export.export_tsv(self.variants, target, self.ss, fields)
            target.seek(0)
            self.assertEqual(len(target.readlines()), self.N+1)
            target.seek(0)
            header = target.readline().strip()
            self.assertEqual(len(header.split('\t')), len(fields))
            target.seek(0)
            for _ in range(1, min(3,self.N)):
                self.assertEqual(len(target.readline().split('\t')), len(fields))

    def test_export_tsv_genotypes(self):
        """Check that the genotypes are reported to the output, and that they are formatted as expected."""
        samples = samples_list_from_db(db=TESTDB)
        nsamples = len(samples)
        with tempfile.TemporaryFile(mode='a+') as target:
            fields = ['chrom','end','genotypes_index']
            export.export_tsv(self.variants, target, self.ss, fields)
            target.seek(0)
            target.readline()
            for _ in range(1, min(2,self.N)):
                L = target.readline()
                genotypes = L.split('\t')[2].split(',')
                self.assertEqual(len(genotypes), nsamples)

    @unittest.skip('TODO')
    def test_export_tsv_with_source(self):
        """The Source column containing only an SVG, it should still print something readable."""
        # TODO


if __name__ == '__main__':
    unittest.main()
