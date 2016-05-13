#!/usr/bin/env python3

import tempfile
import unittest

from varapp.common.genotypes import *
from varapp.common.email import send_email
from varapp.constants.tests import *
from varapp.variants.variants_factory import variants_collection_factory


class TestEmail(unittest.TestCase):
    def test_send_email(self):
        with tempfile.TemporaryFile(mode='a+') as target:
            message = '<div>aaaa</div>'
            send_email('julien.delafontaine@isb-sib.ch', 'test email from varapp',
                       text=message, html=message, tofile=target)
            target.seek(0)
            content = target.readlines()
            self.assertTrue(message in ' '.join(content))
        # Send to real email
        #send_email('julien.delafontaine@isb-sib.ch', 'test email from varapp', message)

class TestEncodeDecode(unittest.TestCase):
    def setUp(self):
        self.variants = variants_collection_factory('test')
        self.v1 = self.variants[0]
        self.v8 = self.variants[8]

    def test_decode(self):
        gts = decode(self.v1.gts_blob)
        self.assertEqual(len(gts), NSAMPLES)

    def test_decode_int(self):
        gts = decode_int(self.v1.gt_types_blob)
        self.assertEqual(len(gts), NSAMPLES)
        self.assertIsInstance(gts[0], int)

    def test_compress_decompress(self):
        """Check that encoding an array and redecoding returns the initial array."""
        x = [0,0,1,2,3,0]
        self.assertEqual(unpack_genotype_blob(zdumps(x)), x)

        x = ['A/C', 'A/C', 'A/A', 'A/C', 'A/A', 'A/C']
        self.assertEqual(unpack_genotype_blob(zdumps(x)), x)


if __name__ == '__main__':
    unittest.main()

