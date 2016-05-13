"""
Defines a GenomicRange class to store genomic coordinates.
"""
class GenomicRange:
    def __init__(self, chrom, start, end):
        """Instanciate a new genomic range."""
        self.chrom = chrom
        self.start = start
        self.end = end

    def __str__(self):
        return "{}:{}-{}".format(self.chrom, self.start, self.end)

    def expose(self):
        return {
            'chrom': self.chrom,
            'start': self.start,
            'end': self.end
        }


