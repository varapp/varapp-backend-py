"""
Defines a service that parses different kind of queries and returns a corresponding GenomicRange.
Uses the more general annotation_service.
"""

from varapp.annotation.annotation_service import gene_summary_service
from varapp.annotation.genomic_range import GenomicRange
import re
import sys, logging
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format='%(message)s')

LOCS_REGEX = re.compile(r'(\w+(?::[ \d,]*\d\-[ \d,]*\d)?)', re.IGNORECASE)
LOC_REGEX = re.compile(r'\s*(chr\w+):([ \d,]*\d)\-([ \d,]*\d)\s*', re.IGNORECASE)


class LocationService:
    def __init__(self, db):
        self._db = db

    def find(self, locstring:str):
        """Tries to parse the str as a genomic range string (chr:start-end).
        If it fails, returns the location attached to the gene name (potentially nothing).
        :rtype: list of `GenomicRange`s
        :param locstring: genomic range string, gene name, or comma-separated list of them.
        """
        locations = []
        for s in re.findall(LOCS_REGEX, locstring):
            s = s.strip()
            loc = self.parse_genomic_range(s)
            # If it is a location of the type 'chr1:123-456'
            if loc:
                locations.append(loc)
            # If it is a gene name or a chrom name
            else:
                loc = gene_summary_service(self._db)[s]
                if loc:
                    locations.extend(loc['location'])
                else:
                    logging.warning("Cannot find genomic location '{}'".format(s))
                    continue
        return locations

    def autocomplete_name(self, prefix, maxi=10):
        l = [x for x in gene_summary_service(self._db).get_genes()
             if x.lower().startswith(prefix.lower())]
        return sorted(l)[:maxi]

    @staticmethod
    def parse_genomic_range(s:str):
        """Create a GenomicRange from a string such as 'chr1:123-456', 'chr1:123,456-123,789'."""
        m = LOC_REGEX.match(s)
        if m:
            chrom = m.group(1)
            chrom = chrom[:3].lower() + chrom[3:]  # 'chr' + '1/12/X'
            return GenomicRange(chrom,
                                int(m.group(2).strip().replace(',','')),
                                int(m.group(3).strip().replace(',','')))
        else:
            return None
