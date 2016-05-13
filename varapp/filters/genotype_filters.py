"""
Filters on the result of boolean operations on multiple samples genotypes,
such as "all have the same genotype" or "all are homozygous".
"""
from django.conf import settings
from varapp.filters.apply_bitwise import c_apply_bitwise  # from cython extension
from varapp.constants.filters import FILTER_CLASS_GENOTYPE
from varapp.constants.genotype import *
from varapp.data_models.samples import SamplesSelection
from varapp.data_models.variants import *
from varapp.filters.filters import Filter, FilterResult, FiltersCollection
from varapp.variants.genotypes_service import genotypes_service
from varapp.variants.variants_factory import set_source
import abc, itertools, multiprocessing as mp
import numpy as np
from functools import reduce
from operator import attrgetter, itemgetter, __and__
from time import time

AND = 'AND'
OR = 'OR'
DEBUG = True and settings.DEBUG

def merge_conditions_array(conds):
    """If there are multiple affected samples sharing the same parents,
    the conditions can be redundant. Simplify the conditions array so that
    there is at most one for each genotype/sample. If there are several constraints
    for the same genotype, check that they are compatible and take the strongest
    (lowest bit value).
    :param conds: an array of couples [sample_index, genotype_bit]
    :rtype: same as input
    """
    merged = []
    if not conds:
        return merged
    # Group by sample index, and get a single common bit for all conds on that sample
    conds.sort(key=itemgetter(0))
    for idx,group in itertools.groupby(conds, itemgetter(0)):
        genbits = [x[1] for x in group]   # only the genotype bit
        common_bits = reduce(__and__, genbits)
        merged.append((idx, common_bits))
    return merged


