"""
Custom filters on Variant QuerySets.
Build the Filter with a Request, then apply() it to a QuerySet.
"""
from django.db.models import Q
from varapp.filters.filters import VariantFilter
from varapp.annotation.location_service import LocationService
from varapp.constants.filters import *
import operator
from functools import reduce

DJANGO_OP = {
    '<': '__lt',
    '<=': '__lte',
    '>': '__gt',
    '>=': '__gte',
    '=': '',
    '==': '',
}


class VariantIDFilter(VariantFilter):
    """Return variants given a (comma-separated string) list of their ids."""
    field_name = 'variant_id'

    def parse_arg(self, arg):
        return set(map(int,arg.split(',')))

    def condition(self, variant):
        return variant.variant_id in self.val

    def sql_condition(self):
        s = 'variant_id IN '+ str(tuple(self.val))
        return s

    def django_condition(self):
        return Q(variant_id__in=tuple(self.val))


class BinaryFilter(VariantFilter):
    """Filters that expect a binary value."""
    def parse_arg(self, arg):
        t = {'1': True, '0': False, 'true': True, 'false': False}
        return True if arg is None else t[arg.lower()]

    def condition(self, variant):
        return getattr(variant, self.field_name) == self.val

    def sql_condition(self):
        s = self.field_name + '=' + str(self.val).lower()
        return s

    def django_condition(self):
        return Q(**{self.field_name: self.val})


class EnumFilter(VariantFilter):
    """Filters taking values in a finite list, possibly several of them.
    *sensitive*: (bool) True = case-sensitive.
    """
    sensitive = False

    def __init__(self, val='', name='', op='=', db=''):
        super().__init__(val=val, name=name, op=op)

    def parse_arg(self, arg):
        if self.sensitive:
            return set(arg.split(','))
        else:
            return set(x.casefold() for x in set(arg.split(',')))

    def condition(self, variant):
        value = getattr(variant, self.field_name)
        if self.sensitive:
            return str(value) in self.val
        else:
            return str(value).casefold() in self.val

    def sql_condition(self):
        s = self.field_name +' IN '+ str(tuple(self.val))
        if self.sensitive:
            s += ' COLLATE SQL_Latin1_General_CP1_CS_AS'  # change 'collation' to case sensitive
        return s

    def django_condition(self):
        if self.sensitive:
            return Q(**{self.field_name+'__in': self.val})
        else:
            if not self.val:
                return Q(**{'variant_id__lt': 0})  # always false
            # Cannot use 'field__iexact__in', so ose OR between Q objects
            q_list = map(lambda n: Q(**{self.field_name+'__iexact': n}), self.val)
            q = reduce(lambda a,b: a|b, q_list)
            return q


class LocationFilter(VariantFilter):
    """Filter based on genomic location: `chromosome:start-end`."""
    field_name = 'location'
    filter_class = FILTER_CLASS_LOCATION

    def parse_arg(self, arg):
        """Return a list of `GenomicRange`s"""
        return LocationService(db=self.db).find(arg)

    def condition(self, variant):
        return any (
            (variant.chrom == loc.chrom) and (variant.start+1 >= loc.start) and (variant.end <= loc.end)
            for loc in self.val)

    def django_condition(self):
        if not self.val:
            return Q(**{'variant_id__lt': 0})  # always false
        elif len(self.val) > 300:
            raise ValueError("Cannot search for more than 300 locations because of SQLite limitations.")
        q_list = map(
            lambda loc: Q(**{'chrom':loc.chrom, 'start__gte':loc.start-1, 'end__lte':loc.end}),
            self.val)
        q = reduce(lambda a,b: a|b, q_list)
        return q

    def sql_condition(self):
        pass


class ContinuousFilter(VariantFilter):
    """Filters taking a float value, and a comparison operator (<=, >, etc.).
    If the actual variant value is None, it is interpreted as -inf in numeric comparisons.
    """
    comparison_operator = {'>=': operator.ge, '<=': operator.le, '=': operator.eq,
                           '<': operator.lt, '>': operator.gt, '==': operator.eq}

    def __init__(self, val='', name='', op='', db='', none_is='exclude'):
        """:param none_is:
            If 'lower', None is inferior to all values (e.g. rare frequency).
            If 'higher', None is superior to all values (e.g. p-values).
            If 'exclude', None values are excluded if the filter is selected (no value means not interesting).
            If 'include', None values are included whatever the filter (no value means we don't know).
        """
        super().__init__(val=val, name=name, op=op)
        self.val = self._tryparse(val)
        if op not in self.comparison_operator:
            raise ValueError("Unknown comparison operator: '{}'.".format(self.op))
        self.op = op
        self.compare = self.comparison_operator.get(op)
        self.none_is = none_is
        self.none_comparison_result = False
        if none_is == 'lower':
            self.none_comparison_result = op in ['<=','<']
        elif none_is == 'higher':
            self.none_comparison_result = op in ['>=','>']
        elif none_is == 'include':
            self.none_comparison_result = True

    def parse_arg(self, val):
        return float(val)

    def condition(self, variant):
        value = getattr(variant, self.field_name)
        if value is None:
            return self.none_comparison_result
        return self.compare(float(value), self.val)

    def sql_condition(self):
        s = '{} {} {}'.format(self.field_name, self.op, self.val)
        if self.none_comparison_result is True:
            s += ' OR {} IS NULL'
        return s

    def django_condition(self):
        q = Q(**{self.field_name + DJANGO_OP[self.op]: self.val})
        if self.none_comparison_result is True:
            q = q | Q(**{self.field_name+'__isnull': self.none_comparison_result})
        return q


