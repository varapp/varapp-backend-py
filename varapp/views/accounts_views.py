"""
Views concerning the UserAccount page
"""
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from jsonview.decorators import json_view
import os, logging
logger = logging.getLogger(__name__)

from varapp.auth import auth
from varapp.common import utils
from varapp.data_models.users import users_list_from_users_db, databases_list_from_users_db, roles_list_from_users_db
from varapp.views.auth_views import protected, JWT_user, TOKEN_DURATION
from varapp.constants import roles

DAY_IN_SECONDS = 86400

## The username and code in the request are the target's, no the corrent user's.

@json_view
def get_users_info(request, db='default', **kwargs):
    users = [u.expose() for u in users_list_from_users_db(db=db)]
    return JsonResponse(users, safe=False)

@json_view
def get_dbs_info(request, db='default', **kwargs):
    dbs = [d.expose() for d in databases_list_from_users_db(db=db)]
    return JsonResponse(dbs, safe=False)

@json_view
def get_roles_info(request, db='default', **kwargs):
    roles = [role.name for role in roles_list_from_users_db(db=db)]
    return JsonResponse(roles, safe=False)

@json_view
def signup(request, email_to_file=None):
    """Adds a new -inactive- user to the db. Send an email to an admin to validate the account.
    Not @protected because the user is unidentified at this point.
    """
    logger.info("Signing up")
    username = request.POST['username']
    password = request.POST['password']
    firstname = request.POST['firstname']
    lastname = request.POST['lastname']
    email = request.POST['email']
    phone = request.POST['phone']
    if '_functest_' in username:
        email_to_file = open(os.devnull, 'w')
    user,msg = auth.create_user(username, password, firstname, lastname, email, phone, email_to_file)
    if user is None:
        return HttpResponseForbidden(msg)
    return JWT_user(user, TOKEN_DURATION)

@json_view
def reset_password_request(request, email_to_file=None):
    """Does not actually change the password, but sends the user an email
    with a link to the change_password view to generate a new random one.
    Not @protected because the user is unidentified at this point.
    """
    logger.info("Reset password request")
    username = request.POST['username']
    email = request.POST['email']
    host = request.POST['host']
    if username == 'test':
        email_to_file = open(os.devnull, 'w')
    user,msg = auth.reset_password_request(username, email, host, email_to_file)
    if user is None:
        return HttpResponseForbidden(msg)
    user_info = {'username':username, 'email':email}
    return JsonResponse(user_info, safe=False)

def change_password(request, new_password=None, email_to_file=None):
    """Change a user's password and sends him an email with the new login.
    Also to validate password reset, in which case it replaces the user's password
    by a random one (if *password* is not set).
    Not @protected because the user is unidentified at this point,
    but the activation code is the protection.
    """
    logger.info("Reset password validation")
    username = request.POST['username']
    email = request.POST['email']
    activation_code = request.POST['activation_code']
    if new_password is None:
        new_password = utils.random_string(10)
    user,msg = auth.change_password(username, email, activation_code, new_password, email_to_file)
    if user is None:
        return HttpResponseForbidden(msg)
    return JWT_user(user, TOKEN_DURATION)

@json_view
def change_attribute(request, user=None, **kwargs):
    """Change a user attribute such as email, role, etc."""
    username = request.POST['username']
    code = request.POST['code']
    attribute = request.POST['attribute']
    new_value = request.POST['new_value']
    logger.info("Change attribute '{}'".format(attribute))
    mod_user,msg = auth.change_attribute(username, code, attribute, new_value)
    # If the user changes himself, need to query again with possible changes
    if user.username == username and user.code == code:
        if attribute == 'username':
            user = auth.find_user(new_value, code)
        elif attribute == 'code':
            user = auth.find_user(username, new_value)
        else:
            user = auth.find_user(username, code)
    # If the user changes another user, check that he has the right to do it
    elif user.role.rank > 2:
        return HttpResponseForbidden("Insufficent credentials")
    return JWT_user(user, TOKEN_DURATION)

@json_view
def user_activation(request, email_to_file=None, **kwargs):
    """Activate a user's account"""
    logger.info("Activate/deactivate user")
    username = request.POST['username']
    code = request.POST['code']
    email = request.POST['email']
    activate = request.POST['activate']
    auth.user_activation(username, code, email, activate, email_to_file)
    return HttpResponse('')

@json_view
def delete_user(request, **kwargs):
    logger.info("Delete user")
    username = request.POST['username']
    code = request.POST['code']
    auth.delete_user(username, code)
    return HttpResponse('')

@json_view
def attribute_db(request, user=None, **kwargs):
    username = request.POST['username']
    code = request.POST['code']
    dbname = request.POST['dbname']
    add = request.POST['add']
    logger.info("Attribute db '{}' to '{}'".format(dbname, username))
    auth.attribute_db(username, code, dbname, add)
    return JWT_user(user, TOKEN_DURATION)


p_get_users_info = protected(get_users_info, level=roles.ADMIN_LEVEL)
p_get_dbs_info = protected(get_dbs_info, level=roles.ADMIN_LEVEL)
p_get_roles_info = protected(get_roles_info, level=roles.ADMIN_LEVEL)

p_user_activation = protected(user_activation, level=roles.ADMIN_LEVEL)
p_attribute_db = protected(attribute_db, level=roles.ADMIN_LEVEL)
p_delete_user = protected(delete_user, level=roles.ADMIN_LEVEL)

p_change_attribute = protected(change_attribute, level=roles.GUEST_LEVEL)

