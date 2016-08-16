import logging
import re
from varapp.samples.samples_factory import *


def samples_selection_from_request(request, db, from_ped=True):
    """Parse a GET request to make the samples groups and return a SamplesSelection.
    :param from_ped: read groups info based on 'phenotype' attribute in the Samples table.
    """
    groups = {}
    sample_requests = request.GET.getlist('samples',[])
    samples = samples_selection_factory(db).sort('sample_id')  # a SamplesCollection
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
