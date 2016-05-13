import unittest

from varapp.annotation.location_service import LocationService
from varapp.annotation.genomic_range import GenomicRange

class TestParseLocation(unittest.TestCase):
    """Try parsing differnt kinds of weird strings with parse_genomic_range.
    They should return all a correct GenomicRange object.
    """
    def test_parse_basic(self):
        r = LocationService.parse_genomic_range("chr1:123-456")
        self.assertIsInstance(r, GenomicRange)
        self.assertEqual(r.chrom, 'chr1')
        self.assertEqual(r.start, 123)
        self.assertEqual(r.end, 456)

        r = LocationService.parse_genomic_range("chr1:0-800000")
        self.assertEqual(r.chrom, 'chr1')
        self.assertEqual(r.start, 0)
        self.assertEqual(r.end, 800000)

    def test_parse_spaces_around(self):
        r = LocationService.parse_genomic_range("  chr1:123-456  ")
        self.assertIsInstance(r, GenomicRange)
        self.assertEqual(r.chrom, 'chr1')
        self.assertEqual(r.start, 123)
        self.assertEqual(r.end, 456)

    def test_parse_uppercase(self):
        r = LocationService.parse_genomic_range("CHR1:123-456")
        self.assertIsInstance(r, GenomicRange)
        self.assertEqual(r.chrom, 'chr1')
        self.assertEqual(r.start, 123)
        self.assertEqual(r.end, 456)

    def test_parse_chrX(self):
        r = LocationService.parse_genomic_range("chrX:123-456")
        self.assertIsInstance(r, GenomicRange)
        self.assertEqual(r.chrom, 'chrX')
        self.assertEqual(r.start, 123)
        self.assertEqual(r.end, 456)

    def test_parse_with_comma(self):
        r = LocationService.parse_genomic_range("chr1:123,456,111-123,456,987")
        self.assertIsInstance(r, GenomicRange)
        self.assertEqual(r.chrom, 'chr1')

    def test_parse_with_spaces_after_colon(self):
        r = LocationService.parse_genomic_range("chr1: 123,456,111-123,456,987")
        self.assertIsInstance(r, GenomicRange)

    def test_parse_with_spaces_after_dash(self):
        r = LocationService.parse_genomic_range("chr1:  123,456,111-  123,456,987")
        self.assertIsInstance(r, GenomicRange)


class TestFindLocation(unittest.TestCase):
    """Check that different kinds of location queries return a correct GenomicRange object."""
    def test_find_chrom_only(self):
        rlist = LocationService(db='test').find("  chr1  ")
        self.assertIsInstance(rlist, list)
        self.assertEqual(len(rlist), 1)
        r = rlist[0]
        self.assertEqual(r.chrom, 'chr1')
        self.assertEqual(r.start, 69510)  # first snp occurrence (select all samples!)
        self.assertEqual(r.end, 167385327) # last snp occurrence

    def test_find_inexistent_feat(self):
        rlist = LocationService(db='test').find("chr77")
        self.assertEqual(rlist, [])

    def test_find_gene(self):
        rlist = LocationService(db='test').find(" NOC2L")
        self.assertIsInstance(rlist, list)
        self.assertEqual(len(rlist), 1)
        r = rlist[0]
        self.assertEqual(r.chrom, 'chr1')
        self.assertEqual(r.start, 879584)  # first snp occurrence
        self.assertEqual(r.end, 894689) # last snp occurrence

    def test_find_gene_2locs(self):
        """This gene is annotated on 2 chromosomes, thus appears at two different locations"""
        rlist = LocationService(db='test').find("AGRN")
        self.assertIsInstance(rlist, list)
        self.assertEqual(len(rlist), 1)
        r = rlist[0]
        self.assertEqual(r.chrom, 'chr1')
        self.assertEqual(r.start, 955503)  # first snp occurrence
        self.assertEqual(r.end, 991496) # last snp occurrence

    def test_autocomplete_name(self):
        suggestions = LocationService(db='test').autocomplete_name("N")
        self.assertEqual(suggestions, ['NADK','NCLN','NCRNA00115','NET15','NET59','NET7','NICALIN','NIR','NOC2L','NPHP4'])

        suggestions = LocationService(db='test').autocomplete_name("NO")
        self.assertEqual(suggestions, ['NOC2L'])

    def test_find_multiple_genes(self):
        rlist = LocationService(db='test').find("AGRN, NOC2L,NIR ,NET7,IDONTEXIST")
        self.assertEqual(len(rlist), 4)

    def test_find_region(self):
        rlist = LocationService(db='test').find("chrX:1-1000000")
        self.assertEqual(len(rlist), 1)

    def test_find_region_2(self):
        rlist = LocationService(db='test').find("chr1:955503-955503")
        self.assertEqual(len(rlist), 1)

    def test_find_region_with_commas(self):
        rlist = LocationService(db='test').find("chr1:955,503-955,503")
        self.assertEqual(len(rlist), 1)

    def test_find_mix(self):
        rlist = LocationService(db='test').find("AGRN,chr2")
        self.assertEqual(len(rlist), 2)

    def test_find_mix_with_commas1(self):
        rlist = LocationService(db='test').find(
            "chr1,chr1:955,503-955,503,AGRN,chr1:955,503-955,503,chr1:955,503-955,503,NIR")
        self.assertEqual(len(rlist), 6)

    def test_find_mix_with_commas2(self):
        rlist = LocationService(db='test').find(
            " chr1:955,503-955,503 ,chr1,AGRN ,  chr1:955,503-955,503, chr1:955,503-955,503,NIR  ")
        self.assertEqual(len(rlist), 6)

    def test_find_with_spaces(self):
        rlist = LocationService(db='test').find(
            "chr1,chr1:  955,503-955,503,AGRN,chr1:955,503-  955,503,chr1: 955,503- 955,503,NIR")
        self.assertEqual(len(rlist), 6)