class GenotypesFilter(Filter):
    """Defines a way to *apply* a filter on variants genotypes."""
    __metaclass__ = abc.ABCMeta
    filter_class = FILTER_CLASS_GENOTYPE
    need_groups = []  # The required group names in the samples selection for the filter to work.
    need_parents = 0  # Whether 0/1/2 parents are required for the filter to work

    def __init__(self, ss:SamplesSelection, val, name='genotype', op='=', db=None):
        super().__init__(name=name, op=op, val=val, ss=ss, db=db)
        self.nsamples = len(ss.active_idx)
        self.merge_op = AND
        self.shortcut = False  # Flag: if True, don't filter anything

        # Need at least one active sample
        if len(self.ss.active_idx) == 0:
            self.shortcut = True
        # If parents are required, check that both are present for at least one of the affected samples
        mothers_aff = [ss.mother_idx_of(s) for s in ss.affected]
        fathers_aff = [ss.father_idx_of(s) for s in ss.affected]
        if self.need_parents == 2 and all(None in x for x in zip(mothers_aff, fathers_aff)):
            self.shortcut = True
        elif self.need_parents == 1 and all((x,y)==(None,None) for x,y in zip(mothers_aff, fathers_aff)):
            self.shortcut = True
        # If certain groups are required, check that they are present in the selection
        if any((x not in ss.groups.keys() or len(ss.groups[x]) == 0) for x in self.need_groups):
            self.shortcut = True
        # The compound case implements its own stuff, but otherwise do that:
        if self.val != GENOTYPE_COMPOUND:
            conditions_array = self.build_conditions_array()
            self.conditions_array = merge_conditions_array(conditions_array)
            if len(self.conditions_array) == 0:
                self.shortcut = True
            self.conditions_vector = self.build_conditions_vector(self.conditions_array)

    def build_conditions_array(self):
        """Construct a list of lists [sample_idx, BITCODE], one for each sample.
        Then a variant passes if in its decoded gts, there is BITCODE at position idx.
        Once only: it is proper to the filter (with the list of all possible samples,
        but no samples selection)."""
        raise NotImplementedError("No `build_conditions_array` method implemented.")

    def build_conditions_vector(self, conditions_array):
        """From a *conditions_array*, of elements [sample_idx, BITCODE],
        build a vector of size len(active_samples) with BITCODE at indices
        where a condition is given, and GENOTYPE_BIT_ANY elsewhere.
        :rtype: np.ndarray[uint8]
        """
        active_idx = self.ss.active_idx
        conds = GENOTYPE_BIT_ANY * np.ones(len(active_idx), dtype=np.uint8)
        shift = {idx:i for i,idx in enumerate(active_idx)}
        for idx,bit in conditions_array:
            conds[shift[idx]] = bit
        return conds

    def scan_genotypes(self, genotypes, sub_ids=None, db=None):
        """Pass through all genotypes and return only the indices of those that pass the filter.
        :param genotypes: np.ndarray[uint64, dim=2]
        :rtype: np.ndarray[uint64]"""
        if self.shortcut:
            return np.zeros(0)
        N = len(genotypes)
        if sub_ids is not None:
            variant_ids = sub_ids
        elif self.val == 'x_linked' and db:
            variant_ids = genotypes_service(db).chrX
        else:
            variant_ids = np.asarray(range(1,N+1), dtype=np.uint64)
        active_idx = np.asarray(self.ss.active_idx, dtype=np.uint16)
        conditions = self.conditions_vector
        is_and = self.merge_op == AND
        if len(conditions) == 0:
            passing = variant_ids
        else:
            passing = self.parallel_apply_bitwise(genotypes, variant_ids, conditions, active_idx, is_and)
        return passing

    @staticmethod
    def parallel_apply_bitwise(genotypes, variant_ids, conditions, active_idx, is_and):
        """Run c_apply_bitwise in parallel. Takes the same arguments."""
        N = len(genotypes)
        nprocs = mp.cpu_count()
        pool = mp.Pool(processes=nprocs)
        B = round(N/nprocs + 0.5)  # batch size
        # Split variant_ids in batches (genotype batches are equally-sized, but not
        #   variant ids, in case a subset was given)
        split_at = variant_ids.searchsorted([(k+1)*B+1 for k in range(nprocs-1)])
        variant_ids_batches = np.split(variant_ids, split_at)
        assert len(variant_ids_batches) == nprocs
        # Run one job for each batch
        passing = [pool.apply(c_apply_bitwise,
            args=(genotypes[k*B:(k+1)*B,:],
                   variant_ids_batches[k],
                   conditions, active_idx, is_and, B))
            for k in range(nprocs)]
        passing = np.concatenate(passing)
        pool.close()
        return passing

    #@timer
    def apply(self, variants=None, genotypes=None, db=None, limit=None, offset=0):
        """Apply this collection of filters on a collection of variants.
        :param variants: a VariantsCollection or a QuerySet of variants.
            If None, makes a QuerySet of the whole *db*.
        :param db: database name. If no set, it tries to be inferred from *variants*.
        :param genotypes: a list of genotypes arrays.
            if None, a GenotypesService is created from the variants' db.
            In principle, set it for testing purposes only.
        :rtype: FilterResult
        """
        sub_ids = None
        if variants is None and db is not None:
            variants = Variant.objects.using(db)
        elif db is None:
            db = variants.db
        if self.shortcut:
            return FilterResult(variants=VariantsCollection([]), ids=[], n_filtered=0)
        if genotypes is None:
            assert db is not None, "Either a db name or a genotypes array is required"
            genotypes = genotypes_service(db).genotypes
        else:
            assert len(genotypes) == len(variants)
        if self.val == 'x_linked':
            if isinstance(variants, VariantsCollection):
                sub_ids = np.asarray([v.variant_id for v in variants if v.chrom=='chrX'], dtype=np.uint64)
            else:
                sub_ids = genotypes_service(db).chrX
        passing = self.scan_genotypes(genotypes, sub_ids=sub_ids, db=db)
        return FilterResult(
            variants=self.variants_from_mask(variants, passing, db, limit, offset),
            ids=passing,
            n_filtered=len(passing),
        )

    @staticmethod
    def variants_from_mask(variants, passing, db=None, limit=None, offset=0):
        """Get the collection of variants which id is in *passing*."""
        if limit is not None:
            passing = passing[offset:offset+limit]
        passing = set(passing)
        return VariantsCollection([v for v in variants if v.variant_id in passing], db=db)

    def __str__(self):
        return "<Filter {}>".format(self.short_str()) + ('-'+str(self.ss) if self.ss else '')

    def __repr__(self):
        return "<Filter {}>".format(self.short_str()) + ('-'+str(self.ss) if self.ss else '')


