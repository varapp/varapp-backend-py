
class DiscreteCounts:
    """Given a list of values, count the occurences."""
    def __init__(self, values_dict):
        self.counts = values_dict
        self.values = list(values_dict.keys())
    def __getitem__(self, v):
        return self.counts[v]
    def expose(self):
        # '' is false in javascript
        if '' in self.counts:
            self.counts['no_value'] = self.counts.pop('')
        return self.counts
    def __str__(self):
        return "<DiscreteCounts\n" + '\n'.join(
                    ["\t{}: {}".format(k,v) for k,v in self.counts.items()]
                ) + "\n>"

class StatsContinuous:
    """Given a list of float values, return various stats about their disribution."""
    def __init__(self, minmax_dict):
        self.min = minmax_dict.get('min', 0)
        self.max = minmax_dict.get('max', 0)

    def expose(self):
        return {'min': self.min,
                'max': self.max,
                #'breaks': self.breaks,
                }

    def __str__(self):
        return "<StatsContinuous (range:{}-{})>".format(self.min, self.max)

class StatsFrequency:
    """Frequency values are always between 0 and 1, and we query
    values at fixed breaks such as [0, 0.01, 0.05]."""
    def __init__(self):
        self.min = 0.0
        self.max = 1.0
        self.breaks = [0, 0.001, 0.01, 0.05, 1]

    def expose(self):
        return {'min': self.min,
                'max': self.max,
                'breaks': self.breaks,
                }

    def __str__(self):
        return "<StatsContinuous (range:{}-{})>".format(self.min, self.max)

