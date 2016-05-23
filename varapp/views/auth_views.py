"""
Views that concern authentication, protecting access to other views or actions
"""

from django.http import JsonResponse, HttpResponseForbidden
from django.conf import settings

from varapp.data_models.users import VariantsDb, user_factory
from varapp.common.manage_dbs import deactivate_if_not_found_on_disk, update_if_db_changed
from varapp.auth import auth
from jsonview.decorators import json_view

secret = settings.SECRET_KEY
DAY_IN_SECONDS = 86400
TOKEN_DURATION = DAY_IN_SECONDS/4
#TOKEN_DURATION = 5

def JWT_user(user, duration=TOKEN_DURATION):
    """Set a JWT with user info (username, code, email, etc.), and return it in a json response"""
    user_info = user_factory(user).expose()
    id_token = auth.set_jwt(user_info, secret, duration)
    return JsonResponse({'id_token': id_token}, safe=False)

class protected:
    """Decorator to force a view to verify the JWT and the existence of the user in the db.
    If the JWT is validated, anyway it was issued here with a valid user,
    but we can check he *still* exists and still has access to that db.
    Protected views can make use of the 'user' keyword argument, binding the User calling the view.
    """
    def __init__(self, view, level=999):
        """:param level: if the user's rank is greater than this, the user cannot access the view."""
        self.view = view
        self.level = level

    def __call__(self, request, **kwargs):
        # Check the token validity
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        payload,msg = auth.verify_jwt(auth_header, secret)
        if payload is None:
            return HttpResponseForbidden(msg)
        ## Check that the user exists
        username = payload['username']
        code = payload['code']
        if not auth.check_user_exists(username, code):
            return HttpResponseForbidden(
                "No account was found with username '{}'.".format(payload['username'])
            )
        user = auth.find_user(username, code)
        # Check user role
        if user.role.rank > self.level:
            return HttpResponseForbidden("This action requires higher credentials")
        # Check db access
        if kwargs.get('db'):
            dbname = kwargs['db']
            vdbs = VariantsDb.objects.filter(name=dbname, is_active=1)
            if not vdbs:
                return HttpResponseForbidden(
                    "Database '{}' does not exist or is not active anymore.".format(dbname))
            vdb = vdbs[0]
            deac = deactivate_if_not_found_on_disk(vdb)
            if deac:
                return HttpResponseForbidden(
                    "Database '{}' was not found on disk and deactivated.".format(dbname))
            changed = update_if_db_changed(vdb)
            if changed:
                return HttpResponseForbidden(
                    "Database '{}' has been modified. Please reload.".format(dbname))
            if not auth.check_can_access_db(user, dbname):
                return HttpResponseForbidden(
                    "User '{}' has no database called '{}'.".format(username, dbname))
        kwargs['user'] = user
        return self.view(request, **kwargs)

@json_view
def authenticate(request, **kwargs):
    """Log in view, only the first time.
    Validates the given username and password, and returns an id_token (jwt)
    containing user data, to avoid login for a session's time.
    """
    username = request.POST['username']
    password = request.POST['password']
    # Check credentials
    user, msg = auth.check_credentials(username, password)
    if not user:
        return HttpResponseForbidden(msg)
    return JWT_user(user, TOKEN_DURATION)

@json_view
def renew_token(request):
    """Refresh the JWT with a new expiration time and updated user data"""
    auth_header = request.META.get('HTTP_AUTHORIZATION')
    payload,msg = auth.verify_jwt(auth_header, secret)
    if payload is None:
        return HttpResponseForbidden(msg)
    # This user must exist, but can yet be inactive
    user = auth.find_user(payload['username'], payload['code'], require_active=False)
    return JWT_user(user, TOKEN_DURATION)

