

class VariantStats:
    def __init__(self, stats, total_count):
        self.total_count = total_count
        self.stats = stats  # {field: {value: count}, field: {min:min,max:max}, ...}

    def __getitem__(self, filter_name):
        return self.stats[filter_name]

    def get(self, filter_name):
        return self.stats.get(filter_name)

    def expose(self):
        return {
            'total_count': self.total_count,
            'stats': { f: self.stats[f].expose() for f in self.stats }  # expose each Histogram
        }

    def __repr__(self):
        return str(self.expose())

    def __str__(self):
        return "<VariantsStats (N={})>".format(self.total_count)
