"""
Pagination: select how many results to display.
"""

# Maybe refactor later the same way as variant_filter,
# but maybe not necessary as long as they are so simple.
def pagination_from_request(request):
    lim = request.GET.get('limit')
    off = request.GET.get('offset', '0')
    assert off.isdigit(), "Argument to 'offset' must be an integer"
    off = int(off)
    if lim is not None:
        assert lim.isdigit(), "Argument to 'limit' must be an integer"
        lim = int(lim)
    return Pagination(lim, off)


class Pagination:
    def __init__(self, limit=None, offset=0):
        """
        :param limit: (int) keep only that many.
        :param offset: (int) skip that many.
        """
        self.lim = limit
        self.off = offset

    def limit(self, variants):
        """Keep only the first *lim* variants.
        Corresponds to the 'LIMIT' and 'OFFSET' SQL statements.
        :param variants: QuerySet.
        """
        return variants[:self.lim]

    def offset(self, variants):
        """Skip the first *off* variants.
        Corresponds to the 'OFFSET' SQL statement.
        :param variants: QuerySet.
        """
        return variants[self.off:]

    def paginate(self, variants):
        var = self.offset(variants)
        if self.lim:
            var = self.limit(var)
        return var