class GenotypesFilterDoNothing(GenotypesFilter):
    """A filter that every variant passes anyway."""
    def __init__(self, ss:SamplesSelection, db=None):
        super().__init__(ss, 'nothing', db=db)

    def build_conditions_array(self):
        assert self
        return [[i, GENOTYPE_BIT_ANY] for i in self.ss.active_idx]


class GenotypesFilterActive(GenotypesFilter):
    """Return a variant only if it is mutant in at least one of the active samples.
    """
    def __init__(self, ss:SamplesSelection, db=None):
        super().__init__(ss, GENOTYPE_ACTIVE, db=db)
        self.merge_op = OR

    def build_conditions_array(self):
        return [[i, GENOTYPE_BIT_CARRIER] for i in self.ss.active_idx]


class GenotypesFilterDominant(GenotypesFilter):
    """Simplest scenario: autosomal dominant.
    Suppose the effect is dominant, i.e. one allele
    mutated is enough to observe a phenotype.
    Filter variants that are mutated in all samples but the controls.
    """
    need_groups = ["affected"]

    def __init__(self, ss:SamplesSelection, db=None):
       super().__init__(ss, GENOTYPE_DOMINANT, db=db)

    def build_conditions_array(self):
        return [[i, GENOTYPE_BIT_CARRIER] for i in self.ss.affected_idx] + \
               [[i, GENOTYPE_BIT_NON_CARRIER] for i in self.ss.not_affected_idx]


class GenotypesFilterRecessive(GenotypesFilter):
    """Suppose the effect is recessive, i.e. a child must inherit a mutated
    allele from both carrier parents to have an observable phenotype.
    Filter mutations that are present in both the parents and homozygous
    in the "affected" children.
    Controls ("not_affected") are samples known to be non-carriers.
    """
    need_groups = ["affected"]

    def __init__(self, ss:SamplesSelection, db=None):
        super().__init__(ss, GENOTYPE_RECESSIVE, db=db)

    def build_conditions_array(self):
        conds = []  # 1 per sample, because of its particular parents
        for s in self.ss.affected:
            idx = self.ss.idx_of(s.name, active=True)
            conds.append([idx, GENOTYPE_BIT_CARRIER_HOM])
            for i in self.ss.parents_idx_of(s):
                conds.append([i, GENOTYPE_BIT_CARRIER])
        for i in self.ss.not_affected_idx:
            conds.append([i, GENOTYPE_BIT_NOT_CARRIER_HOM])
        return conds


class GenotypesFilterDeNovo(GenotypesFilter):
    """Case where a mutation is present in a child but not in the parents.
    So the controls should be the parents, but can include other non-carriers.
    Otherwise it is the same as the Dominant case.
    """
    need_groups = ["affected"]
    need_parents = 2

    def __init__(self, ss:SamplesSelection, db=None):
        super().__init__(ss, GENOTYPE_DENOVO, db=db)

    def build_conditions_array(self):
        conds = []   # 1 per sample, because of its particular parents
        for s in self.ss.affected:
            idx = self.ss.idx_of(s.name, active=True)
            parents_idx = self.ss.parents_idx_of(s)
            if len(parents_idx) == 2:   # pointless if not both parents present
                if len(set(parents_idx) & set(self.ss.affected_idx)) > 0:
                    continue            # pointless if one of the parents is affected
                conds.append([idx, GENOTYPE_BIT_CARRIER_HET])
                for i in parents_idx:
                    conds.append([i, GENOTYPE_BIT_NON_CARRIER])
        if conds:
            for i in self.ss.not_affected_idx:
                conds.append([i, GENOTYPE_BIT_NON_CARRIER])
        return conds


