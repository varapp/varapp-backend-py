"""
Defines abstract Filter and VariantFilter classes, and a FilterCollection class.
"""
from django.conf import settings
from varapp.constants.filters import *
from varapp.constants.genotype import *
from varapp.data_models.variants import VariantsCollection, Variant, VARIANT_FIELDS
from varapp.variants.genotypes_service import genotypes_service
from varapp.variants.variants_factory import namedtuples, extract_variants_from_ids_bin_array
from varapp.common import masking
import abc, hashlib
import numpy as np
from operator import attrgetter
from time import time

DEBUG = False and settings.DEBUG


class FilterResult:
    """Stores info about the result of applying a filter (-collection)"""
    def __init__(self, variants=None, ids=None, n_filtered=0, sources=None):
        self.variants = variants      # (list) A (sub)set of filtered variants to expose (send to frontend)
        self.ids = ids                # (set) The set of all filtered variant ids (not just the subset)
        self.n_filtered = n_filtered  # (int) Total number of filtered variants


class Filter:
    __metaclass__ = abc.ABCMeta
    filter_class = ''  # the category of filter ('pathogenicity', 'location', etc.)

    def __init__(self, name='', op='=', val='', db=None, ss=None):
        """Filter: <name><op><val>, e.g. quality<=100.
        :param ss: SamplesSelection"""
        self.db = db
        self.ss = ss
        self.name = name
        self.op = op
        self.val = val

    def apply(self, *args, **kwargs):
        """A filter must be applied on a collection/QuerySet/whatever.
        :rtype: FilterResult"""

    def short_str(self):
        return "{}{}{}".format(self.name, self.op, self.val)

    def __str__(self):
        return "<Filter {}>".format(self.short_str())

    def __repr__(self):
        return "<Filter {}>".format(self.short_str())

    def cache_key(self):
        key = self.short_str()
        hashed_key = hashlib.md5(key.encode('utf-8')).hexdigest()
        return hashed_key


class VariantFilter(Filter):
    """Abstract class for QuerySet filters."""
    __metaclass__ = abc.ABCMeta
    field_name = ''  # name used in the local variant model (the db column name)

    def __init__(self, val='', name='', op='=', ss=None, db=None):
        super().__init__(op=op, ss=ss, db=db)
        self.name = name if name!='' else self.field_name
        self.val = self._tryparse(val)

    def parse_arg(self, val):
        """Convert an argument *val* (string, because it may come from a url)
        to a more useful type, if necessary. E.g. [impact=]exon,intron -> val = ['exon','intron']."""
        return val

    def _tryparse(self, val):
        """Wrapper to `parse_arg` that throws a more sensible error if the conversion fails."""
        try:
            return self.parse_arg(val)
        except ValueError as ve:
            raise ValueError("Unexpected query: 'filter={}{}{}'.\n{}".format(self.name, self.op, val, ve))

    def sql_condition(self):
        """The complement to WHERE in the SQL query that performs the filtering."""

    def django_condition(self):
        """Return a Q object that can be passed as argument to Variant.objects.filter()."""

    def condition(self, variant):
        """The condition that a *variant* must satisfy in order to pass the filter.
        condition(v) -> Boolean."""

    def apply(self, db=None, initqs=None, limit=None, offset=0):
        """Applies a unique filter to the database.
        :rtype: FilterResult"""
        if initqs is None:
            initqs = Variant.objects.using(db)
        qs = initqs.filter(self.django_condition())
        if limit is not None:
            qs = qs[offset:offset+limit]
        variants = namedtuples(qs)  # more efficient than a list
        return FilterResult(
            variants = VariantsCollection(variants),
            n_filtered = len(variants),
            ids = np.asarray([v.variant_id for v in variants], dtype=np.uint64),
        )

    @property
    def query(self):
        """Return the SQL statement that is run by Django to apply this filter."""
        qs = Variant.objects.using(self.db).filter(self.django_condition())
        return qs.query.__str__()


