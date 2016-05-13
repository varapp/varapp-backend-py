"""
Compression/decompression of genotype blobs, and genotypes arrays formatting.
"""

def decode_int(gt):
    """Return an array with decoded elements of the binary array *gt*
    (such as genotypes: Variants.gt_types)"""
    return [int(i) for i in unpack_genotype_blob(gt)]

# Unused?
def decode(gts):
    """Return an array with decoded elements of the binary array *gts*
    (such as genotypes: Variants.gts)"""
    return [bytes.decode(x) for x in unpack_genotype_blob(gts)]

# Unused?
def format_genotypes(gts, ref):
    gts = decode(gts)
    gts = [x.split('/') for x in gts]
    gts = [('-' if x==ref else x, '-' if y==ref else y) for x,y in gts]
    gts = ['/'.join(x) for x in gts]
    return gts


### From GEMINI source ###


import zlib
import pickle
import sqlite3
import collections

# http://stackoverflow.com/questions/695794/more-efficient-way-to-pickle-a-string
# Now in Python3 pickle HIGHEST_PROTOCOL is 3 (automatic)

def pack_blob(obj):
    return sqlite3.Binary(zdumps(obj))

def unpack_genotype_blob(blob):
    return pickle.loads(zlib.decompress(blob))

def unpack_ordereddict_blob(blob):
    blob_val = pickle.loads(zlib.decompress(blob))
    if blob_val is not None:
        return collections.OrderedDict(blob_val)
    return None

def zdumps(obj):
    return zlib.compress(pickle.dumps(obj, pickle.HIGHEST_PROTOCOL), 9)

def zloads(obj):
    return pickle.loads(zlib.decompress(obj))

