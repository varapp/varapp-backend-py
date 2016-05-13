import random, string, time, functools, os, hashlib


def inspect_db(dbname=''):
    """Debugging tool: print the table names and available models for that db."""
    from django.db import connections, connection
    if dbname:
        tables = connections[dbname].introspection.table_names()
        seen_models = connections[dbname].introspection.installed_models(tables)
    else:
        tables = connection.introspection.table_names()
        seen_models = connection.introspection.installed_models(tables)
    print('Tables: ',tables)
    print('Models:', seen_models)

def random_string(N=20):
    return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(N))

def timer(function):
    """ A decorator that makes the decorated *function* return its execution time."""
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        t1 = time.time()
        result = function(*args, **kwargs)
        t2 = time.time()
        print("  @time '{}': {:.4f} s.".format(str(function), t2-t1))
        return result
    return wrapper

class Timer(object):
    """Use as a context manager:

       with Timer() as t:
           <block>
    """
    def __init__(self, verbose=True):
        self.verbose = verbose

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.secs = self.end - self.start
        self.msecs = self.secs  # millisecs
        if self.verbose:
            print("@Timer: {:.5f} s".format(self.msecs))

def sha1sum(filename, blocksize=65536):
    """Calculate the SHA1 hash of that file"""
    hasher = hashlib.sha1()
    if not os.path.exists(filename):
        return
    with open(filename, 'rb') as f:
        for block in iter(lambda: f.read(blocksize), b''):
            hasher.update(block)
    return hasher.hexdigest()

def is_sqlite3(filename):
    """Return whether the file is an sqlite3 database."""
    if not os.path.isfile(filename):
        return False
    if os.path.getsize(filename) < 100: # SQLite database file header is 100 bytes
        return False
    with open(filename, 'rb') as fd:
        header = fd.read(100)
    checks = header[:16] == 'SQLite format 3\x00' or header[:16] == b'SQLite format 3\000'  # bytes for python3
    return checks

def normpath(path):
    """Transforms '~/a/b/../c/x to '/home/user/a/c/x'."""
    return os.path.abspath(os.path.normpath(os.path.expanduser(path)))

