import numpy as np
from varapp.common.utils import timer


def to_binary_array(a, size):
    """Transform an array of indices *a* to a binary array of length *size*,
    with 1 at the given indices and 0 elsewhere."""
    a = np.asarray(a)
    z = np.zeros(size, dtype=np.bool_)
    if len(a) != 0:
        z[a-1] = 1
    return z

def pack(a):
    """Pack a boolean array *a* so that it takes 8x less space."""
    return np.packbits(a.view(np.uint8))

def unpack(a, size):
    """From a packed array *a*, return the boolean array. Remove byte padding at the end."""
    return np.unpackbits(a)[:size]

def binary_and(a,b):
    """Compare two binary arrays of the same length and return a third one,
    the bitwise addition of the first two."""
    # return np.logical_and(a,b)  # does not work with packed arrays
    return np.bitwise_and(a, b)

def to_indices(a):
    """Return the array of indices (0-based) where elements of *a* are True."""
    return np.flatnonzero(a)

