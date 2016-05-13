
import numpy as np
cimport numpy as np

DTYPE_UINT64 = np.uint64
DTYPE_UINT8 = np.uint8
DTYPE_UINT16 = np.uint16
DTYPE_BOOL = np.bool_
ctypedef np.uint8_t DTYPE_UINT8_t
ctypedef np.uint16_t DTYPE_UINT16_t
ctypedef np.uint64_t DTYPE_UINT64_t


# Compare each line of the *genotypes* array, corresponding to 1 variant,
# to a vector of conditions that the elements must satisfy in order to pass the filter.
# This condition vector is built out of *conditions_array* and *active_idx*.

def c_apply_bitwise(np.ndarray[DTYPE_UINT8_t, ndim=2] genotypes,        # genotypes array [N,m]
                    np.ndarray[DTYPE_UINT64_t] variant_ids,             # list of variant ids, [n<=N]
                    np.ndarray[DTYPE_UINT8_t] conditions,               # array of genotype_bits, [m]
                    np.ndarray[DTYPE_UINT16_t] active_idx,              # indices of active samples, [m]
                    bint is_and,                                        # True: AND, False: OR
                    unsigned int batch_size):

    cdef unsigned long n = variant_ids.shape[0]
    cdef unsigned int m = active_idx.shape[0]
    cdef DTYPE_UINT8_t GEN_BIT_ANY = 7
    cdef DTYPE_UINT8_t bit, cond_bit, real_bit

    cdef np.ndarray[DTYPE_UINT64_t] passing = np.empty(n, dtype=DTYPE_UINT64)   # for each variant, return 1 if it passes, 0 otherwise
    cdef np.ndarray[DTYPE_UINT8_t] gts = np.empty(m, dtype=DTYPE_UINT8)         # array of genotypes bits of active samples for 1 variant

    cdef bint x, r
    cdef unsigned int vid, i,k,v
    cdef unsigned int N = 0

    # All but 'active'
    if is_and:
        for i in range(n):
            vid = variant_ids[i]
            v = (vid-1) % batch_size
            x = 1
            for k in range(m):
                cond_bit = conditions[k]
                real_bit = genotypes[v, active_idx[k]]
                r = <bint>(real_bit & cond_bit)
                x = x & r
                if not x:
                    break
            if x:
                passing[N] = vid
                N = N + 1

    # 'Active' filter
    else:
        for i in range(n):
            vid = variant_ids[i]
            v = (vid-1) % batch_size
            x = 0
            for k in range(m):
                cond_bit = conditions[k]
                real_bit = genotypes[v, active_idx[k]]
                r = <bint>(real_bit & cond_bit)
                x = x | r
            if x:
                passing[N] = vid
                N += 1

    passing = passing[:N]
    return passing