class GenotypesFilterXLinked(GenotypesFilter):
    """A deleterious mutation os present on chromosome X. Possible cases:
    a) Dominant case: Apart from the proportion of affected children
       of each sex, it behaves exactly like a usual dominant mutation,
       so we don't cover that case here:
       - Affected <=> carrier;
       - In principle one of the parents should carry it, but it could be de novo.
    b) Recessive case:
       - Affected <=> woman carrier hom, or man carrier het;
       - For a woman, both parents must be carriers (and the father is affected);
       - For a man, only the mother must be carrier.
    """
    need_groups = ["affected"]
    need_parents = 0

    def __init__(self, ss:SamplesSelection, db=None):
        super().__init__(ss, GENOTYPE_XLINKED, db=db)

    def build_conditions_array(self):
        conds = []  # 1 per sample, because of its particular parents
        for s in self.ss.affected:
            idx = self.ss.idx_of(s.name, active=True)
            # Male: carrier het, and the mother is carrier
            if s.sex == 'M':
                conds.append([idx, GENOTYPE_BIT_CARRIER_HET])
                i = self.ss.mother_idx_of(s)
                if i is not None:
                    conds.append([i, GENOTYPE_BIT_CARRIER])
            # Female: carrier hom, and both parents are carriers
            elif s.sex == 'F':
                conds.append([idx, GENOTYPE_BIT_CARRIER_HOM])
                for i in self.ss.parents_idx_of(s):
                    conds.append([i, GENOTYPE_BIT_CARRIER])
        for s in self.ss.not_affected:
            idx = self.ss.idx_of(s.name, active=True)
            # Male unaffected cannot be carriers
            if s.sex == 'M':
                conds.append([idx, GENOTYPE_BIT_NON_CARRIER])
            # Female unaffected could be carrier het
            elif s.sex == 'F':
                conds.append([idx, GENOTYPE_BIT_NOT_CARRIER_HOM])
        return conds


