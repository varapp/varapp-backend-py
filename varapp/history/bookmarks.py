
from varapp.models.users import Bookmarks, VariantsDb, DbAccess

def format_datetime(t):
    """Transform a datetime.datetime object *t* to a string."""
    return t.strftime('%d/%m/%Y %H:%M:%S %p')

def get_bookmarks(user, dbname):
    """
    :param user: the current user, sending this request.
    :param dbname: the database bookmarks point to - not the db to read from !
    """
    db = VariantsDb.objects.get(name=dbname, is_active=1)
    db_access = DbAccess.objects.get(user=user, variants_db=db, is_active=1)
    bks = [{
               'url': h.query,
               'description': h.long_description,
               'time': int(h.description),
           }
           for h in Bookmarks.objects.filter(db_access=db_access, is_active=1).order_by('created_at')]
    return bks

def delete_bookmark(user, timeMillis, dbname):
    """Remove bookmark at the given time"""
    db = VariantsDb.objects.get(name=dbname, is_active=1)
    db_access = DbAccess.objects.get(user=user, variants_db=db, is_active=1)
    bk = Bookmarks.objects.get(db_access=db_access, description=str(timeMillis))
    bk.is_active = False
    bk.save()

def set_bookmark(user, query, timeMillis, text, dbname):
    """
    :param user: the current user, sending this request.
    :param query: (str) a unique representation of the browser state.
    :param timeMillis: (int) the creation time of the bookmark, in milliseconds.
    :param dbname: the database concerned by this url - not the db to write to !
    """
    db = VariantsDb.objects.get(name=dbname, is_active=1)
    db_access = DbAccess.objects.get(user=user, variants_db=db, is_active=1)
    Bookmarks.objects.create(db_access=db_access, query=query,
        description=timeMillis, long_description=text, created_by=user.username, updated_by=user.username)
