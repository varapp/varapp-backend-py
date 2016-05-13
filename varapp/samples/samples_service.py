import logging
import re
from varapp.samples.samples_factory import *


class _SamplesService:
    """Read samples from the database.
    :param db: the database name ('default', 'test'...)"""
    def __init__(self, db):
        self._db = db
        self._samples_selection = None

    def all(self):
        """:return the list of all samples, only read once."""
        if self._samples_selection is None:
            self._samples_selection = samples_selection_factory(self._db)
        return self._samples_selection

_samplesServiceCache = {}

def samples_service(db):
    """
    Provides a cached samples service to access the given database.
    :param db: database name (default is 'default')
    """
    if _samplesServiceCache.get(db) is None:
        logging.info("Init samples cache for db {}.".format(db))
        _samplesServiceCache[db] = _SamplesService(db)
    return _samplesServiceCache[db]


def samples_selection_from_request(request, db, from_ped=True):
    """Parse a GET request to make the samples groups and return a SamplesSelection.
    :param from_ped: read groups info based on 'phenotype' attribute in the Samples table.
    """
    groups = {}
    sample_requests = request.GET.getlist('samples',[])
    samples = samples_service(db).all().sort('sample_id')  # a SamplesCollection
    if not sample_requests:
        if from_ped:
            groups = fetch_ped_info_groups(samples)
        else:
            groups = {}
        return SamplesSelection(samples, groups, db=db)
    elif all(x == '' for x in sample_requests):
        return SamplesSelection(samples, {}, db=db)
    else:
        for sr in sample_requests:
            m = re.match(r"(\S+?)=(\S+)", sr)
            if not m:
                raise ValueError("Wrong samples request (expected '<group>=<samples list>', got '{}').".format(sr))
            gname,snames = m.groups()
            snames = snames.split(',')
            group = samples.get_list(snames)
            if len(group) != len(snames):
                raise ValueError("Unknown samples: {}".format(
                    set(snames) - set([s.name for s in group])))
            groups[gname] = [s.name for s in group]
        return SamplesSelection(samples, groups, db=db)
