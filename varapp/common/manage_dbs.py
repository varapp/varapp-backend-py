"""
To sync Gemini databases found on disk with
- django.conf.settings.DATABASES
- django.db.connections.databases
- VariantsDb table
When a new db is found, edit the first two to have a direct access,
but also record it to VariantsDb so that the next time the app is loaded,
it can be read from there before any request is made (and already knowing hash etc.).
"""
from varapp.common.utils import sha1sum, is_sqlite3, normpath
from varapp.models.users import VariantsDb, DbAccess
from django.db import connections
from django.conf import settings
from django.core.cache import caches
import os, sys, logging, time
from os.path import join
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format='%(message)s')

DEBUG = False and settings.DEBUG
TEST_PATH = join(normpath(settings.TEST_DB_PATH), settings.DB_TEST)


## Utils

def scan_dir_for_dbs(path=settings.GEMINI_DB_PATH):
    """Return the file names of all sqlite3 databases in *path*."""
    filenames = [x for x in os.listdir(path) if is_sqlite3(join(path, x))]
    return filenames

def is_on_disk(filename, path=settings.GEMINI_DB_PATH):
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
        normpath(vdb.location) or '',
        vdb.filename or ''
    )

def add_db_to_settings(dbname, filename, gemini_path=settings.GEMINI_DB_PATH):
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

def remove_db(vdb):
    """Remove that db from settings, connections, cache, and deactivate it."""
    vdb.is_active = 0
    vdb.save()
    remove_db_from_settings(vdb.name)
    remove_db_from_cache(vdb.name)

def is_demo_db(vdb):
    """Check if the location and filename of that VariantsDb points to the demo db."""
    vdb_path = vdb_full_path(vdb)
    return os.path.exists(TEST_PATH) and os.path.exists(vdb_path) and os.path.samefile(vdb_path, TEST_PATH)

def is_demo_db_path(path):
    """Check if *path* points to the demo db."""
    return os.path.exists(TEST_PATH) and os.path.exists(path) and os.path.samefile(normpath(path), TEST_PATH)

def is_newer(path, vdb):
    """Check if the file at *path* is newer than the VariantsDb *vdb*"""
    if not os.path.exists(path):
        return False
    if not vdb.updated_at:
        return True
    fctime = int(os.path.getctime(path))
    vctime = int(time.mktime(vdb.updated_at.timetuple()))
    return fctime > vctime



## Startup

def deactivate_if_not_found_on_disk():
    """Compare VariantsDb with what is found on disk; deactivate if not found."""
    vdbs = VariantsDb.objects.filter(is_active=1)
    for vdb in vdbs:
        if is_demo_db(vdb):
            continue
        if not is_on_disk(vdb.filename, vdb.location):
            path = vdb_full_path(vdb)
            logging.info("x - Db '{}' not found on disk. Deactivating.".format(path))
            remove_db(vdb)

def copy_VariantsDb_to_settings():
    """Store all active VariantDbs into settings.DATABASES (at startup).
       (After that, VariantsDb and settings are in sync)."""
    vdbs = VariantsDb.objects.filter(is_active=1)
    added = []
    for vdb in vdbs:
        if settings.DATABASES.get(vdb.name):
            continue
        elif is_demo_db(vdb):
            # Exclude test db, already present in settings/base.py
            continue
        added.append(vdb.name)
        add_db_to_settings(vdb.name, vdb.filename)
    if added:
        logging.info("v - Copied '{}' to settings.".format("','".join(added)))
    else:
        logging.info("! - No db was found.")


## Dynamic

def update_db(newdb, parent):
    """Deactivate the parent db, deactivate all accesses to the older one,
    and create accesses to the new one for the same users.
    """
    logging.info("Found newer version of '{}'. Replacing.".format(newdb.filename))
    # Deactivate the old one
    parent.is_active = 0
    parent.save()
    remove_db(parent)
    # All accesses to the old one to target the new one instead
    old_accesses = DbAccess.objects.filter(variants_db=parent)
    for acc in old_accesses:
        acc.is_active = 0
        acc.save()
        DbAccess.objects.create(variants_db=newdb, user=acc.user, is_active=1)

def diff_disk_VariantsDb(path=settings.GEMINI_DB_PATH, check_hash=False, check_time=True):
    """If a new db is found on disk but is not yet in VariantsDb, add it.
    :param check_hash: compare SHA hashes of the new dbs with the ones available
         with the same file name to see if there was an update.
    """
    vdbs = VariantsDb.objects.filter(is_active=1)
    vdb_names = [v.filename for v in vdbs]
    ondisk = scan_dir_for_dbs(path)
    diff = set(ondisk) - set(vdb_names)
    # All brand new filenames
    for filename in diff:
        fpath = join(path, filename)
        fsha = sha1sum(fpath) if check_hash else None
        add_new_db(fpath, fsha)
    # Already existing filenames could be updates. Check SHA hash
    if check_hash:
        for vdb in vdbs:
            if is_demo_db(vdb):
                continue
            fpath = join(path, vdb.filename)      # the one on disk
            # Check the creation time. If same as the one in VariantsDb, nothing to do
            if check_time and not is_newer(fpath, vdb):
                continue
            # Compare hashes
            if not vdb.hash:
                vdb.hash = sha1sum(vdb_full_path(vdb))
                vdb.save()
            fsha = sha1sum(fpath)                 # the hash of the one on disk
            if fsha != vdb.hash:
                newdb = add_new_db(fpath, fsha)   # add a new entry with same filename
                update_db(newdb, vdb)             # deactivate the older one

def add_new_db(path, sha=None):
    """Add a new db found on disk at *path* to both settings and VariantsDb.
    :param sha: hash of the new db.
    """
    assert os.path.exists(path)
    filename = os.path.basename(path)
    dirname = os.path.dirname(path)
    dbname = db_name_from_filename(filename)
    size = os.path.getsize(path)
    logging.info("+ - Adding '{}' as '{}' to settings/users_db".format(path, dbname))
    add_db_to_settings(dbname, filename)
    newdb,created = VariantsDb.objects.get_or_create(
        name=dbname, filename=filename, location=dirname, is_active=1,
        hash=sha, size=size, visible_name=dbname)
    return newdb

