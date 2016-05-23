#!/usr/bin/env python3

import tempfile
import unittest
from varapp.common.email import send_email

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


if __name__ == '__main__':
    unittest.main()
