
import unittest
from varapp.auth.auth import *

class TestValidators(unittest.TestCase):
    def test_validate_username(self):
        for username in ['username', 'user_name', 'user.name', 'user-name', 'UsErNaMe', 'user@name']:
            isvalid = validate_username(username)
            self.assertTrue(isvalid)
        for username in ['-username', '.username', '<user></name>', 'user?name']:
            isvalid = validate_username(username)
            self.assertFalse(isvalid)

    def test_validate_email(self):
        for email in ['test@test.com', 'j.d@isb-sib.ch', 'TeSt@UNIL.ch']:
            isvalid = validate_email(email)
            self.assertTrue(isvalid)
        for email in ['test@test', 'j-d@isb-sib', 'test', '@test.ch', 'test@', 'test.test']:
            isvalid = validate_email(email)
            self.assertFalse(isvalid)

    def test_user_exists(self):
        self.assertTrue(check_user_exists('test','test'))
        self.assertFalse(check_user_exists('test2','test'))
        self.assertFalse(check_user_exists('test','test2'))


if __name__ == '__main__':
    unittest.main()
