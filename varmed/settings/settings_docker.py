from varmed.settings.base import *
import os, sys, logging
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format='%(message)s')
logging.info("\n-----------  << RESTART >> -----------\n")
logging.info("Settings file: " + os.path.basename(__file__))

## General
DEBUG = True                        # If True, will return full tracebacks when an HTTP error is produced. Set to False in production!
HOST = 'localhost'                  # Hostname, as returned by "hostname --fqdn" on unix.
BASE_URL = 'http://localhost:8000'  # URL to serve the app to.
SECRET_KEY = 'K6QKN6C2xtcl.'        # Used to generate authentication tokens. Change it and keep it secret!

## Email: SMTP server configuration
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_FROM = 'varapp@varapp.vital-it.ch'

## Gemini dbs
GEMINI_DB_PATH = './resources/db'   # Path to Gemini databases container
WARMUP_STATS_CACHE = True           # Generate stats cache for all active dbs at startup
WARMUP_GENOTYPES_CACHE = True       # Generate genotypes cache for all active dbs at startup

## Users db
DB_USERS = 'users_db'               # Name of the main database, that stores sessions, db connections etc.
MYSQL_HOST = 'mysql_1'   # called like this in a docker container, for whatever reason
MYSQL_USER = 'root'   # cf. docker-compose.yml
MYSQL_PWD = 'pwd'     # cf. docker-compose.yml
MYSQL_PORT = '3306'   # cf. docker-compose.yml

## Adds the users_db to DATABASES
DATABASES['default'] = {
    'ENGINE': 'django.db.backends.mysql',
    'NAME': DB_USERS,
    'USER': MYSQL_USER,
    'PASSWORD': MYSQL_PWD,
    'HOST': MYSQL_HOST,
    'PORT': MYSQL_PORT,
}

# Change the location of the redis service
CACHES['redis']['LOCATION'] = 'redis://redis:6379'

logging.info("--------------------------------------")

