"""
Django conf file for Jenkins. The test db is an sqlite, and users and variants cohabit.
"""

from varmed.settings.base import *
from os.path import join
import os, sys, logging
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format='%(message)s')

logging.info("\n-----------  << RESTART >> -----------\n")
logging.info("// TEST // settings file (env.py): " + os.path.basename(__file__))

# General
DEBUG = True
HOST = 'localhost'
BASE_URL = 'http://localhost:8000'
SECRET_KEY = 'K6QKN6C2xtcl.'
#ALLOWED_HOSTS = ['localhost']  # CORS

## Email
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_FROM = 'varapp@varapp.vital-it.ch'

## Gemini dbs
GEMINI_DB_PATH = TEST_DB_PATH
DB_TEST = 'testdb_0036.db'
FILL_DBS = False  # whether to fill VariantsDb with Gemini databases found in DB_PATH
CHECK_HASH = False  # whether to check if a db with the same name as in users_db is an upgrade or identical
WARMUP_STATS_CACHE = False  # Generate stats cache for all active dbs at startup
WARMUP_GENOTYPES_CACHE = False  # Generate genotypes cache for all active dbs at startup

## Users db
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PWD = 'pwd'
MYSQL_DB = 'users_db'

dbs = {
        'default': join(TEST_DB_PATH, DB_TEST),
        'test': join(TEST_DB_PATH, DB_TEST),  # already in settings/base.py
        'lgueneau': '/Users/jdelafon/Workspace/sib/gemini/Exome_AR_130730_OBIWAN_0036.db',
      }
for name, path in dbs.items():
    DATABASES[name] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': path
    }

logging.info("--------------------------------------")
