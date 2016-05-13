"""
Many entries in the database can be None. It becomes difficult to sort
a column because of that. Calling `Sort(key, reverse).sort(items)` instead of
`items.sort(key, reverse)` will reorder items in-place, but taking care of None
(which is always the smallest element).
"""

from functools import total_ordering

@total_ordering
class MinType(object):
    """Defines an object that is lower than anything, to replace None"""
    def __le__(self, other):
        """It is lower than anything else"""
        return True
    def __eq__(self, other):
        """It is only equal to itself"""
        return self is other

# A singleton on the above class
Min = MinType()


def sort_from_request(request):
    """From a GET request, extract '?order_by=<key>,<ASC/DESC>', if present.
    Return a Sort object.
    """
    order = request.GET.get('order_by')
    if order:
        key, direction = order.split(',')
        reverse = False if direction == 'ASC' else True
        return Sort(key, reverse)
    else:
        return Sort(None)


class Sort:
    def __init__(self, key, reverse=False):
        self.key = key
        self.reverse = reverse

    def sort(self, variants_collection, inplace=False):
        """Return a new list of Variants"""
        return sorted(variants_collection, key=self.key_condition, reverse=self.reverse)

    def sort_dict(self, variants_exposed, inplace=False):
        """Return a new list of Variants"""
        if inplace:
            variants_exposed.order_by(key=self.key_condition_dict, reverse=self.reverse)
        else:
            return sorted(variants_exposed, key=self.key_condition_dict, reverse=self.reverse)

    @property
    def key_condition(self):
        return lambda x: Min if getattr(x,self.key) is None else getattr(x,self.key)

    @property
    def key_condition_dict(self):
        return lambda x: Min if x[self.key] is None else x[self.key]

    def __str__(self):
        return "<Sort {} {}>".format(self.key, self.reverse)