#!/usr/bin/env python3
"""
Read the 'resources' and 'vcf_header' tables from the Gemini database to
record the annotations versions in our Annotation table in users_db,
in order to keep track of previous works when a Gemini database is updated.

If the annotations for that db already exist, does nothing unless 'overwrite' is set to 1.
"""

from django.conf import settings
from varapp.models.users import Annotation, VariantsDb
from varapp.common import gemini
from varapp.common.db_utils import is_test_vdb
import sys, logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(message)s')

DEBUG = False and settings.DEBUG


def add_versions(dbname, overwrite=False):
    """Add versions info for an active connection *dbname* (assumed to be unique)"""
    vcf_header = gemini.fetch_vcf_header(dbname)
    gemini_resources = gemini.fetch_resources(dbname)
    gemini_version = gemini.get_gemini_version(dbname)
    gatk_version = gemini.get_gatk_version(vcf_header)
    vep_version, vep_resources = gemini.get_vep_info(vcf_header)

    db = VariantsDb.objects.get(name=dbname, is_active=1)
    if is_test_vdb(db):
        return

    annots = Annotation.objects.filter(variants_db=db)
    if annots and overwrite:
        annots.delete()
        annots = None
    if not annots:
        logging.info("Adding versions info to database '{}'".format(dbname))
        Annotation.objects.get_or_create(variants_db=db, source='GATK', source_version=gatk_version)
        for resource,version in vep_resources.items():
            Annotation.objects.get_or_create(variants_db=db, source='VEP', source_version=vep_version,
                                      annotation=resource, annotation_version=version)
        for resource,version in gemini_resources:
            Annotation.objects.get_or_create(variants_db=db, source='Gemini', source_version=gemini_version,
                                      annotation=resource, annotation_version=version)
