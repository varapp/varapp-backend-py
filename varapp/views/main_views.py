from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.cache import cache_page

from varapp.annotation.location_service import LocationService
from varapp.stats.stats_service import stats_service
from varapp.common.utils import timer
from varapp.data_models.variants import Variant, expose_variant_full, annotate_variants
from varapp.export import export
from varapp.filters.filters_factory import variant_filters_from_request
from varapp.filters.pagination import pagination_from_request
from varapp.filters.sort import sort_from_request
from varapp.samples.samples_service import samples_selection_from_request
from varapp.views.auth_views import protected

from jsonview.decorators import json_view
from time import time
import sys, logging
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format='%(message)s')

DEBUG = True and settings.DEBUG


class AllFilters:
    """Treats an HTTP request to build the samples selection, pagination and variant filters
    according to the request's parameters."""
    def __init__(self, request, db):
        """Extract filters etc. information from http request."""
        self.db = db
        self.sort = sort_from_request(request)
        self.pg = pagination_from_request(request)
        self.ss = samples_selection_from_request(request, db)
        self.fc = variant_filters_from_request(request, db, self.ss)
        self.stats = stats_service(db)

    #@timer
    def apply_all_filters(self):
        """Return a filtered and sorted variants collection."""
        # If the sorting field is is the db, use the db engine to sort.
        # Else, manage the case when the sorting field is added at expose time, after exposition...
        var = self.fc.apply(db=self.db,
            sort_by=self.sort.key, reverse=self.sort.reverse,
            limit=self.pg.lim, offset=self.pg.off)
        return var

    #@timer
    def expose(self):
        """Return a dict exposing variants, filters, stats etc. to be sent to the view."""
        t1 = time()
        filter_result = self.apply_all_filters()
        t2 = time()
        var = filter_result.variants
        stat = self.stats.make_stats(filter_result.ids)
        t3 = time()
        var = [expose_variant_full(v, self.ss) for v in var]
        t4 = time()
        var = annotate_variants(var, self.db)
        t5 = time()
        logging.info("Apply/Stats/Expose/Annotate: {:.3f}s {:.3f}s {:.3f}s {:.3f}s".format(t2-t1, t3-t2, t4-t3, t5-t4))
        # TODO? How can one sort wrt. these fields?
        #if self.sort.key is not None and self.sort.key not in VARIANT_FIELDS:
        #    self.sort.sort_dict(var, inplace=True)
        response = {'variants': var}
        response["filters"] = [str(x) for x in self.fc.list]
        response["nfound"] = stat.total_count
        response["stats"] = stat.expose()
        return response

def index(request):
    """Return the string 'Hello, World !'."""
    return HttpResponse("Hello World !\n")

@json_view
def samples(request, db, user=None):
    """Return a JSON with the list of Samples."""
    ss = samples_selection_from_request(request, db)
    return JsonResponse(ss.expose(), safe=False)

@json_view
def variants(request, db, user=None):
    """Return a JSON with info on the requested Variants."""
    filters = AllFilters(request, db)
    response = filters.expose()
    return JsonResponse(response, safe=False)

@json_view
def stats(request, db, user=None):
    """Return a JSON with stats over the whole db (to query only once at startup)."""
    stat = stats_service(db).get_global_stats()
    return JsonResponse(stat.expose(), safe=False)

@json_view
def count(request, db, **kwargs):
    """Return the total number of variants in the database.
    Used for filling up the cache and REST tests.
    """
    n = Variant.objects.using(db).count()
    response = HttpResponse(n)
    return response

@json_view
def location_find(request, db, loc='', **kwargs):
    """Return an exposed GenomicRange for each location in the comma-separated list *loc*."""
    locs = LocationService(db).find(loc)
    locations = [l.expose() for l in locs]
    return JsonResponse(locations, safe=False)

@json_view
def location_names_autocomplete(request, db, prefix=''):
    """Return gene names starting with *prefix*."""
    ans = LocationService(db).autocomplete_name(prefix, maxi=10)
    return JsonResponse(ans, safe=False)

@json_view
def export_variants(request, db, **kwargs):
    """Create a TSV file with the variants data and serve it."""
    file_format = request.GET['format']
    fields = request.GET.get('fields', '').split(',')
    filters = AllFilters(request, db)
    var = filters.apply_all_filters().variants
    if file_format == 'report':
        filename = 'varapp_report.txt'
    else:
        filename = 'variants.' + file_format
    response = HttpResponse(content_type="text/plain")
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
    response['Access-Control-Expose-Headers'] = 'Content-Disposition'
    response['Access-Control-Allow-Headers'] = 'Content-Disposition'
    if file_format == 'txt':
        export.export_tsv(var, response, filters.ss, fields)
    elif file_format == 'vcf':
        export.export_vcf(var, response, filters.ss)
    elif file_format == 'report':
        params = dict(request.GET)
        export.export_report(var, response, db, params)
    return response


p_samples = protected(samples)
p_stats = protected(stats)
p_variants = protected(variants)
p_export_variants = protected(export_variants)
#p_variants = cache_page(60*60*2)(p_variants)

