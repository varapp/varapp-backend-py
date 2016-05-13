"""
Methods that modify the users database
"""

import datetime, re, warnings, crypt
import logging, sys
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(message)s')

import jwt
from django.conf import settings

from varapp.common import utils
from varapp.common.email import send_email
from varapp.models.users import Users, VariantsDb, DbAccess, People, Roles


USER_NOT_FOUND_WITH_EMAIL_MSG = "No account was found with this username and email"
USER_NOT_FOUND_MSG = "No account was found with this username"
DEFAULT_ROLE = "demo"  # role given on account creation


def validate_username(username):
    pattern = r"^[\w][A-zÀ-ú0-9-.@_ ]*$"
    return re.match(pattern, username)

def validate_email(email):
    p1 = r"[\w!#$%&'*+/=?^_`{|}~-]+(?:\.[\w!#$%&'*+/=?^_`{|}~-]+)*"  # address
    p2 = r"@(?:\w(?:[\w-]*\w)?\.)+\w(?:[\w-]*\w)?"                   # @domain.ext
    pattern = re.compile(p1+p2, re.I)
    return re.match(pattern, email)

def check_user_exists(username, code):
    """Check that a user with this username and code exists, and that it is active."""
    return len(Users.objects.filter(username=username, code=code, is_active=1)) > 0

def check_can_access_db(user, dbname):
    db = VariantsDb.objects.get(name=dbname, is_active=1)
    access = DbAccess.objects.filter(user=user, variants_db=db, is_active=1)
    return len(access) > 0

def find_user(username, code, require_active=True):
    """Return the unique active User with that username and private code, or None if not found"""
    try:
        if require_active:
            return Users.objects.get(username=username, code=code, is_active=1)
        else:
            return Users.objects.get(username=username, code=code)
    except Users.DoesNotExist:
        warnings.warn("No account was found with username '{}' and private code".format(username))
        return None

def find_user2(username, email, require_active=True):
    """Return the unique active User with that username and email, or None if not found"""
    try:
        if require_active:
            return Users.objects.get(username=username, email=email, is_active=1)
        else:
            return Users.objects.get(username=username, email=email)
    except Users.DoesNotExist:
        warnings.warn("No account was found with username '{}' and email '{}'".format(username, email))
        return None

def check_credentials(username, password):
    """Compare the crypted password of this user with the one stored in the db.
    Return the User instance if authenticated successfully.
    """
    users_with_that_name = Users.objects.filter(username=username)
    if not users_with_that_name:
        return [None, "User '{}' does not exist".format(username)]
    active_users_with_that_name = users_with_that_name.filter(is_active=1)
    if not active_users_with_that_name:
        return [None, "Account '{}' has not been activated".format(username)]
    user = users_with_that_name[0]
    users_with_that_name_and_pwd = users_with_that_name.filter(password=crypt.crypt(password, user.salt))
    if not users_with_that_name_and_pwd:
        return [None, "Wrong password"]
    user = users_with_that_name_and_pwd[0]
    return [user, '']

def set_jwt(info, secret, duration=3600):
    """Create a jwt containing user information.
    :param info: dict containing arbitrary data
    :param secret: salt string
    :duration: time before expiration of the token, in seconds

    Method: HMAC-SHA256 ("16 character salt and 43 character hash")
    """
    if duration:
        info['exp'] = datetime.datetime.utcnow() + datetime.timedelta(seconds=duration)
    token = jwt.encode(info, secret, algorithm='HS256').decode('utf-8')
    return token

def verify_jwt(auth_header, secret):
    """Extract the jwt token from the header, verify its signature,
       its expiration time, and return the payload."""
    if not auth_header or auth_header == 'null':
        warnings.warn("No Authorization header")
        return [None, "Unauthorized access: missing authentication"]
    method,token = auth_header.split()   # separate 'JWT' from the jwt itself
    token = bytes(token, 'utf-8')
    try:
        payload = jwt.decode(token, secret, algorithms=['HS256'], verify=True)
    except (jwt.ExpiredSignatureError, jwt.DecodeError) as err:
        return [None, str(err)]
    return [payload, '']

def allow_access_to_demo(user:Users):
    """Give access to the 'demo' db, if it exists and if the host is our demo VM."""
    import socket
    hostname = socket.getfqdn()
    if not (hostname in ['varapp-dev.vital-it.ch', 'varapp-demo.vital-it.ch'] or hostname.startswith('mac-')):
        return
    if VariantsDb.objects.filter(name='demo', is_active=1).count() == 0:
        logging.info("[init] demo db not found: skip.")
        return
    else:
        logging.info("[init] allow access to demo db to user '{}'".format(user.username))
        vdb = VariantsDb.objects.get(name='demo')
        DbAccess.objects.get_or_create(user=user, variants_db=vdb, is_active=1)

