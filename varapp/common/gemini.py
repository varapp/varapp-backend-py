"""
Extracting info from a Gemini database
"""
from django.db import connections
import os, re

def get_gemini_version(db):
    """Return the version of Gemini used to produce this database."""
    cursor = connections[db].cursor()
    version = cursor.execute('SELECT * FROM version').fetchone()[0]
    return version

def fetch_resources(db):
    """Get the list of gemini databases used for the annotation.
    Return a list ["##header_line1", "##header_line2", ...]"""
    cursor = connections[db].cursor()
    names = cursor.execute('SELECT * FROM resources').fetchall()  # last is blank
    return names

def fetch_vcf_header(db):
    """Get the VCF header as a list of strings, each starting with ## or #.
        Return a list [(key, "filename.gz"), ...]"""
    cursor = connections[db].cursor()
    vcf_header = cursor.execute('SELECT * FROM vcf_header').fetchone()[0].split('\n')[:-1]  # last is blank
    return vcf_header

def get_gatk_version(vcf_header):
    gatk_version = None
    for line in vcf_header:
        if line.startswith('##GATKCommandLine'):
            v = re.search(r'Version=(\S*),', line)
            if v:
                gatk_version = v.group(1)
    return gatk_version

def get_vep_info(vcf_header):
    vep_info = {}
    vep_version = None
    for line in vcf_header:
        if line.startswith('##VEP'):
            for x in line.strip().lstrip('#').split():
                if '=' in x:
                    x = x.split('=')
                    vep_info[x[0]] = os.path.basename(x[1])
            vep_version = vep_info.pop('VEP')
    return vep_version, vep_info

