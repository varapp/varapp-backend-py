from django.conf.urls import url
from varapp.views.views import *
from varapp.views.accounts import *
from varapp.views.bookmarks import *
from varapp.views.auth import *

urlpatterns = [
    url(r'^$', index),

    # users_db
    url(r'^authenticate$', authenticate),
    url(r'^renew_token$', renew_token),
    url(r'^signup$', signup),
    url(r'^resetPasswordRequest$', reset_password_request),
    url(r'^changePassword', change_password),
    url(r'^deleteUser$', p_delete_user),
    url(r'^userActivation$', p_user_activation),
    url(r'^attributeDb$', p_attribute_db),
    url(r'^changeAttribute', p_change_attribute),
    url(r'^usersInfo', p_get_users_info),
    url(r'^dbsInfo', p_get_dbs_info),
    url(r'^rolesInfo', p_get_roles_info),

    # variants_db
    url(r'^(?P<db>.*)/count$', count, name='count'),
    url(r'^(?P<db>.*)/samples$', p_samples, name='samples'),
    url(r'^(?P<db>.*)/variants$', p_variants, name='variants'),
    url(r'^(?P<db>.*)/variants/export$', p_export_variants, name='export'),
    url(r'^(?P<db>.*)/stats$', p_stats, name='stats'),
    url(r'^(?P<db>.*)/location/autocomplete/(?P<prefix>[\w\-,:\s]+)$', location_names_autocomplete),
    url(r'^(?P<db>.*)/location/(?P<loc>[\w\-,:\s]+)$', location_find),
    url(r'^(?P<db>.*)/getBookmarks$', p_get_bookmarks),
    url(r'^(?P<db>.*)/setBookmark$', p_set_bookmark),
    url(r'^(?P<db>.*)/deleteBookmark$', p_delete_bookmark),

    # Older shorter versions with the default db
    url(r'^location/autocomplete/(?P<prefix>[\w\-,:\s]+)$', location_names_autocomplete),
    url(r'^location/(?P<loc>[\w\-,:\s]+)$', location_find),

]

