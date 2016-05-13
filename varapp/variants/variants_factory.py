from varapp.data_models.variants import *
from varapp.constants.filters import ALL_VARIANT_FILTER_NAMES
from varapp.common.utils import timer
import numpy as np
import itertools


def variants_collection_factory(db, qs=None):
    """Create a VariantsCollection instance from a Variant QuerySet *qs*,
    or the entire database *db* (is *qs* is None)."""
    if qs is None:
        qs = Variant.objects.using(db).all()
    return VariantsCollection(qs, cache_key=db, db=db)


#@timer
def extract_variants_from_ids_bin_array(qs, bin_ids, ordered_qs_indices=None, limit=None, offset=0,
    batch_size=500, sources=None):
    """Given a set of variant_ids, return a list of fully annotated
       Variant objects (e.g. for exposition to frontend),
       in the same order as given in *ids*.
      (If *limit* is over a few hundreds, one cannot get them all at once
       because of SQL limitation on query length, so we extract them in batches - e.g. for export)
    :param qs: a QuerySet of variants
    :param bin_ids: the binary mask, where the non-zero indices are the variant ids to extract.
    :param ordered_qs_indices: indices that pass only variant filters, but in the same order as in *qs*.
    :param batch_size: max number of variant ids that can be fetched in one sql query.
    :param sources: to annotate the compounds with a source attribute,
        provide a {variant_id: source} mapping.
    """
    B = batch_size
    k = 0
    variants = []
    if ordered_qs_indices is None:
        ordered_qs_indices = list(qs.values_list('variant_id', flat=True))
    ordered_indices = filter(lambda x:bin_ids[x-1], ordered_qs_indices)
    if limit is None:
        limit = np.count_nonzero(bin_ids)
    while k*B < limit:
        R = min(B, limit-(k*B))  # how many remain to extract
        ids_to_extract = itertools.islice(ordered_indices, offset, offset+R)
        sub_qs = qs.filter(variant_id__in=ids_to_extract)
        k += 1
        #variants = namedtuples(sub_qs)
        variants.extend(list(sub_qs))
        if sources:
            for i,v in enumerate(variants):
                #variants[i] = set_source(v, sources[v.variant_id])
                v.source = sources[v.variant_id]
    return variants

def set_source(v, value):
    """Return a new namedtuple with the source replaced by this value."""
    if isinstance(v, Variant):
        v.source = value
    elif isinstance(v, VariantTriplet) or isinstance(v, VariantTuple):
        v = v._replace(**{'source': value})
    return v


################################
# High-performance collections #
################################

def namedtuples(qs):
    """Build a list of namedtuples from a QuerySet *qs*."""
    return [VariantTuple(*(v+('',))) for v in qs.values_list()]

def namedtriplets(qs):
    """Build a list of namedtuples with only variant_id, gene_symbol and source
    from a QuerySet *qs*, for use in FilterCollection.apply with compound het."""
    return [VariantTriplet(*(v+('',))) for v in qs.values_list('variant_id','gene_symbol')]

def namedmonos(qs):
    """Build a list of namedtuples with only variant_id, from a QuerySet *qs*,
    for use in FilterCollection.apply with other genotype filters."""
    return [VariantMono(v) for v in qs.values_list('variant_id', flat=True)]

def namedtuplestats(qs):
    """Build a list of namedtuples with only filter fields, from a QuerySet *qs*."""
    return [VariantTupleStats(*v) for v in qs.values_list(*ALL_VARIANT_FILTER_NAMES)]