def create_user(username, password, firstname, lastname, email, phone, email_to_file=None):
    if not validate_username(username):
        return [None, "Wrong user name format (are allowed a-Z|0-9|.|-|_)"]
    if not validate_email(email):
        return [None, "Wrong email format"]
    if Users.objects.filter(username=username):
        warnings.warn("Cannot create account: username {} already exists".format(email))
        return [None, "This username already exists"]
    if Users.objects.filter(email=email):
        warnings.warn("Cannot create account: email {} already exists".format(email))
        return [None, "This email already exists"]
    person = People.objects.create(firstname=firstname, lastname=lastname, phone=phone, is_laboratory=0)
    role = Roles.objects.get(name=DEFAULT_ROLE)
    salt = crypt.mksalt(method=crypt.METHOD_SHA256)
    newuser = Users(username=username, password=crypt.crypt(password, salt),
                    salt=salt, email=email, person=person, role=role,
                    is_active=0, is_password_reset=0, code=utils.random_string())
    newuser.save()
    allow_access_to_demo(newuser)
    text = "Your account '{}' has been created. ".format(username) + \
        "It will be validated by an admin shortly. You will receive an email at this " + \
        "address when your account has been activated."
    html = text
    send_email(email, "New varapp account", text=text, html=html, tofile=email_to_file)
    send_email(settings.EMAIL_ADMIN, "Account for user {} awaits validation".format(username),
                     text='', html='', tofile=email_to_file)
    return [newuser, '']

def delete_user(username, code):
    Users.objects.filter(username=username, code=code).delete()
    return

def reset_password_request(username, email, host, email_to_file=None):
    if not find_user2(username=username, email=email):
        return [None, USER_NOT_FOUND_WITH_EMAIL_MSG]
    user = Users.objects.get(username=username, email=email, is_active=1)
    activation_code = utils.random_string(10)
    user.activation_code = activation_code
    user.save()
    reset_url = host + '/#/passwordHasBeenReset' + \
        '?username={}&email={}&activation_code={}'.format(username, email, activation_code)
    text = "A new password has been demanded for user {}. Please click on the link below ".format(username) + \
        "to verify that you are the author of this request. " \
        "Shortly after verification, your new login information will be sent at this address. " + \
        "\n\n{}\n\n".format(reset_url)
    html = "<p>A new password has been demanded for user '{}'. Please click on the link below ".format(username) + \
        "to verify that you are the author of this request. " \
        "Shortly after verification, your new login information will be sent at this address.</p>" + \
        "<p><a href={}>I want to reset my password</a></p>".format(reset_url)
    send_email(email, "New password request", text=text, html=html, tofile=email_to_file)
    return [user, '']

def change_password(username, email, activation_code, password, email_to_file=None, send=True):
    if not find_user2(username=username, email=email):
        return [None, USER_NOT_FOUND_WITH_EMAIL_MSG]
    user = Users.objects.get(username=username, email=email, is_active=1)
    if user.activation_code != activation_code:
        warnings.warn("Invalid activation code: {}".format(activation_code))
        return [None, "Password has already been reset"]
    user.password = crypt.crypt(password, user.salt)
    user.activation_code = None
    user.save()
    if send:
        text = "Your varapp password has changed. " + \
            "Please use the new login information below:" + \
            "\n\n\tLogin: {}\n\tPassword: {}\n\n".format(username, password)
        html = "<p>Your varapp password changed. " + \
            "Please use the new login information below:</p>" + \
            "<table><tr><td>Login:</td><td>{}</td></tr>".format(username) + \
            "<tr><td>Password:</td><td>{}</td></tr></table>".format(password)
        send_email(email, "Password reset", text=text, html=html, tofile=email_to_file)
    return [user, '']

def change_attribute(username, code, attribute, new_value):
    user = find_user(username=username, code=code)
    if not user:
        return [None, USER_NOT_FOUND_MSG]
    if attribute == 'password':
        return change_password(username, user.email, user.activation_code, new_value, send=False)
    elif attribute == 'role':
        new_role = Roles.objects.get(name=new_value)
        user.role = new_role
    elif attribute in ['firstname','lastname']:
        setattr(user.person, attribute, new_value)
        user.person.save()
    else:
        setattr(user, attribute, new_value)
    user.save()
    return [user, '']

def user_activation(username, code, email, activate, email_to_file=None):
    """Activate a user's account"""
    user = Users.objects.get(username=username, code=code)
    if not user:
        return [None, USER_NOT_FOUND_MSG]
    if activate=='true':
        user.is_active = 1
        user.save()
        text = "Your varapp account '{}' has been activated.".format(username)
        html = "<p>Your varapp account '{}' has been activated.</p>".format(username)
        send_email(email, "Your account is now active",
                         text=text, html=html, tofile=email_to_file)
    else:
        user.is_active = 0
        user.save()
    return [user, '']

def attribute_db(username, code, dbname, add):
    """Add (*add*=True) or remove (*add=False*) access of a user <username, code> to a database <dbname>."""
    user = find_user(username=username, code=code)
    if not user:
        return [None, USER_NOT_FOUND_MSG]
    dbs = VariantsDb.objects.filter(name=dbname)
    if add == 'true':
        db = dbs.get(is_active=1)
        found, created = DbAccess.objects.get_or_create(user=user, variants_db=db)
        found.is_active = 1
        found.save()
    else:
        access = DbAccess.objects.filter(user=user, variants_db__in=dbs)
        access.update(is_active=0)
    return user

