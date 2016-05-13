from varapp.models.gemini import Samples
from varapp.data_models.samples import SamplesSelection, Sample
import itertools
from operator import attrgetter


def sample_factory(s:Samples):
    """Create a more useful Sample instance from a Django Samples instance *s*."""
    return Sample(s.name, s.sample_id, s.family_id, s.maternal_id, s.paternal_id, s.sex, s.phenotype)

def samples_list_from_db(db, query_set=None):
    """Return a list of `Sample`s from database content."""
    if query_set is None:
        query_set = Samples.objects.using(db).all().order_by('sample_id')
    return [sample_factory(s) for s in query_set]

def samples_selection_factory(db, groups=None, query_set=None):
    """Create a more useful SamplesCollection instance from a Django Samples QuerySet *query_set*,
    or from the whole database content (with *db*).
    :param groups: a dict {group_name: list of sample names}. If set to 'ped', use the samples'
        'phenotype' attribute to build the groups.
    """
    samples_list = samples_list_from_db(db, query_set)
    if groups == 'ped':
        groups = fetch_ped_info_groups(samples_list)
    return SamplesSelection(samples_list, groups, db=db)

def fetch_ped_info_groups(samples):
    """Read phenotype info in the Samples table of Gemini, which is built on the PED.
    :param samples: a SamplesCollection
    """
    names = {'1':'not_affected', '2':'affected'}
    groups = {}
    for phenotype, group in itertools.groupby(sorted(samples, key=attrgetter('phenotype')), attrgetter('phenotype')):
        if names.get(phenotype):
            group_name = names[phenotype]
            groups[group_name] = [s.name for s in group]
    return groups

