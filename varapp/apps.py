"""
Code to be executed only once *per wsgi process* at startup.
It is a hook called in varapp/__init__.py .
"""
from django.apps import AppConfig
from django.conf import settings
import sys, logging
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='%(message)s')


class VarappConfig(AppConfig):
    """`this.ready()` gets executed when the app is fully loaded (models etc.)
    It is called in varapp/__init__.py, and once per Apache process.
    """
    name = 'varapp'
    verbose_name = "Varapp"

    def ready(self):
        from varapp.common import manage_dbs, utils, db_utils
        from varapp.common.versioning import add_versions
        from varapp.stats.stats_service import stats_service
        from varapp.variants.genotypes_service import genotypes_service

        # Check that there are tables in the users_db,
        # because this code is also run when manage.py is used,
        # for instance to generate the tables.
        user_db_ready = db_utils.connection_has_tables('default')

        # Manage.py must work without the following to execute.
        if user_db_ready:
            # At startup, fill settings.DATABASES with what is in VariantsDb.
            # Do not add any new db here, as unlike deactivation, inserts
            # are not idempotent and this code could be executed several times.
            # Return the valid databases added to connections,
            # since they need to be in there to be read for vcf_header, stats etc.
            added_connections = manage_dbs.copy_VariantsDb_to_settings()

            # Check that the Redis service is running.
            # It is necessary for stats and genotypes cache.
            redis_ready = utils.check_redis_connection()
            if not redis_ready:
                raise Exception("Could not connect to Redis. Make sure Redis is installed, "
                                "is up and running (try `redis-cli ping`) "
                                "and serves at 127.0.0.1:6379 (or whatever is defined in settings.")

            # Fill the stats cache
            if settings.WARMUP_STATS_CACHE:
                for dbname in added_connections:
                    stats_service(dbname)

            # Fill the genotypes cache
            if settings.WARMUP_GENOTYPES_CACHE:
                for dbname in added_connections:
                    genotypes_service(dbname)

            # Update the *annotation* table with versions of all programs used,
            # i.e. Gemini, VEP, their dbs, etc.
            for dbname in added_connections:
                add_versions(dbname)

            return 1

        else:
            return 0


