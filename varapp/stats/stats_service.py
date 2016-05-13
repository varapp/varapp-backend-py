"""
Cached stats service. Arrays are stored in Redis, but a local memory cache is used
for faster access, as long as the current wsgi process exists.
In Redis, arrays are packed and tostring, objects are pickled.

Cached objects:
- enum_values: enumerates all possible discrete values that each enum filter can take
- global_stats: a VariantStats object for the full dataset
- masks: packed binary arrays (bitmasks).
  The unpacked array has 1 at the index of each variant_id passing the filter.
"""
from django.db import connections
from django.conf import settings
from django.core.cache import caches
from varapp.common import masking
from varapp.common.utils import timer
from varapp.constants.filters import *
from varapp.data_models.variants import Variant
from varapp.stats.histograms import DiscreteCounts, StatsContinuous, StatsFrequency
from varapp.stats.variant_stats import VariantStats
from varapp.constants.common import WEEK, MONTH
from collections import defaultdict
from functools import partial
import numpy as np
import sys, logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(message)s')


STATS_CACHE_TIMEOUT = MONTH
CACHE = True
DEBUG = False and settings.DEBUG


class GlobalStatsService:
    """Interface to a cached stats service for all variants of database *db*."""
    def __init__(self, db, new=False):
        self.db = db
        self.cache = caches['redis']
        self.service_key = 'services:stats:{}'.format(db)
        self.global_stats_key = 'stats:{}:global'.format(db)
        self.enum_values_key = 'stats:{}:enum_values'.format(db)
        self.mask_key_prefix = 'stats:{}:mask:'.format(db)
        self._initqs = Variant.objects.using(db)
        self._N = self._initqs.count()
        self._masks_ready = False
        if new or not CACHE or DEBUG:
            self.cache.delete(self.service_key)
            self.cache.delete_pattern("stats:{}:*".format(db))
        self.init()

    def init(self):
        """Check all related cache keys, and if one is not found, recreate the object."""
        if not self._check_masks_ready() or not CACHE:  # generate masks and enum_values
            logging.info("[cache] unset: init filter masks for db '{}'".format(self.db))
            self._init_discrete_filter_masks()
        if (not self.global_stats_key in self.cache) or not CACHE:  # generate global_stats and impacts
            logging.info("[cache] unset: init global stats for db '{}'".format(self.db))
            global_stats = self._init_global_stats()
            self.save_global_stats(global_stats)
        self.cache.set(self.service_key, 1, timeout=STATS_CACHE_TIMEOUT)
        return self

    def make_stats(self, variant_ids):
        """Get stats (dynamically) for a subset of *variant_ids*.
           We only need counts for discrete filters.
           This is what is accessed to update 'local' stats when a new variants query is made
        """
        if not self._masks_ready:  # shortcut
            if not self._check_masks_ready():
                self._init_discrete_filter_masks()
        variants_mask = masking.pack(masking.to_binary_array(variant_ids, self._N))
        discrete_counts = {}
        for f in DISCRETE_FILTER_NAMES:
            counts = {}
            for val in self.get_enum_values()[f]:
                mask = self.get_mask(f, val)
                assert len(mask) == len(variants_mask), "{} != {}".format(len(mask), len(variants_mask))
                common = masking.unpack(masking.binary_and(variants_mask, mask), self._N)
                counts[val] = np.count_nonzero(common)
            discrete_counts[f] = DiscreteCounts(counts)
        return VariantStats(discrete_counts, len(variant_ids))

    ## Cache transactions

    def key_mask(self, filter_name, value):
        """Return the cache key for that filter name and value,
        of the form 'stats:<db>:mask:<filter_name>:<enum_value>'."""
        return self.mask_key_prefix + '{}:{}'.format(filter_name, value)

    def save_mask(self, mask, filter_name, value):
        """Cache the enum mask for that filter name and value"""
        key = self.key_mask(filter_name, value)
        self.cache.set(key, mask.tostring(), timeout=STATS_CACHE_TIMEOUT)

    def get_mask(self, filter_name, value):
        """Retreive from cache the mask for that filter name and value"""
        key = self.key_mask(filter_name, value)
        mask = np.fromstring(self.cache.get(key), dtype=np.uint8)
        self.cache.expire(key, STATS_CACHE_TIMEOUT)
        return mask

    def save_enum_values(self, v):
        """Cache the enum_values dict ({filter_name: [possible_values]})"""
        self.cache.set(self.enum_values_key, v, timeout=STATS_CACHE_TIMEOUT)

    def get_enum_values(self):
        """Retreive from cache the enum_values dict"""
        self.cache.expire(self.enum_values_key, STATS_CACHE_TIMEOUT)
        return self.cache.get(self.enum_values_key)

    def save_global_stats(self, g):
        """Cache the global_stats object"""
        self.cache.set(self.global_stats_key, g, timeout=STATS_CACHE_TIMEOUT)

    def get_global_stats(self):
        """Retreive from cache the global_stats:VariantStats object"""
        self.cache.expire(self.enum_values_key, STATS_CACHE_TIMEOUT)
        return self.cache.get(self.global_stats_key)

    ## Initialization - private methods

    @timer
    def _init_global_stats(self):
        """Get stats for the entire database, and store the result for reuse.
           Return a VariantStats object."""
        stats = {}
        stats.update(self._counts_enum())
        stats.update(self._stats_continuous())
        global_stats = VariantStats(stats, self._N)
        return global_stats

    def _stats_continuous(self):
        """Return a map `{filter_name: StatsContinuous}`,
           storing the values distribution, min/max, etc."""
        stats_continuous = {}
        translated = [TRANSLATION.get(f,f) for f in CONTINUOUS_FILTER_NAMES]
        minmax_query = ','.join(['MIN({}),MAX({})'.format(f,f) for f in translated])
        cursor = connections[self.db].cursor()
        cursor.execute('SELECT {} FROM variants'.format(minmax_query))
        minmax = cursor.fetchone()  # [min, max, min, max, ...]
        minmax = [{'min':x[0], 'max':x[1]} for x in zip(minmax[::2], minmax[1::2])]
        for i,f in enumerate(CONTINUOUS_FILTER_NAMES):
            stats_continuous[f] = StatsContinuous(minmax[i])
        for f in FREQUENCY_FILTER_NAMES + PVALUE_FILTER_NAMES + ZERO_ONE_FILTER_NAMES:
            stats_continuous[f] = StatsFrequency()
        return stats_continuous

    def _counts_enum(self):
        """Return a map `{filter_name: DiscreteCounts}`,
           storing the number of variants in each category
           by counting the nonzero entries in each binary mask.
           Called only once at init."""
        discrete_counts = {}
        for f in DISCRETE_FILTER_NAMES:
            counts = {}
            for val in self.get_enum_values()[f]:
                mask = self.get_mask(f, val)
                common = masking.unpack(mask, self._N)
                counts[val] = np.count_nonzero(common)
            if f == 'impact':
                counts['pairs'] = self._init_impacts()
            discrete_counts[f] = DiscreteCounts(counts)
        return discrete_counts

    def _check_masks_ready(self):
        """Check that masks are in the cache for all enum filters"""
        if self.enum_values_key in self.cache:
            enum_values = self.get_enum_values()
            ready = True
            for fname, vals in enum_values.items():
                for val in vals:
                    if not self.key_mask(fname, val) in self.cache:
                        ready = False
        else:
            ready = False
        self._masks_ready = ready  # provide a shortcut
        return ready

    @timer
    def _init_discrete_filter_masks(self):
        """Create an array of passing ids for every discrete valued filter.
           :rtype: dict `{filter_name: {value: [ids]}}`"""
        translated = tuple(TRANSLATION.get(f,f) for f in ['variant_id']+DISCRETE_FILTER_NAMES)
        cursor = connections[self.db].cursor()
        cursor.execute("SELECT {} FROM variants".format(','.join(translated)))
        # Create a variants mask per couple (filter, value), with 1 at indices corresponding to passing variants
        variant_masks = {t:defaultdict(partial(np.zeros, self._N, dtype=np.bool_)) for t in DISCRETE_FILTER_NAMES}
        enum_values = {t:set() for t in DISCRETE_FILTER_NAMES}
        irange = range(1,len(translated))
        for row in cursor:
            vid = row[0]  # variant id
            for i in irange:
                val = row[i]
                fname = DISCRETE_FILTER_NAMES[i-1]
                variant_masks[fname][val][vid-1] = 1
                enum_values[fname].add(val)
        # Pack and cache the result
        for fname in DISCRETE_FILTER_NAMES:
            for val, mask in variant_masks[fname].items():
                mask = masking.pack(mask)
                self.save_mask(mask, fname, val)
        self.save_enum_values(enum_values)
        self._masks_ready = True

    def _init_impacts(self):
        """Return a dict {impact_severity: [impact_terms]}.
           It is added to global stats, so no need to cache it separately."""
        cursor = connections[self.db].cursor()
        cursor.execute("""SELECT impact_severity, group_concat(distinct impact) FROM variants
                          WHERE impact IS NOT NULL GROUP BY impact_severity;""")
        impacts = {row[0]: row[1].split(',') for row in cursor}
        return impacts


def stats_service(db):
    """Creates a new GlobalStatsService, if not already found in local process cache."""
    return GlobalStatsService(db)

