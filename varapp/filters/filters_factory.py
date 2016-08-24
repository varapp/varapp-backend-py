"""
Defines ways to create FilterCollections (from a list of parameters
or a GET request that provides them).
"""

from varapp.filters.filters import FiltersCollection
from varapp.filters.variant_filters import *
from varapp.filters.genotype_filters import *
from varapp.samples.samples_service import samples_selection_from_request
import re


variant_filters_map = {
    'variant_id': VariantIDFilter,
    # Quality
    'quality': QualityFilter,
    'pass_filter': PassFilter,
    'qual_depth': QualDepthFilter,
    'fisher_strand_bias': StrandBiasFilter,
    'strand_bias_odds_ratio': SorFilter,
    'rms_map_qual': RmsMapQualFilter,
    'base_qual_rank_sum': BaseQualRankSumFilter,
    'map_qual_rank_sum': MapQualRankSumFilter,
    'read_pos_rank_sum': ReadPosRankSumFilter,
    # Location
    'gene_symbol': GeneFilter,
    'transcript': TranscriptFilter,
    'location': LocationFilter,
    # Frequency
    'in_dbsnp': DbsnpFilter,
    'in_1kg': ThousandGenomesFilter,
    'in_esp': ESPFilter,
    'in_exac': EXACFilter,
    # Impact
    'type': TypeFilter,
    'is_exonic': IsExonicFilter,
    'is_coding': IsCodingFilter,
    'is_lof': IsLofFilter,
    'impact': ImpactFilter,
    'impact_so': ImpactSoFilter,
    'impact_severity': ImpactSeverityFilter,
    # Pathogenicity
    'cadd_raw': CaddRawFilter,
    'cadd_scaled': CaddScaledFilter,
    'gerp_bp_score': GERPScoreFilter,
    #'gerp_element_pval': GERPPvalueFilter,
    'polyphen_pred': PolyphenPredFilter,
    'polyphen_score': PolyphenScoreFilter,
    'sift_pred': SiftPredFilter,
    'sift_score': SiftScoreFilter,
}
for freqdb in FrequencyFilter.dbs:
    for pop in FrequencyFilter.pops[freqdb]:
        variant_filters_map["aaf_{}_{}".format(freqdb,pop)] = FrequencyFilter(freqdb, pop)

genotype_filters_map = {
    'nothing': GenotypesFilterDoNothing,
    'active': GenotypesFilterActive,
    'dominant': GenotypesFilterDominant,
    'recessive': GenotypesFilterRecessive,
    'de_novo': GenotypesFilterDeNovo,
    'compound_het': GenotypesFilterCompoundHeterozygous,
    'x_linked': GenotypesFilterXLinked,
}


def genotype_filter_factory(filter_name, db, samples_selection):
    """From a string such as 'dominant', build the actual Genotype Filter
    :rtype: GenotypeFilter
    """
    return genotype_filters_map[filter_name](samples_selection, db=db)

def variant_filter_factory(name, op, val, db=None, samples_selection=None):
    """Create a VariantFilter from its characteristics.
    :rtype: VariantFilter
    """
    if name in variant_filters_map:
        f = variant_filters_map[name](name=name, val=val, op=op, db=db)
    elif name == 'genotype':
        f = genotype_filter_factory(val, db, samples_selection)
    else:
        raise ValueError("Unknown filtering option: '{}={}'.".format(name, val))
    return f

def variant_filters_collection_factory(filters, samples_selection=None, db='default'):
    """Creates a list of Filter subclass instances from a list of (name,op,val) tuples.
    (name: filter name, op: '[<>=]', val: filter value).
    :param samples_selection: SamplesSelection, in case it had already been calculated.
    :param filters: list of tuples (name,op,val).
    :rtype: FiltersCollection
    """
    filters_collection = []
    for name, op, val in filters:
        f = variant_filter_factory(name, op, val, db, samples_selection)
        filters_collection.append(f)
    return FiltersCollection(filters_collection)

def variant_filters_from_request(request, db, samples_selection=None):
    """Parse a GET Request and return a list of requested filters.
    A filter is a tuple (name, operation, value), corresponding to a request
    of the type '?name=value'. See the REST API documentation for more information.
    :rtype: FiltersCollection
    """
    filters = []
    filterlist = request.GET.getlist('filter', [])
    if samples_selection is None:
        samples_selection = samples_selection_from_request(request, db)
    for f in filterlist:
        m = re.match(r"(\S+?)([<>=]{1,2})(.+)", f)
        if m:
            k, op, v = m.groups()
            filters.append((k, op, v))
        else:
            filters.append((f, '=', '1'))
    return variant_filters_collection_factory(filters, samples_selection, db)

