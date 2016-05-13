import collections
from varapp.common.genotypes import decode_int
from varapp.constants.filters import ALL_VARIANT_FILTER_NAMES
from varapp.filters.sort import Sort
from varapp.models.gemini import Variants, GeneDetailed

# For export to frontend
_variant_genotype_expose = {0: [0,0], 1: [0,1], 2: [None,None], 3: [1,1]}
# Actually gt_types=2 means that it is unknown,
# cf. https://github.com/arq5x/gemini/blob/master/gemini/gemini_constants.py and google groups.

VARIANT_FIELDS = [f.name for f in Variants._meta.get_fields()] + ['source']

# A simple, lighter model of Variant - an object with same fields but without special methods
VariantTuple = collections.namedtuple('VariantTuple', VARIANT_FIELDS)
VariantTriplet = collections.namedtuple('VariantTriplet', ['variant_id','gene_symbol','source'])  # for compound het
VariantMono = collections.namedtuple('VariantMono', 'variant_id')  # for other gen filters
VariantTupleStats = collections.namedtuple('VariantTupleStats', ALL_VARIANT_FILTER_NAMES)  # for stats

# Proxy model for variants
# Making all the changes to the data that are necessary to filter correctly
class Variant(Variants):
    source = ''
    class Meta:
        proxy = True


class VariantsCollection:
    """A list of variants - such as the result of evaluating a QuerySet,
    the result of a query (filtering) of the databse.
    """
    def __init__(self, variants, cache_key=None, db=None):
        """Construct a VariantsCollection based on either a QuerySet
        (which we evaluate with `list()`) or a list of Variant objects.
        :param db: the name of the db these variants come from.
        """
        self.list = list(variants)
        self.cache_key = cache_key
        self.db = db

    def __getitem__(self, item):
        return self.list[item]

    def __len__(self):
        return len(self.list)
        #return self.variants.count() if self._n is None else self._n

    def __next__(self):
        return next(self.list)

    def __add__(self, other):
        return VariantsCollection(self.list + other.list, db=self.db)

    @property
    def ids(self):
        return [v.variant_id for v in self.list]

    def pop(self, i):
        self.list.pop(i)

    def remove(self, elt):
        self.list.remove(elt)

    def append(self, sample):
        self.list.append(sample)

    def extend(self, other):
        self.list.extend(other.list)

    def sub(self, a, b=None):
        """Return a new collection with only the first N variants."""
        if b is None:
            return VariantsCollection(self.list[:a], db=self.db)
        else:
            return VariantsCollection(self.list[a:b], db=self.db)

    def get_field_values(self, field_name):
        """ Return a list of all values for the given field_name."""
        return [getattr(v, field_name) for v in self.list]

    def order_by(self, key, reverse=False):
        """Return a new ordered collection of the same elements.
        :param key: either a string with the attribute or a list of keys. The special
            'location' parameter can be passed, to sort them by chrom + start (chromosome as a string)
        :param reverse: if True, sort in the reverse order.
        """
        keyl = Sort(key, reverse).key_condition
        return VariantsCollection(sorted(self.list, key=keyl, reverse=reverse), db=self.db)

    def sort_inplace(self, key, reverse=False):
        """Order the collection in-place"""
        keyl = Sort(key, reverse).key_condition
        self.list.sort(key=keyl, reverse=reverse)

    def __str__(self):
        return "<Collection of {} variants>".format(len(self.list))

    def expand(self):
        return '\n'.join([str(v) for v in self.list])

    def expose(self):
        return [v.expose() for v in self.list]


def expose_variant(v):
    """The JSON to return to the frontend"""
    return {
        "variant_id": v.variant_id,
        "chrom": v.chrom,
        "start": v.start + 1,
        "end": v.end,
        "ref": v.ref,
        "alt": v.alt,
        "quality": v.quality,
        "genotypes_index": [_variant_genotype_expose[i] for i in decode_int(v.gt_types_blob)] if v.gt_types_blob else [],
        "pass_filter": v.pass_filter or 'PASS',
        "dbsnp": v.dbsnp.split(',') if v.dbsnp is not None else [],
        "is_exonic": v.is_exonic,
        "is_coding": v.is_coding,
        "aaf_1kg_all": v.aaf_1kg_all,
        "aaf_esp_all": v.aaf_esp_all,
        "aaf_exac_all": v.aaf_exac_all,
        "aaf_max_all": v.aaf_max_all,
        "gene_symbol": v.gene_symbol,
        "ensembl_transcript_id": v.transcript,
        "impact": v.impact,
        "impact_severity": v.impact_severity,
        "aa_change": v.aa_change,
        "polyphen_pred": v.polyphen_pred,
        "polyphen_score": v.polyphen_score,
        "sift_pred": v.sift_pred,
        "sift_score": v.sift_score,
        "cadd_raw": v.cadd_raw,
        "cadd_scaled": v.cadd_scaled,
        "clinvar_sig": v.clinvar_sig,
        "clinvar_disease_acc": v.clinvar_disease_acc.split("|") if v.clinvar_disease_acc is not None else [],
        "gerp_bp_score": v.gerp_bp_score,
        "gerp_element_pval": v.gerp_element_pval,
        "source": v.source,
        "qual_depth": v.qual_depth,
        "fisher_strand_bias": v.fisher_strand_bias,
        "rms_map_qual": v.rms_map_qual,
        "hgvsp": v.hgvsp,
        "hgvsc": v.hgvsc,
        "read_depth": v.read_depth,
        "allele_count": v.allele_count,
        "allele_freq": v.allele_freq,
        "base_qual_rank_sum": v.base_qual_rank_sum,
        "map_qual_rank_sum": v.map_qual_rank_sum,
        "read_pos_rank_sum": v.read_pos_rank_sum,
        "strand_bias_odds_ratio": v.strand_bias_odds_ratio,
    }

def add_genotypes_selection(v_exposed, samples_selection):
    v_exposed["genotypes_index"] = samples_selection.select_x_active(v_exposed["genotypes_index"])
    return v_exposed

def expose_variant_full(v, samples_selection):
    exp = expose_variant(v)
    exp = add_genotypes_selection(exp, samples_selection)
    return exp

def annotate_variants(variants, db):
    transcripts = [v['ensembl_transcript_id'] for v in variants]
    gd = GeneDetailed.objects.using(db).filter(transcript__in=transcripts).values_list(
        'transcript', 'ensembl_gene_id', 'entrez_id'
    )
    annot = {}
    for t,ensg,entrez in gd:
        annot[t] = (ensg, entrez)
    for v in variants:
        enst = v['ensembl_transcript_id']
        ann = annot.get(enst)
        if ann:
            v['ensembl_gene_id'] = ann[0]
            v['entrez_gene_id'] = ann[1]
    return variants