## Handle Nones. By default they are excluded whatever the filter value is.

class ContinuousFilterNoneLower(ContinuousFilter):
    """None is lower than any other value"""
    def __init__(self, val='', name='', op='', db=''):
        super().__init__(val, name, op, db, none_is='lower')

class ContinuousFilterNoneHigher(ContinuousFilter):
    """None is higher than any other value"""
    def __init__(self, val='', name='', op='', db=''):
        super().__init__(val, name, op, db, none_is='higher')

class ContinuousFilterNoneInclude(ContinuousFilter):
    """None is included whatever the filter value is"""
    def __init__(self, val='', name='', op='', db=''):
        super().__init__(val, name, op, db, none_is='include')


# FILTER_CLASS_QUALITY

class QualityFilter(ContinuousFilter):
    """Return variants with quality (VCF `QUAL` field) greater/lesser than a given value."""
    field_name = 'quality'
    filter_class = FILTER_CLASS_QUALITY

class PassFilter(EnumFilter):
    """Filter according to the VCF `FILTER` field."""
    field_name = 'pass_filter'
    filter_class = FILTER_CLASS_QUALITY

    def parse_arg(self, arg):
        val = set(x.casefold() for x in set(arg.split(',')))
        return [None if v == 'pass' else v for v in val]

class QualDepthFilter(ContinuousFilter):
    """Variant confidence or quality by depth."""
    field_name = 'qual_depth'
    filter_class = FILTER_CLASS_QUALITY

class StrandBiasFilter(ContinuousFilter):
    """Strand bias at the variant position"""
    field_name = 'fisher_strand_bias'
    filter_class = FILTER_CLASS_QUALITY

class SorFilter(ContinuousFilter):
    """Symmetric Odds Ratio of 2x2 contingency table to detect strand bias."""
    field_name = 'strand_bias_odds_ratio'
    filter_class = FILTER_CLASS_QUALITY

class RmsMapQualFilter(ContinuousFilter):
    field_name = 'rms_map_qual'
    filter_class = FILTER_CLASS_QUALITY

class BaseQualRankSumFilter(ContinuousFilter):
    field_name = 'base_qual_rank_sum'
    filter_class = FILTER_CLASS_QUALITY

class MapQualRankSumFilter(ContinuousFilter):
    field_name = 'map_qual_rank_sum'
    filter_class = FILTER_CLASS_QUALITY

class ReadPosRankSumFilter(ContinuousFilter):
    field_name = 'read_pos_rank_sum'
    filter_class = FILTER_CLASS_QUALITY


# FILTER_CLASS_LOCATION

class GeneFilter(EnumFilter):
    """Return variants located inside a given gene (given by its name/symbol)."""
    field_name = 'gene_symbol'
    filter_class = FILTER_CLASS_LOCATION

class TranscriptFilter(EnumFilter):
    """Return variants located inside a given transcript (given by Ensembl ID)."""
    field_name = 'transcript'
    filter_class = FILTER_CLASS_LOCATION


# FILTER_CLASS_FREQUENCY

class DbsnpFilter(BinaryFilter):
    """Is this variant found in dbSNP? [0/1]"""
    field_name = 'in_dbsnp'
    filter_class = FILTER_CLASS_FREQUENCY

class ThousandGenomesFilter(BinaryFilter):
    """Is this variant in the 1000 genome project data (phase 3)? [0/1]."""
    field_name = 'in_1kg'
    filter_class = FILTER_CLASS_FREQUENCY

class ESPFilter(BinaryFilter):
    """Is this variant in the ESP project data? [0/1]."""
    field_name = 'in_esp'
    filter_class = FILTER_CLASS_FREQUENCY

class EXACFilter(BinaryFilter):
    """Is this variant in the ESP project data? [0/1]."""
    field_name = 'in_exac'
    filter_class = FILTER_CLASS_FREQUENCY

