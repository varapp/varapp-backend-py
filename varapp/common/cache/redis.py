from django.core.cache import caches
import sys, logging
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format='%(message)s')

stats_cache = caches['stats']
genotypes_cache = caches['genotypes']

def remove_db_from_cache(dbname):
    """Remove all cached items relative to a db that got deactivated"""
    logging.info("[cache] Removing Redis-cached keys for db '{}'".format(dbname))
    logging.info("[cache] -Stats keys: {}".format(stats_cache.keys("stats:{}:*")))
    logging.info("[cache] -Genotypes keys: {}".format(genotypes_cache.keys("stats:{}:*")))
    stats_cache.delete_pattern("stats:{}:*".format(dbname))
    genotypes_cache.delete_pattern("stats:{}:*".format(dbname))
