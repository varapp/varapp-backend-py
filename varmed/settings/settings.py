from varmed.settings.base import *

import os, sys, logging
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format='%(message)s')

logging.info("\n-----------  << RESTART >> -----------\n")
logging.info("Settings file: " + os.path.basename(__file__))

## General
DEBUG = True
HOST = 'localhost'
BASE_URL = 'http://localhost:8000'
SECRET_KEY = 'K6QKN6C2xtcl.'
ALLOWED_HOSTS = ['localhost']  # CORS

## Email
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_FROM = 'varapp@varapp.vital-it.ch'

## Gemini dbs
GEMINI_DB_PATH = '/path/to/gemini/dbs'  # path to Gemini databases container
FILL_DBS = True  # whether to fill VariantsDb with Gemini databases found in DB_PATH
CHECK_HASH = False  # whether to check if a db with the same name as in users_db is an upgrade or identical
WARMUP_STATS_CACHE = False  # Generate stats cache for all active dbs at startup
WARMUP_GENOTYPES_CACHE = False  # Generate genotypes cache for all active dbs at startup

## Users db
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PWD = 'pwd'

## Add the users_db to DATABASES
DATABASES['default'] = {
    'ENGINE': 'django.db.backends.mysql',
    'NAME': DB_USERS,
    'USER': MYSQL_USER,
    'PASSWORD': MYSQL_PWD,
    'HOST': MYSQL_HOST,
    #'PORT': '',
}

logging.info("--------------------------------------")

