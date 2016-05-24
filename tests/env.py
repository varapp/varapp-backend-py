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

## Email
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_FROM = 'varapp@varapp.vital-it.ch'

## Gemini dbs
GEMINI_DB_PATH = './resources/db/test'
DB_TEST = 'testdb_0036.db'
WARMUP_STATS_CACHE = True
WARMUP_GENOTYPES_CACHE = True

## Users db
DB_USERS = 'testdb_0036.db'
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PWD = 'pwd'

dbs = {
        'default': join(GEMINI_DB_PATH, DB_USERS),
        'test': join(GEMINI_DB_PATH, DB_TEST),
      }
for name, path in dbs.items():
    DATABASES[name] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': path
    }

logging.info("--------------------------------------")
