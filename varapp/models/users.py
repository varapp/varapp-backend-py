from django.db import models

## Login stuff.
## Care, this stupid Django automatically adds '_id' to foreign key fields,
## e.g. a foreign key named 'variants_db' here corresponds to 'variants_db_id' in the db.


class UsersModel(models.Model):
    """Abstract, to add these fields to all models"""
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    created_by = models.CharField(max_length=50, null=True)
    updated_by = models.CharField(max_length=50, null=True)

    class Meta:
        abstract = True

class Roles(UsersModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    rank = models.IntegerField(null=True)
    can_validate_user = models.IntegerField(default=0)
    can_delete_user = models.IntegerField(default=0)

    class Meta:
        managed = True
        db_table = 'roles'

class People(UsersModel):
    """Extra data on users"""
    id = models.AutoField(primary_key=True)
    firstname = models.CharField(max_length=255)
    lastname = models.CharField(max_length=255)
    institution = models.CharField(max_length=255, null=True)
    street = models.CharField(max_length=255, null=True)
    city = models.CharField(max_length=255, null=True)
    phone = models.CharField(max_length=30, null=True)
    is_laboratory = models.IntegerField(null=True)

    laboratory = models.ForeignKey('People', null=True)

    class Meta:
        managed = True
        db_table = 'people'

class Users(UsersModel):
    id = models.AutoField(primary_key=True)
    username = models.CharField(unique=True, max_length=25)
    password = models.CharField(max_length=255)
    salt = models.CharField(max_length=255, default='')
    email = models.CharField(max_length=255)
    code = models.CharField(max_length=25)
    activation_code = models.CharField(max_length=25, null=True)
    is_active = models.IntegerField(default=1)
    is_password_reset = models.IntegerField(null=True)

    person = models.ForeignKey(People, null=True)
    role = models.ForeignKey(Roles, null=True)

    class Meta:
        managed = True  # If True, Django will create a table on migration
        db_table = 'users'

class VariantsDb(UsersModel):
    """Gemini databases"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    visible_name = models.CharField(max_length=255, null=True)
    filename = models.CharField(max_length=255, null=True)
    location = models.TextField(null=True, default='')
    hash = models.CharField(max_length=255, null=True)
    description = models.TextField(null=True, default='')
    size = models.IntegerField(null=True)
    is_active = models.IntegerField(default=1)

    parent_db = models.ForeignKey('self', null=True)

    class Meta:
        managed = True
        db_table = 'variants_db'

class DbAccess(UsersModel):
    """Many-to-many access of users to databases"""
    id = models.AutoField(primary_key=True)
    is_active = models.IntegerField(default=1)

    user = models.ForeignKey(Users, null=True)
    variants_db = models.ForeignKey(VariantsDb, null=True)

    class Meta:
        managed = True
        db_table = 'db_accesses'

class Preferences(UsersModel):
    """User preferences, such as columns selection"""
    id = models.AutoField(primary_key=True)
    preferences = models.TextField(default='')
    description = models.TextField(default='')
    is_active = models.IntegerField(default=1)

    user = models.ForeignKey(Users, null=True)

    class Meta:
        managed = True
        db_table = 'preferences'

class Annotation(UsersModel):
    """Versions of databases, programs, gemini etc."""
    id = models.AutoField(primary_key=True)
    source = models.CharField(max_length=255, null=True)
    source_version = models.CharField(max_length=255, null=True)
    annotation = models.CharField(max_length=255, null=True)
    annotation_version = models.CharField(max_length=255, null=True)
    is_active = models.IntegerField(default=1)

    variants_db = models.ForeignKey(VariantsDb, null=True)

    class Meta:
        managed = True
        db_table = 'annotation'

class Bookmarks(UsersModel):
    """App states saved by user"""
    id = models.AutoField(primary_key=True)
    query = models.TextField()
    description = models.CharField(max_length=255)
    long_description = models.TextField(default='')
    is_active = models.IntegerField(default=1)

    db_access = models.ForeignKey(DbAccess, null=True)

    class Meta:
        managed = True
        db_table = 'bookmarks'

class History(UsersModel):
    """Record user actions"""
    id = models.AutoField(primary_key=True)
    session_start = models.DateTimeField()
    url = models.TextField()
    query = models.TextField(default='')
    description = models.CharField(max_length=255)
    long_description = models.TextField(default='')
    ip_address = models.CharField(max_length=255)
    is_active = models.IntegerField(default=1)

    user = models.ForeignKey(Users, null=True)

    class Meta:
        managed = True
        db_table = 'history'