class FrequencyFilter:
    """Filter based on allele frequency in 1000 Genomes/ESP.
    Not a Filter itself, it returns a ContinuousFilter instance when called.

    :param freqdb: either '1kg' (100 Genomes) or 'esp' (ESP)
    :param pop: one of 'all','amr','eas','sas','afr','eur' (1000 Genomes)
        or one of 'all','ea','aa' (ESP).
    """
    dbs = ['1kg', 'esp', 'exac', 'max']
    #pops = {'1kg': ['all','amr','eas','sas','afr','eur' ], 'esp': ['all','ea','aa'], 'exac': ['all']}
    pops = {'1kg': ['all'], 'esp': ['all'], 'exac': ['all'], 'max': ['all']}

    def __init__(self, freqdb='1kg', pop='all'):
        self.freqdb = freqdb
        self.pop = pop
        self.name = 'aaf_{}_{}'.format(self.freqdb, self.pop)
        self.field_name = self.name

    def __call__(self, val, name=None, op='<=', db=''):
        name = name or self.name
        cf = ContinuousFilterNoneLower(val=val, name=name, op=op)  # None: super rare -> freq=0
        cf.field_name = name
        cf.filter_class = 'frequency'
        return cf


# FILTER_CLASS_IMPACT

# See http://gemini.readthedocs.org/en/latest/content/database_schema.html#details-of-the-impact-and-impact-severity-columns

class IsExonicFilter(BinaryFilter):
    """Does the variant affect an exon for >= 1 transcript? [0/1]"""
    field_name = 'is_exonic'
    filter_class = FILTER_CLASS_IMPACT

class IsCodingFilter(BinaryFilter):
    """Does the variant fall in a coding region (excl. 3’ & 5’ UTRs) for >= 1 transcript? [0/1]"""
    field_name = 'is_coding'
    filter_class = FILTER_CLASS_IMPACT

class IsLofFilter(BinaryFilter):
    """Based on the value of the impact col, is the variant LOF for >= transcript? [0/1]"""
    field_name = 'is_lof'
    filter_class = FILTER_CLASS_IMPACT

class ImpactFilter(EnumFilter):
    """The consequence of the most severely affected transcript."""
    field_name = "impact"
    filter_class = FILTER_CLASS_IMPACT
    sensitive = True

class ImpactSeverityFilter(EnumFilter):
    """Severity of the impact (HIGH, MED, LOW categories of impacts)."""
    field_name = "impact_severity"
    filter_class = FILTER_CLASS_IMPACT

class ImpactSoFilter(EnumFilter):
    """The Sequence ontology term for the most severe consequence."""
    field_name = "impact_so"
    filter_class = FILTER_CLASS_IMPACT
    sensitive = True


# FILTER_CLASS_PATHOGENICITY

class CaddRawFilter(ContinuousFilterNoneInclude):
    """Raw CADD scores for scoring deleteriousness of SNV’s in the human genome."""
    field_name = 'cadd_raw'
    filter_class = FILTER_CLASS_PATHOGENICITY

class CaddScaledFilter(ContinuousFilterNoneInclude):
    """Scaled CADD scores (Phred like) for scoring deleteriousness of SNV’s."""
    field_name = 'cadd_scaled'
    filter_class = FILTER_CLASS_PATHOGENICITY

class GERPScoreFilter(ContinuousFilterNoneInclude):
    """GERP conservation score. Higher scores reflect greater conservation."""
    field_name = 'gerp_bp_score'
    filter_class = FILTER_CLASS_PATHOGENICITY

class GERPPvalueFilter(ContinuousFilterNoneHigher):
    """GERP elements P-value. Lower P-values scores reflect greater conservation."""
    field_name = 'gerp_element_pval'
    filter_class = FILTER_CLASS_PATHOGENICITY

class PolyphenPredFilter(EnumFilter):
   """Polyphen predictions for the snps for the severely affected transcript (only VEP)."""
   field_name = 'polyphen_pred'
   filter_class = FILTER_CLASS_PATHOGENICITY

class PolyphenScoreFilter(ContinuousFilterNoneLower):
   """Polyphen scores for the severely affected transcript (only VEP)."""
   field_name = 'polyphen_score'
   filter_class = FILTER_CLASS_PATHOGENICITY

class SiftPredFilter(EnumFilter):
   """SIFT predictions for the snp’s for the most severely affected transcript (only VEP)."""
   field_name = 'sift_pred'
   filter_class = FILTER_CLASS_PATHOGENICITY

class SiftScoreFilter(ContinuousFilterNoneHigher):
   """SIFT scores for the predictions (only VEP)."""
   field_name = 'sift_score'
   filter_class = FILTER_CLASS_PATHOGENICITY
