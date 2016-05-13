"""
Extract annotation information from the supplementary tables shipped with
Gemini: gene_summary, gene_detailed.
"""

from django.db import connections, OperationalError
from django.core.cache import caches
from varapp.annotation.genomic_range import GenomicRange
import sys, logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(message)s')


def _check_table_exists(db, table_name):
    assert db is not None, "Expected table name (str), got None."
    cursor = connections[db].cursor()
    request = 'SELECT gene FROM {} LIMIT 1'.format(table_name)
    try:
        cursor.execute(request)
    except OperationalError:
        raise FileNotFoundError("Table not found: {}.")


class GeneSummaryService:
    """Read gene location from gene_summary table.
    This table has one line for one gene, no distinction between transcripts.
    This is the connection to the database table, only once.
    Used to find the genomic range of a chromosome or a gene given its symbol.

    :param db: the database name
    """
    def __init__(self, db):
        self._db = db
        self._gene_names = None
        self._gene_dict = None
        self._chrom_dict = None
        _check_table_exists(db, "gene_summary")
        self._init()

    def ready(self):
        return self._gene_names is not None and self._gene_dict is not None and self._chrom_dict is not None

    def _init(self):
        if self._chrom_dict is None:
            self.chrom_dict()
        if self._gene_names is None:
            self.gene_names()
        if self._gene_dict is None:
            self.gene_dict()
        return self

    def chrom_dict(self):
        """Build (and cache) a map {chrom -> range}.
        Actually we cannot know the real chromosome range from Gemini,
        only from the first to the last variant, but anyway we filter only those."""
        if self._chrom_dict is None:
            cursor = connections[self._db].cursor()
            request = 'SELECT chrom,MIN(start),MAX(end) FROM variants GROUP BY chrom'
            cursor.execute(request)
            self._chrom_dict = {
                r[0].lower(): {'location': [GenomicRange(r[0], int(r[1]), int(r[2]))]}
                for r in cursor.fetchall()
            }
        return self._chrom_dict

    def gene_names(self):
        """Build and cache a set of gene names."""
        if self._gene_names is None:
            cursor = connections[self._db].cursor()
            request = 'SELECT DISTINCT gene FROM gene_summary'
            cursor.execute(request)
            self._gene_names = {x[0] for x in cursor.fetchall()}
            # gemini bug before 0.18.3
            if 'None' in self._gene_names:
                self._gene_names.remove('None')
            if None in self._gene_names:
                self._gene_names.remove(None)
        return self._gene_names or set()

    def gene_dict(self):
        """
        Build (and cache) a map {gene_name -> annotation}
        :return a dictionary {gene_name -> {annotation}}
        """
        if self._gene_dict is None:
            cursor = connections[self._db].cursor()
            request = 'SELECT gene,chrom,transcript_min_start,transcript_max_end FROM gene_summary'
            cursor.execute(request)
            self._gene_dict = {}
            for r in cursor.fetchall():
                symbol = r[0]
                if symbol is None:
                    continue
                symbol = symbol.lower()
                self._gene_dict.setdefault(symbol, {'location': []})
                self._gene_dict[symbol]['location'].append(GenomicRange(r[1], int(r[2]), int(r[3])))
        return self._gene_dict

    def __getitem__(self, symbol):
        """Given a gene symbol, return the associated annotation
        (a dict `{'location':GenomicRange, ...}`).
        If the gene is not found, search for a chromosome name instead."""
        return self.gene_dict().get(symbol.lower(),
               self.chrom_dict().get(symbol.lower()))

    def get_genes(self):
        return self.gene_names()


def gene_summary_service(db, new=False):
    """
    Provides a cached variant service to access the given database.
    :param db: database name
    """
    gene_summary_cache = caches['gene_summary']
    if gene_summary_cache.get(db) is None or new is True:
        logging.info("Init gene summary cache for db {}.".format(db))
        gene_summary_cache.set(db, GeneSummaryService(db))
    return gene_summary_cache.get(db)

