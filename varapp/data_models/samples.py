
from operator import attrgetter
from collections import defaultdict
import itertools
import hashlib
import copy

GENDER_MAP = {
     1 :'M',  2 :'F',
    '1':'M', '2':'F',
    'M':'M', 'F':'F',
}


class Sample:
    def __init__(self, name,
            sample_id=None, family_id=None, mother_id=None, father_id=None, sex=None, phenotype=None,
            group=None, active=False):
        """PED: sex: 1:male / 2:female / other:unknown
                phenotype: 0:unknown / 1:unaffected / 2:affected"""
        self.i = None
        self.name = name                    # from PED, sample name
        self.sample_id = sample_id          # from PED, int
        self.family_id = family_id          # from PED, int
        self.mother_id = mother_id          # from PED, name of mother Sample, str
        self.father_id = father_id          # from PED, name of father Sample, str
        self.mother = None,
        self.father = None,
        self.children = None,
        self.sex = GENDER_MAP.get(sex, 'U') # from PED
        self.phenotype = phenotype          # from PED
        self.group = group                  # group name, from samples selection
        self.active = active                # bool

    def expose(self):
        return {
            'i': self.i,
            'name': self.name,
            'sample_id': self.sample_id,
            'family_id': self.family_id,
            'mother_id': self.mother_id,
            'father_id': self.father_id,
            'sex': self.sex,
            'phenotype': self.phenotype,
            'group': self.group,
            'active': self.active,
        }

    def __str__(self):
        return "<Sample {}>".format(self.name)


class SamplesSelection:
    """A list of samples. Faster to manipulate than going back to the django data model.
    """
    def __init__(self, samples, groups=None, db=None):
        """:param samples: the original list of Sample's
        :param groups: a dict {group_name: list of sample names}
        :param db: the db name at the origin of this selection.
        """
        self.db = db
        self.samples = copy.deepcopy(samples) # make a copy to not mutate it
        self.ids = [s.sample_id for s in self.samples]
        self.names = [s.name for s in self.samples]
        if len(set(self.names)) != len(self.names):
            raise ValueError("Sample names in a SamplesCollection must be unique.")
        for i,s in enumerate(self.samples):
            s.i = i
            s.mother = self.mother_of(s)
            s.father = self.father_of(s)
            s.children = self.children_of(s)
        self.groups = {}
        self.affected = None      # a list of the affected samples
        self.affected_idx = None  # the positions of the affected samples in the whole collection
        self.not_affected = None
        self.not_affected_idx = None
        self.active = None       # a list of the active samples
        self.active_idx = None   # the positions of active samples in the whole collection
        self._define_groups(groups)

    def _define_groups(self, groups:dict):
        """Add to every sample mentioned in *groups* the `group` tag and make it `active`."""
        groups = groups or {}
        for s in self.samples:
            s.active = False
        for group_name, samples in groups.items():
            self.groups[group_name] = samples
            for s in self.get_list(samples):
                s.group = group_name
                s.active = True
        self.affected = self.get_group('affected', True) if ('affected' in self.groups) else []
        self.affected_idx = self.idxs_of_group("affected", True) or []
        self.not_affected = self.get_group('not_affected', True) if ('not_affected' in self.groups) else []
        self.not_affected_idx = self.idxs_of_group("not_affected", True) or []
        self.active = [s for s in self.samples if s.active]
        self.active_idx = [i for i,s in enumerate(self.samples) if s.active]

    def __getitem__(self, item):
        return self.samples[item]

    def __len__(self, active=False):
        if active:
            return len([s for s in self.samples if s.active])
        else:
            return len(self.samples)

    def __next__(self):
        return next(self.samples)

    def sort(self, key, reverse=False):
        """Orders the collection.
        :param key: either a string with the attribute or a list of keys.
        :param reverse: if True, sort in the reverse order.
        :return a new SamplesCollection
        """
        keyl = attrgetter(key)
        return SamplesSelection(sorted(self.samples, key=keyl, reverse=reverse))

# SELECTION

    def get(self, name):
        """Return the Sample with that name."""
        for s in self.samples:
            if s.name == name:
                return s

    def get_list(self, names, active=False):
        """Return a list of samples with these names."""
        if active:
            return [s for s in self.samples if s.name in set(names) and s.active]
        else:
            return [s for s in self.samples if s.name in set(names)]

    def get_group(self, group_name, active=False):
        """Return a list of samples corresponding to the given *group_name*."""
        return self.get_list(self.groups[group_name], active)

    def idx_of(self, name, active=False):
        """Get the position of the sample with that *name* in the samples list.
        Return None if not found."""
        for i,s in enumerate(self.samples):
            if active and not s.active:
                continue
            if s.name == name:
                return i

    def idxs_of(self, names, active=False):
        """Get the positions of the samples with these *names* in the samples list."""
        idxs = []
        for n in names:
            i = self.idx_of(n, active)
            if i is not None:
                idxs.append(i)
        return idxs

    def idxs_of_group(self, group_name, active=False):
        """Return the position indices of the members of *group_name* in the samples list."""
        if not self.groups.get(group_name):
            return None
        else:
            return self.idxs_of(self.groups[group_name], active)

    def mother_of(self, sample):
        for s in self.samples:
            if s.name == sample.mother_id:
                return s

    def father_of(self, sample):
        for s in self.samples:
            if s.name == sample.father_id:
                return s

    def children_of(self, sample):
        return [s for s in self.samples if s.father_id == sample.name
                                        or s.mother_id == sample.name]

# FOR GENOTYPE FILTERS (ACTIVE ONLY). OTHERWISE USE .get_group

    def mother_idx_of(self, s):
        mother = self.mother_of(s)
        if mother and mother.active:
            return self.idx_of(mother.name, active=True)
    def father_idx_of(self, s):
        father = self.father_of(s)
        if father and father.active:
            return self.idx_of(father.name, active=True)
    def parents_idx_of(self, sample):
        """Get the list of indices in the samples list corresponding to the parents
        of the given samples, when they exist.
        """
        mother = self.mother_idx_of(sample)
        father = self.father_idx_of(sample)
        parents = []
        if mother is not None:
            parents.append(mother)
        if father is not None:
            parents.append(father)
        return parents

# SUBSET VECTORS

    def _check_len(self, x, active=False):
        """Check that vector *x* has as many elements as there are samples in the selection."""
        if len(x) != self.__len__(active):
            raise ValueError(("The given vector must have as many elements "
                "as there are samples in the selection (Expected {}, got {})."
                .format(self.__len__(active), len(x))))

    def select_x_active(self, x):
        """Return only elements of iterable *x* corresponding to active samples"""
        self._check_len(x)
        return [x[k] for k in self.active_idx]

    def cache_key(self):
        key = '&'.join(['{}/{}/{}'.format(s.name, s.group, s.active)
                        for s in sorted(self.samples, key=attrgetter('name'))])
        hashed_key = hashlib.md5(key.encode('utf-8')).hexdigest()
        return hashed_key

    def __str__(self):
        group_counts = {g:len(v) for g,v in self.groups.items()}
        return "<SamplesSelection ({}) {}>".format(len(self.samples), group_counts)

    def expose(self):
        return [s.expose() for s in self.samples]


