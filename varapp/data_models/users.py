"""
Models concerning the login (User, Role, Database, etc.), and their utility functions.
"""

from varapp.models.users import Users, VariantsDb, DbAccess, Roles, People
from varapp.common import manage_dbs
from django.conf import settings
from django.db import connections
import os
import sys, logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(message)s')


def user_factory(u: Users):
    """Create a more useful User instance from a Django Users instance *u*."""
    role = role_factory(u.role)
    person = person_factory(u.person)
    accesses_qs = DbAccess.objects.filter(user=u, is_active=1)
    databases_qs = [acc.variants_db for acc in accesses_qs]
    user_dbs = [database_factory(db) for db in databases_qs if db.is_active]
    databases = []
    for db in user_dbs:
        if not db.name in connections:
            logging.warning("Database '{}' found in users db but not in settings.DATABASES".format(db.name))
            continue
        if not os.path.exists(settings.DATABASES.get(db.name)['NAME']):
            logging.warning("Database '{}' not found on disk!".format(db.name))
            continue
        databases.append(db)
    return User(u.username, u.email, u.code, u.salt, u.is_active, person, role, databases)

def users_list_from_users_db(query_set=None, db='default'):
    """Return a list of `User`s from database content."""
    if query_set is None:
        query_set = Users.objects.using(db).filter()
    return [user_factory(u) for u in query_set]

def database_factory(d: VariantsDb):
    """Create a Database from a users_db.VariantsDb."""
    users = [acc.user.username for acc in DbAccess.objects.filter(variants_db=d)]
    return Database(d.name, d.location, d.filename, d.hash, d.description, d.is_active, d.size, users)

def databases_list(query_set=None, db='default'):
    """Return a list of Database objects, one per active entry in VariantsDb."""
    manage_dbs.deactivate_if_not_found_on_disk_all()
    manage_dbs.diff_disk_VariantsDb()
    if query_set is None:
        query_set = VariantsDb.objects.using(db).filter(is_active=1)
    return [database_factory(d) for d in query_set]

def role_factory(r: Roles):
    """Create a Role from a users_db.Roles."""
    return Role(r.name, r.rank, r.can_validate_user, r.can_delete_user)

def roles_list_from_users_db(query_set=None, db='default'):
    """Create a list of Roles, one per entry in users_db.Roles"""
    if query_set is None:
        query_set = Roles.objects.using(db).all()
    return [role_factory(d) for d in query_set]

def person_factory(p: People):
    """Create a Person from a users_db.People."""
    return Person(p.firstname, p.lastname, p.institution, p.street, p.city, p.phone, p.is_laboratory, p.laboratory)

def persons_list_from_db(query_set=None, db='default'):
    """Return a list of Persons, one per entry in users_db.People"""
    if query_set is None:
        query_set = People.objects.using(db).all()
    return [person_factory(d) for d in query_set]


class User:
    def __init__(self, username, email='', code='', salt='', is_active=0, person=None, role=None, dbs=None):
        self.username = username
        self.email = email
        self.salt = salt
        self.code = code
        self.is_active = is_active
        self.person = person
        self.role = role
        self.databases = dbs  # list of db names

    def expose(self):
        return {
            'username': self.username,
            'email': self.email,
            'code': self.code,
            'isActive': self.is_active,
            'role': self.role.expose(),
            'databases': [d.expose() for d in (self.databases or [])],
            'firstname': self.person.firstname,
            'lastname': self.person.lastname,
        }
    def __str__(self):
        return "<User {}>".format(self.username)


class Database:
    def __init__(self, name, location='', filename='', hashsum='', description='',
                 is_active=None, size=None, users=None):
        self.name = name
        self.location = location
        self.filename = filename
        self.hash = hashsum
        self.description = description
        self.is_active = is_active
        self.size = size
        self.users = users  # list of user names

    def expose(self):
        return {
            'name': self.name,
            'description': self.description,
            'size': self.size,
            'users': self.users,
        }
    def __str__(self):
        return "<Database {}>".format(self.name)


class Role:
    def __init__(self, name, rank=99, can_validate_user=0, can_delete_user=0):
        self.name = name
        self.rank = rank
        self.can_validate_user = can_validate_user
        self.can_delete_user = can_delete_user

    def expose(self):
        return {
            'name': self.name,
            'rank': self.rank,
            'can_validate_user': self.can_validate_user,
            'can_delete_user': self.can_delete_user
        }
    def __str__(self):
        return "<Role {}>".format(self.name)


class Person:
    def __init__(self, firstname='', lastname='', institution='', street='', city='', phone='',
                 is_laboratory=0, laboratory=''):
        self.firstname = firstname
        self.lastname = lastname

    def expose(self):
        return {
            'firstname': self.firstname,
            'lastname': self.lastname,
        }
    def __str__(self):
        return "<Person {} {}>".format(self.firstname, self.lastname)