class GenotypesFilterCompoundHeterozygous(GenotypesFilter):
    """Case where two mutations, inherited one from each parent,
    occur in the same gene and thus code for two defective proteins.
    Compose two results:
        - father is carrier in that gene and child has it;
        - mother is carrier in that same gene and child has it.
    Notes:
    - We cannot group conditions for many samples as we did before, because
      they can be touched by different compounds pairs in the same gene (rare ?).
    - Neither of the parents can be homozygous, or he would be affected (both proteins are touched).
    - A child cannot be homozygous at any position of the compounds pair, because
      that would suffice to invalidate both proteins and is indistinguishable from the
      recessive case.
    - Both parents could be affected at one position of the compounds pair (rare ?).
    """
    need_groups = ["affected"]
    need_parents = 2

    def __init__(self, ss:SamplesSelection, db=None):
        super().__init__(ss, val=GENOTYPE_COMPOUND, db=db)
        self.conditions_array = self.build_conditions_array()
        if not self.conditions_array:
            self.shortcut = True
        else:
            self.conditions_vector = self.build_compound_conditions_vector()

    def build_conditions_array(self):
        """Returns pairs of condition (paternal, maternal), one for each sample,
        in a dict {sample_name: [cond1, cond2]}.
        Make it also for non affected, because we want to find false positives searching
        as if they were affected. An unaffected sample could well carry one of the two variants.
        """
        conds = {}
        # Common condition: all affected are carriers het, and no unaffected can be homozygous
        base_cond = [(i, GENOTYPE_BIT_NOT_CARRIER_HOM) for i in self.ss.not_affected_idx] \
                +   [(i, GENOTYPE_BIT_CARRIER_HET) for i in self.ss.affected_idx]
        for s in self.ss.active:
            idx = self.ss.idx_of(s.name, active=True)
            father_idx = self.ss.father_idx_of(s)
            mother_idx = self.ss.mother_idx_of(s)
            if father_idx is None or mother_idx is None:
                continue
            if father_idx in self.ss.affected_idx or mother_idx in self.ss.affected_idx:
                continue            # pointless if one of the parents is affected
            # Father carrier
            c1 = base_cond + [
                (idx, GENOTYPE_BIT_CARRIER_HET),  # in case it is not affected, but we simulate for false positives
                (father_idx, GENOTYPE_BIT_CARRIER),
                (mother_idx, GENOTYPE_BIT_NON_CARRIER),
            ]
            # Mother carrier
            c2 = base_cond + [
                (idx, GENOTYPE_BIT_CARRIER_HET),
                (father_idx, GENOTYPE_BIT_NON_CARRIER),
                (mother_idx, GENOTYPE_BIT_CARRIER),
            ]
            # Note: c1 and c2 cannot both be true at the same genomic position
            c1 = tuple(merge_conditions_array(c1))
            c2 = tuple(merge_conditions_array(c2))
            conds[s.name] = (c1, c2)
            # Remove duplicate conditions to speed it up
            seen = set()
            dups = set()
            for k,v in conds.items():
                if v in seen:
                    dups.add(k)
                else:
                    seen.add(v)
            for name in dups:
                conds.pop(name)
        return conds

    def build_compound_conditions_vector(self):
        """Extend *self.build_conditions_vector()* to apply it to all sub-elements
        *c1*,*c2* of the more complicated {sample: [c1, c2]} of the compound case."""
        conditions = {}
        for sample, conds in self.conditions_array.items():
            conditions[sample] = [None,None]
            conditions[sample][0] = self.build_conditions_vector(conds[0])
            conditions[sample][1] = self.build_conditions_vector(conds[1])
        return conditions

    def apply(self, variants=None, genotypes=None, db=None, limit=None, offset=0, sub_ids=None, parallel=True):
        """:param sub_ids: does nothing, just inheritance"""
        if self.shortcut:
            return FilterResult(variants=VariantsCollection([]), ids=[], n_filtered=0)
        if variants is None and db is not None:
            variants = Variant.objects.using(db)
        elif db is None:
            db = variants.db
        if db is None:
            batches = {gene: np.array([v.variant_id for v in var], dtype=np.uint64)
                for gene,var in itertools.groupby(variants, key=attrgetter('gene_symbol'))}
        else:
            gs = genotypes_service(db)
            batches = gs.variant_ids_batches_by_gene
        if genotypes is None:
            assert db is not None, "Either a db name or a genotypes array is required"
            genotypes = genotypes_service(db).genotypes
        else:
            assert len(genotypes) == len(variants)
        passing, sources, pairs = self.scan_genotypes_compound(genotypes, batches, parallel)
        variants = self.variants_from_mask(variants, passing, db, limit, offset)
        for v in variants:
            set_source(v, sources[v.variant_id])
        return FilterResult(
            variants=variants,
            ids=passing,
            n_filtered=len(passing),
        )

    def scan_genotypes_compound(self, genotypes, batches, parallel=True):
        """Scan the *genotypes* array for compounds. Variant ids are treated in batches,
           - one list of variant_ids per gene."""
        if self.shortcut:
            passing, sources, pairs = np.zeros(0), {}, []
        else:
            N = len(genotypes)
            active_idx = np.asarray(self.ss.active_idx, dtype=np.uint16)
            batches = list(batches.items())
            if parallel:
                passing, sources, pairs = self.parallel_batches(genotypes, batches, active_idx, N)
            else:
                passing, sources, pairs = self.process_batches(genotypes, batches, active_idx, N)
            passing = np.array(list(passing), dtype=np.uint64)
            passing.sort()
        return passing, sources, pairs

    def parallel_batches(self, genotypes, batches, active_idx, N):
        """Parallelize the scanning of genotypes for compounds over groups of genes."""
        passing = set()
        sources = {}
        pairs = []
        nprocs = mp.cpu_count()
        NB = len(batches)
        B = round(NB/nprocs + 0.5)  # batch size
        split_batches = [batches[k*B:(k+1)*B] for k in range(nprocs)]
        if DEBUG and 0:
            print("  @parallel_batches {} CPUs: {}".format(nprocs, [len(x) for x in split_batches]))
        pool = mp.Pool(processes=nprocs)
        res = [pool.apply_async(self.process_batches,
            args=(np.copy(genotypes), list(split_batches[k]), np.copy(active_idx), N))
            for k in range(nprocs)]
        output = [x.get() for x in res]
        for x in output:
            passing |= x[0]
            sources.update(x[1])
            pairs += x[2]
        pool.close()
        return passing, sources, pairs

    def process_batches(self, genotypes, batches, active_idx, N):
        """Search a batch of genes for compounds."""
        passing = set()
        sources = {}
        pairs = []
        tbatch = 0
        for gene,variant_ids in batches:
            t1 = time()
            local_passing, local_sources, local_pairs = self.process_1_batch(variant_ids, genotypes, active_idx, N)
            t2 = time()
            tbatch += t2-t1
            passing |= local_passing
            pairs += local_pairs
            sources.update(local_sources)
        if DEBUG and 0:
            print("  Processed batches in {:.3f}s ({} passing)".format(tbatch,len(passing)))
        return passing, sources, pairs

    def process_1_batch(self, variant_ids, genotypes, active_idx, N):
        """Search 1 gene for compounds. Return:
        local_passing: set of variant_ids passing the filter
        local_sources: dict `{variant_id: 'paternal'/'maternal'}`
        local_pairs: list of compound pairs `(variant_id1, variant_id2)`
        """
        # Check that all affected samples have the compound
        local_passing_mother = set()
        local_passing_father = set()
        local_sources = {}
        for affected in self.ss.affected:
            if affected.name not in self.conditions_vector:
                continue
            conds = self.conditions_vector[affected.name]
            passing_father = set(c_apply_bitwise(genotypes, variant_ids, conds[0], active_idx, True, N))
            passing_mother = set(c_apply_bitwise(genotypes, variant_ids, conds[1], active_idx, True, N))

            # Exclude compounds that healthy samples carry as well
            if len(passing_father) > 0 and len(passing_mother) > 0:
                fp1 = set()
                fp2 = set()
                local_ids = np.array(list(passing_father | passing_mother), dtype=np.uint64)
                for healthy in self.ss.not_affected:
                    if healthy.name not in self.conditions_vector:
                        continue
                    conds = np.asarray(self.conditions_vector[healthy.name], dtype=np.uint8)
                    false_father = c_apply_bitwise(genotypes, local_ids, conds[0], active_idx, True, N)
                    false_mother = c_apply_bitwise(genotypes, local_ids, conds[1], active_idx, True, N)

                    false_pairs = list(itertools.product(false_father, false_mother))
                    for p1, p2 in false_pairs:
                        if p1 in passing_father and p2 in passing_mother:
                            fp1.add(p1)
                            fp2.add(p2)
                passing_father = passing_father - fp1
                passing_mother = passing_mother - fp2

                # If there are any left in both lists, add them to the result set
                if len(passing_father) > 0 and len(passing_mother) > 0:
                    for k in passing_father:
                        local_sources[k] = 'paternal'
                    for k in passing_mother:
                        local_sources[k] = 'maternal'
                    if len(local_passing_father) == 0:
                        local_passing_father = passing_father
                    else:
                        local_passing_father &= passing_father
                    if len(local_passing_mother) == 0:
                        local_passing_mother = passing_mother
                    else:
                        local_passing_mother &= passing_mother

            # All affected samples must have at least one of the combinations
            else:
                local_passing_father = set()
                local_passing_mother = set()
                local_sources = {}
                break  # go to next gene

        local_passing = local_passing_father | local_passing_mother
        local_pairs = list(itertools.product(
            map(int,local_passing_father),   # map to int because of new numpy warning when used as index
            map(int,local_passing_mother)
        ))
        return local_passing, local_sources, local_pairs

