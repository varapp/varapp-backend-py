"""
To sync Gemini databases found on disk with
- django.conf.settings.DATABASES
- django.db.connections.databases
- VariantsDb table
When a new db is found, edit the first two to have a direct access,
but also record it to VariantsDb so that the next time the app is loaded,
it can be read from there before any request is made (and already knowing hash etc.).
"""
from varapp.common.db_utils import *
from varapp.models.users import VariantsDb, DbAccess
from django.conf import settings
import os, sys, logging
from os.path import join
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format='%(message)s')

DEBUG = False and settings.DEBUG


## Startup

def activate_if_found_on_disk(vdb):
    if is_valid_vdb(vdb, warn=True):
        logging.info("(+) Activating '{}'.".format(vdb.name))
        add_db(vdb)
        return True
    return False

def deactivate_if_not_found_on_disk(vdb):
    """Return whether it was deactivated."""
    if not is_valid_vdb(vdb, warn=True):
        logging.info("(x) Deactivating '{}'.".format(vdb.name))
        remove_db(vdb)
        return True
    return False

def activate_deactivate_at_gemini_path():
    """Compare VariantsDb with what is found on disk; deactivate if not found.
       If *dbname* is None, checks all VariantDbs."""
    vdbs = VariantsDb.objects.all()
    for vdb in vdbs:
        expected_path = os.path.join(GEMINI_DB_PATH, vdb.filename)
        if is_valid_vdb(vdb, path=expected_path, warn=True):
            if not vdb.is_active:
                logging.info("(+) Activating '{}'.".format(vdb.name))
                add_db(vdb)
        else:
            if vdb.is_active:
                logging.info("(-) Deactivating '{}'.".format(vdb.name))
                remove_db(vdb)

def copy_VariantsDb_to_settings():
    """Store all active VariantDbs into settings.DATABASES (at startup).
       (After that, VariantsDb and settings are in sync,
       and all connections point to valid sqlite databases)."""
    vdbs = VariantsDb.objects.filter(is_active=1)
    added = []
    for vdb in vdbs:
        if settings.DATABASES.get(vdb.name):
            continue
        elif not is_valid_vdb(vdb, warn=True):
            continue
        added.append(vdb.name)
        add_db_to_settings(vdb.name, vdb.filename)
    if added:
        logging.info("(v) Connections: '{}'.".format("','".join(sorted(added))))
    else:
        logging.info("(!) No db was found.")
    return added


## Dynamic

def scan_dir_for_dbs(path=settings.GEMINI_DB_PATH):
    """Return the file names of all sqlite3 databases in *path*."""
    filenames = [x for x in os.listdir(path) if is_sqlite3(join(path, x))]
    return filenames

def add_new_db(path, dbname=None, sha=None, parent_db_id=None):
    """Add a new db found on disk at *path* to both settings and VariantsDb.
    :param sha: hash of the new db.
    """
    assert os.path.exists(path)
    filename = os.path.basename(path)
    dirname = os.path.dirname(path)
    dbname = dbname or db_name_from_filename(filename)
    size = os.path.getsize(path)
    logging.info("(+) Adding '{}' as '{}' to settings and users_db".format(path, dbname))
    add_db_to_settings(dbname, filename)
    newdb,created = VariantsDb.objects.get_or_create(
        name=dbname, filename=filename, location=dirname, is_active=1,
        hash=sha, size=size, visible_name=dbname, parent_db_id=parent_db_id)
    return newdb

def update_db(parent:VariantsDb, newdb:VariantsDb):
    """Deactivate the parent db, deactivate all accesses to the older one,
    and create accesses to the new one for the same users.
    """
    logging.info("(+) Found newer version of '{}'. Replacing.".format(parent.filename))
    # Deactivate the old one
    remove_db(parent)
    # All accesses to the old one to target the new one instead
    old_accesses = DbAccess.objects.filter(variants_db=parent)
    for acc in old_accesses:
        acc.is_active = 0
        acc.save()
        DbAccess.objects.get_or_create(variants_db=newdb, user=acc.user, is_active=1)

def update_if_db_changed(vdb, check_time=True, warn=True):
    """Return whether the db changed.
    :param check_time: if False, skip the timestamp comparison - especially for testing.
    """
    if is_test_vdb(vdb):
        # Changing a hash value in the sqlite makes the hash of the whole sqlite change in turn...
        return False
    new_time = is_source_updated(vdb, warn=warn)
    if new_time or not check_time:
        new_hash = is_hash_changed(vdb, warn=warn)
        if new_hash:
            newdb = add_new_db(vdb_full_path(vdb), vdb.name, new_hash, parent_db_id=vdb.pk)
            update_db(vdb, newdb)   # add a new entry with same filename
            return True
        else:
            logging.info("(v) Same hash for '{}', refresh the updated_time.".format(vdb.name))
            vdb.save()
    return False

def diff_disk_VariantsDb(path=settings.GEMINI_DB_PATH, check_time=True):
    """If a new db is found on disk but is not yet in VariantsDb, add it."""
    def add_new_found_db(filename):
        """Add the new *filename* to VariantsDb and settings"""
        fpath = join(path, filename)
        fsha = sha1sum(fpath)
        # Check if a deactivated db has the same hash. If so, reactivate it
        deac = VariantsDb.objects.filter(filename=filename, is_active=0, hash=fsha)
        if deac.count() > 0:
            logging.info("(+) Reactivating '{}'".format(fsha))
            newdb = deac[0]
            newdb.is_active = 1
            newdb.save()
        else:
            add_new_db(fpath, sha=fsha)

    vdbs = VariantsDb.objects.filter(is_active=1)
    vdb_names = [v.filename for v in vdbs]
    ondisk = scan_dir_for_dbs(path)
    # Add dbs that are newly found on disk
    diff = set(ondisk) - set(vdb_names)
    for fname in diff:
        add_new_found_db(fname)
    # Already existing filenames could be updates. Check SHA hash to update
    for vdb in vdbs:
        update_if_db_changed(vdb, check_time=check_time, warn=True)

