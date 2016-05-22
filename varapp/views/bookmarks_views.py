from django.http import HttpResponse, JsonResponse
from varapp.views.main_views import protected
from jsonview.decorators import json_view
from varapp.history import bookmarks


@json_view
def get_bookmarks(request, db, user=None, **kwargs):
    """Get the list of all bookmarks concerning database *db* and this *user*."""
    bks = bookmarks.get_bookmarks(user, db)
    return JsonResponse(bks, safe=False)

def set_bookmark(request, db, user=None, **kwargs):
    """Write a bookmark in history, concerning database *db* and this *user*"""
    url = request.POST['url']
    time = request.POST['time']
    text = request.POST['text']
    bookmarks.set_bookmark(user, url, time, text, db)
    return HttpResponse('')

def delete_bookmark(request, db, user=None, **kwargs):
    time = request.POST['time']
    bookmarks.delete_bookmark(user, time, db)
    return HttpResponse('')


p_get_bookmarks = protected(get_bookmarks)
p_set_bookmark = protected(set_bookmark)
p_delete_bookmark = protected(delete_bookmark)
