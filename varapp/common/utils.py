import sys, random, string, time, functools, os, hashlib, logging
logging.basicConfig(stream=sys.stderr, level=logging.ERROR, format='%(message)s')

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

def normpath(path):
    """Transforms '~/a/b/../c/x to '/home/user/a/c/x'."""
    return os.path.abspath(os.path.normpath(os.path.expanduser(path)))

def check_redis_connection():
    """Return whether I can access the Redis cache."""
    import django.core.cache as django_cache
    import django.core.cache.backends.base
    try:
        redis_cache = django_cache.caches['redis']
    except django_cache.backends.base.InvalidCacheBackendError:
        logging.error("django_redis.cache.RedisCache backend not found")
        return False
    try:
        return 'somekey' in redis_cache or True
    except Exception:
        logging.error("Could not connect to Redis")
        return False




