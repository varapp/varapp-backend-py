
import threading
import os, sqlite3
from varapp.common.utils import random_string
from varapp.common.db_utils import db_name_from_filename
from django.conf import settings
from django.db import connections
TEST_DB_PATH = settings.GEMINI_DB_PATH

def create_dummy_db(filename, path, overwrite=False):
    """Create a minimal testing sqlite with a random table name.
    It is not easy to have a tempfile that has the structure of an sqlite.
    :param filename: the name of the sqlite.
    :param path: the directory where to put the sqlite file.
    :param overwrite: whether to overwrite an existing file with the same name.
    """
    path = os.path.join(path, filename)
    if overwrite:
        if os.path.exists(path):
            os.remove(path)
    conn = sqlite3.connect(path)
    c = conn.cursor()
    tablename = random_string(10)
    c.execute("CREATE TABLE '{}' (id INT)".format(tablename))
    return path


class TempSqliteContext():
    def __init__(self, filename, path=TEST_DB_PATH, overwrite=False):
        self.filename = filename
        self.path = path
        self.overwrite = overwrite
        self.fullpath = os.path.join(self.path, self.filename)

    def __enter__(self):
        create_dummy_db(self.filename, path=self.path, overwrite=self.overwrite)
        return self.fullpath

    def __exit__(self, return_type, return_value, traceback):
        if os.path.exists(self.fullpath):
            os.remove(self.fullpath)
        name = db_name_from_filename(self.filename)
        if name in settings.DATABASES:
            settings.DATABASES.pop(name)
        if name in connections.databases:
            connections.databases.pop(name)


def with_concurrency(times):
    """
    Add this decorator to small pieces of code that you want to test
    concurrently to make sure they don't raise exceptions when run at the
    same time.  E.g., some Django views that do a SELECT and then a subsequent
    INSERT might fail when the INSERT assumes that the data has not changed
    since the SELECT.

    To use this in a test, create a small function that includes the thread-safe code inside your test.
    Apply the decorator, passing the number of times you want to run the code simultaneously,
    and then call the function::

        class MyTestCase(TestCase):
            def testRegistrationThreaded(self):
                url = reverse('toggle_registration')
                @test_concurrently(15)
                def toggle_registration():
                    # perform the code you want to test here; it must be thread-safe
                    # (e.g., each thread must have its own Django test client)
                    c = Client()
                    c.login(username='user@example.com', password='abc123')
                    response = c.get(url)
                toggle_registration()

    Source: https://www.caktusgroup.com/blog/2009/05/26/testing-django-views-for-concurrency-issues/
    """
    def test_concurrently_decorator(test_func):
        def wrapper(*args, **kwargs):
            exceptions = []
            def call_test_func():
                try:
                    test_func(*args, **kwargs)
                except Exception as e:
                    exceptions.append(e)
                    raise
            threads = []
            for i in range(times):
                threads.append(threading.Thread(target=call_test_func))
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            if exceptions:
                raise Exception('test_concurrently intercepted %s exceptions: %s' % (len(exceptions), exceptions))
        return wrapper
    return test_concurrently_decorator