class FiltersCollection:
    """Maps filter names with their actual class and allows to apply
    them all to a QuerySet."""
    def __init__(self, filters):
        """:param filters: list of Filter subclass instances."""
        self._dict = {}  # {filter_name: Filter}
        self.filters = filters
        for f in filters:
            self.append(f)  # updates _dict

    @property
    def list(self):
        """Return a sorted list of the filters. Ideally the order should be tuned
        for performance, but at least, because of the compound case, the 'genotypes'
        filter must be first."""
        qual = self.get_filters_by_class('quality')
        freq = self.get_filters_by_class('frequency')
        impa = self.get_filters_by_class('impact')
        loca = self.get_filters_by_class('location')
        path = self.get_filters_by_class('pathogenicity')
        geno = self.get_filters_by_class('genotype')
        return qual + freq + impa + loca + path + geno

    def __len__(self):
        """Return the number of filters in the collection."""
        return len(self._dict)

    def __add__(self, other):
        return FiltersCollection(self.list + other.list)

    def __sub__(self, filter_name):
        return FiltersCollection([f for f in self.list if f.name != filter_name])

    def __getitem__(self, field_name):
        return self._dict[field_name]

    def __iter__(self):
        for x in self.list:
            yield x

    def has(self, filter_name):
        """Return True if the filter name is in the collection, False otherwise."""
        return self._dict.get(filter_name) is not None

    def append(self, f):
        """Add a filter to the collection"""
        name = f.name
        if self._dict.get(name) is not None:
            raise ValueError("Duplicate name '{}' in filter collection.".format(name))
        self._dict[name] = f

    def extend(self, filters_collection):
        """Extend the current collection with another.
        :param filters_collection: another FiltersCollection"""
        for f in filters_collection.list:
            self.append(f)

    def get_filter_names(self):
        """Return the list of filter names."""
        l = list(self._dict.keys())
        l.sort()
        return l

    def get_filters_by_class(self, filter_class):
        """Return a list of the filters of a given class, such as 'pathogenicity'."""
        return [f for f in self._dict.values() if f.filter_class == filter_class]

    @property
    def variant_filters(self):
        return [f for f in self._dict.values() if f.filter_class != FILTER_CLASS_GENOTYPE]
    @property
    def genotype_filters(self):
        return [f for f in self._dict.values() if f.filter_class == FILTER_CLASS_GENOTYPE]

    def cache_key(self):
        """build a cache key as a string concatenating filters key/op/val"""
        key = '&'.join([f.cache_key() for f in sorted(self.list, key=attrgetter('name'))])
        hashed_key = hashlib.md5(key.encode('utf-8')).hexdigest()
        return hashed_key

    ######################################################################################

    #@timer
    def apply(self, db=None, initqs=None, limit=None, offset=0, sort_by=None, reverse=False, batch_size=500):
        """Applies all filters in list to the database. Return a FilterResult with
         *limit* variants to expose.
        :param initqs: A QuerySet to be further filtered.
            Otherwise all entries of *db* will be fetched.
        :param db: The alias of the database to query from.
            If not set, try to get it from the first filter in list.
        :param limit: maximum number or variants to return.
        :param offset: number of variants to skip before returning *limit* of them.
        :param sort_by: (str) name of the field to sort by.
        :param reverse: (bool) whether to reverse the ordering.
        :rtype: FilterResult
        """
        is_sorted = sort_by and sort_by in VARIANT_FIELDS
        is_gen_filter = len(self.genotype_filters) > 0
        is_var_fiter = len(self.variant_filters) > 0

        if initqs is None:
            initqs = Variant.objects.using(db)

        # Filter what can be filtered directly in the db
        conds = [f.django_condition() for f in self.variant_filters]
        conds = [x for x in conds if x]
        qs = initqs.filter(*conds)

        # Sort what can be sorted directly in the db
        if is_sorted:
            sort_key = '-'+sort_by if reverse else sort_by
            qs = qs.order_by(sort_key)
        else:
            qs = qs.order_by('chrom','start')  # trust Gemini for that

        # If no genotype filter, paginate from db and return the collection.
        # For the moment it never happens because there is always at least the 'active' gen filter.
        n_filtered = qs.count()
        if not is_gen_filter or n_filtered == 0:
            ids = np.asarray(list(qs.values_list('variant_id', flat=True)), dtype=np.uint64)
            if limit is not None:
                qs = qs[offset:offset+limit]
            variants = namedtuples(qs)  # instead of list

        # If genotype filter, get indices from gen service, indices from
        # the variant filters (nothing is evaluated yet), and return the intersection.
        else:
            gf = self.genotype_filters[0]
            is_compound = gf.val == GENOTYPE_COMPOUND
            gs = genotypes_service(db=db)
            sources = {}; pairs = []
            sql_indices = []; bin_ids = np.zeros(0)
            if is_compound:
                gen_indices,sources,pairs = gf.scan_genotypes_compound(genotypes=gs.genotypes, batches=gs.variant_ids_batches_by_gene)
            elif gf.val == 'x_linked':
                gen_indices = gf.scan_genotypes(genotypes=gs.genotypes, sub_ids=gs.chrX)
            else:
                gen_indices = gf.scan_genotypes(genotypes=gs.genotypes) # type: np.ndarray
            # If nothing left, return
            if len(gen_indices) == 0:
                ids = np.zeros(0)
            # Find the variant ids that are present in both var filtered and gen filtered sets
            elif is_var_fiter or is_sorted or initqs is not None:
                max_gen_index = gen_indices[-1]
                qs_indices = qs.values_list('variant_id', flat=True).filter(variant_id__lte=max_gen_index)
                t1 = time()
                sql_indices = list(qs_indices)  # qs is already ordered_by, so are sql_indices
                t2 = time()
                if DEBUG: print("  Apply fc :: Instantiate sql indices:", t2-t1)
                bin_sql = masking.pack(masking.to_binary_array(sql_indices, max_gen_index))
                bin_gen = masking.pack(masking.to_binary_array(gen_indices, max_gen_index)),
                bin_ids = masking.unpack(masking.binary_and(bin_sql, bin_gen), max_gen_index)  # always sorted by id
                t3 = time()
                if DEBUG: print("  Apply fc :: Sets intersection:", t3-t2)
                # If compound, filter out those were after intersection, a gene has only one component left
                if is_compound:
                    bin_keep = np.zeros(max_gen_index, dtype=np.bool_)
                    for a,b in pairs:
                        if bin_ids[a-1] & bin_ids[b-1]:
                            bin_keep[a-1] = 1
                            bin_keep[b-1] = 1
                    bin_ids = masking.binary_and(bin_ids, bin_keep)
                    t4 = time()
                    if DEBUG: print("  Apply fc :: Compound pairs filtering:", t4-t3)
                ids = masking.to_indices(bin_ids)+1
            # If the only filter is on genotypes and no need to sort, skip slow steps
            else:
                ids = gen_indices

            n_filtered = len(ids)
            # Extract the variants for the filtered ids from the inital QuerySet,
            # up to limit (i.e. up to ~300 variants to expose).
            # We need to pass `sql_indices` on top of `ids` because the latter is sorted,
            # and we want the top of the sorted QuerySet.
            variants = extract_variants_from_ids_bin_array(qs, bin_ids, sql_indices, limit, offset, batch_size, sources)

        return FilterResult(
            variants = VariantsCollection(variants, db=db),
            n_filtered = n_filtered,
            ids = np.asarray(ids, dtype=np.uint64),
        )

    def __str__(self):
        return "<FilterCollection ({}): >".format(len(self.list)) + \
                '\n\t'.join([str(f) for f in self.list])

    def __repr__(self):
        return "<FilterCollection {}>".format('.'.join([f.short_str() for f in self.list]))

    def expose(self):
        return [str(f) for f in self.list]

