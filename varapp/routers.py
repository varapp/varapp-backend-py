
auth_models = ['Roles','People','Users','VariantsDb','DbAccess','History','Preferences','VariantsQC']


AUTH_DB = 'default'

class AuthRouter(object):
    def db_for_read(self, model, **hints):
        #print('AuthRouter: using database `{}` for reading {}.'.format(AUTH_DB, model.__name__))
        if model.__name__ in auth_models:
            return AUTH_DB
        return None

    def db_for_write(self, model, **hints):
        #print('AuthRouter: using database `{}` for writing to {}.'.format(AUTH_DB, model.__name__))
        if model.__name__ in auth_models:
            return AUTH_DB
        return None

