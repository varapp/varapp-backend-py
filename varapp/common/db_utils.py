from varapp.models.users import VariantsDb
from varapp.common.utils import normpath, random_string, sha1sum
from django.conf import settings
from django.core.cache import caches
from django.db import connections
import os, sys, logging, time, datetime
import sqlite3
from os.path import join
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format='%(message)s')

DEBUG = False and settings.DEBUG
GEMINI_DB_PATH = settings.GEMINI_DB_PATH
TEST_PATH = join(normpath(GEMINI_DB_PATH), settings.DB_TEST)


def table_names(dbname):
    return connections[dbname].introspection.table_names()

def connection_has_tables(dbname, N=0):
    return len(table_names(dbname)) > N

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
    return tables, seen_models

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

def is_on_disk(filename, path=GEMINI_DB_PATH):
    """Check if *path*/*filename* exists on disk."""
    return os.path.exists(join(normpath(path), filename))

def db_name_from_filename(filename, fallback=None):
    """If *filename* has the expected pattern, return a database name.
       Otherwise return the *fallback* name, or finally the original file name without extension."""
    if fallback:
        return fallback
    else:
        return os.path.splitext(os.path.basename(filename))[0]

def vdb_full_path(vdb:VariantsDb):
    """Return an absolute path to the file, filename included, given a dict such as returned by
       `fetch_variant_dbs`, representing one row of VariantsDb."""
    return join(
        normpath(GEMINI_DB_PATH) or '',
        vdb.filename or ''
    )

def add_db_to_settings(dbname, filename, gemini_path=GEMINI_DB_PATH):
    """Add a new db to settings.DATABASES"""
    connection = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': join(gemini_path, filename)
    }
    settings.DATABASES[dbname] = connection
    connections.databases[dbname] = connection
    if DEBUG:
        logging.info("v - Adding connection '{}'".format(dbname))

def remove_db_from_settings(dbname):
    """Remove that connection from settings.DATABASES and connections.databases."""
    settings.DATABASES.pop(dbname, None)
    connections.databases.pop(dbname, None)

def remove_db_from_cache(dbname):
    """Delete all Redis keys related to *dbname*."""
    cache = caches['redis']
    gen_service_cache = caches['genotypes_service']
    cache.delete_pattern("stats:{}:*".format(dbname))
    cache.delete_pattern("gen:{}:*".format(dbname))
    gen_service_cache.delete(dbname, None)

def add_db(vdb:VariantsDb):
    """Add that db to settings, connections, and activate it"""
    vdb.is_active = 1
    vdb.save()
    add_db_to_settings(vdb.name, vdb.filename)

def remove_db(vdb:VariantsDb):
    """Remove that db from settings, connections, cache, and deactivate it."""
    vdb.is_active = 0
    vdb.save()
    remove_db_from_settings(vdb.name)
    remove_db_from_cache(vdb.name)

def is_test_vdb(vdb:VariantsDb):
    """Check if the location and filename of that VariantsDb points to the demo db."""
    vdb_path = join(normpath(GEMINI_DB_PATH), vdb.filename)
    return os.path.exists(vdb_path) and vdb.filename == settings.DB_TEST

def is_test_db(path):
    """Check if *path* points to the demo db."""
    return os.path.exists(TEST_PATH) and os.path.exists(path) and os.path.samefile(normpath(path), TEST_PATH)

def is_source_updated(vdb:VariantsDb, path=None, warn=False):
    """Check if the file at *path* is newer than the VariantsDb *vdb*,
    based on the file timestamp and the vdb updated_at field.
    Return the new Datetime if the source is newer, and False otherwise.
    """
    path = path or vdb_full_path(vdb)
    if not os.path.exists(path):
        return False
    if not vdb.updated_at:
        return True
    fctime = int(os.path.getctime(path))
    vctime = int(time.mktime(vdb.updated_at.timetuple()))
    if fctime > vctime:
        if warn: logging.info("x - '{}' is older than its source at {}".format(vdb.name, path))
        return datetime.datetime.fromtimestamp(fctime)
    else:
        return False

def is_valid_vdb(vdb:VariantsDb, path=None, warn=False):
    """Check that VariantDb entry points to an existing, well-formatted database file."""
    path = path or vdb_full_path(vdb)
    if not is_on_disk(vdb.filename):
        if warn: logging.info("x - '{}' not found on disk at {}.".format(vdb.name, path))
        return False
    elif not is_sqlite3(path):
        if warn: logging.info("x - '{}' is not SQLite.".format(vdb.name))
        return False
    return True

def is_hash_changed(vdb:VariantsDb, path=None, warn=False):
    """Check that the VariantDb hash is the same as that of its source file.
       Fills the hash field if not present.
       Return False if unchanged, or the new hash if it changed."""
    path = path or vdb_full_path(vdb)
    fhash = sha1sum(path)
    if not vdb.hash:
        return True
    if fhash != vdb.hash:
        if warn: logging.info("x - '{}'s hash has changed "
                              "from {} to {} at {}.".format(vdb.name, vdb.hash, fhash, path))
        return fhash
    else:
        return False

def create_dummy_db(filename, path, overwrite=False):
    """Create a minimal testing sqlite with a random table name.
    It is not easy to have a tempfile that has the structure of an sqlite."""
    path = os.path.join(path, filename)
    if overwrite:
        if os.path.exists(path):
            os.remove(path)
    conn = sqlite3.connect(path)
    c = conn.cursor()
    tablename = random_string(10)
    c.execute("CREATE TABLE '{}' (id INT)".format(tablename))
    return path


