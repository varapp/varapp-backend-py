"""
Cached genotypes service. Arrays are stored in Redis, but a local memory cache is used
for faster access, as long as the current wsgi process exists.
In Redis, arrays are packed and tostring, objects are pickled.
"""

from django.db import connections
from varapp.common.utils import timer
from varapp.common.genotypes import decode_int
from varapp.constants.genotype import *
from varapp.data_models.variants import Variant
from varapp.models.gemini import Samples
import numpy as np
import itertools
from operator import itemgetter
import logging, sys
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(message)s')

from django.core.cache import caches
from varapp.constants.common import WEEK, MONTH

GENOTYPES_CACHE_TIMEOUT = MONTH


gt_to_bit = {
    0: GENOTYPE_BIT_NON_CARRIER,
    1: GENOTYPE_BIT_CARRIER_HET,
    2: GENOTYPE_BIT_NON_CARRIER, # unknown: consider as ref/ref
    3: GENOTYPE_BIT_CARRIER_HOM,
}
def variant_build_gt_type_bit(gt):
    """From a gt_types_decoded single value in (0, 1, 2, 3) from gemini,
    build the mask aggregating the various GENOTYPE_BIT_* (powers of 2)."""
    return gt_to_bit.get(gt, GENOTYPE_BIT_UNKNOWN)

def extract_genotypes(db, qs=None):
    """Make an int8 numpy array from all the sample genotypes.
    The index of a variant in this array is the primary key of the variant, minus 1.
    """
    # Using 'only' instead of 'values_list' makes it 3 times slower
    gts_queryset_iter = Variant.objects.using(db).values_list('gt_types_blob', flat=True)
    gts_array = np.array([decode_int(x) for x in gts_queryset_iter], dtype=np.int8)
    return gts_array


class GenotypesService:
    """Read genotypes from the database.
    :param db: the database name ('default', 'test'...)"""
    def __init__(self, db):
        self.db = db
        self._gt_types_bit = None
        self.N = Variant.objects.using(db).count()
        self.S = Samples.objects.using(db).count()
        self.cache = caches['redis']
        self.chrX_key = "gen:{}:chrX".format(self.db)
        self.gene_batches_key = "gen:{}:gene_batches".format(self.db)
        self.genotypes_key = "gen:{}:genotypes".format(self.db)
        self._init()

    @timer
    def _init(self):
        """Build the array _gt_types_bit containing all the genotypes."""
        if self._gt_types_bit is None:
            logging.info("[cache] unset: init genotypes for db '{}'".format(self.db))
            self._init_genotypes()
        if not self.gene_batches_key in self.cache:
            logging.info("[cache] unset: init gene batches for db '{}'".format(self.db))
            self._init_variant_batches_by_gene()
        if not self.chrX_key in self.cache:
            logging.info("[cache] unset: init chrX for db '{}'".format(self.db))
            self._init_chrX()
        return self

    def clear_cache(self):
        self._gt_types_bit = None
        self.cache.delete(self.gene_batches_key)
        self.cache.delete(self.chrX_key)
        self.cache.delete(self.genotypes_key)

    def reset(self):
        self.clear_cache()
        self._init()

    ## Getters and setters

    @property
    def chrX(self):
        """Return the bitmask for chrX variants."""
        self.cache.expire(self.chrX_key, GENOTYPES_CACHE_TIMEOUT)
        return np.fromstring(self.cache.get(self.chrX_key), dtype=np.uint64)

    @property
    def variant_ids_batches_by_gene(self):
        self.cache.expire(self.gene_batches_key, GENOTYPES_CACHE_TIMEOUT)
        return self.cache.get(self.gene_batches_key)

    @property
    def genotypes(self):
        """Return the array containing all genotypes. There is one per
        variant, and each one is a numpy array with nsamples elements."""
        return self._gt_types_bit

    def _save_genotypes(self, genotypes):
        """Cache the genotypes binary array, for a week"""
        self.cache.set(self.genotypes_key, genotypes.flatten().tostring(), timeout=GENOTYPES_CACHE_TIMEOUT)

    def _get_genotypes(self):
        """Get genotypes binary array from cache"""
        gen_bits = self.cache.get(self.genotypes_key)
        gen_bits = np.fromstring(gen_bits, dtype=np.uint8).reshape(self.N, self.S)
        self.cache.expire(self.genotypes_key, GENOTYPES_CACHE_TIMEOUT)
        return gen_bits

    ## Initialization

    def _init_chrX(self):
        """Construct an array of variant_ids belonging to chromosome X."""
        chrX = np.asarray(list(
            Variant.objects.using(self.db).filter(chrom='chrX').values_list('variant_id', flat=True)),
            dtype=np.uint64)
        chrX.flags.writeable = False  # make it immutable
        self.cache.set(self.chrX_key, chrX.tostring(), timeout=GENOTYPES_CACHE_TIMEOUT)

    def _init_variant_batches_by_gene(self):
        """Construct a dict `{gene_name: set(variant_ids)}`"""
        ids_by_gene = {}
        query = "select variant_id,gene from variants where gene is NOT NULL order by gene"
        cursor = connections[self.db].cursor()
        cursor.execute(query)
        batches = cursor.fetchall()
        for gene,batch in itertools.groupby(batches, key=itemgetter(1)):
            ids_by_gene[gene] = np.array([x[0] for x in batch], dtype=np.uint64)
            ids_by_gene[gene].flags.writeable = False  # make it immutable
        self.cache.set(self.gene_batches_key, ids_by_gene, timeout=GENOTYPES_CACHE_TIMEOUT)

    def _init_genotypes(self):
        """Construct an array of genotype vectors, one per variant.
           If it is found in cache, use the cached version,
           otherwise recompute it and cache the result.
           Either way, store a copy in local process memory.
        """
        if self.genotypes_key in self.cache:
            # Read cache, store in local memory
            self._gt_types_bit = self._get_genotypes()
        else:
            # Regenerate, cache, and store in local memory
            gt_types = extract_genotypes(db=self.db)
            f = np.vectorize(variant_build_gt_type_bit, otypes=[np.uint8])  # apply to all array elements
            self._gt_types_bit = f(gt_types)
            self._gt_types_bit.flags.writeable = False  # make it immutable
            self._save_genotypes(self._gt_types_bit)


def genotypes_service(db):
    """Creates a new GenotypesService, if not already found in local process cache"""
    gen_cache = caches['genotypes_service']
    if gen_cache.get(db) is None:
        logging.info("[cache] Init genotypes cache '{}'".format(db))
        gen_cache.set(db, GenotypesService(db))
    return gen_cache.get(db)



