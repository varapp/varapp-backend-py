import unittest

from varapp.annotation.annotation_service import *
from varapp.annotation.genomic_range import GenomicRange

class TestGeneSummaryService(unittest.TestCase):
    def setUp(self):
        self.gs = GeneSummaryService(db='test')

    def test_find_chrom(self):
        loc = self.gs['chr6']['location']
        self.assertIsInstance(loc, list)
        self.assertIsInstance(loc[0], GenomicRange)
        self.assertEqual(loc[0].chrom, 'chr6')

    def test_find_gene_symbol(self):
        """hg19 / GRCh37, HUNK gene:
        http://feb2014.archive.ensembl.org/Homo_sapiens/Gene/Splice?g=ENSG00000142149;r=21:31873315-32044633
        """
        loc = self.gs['HUNK']['location']
        self.assertIsInstance(loc, list)
        symbol = loc[0]
        self.assertIsInstance(symbol, GenomicRange)
        self.assertEqual(symbol.chrom, 'chr21')
        self.assertEqual(symbol.start, 33245628)
        self.assertEqual(symbol.end, 33416946)

