#!/usr/bin/env python3

import unittest
from django.test.client import RequestFactory
from varapp.samples.samples_factory import samples_selection_factory
from varapp.variants.variants_factory import variants_collection_factory
from varapp.filters.genotype_filters import *
from varapp.constants.tests import *
from varapp.filters.filters_factory import variant_filters_from_request, variant_filters_collection_factory
from varapp.filters.filters import FiltersCollection
from varapp.data_models.samples import Sample
from varapp.data_models.variants import Variant
from numpy import array, uint8

DTYPE = uint8

class Family:
    """Hand-made family"""
    def __init__(self):
        self.ss = SamplesSelection([
            Sample('Mother', sex=2),
            Sample('Father', sex=1),
            Sample('Sasha', mother_id='Mother', father_id='Father', sex=1),
            Sample('Dasha', mother_id='Mother', father_id='Father', sex=2),
            Sample('Lesha', mother_id='Mother', father_id='Father', sex=1),
            Sample('Lena', sex=2),
        ])
        self.samples = self.ss.samples


#@unittest.skip('')
class TestGenotypeFilters(unittest.TestCase):
    """Test generic GenotypesFilterAbstract things."""
    def setUp(self):
        self.variants = variants_collection_factory(db='test')

    def test_no_active_sample(self):
        ss = samples_selection_factory(db='test', groups={})
        try:
            var = GenotypesFilterDominant(ss).apply(self.variants).variants
        except ValueError as ve:
            self.fail("Calling genotype filter with no active samples raised an error: " + str(ve))
        self.assertEqual(len(var), 0)

    def test_missing_group(self):
        """Missing a required group results in no variant passing."""
        ss = samples_selection_factory(db='test', groups={"not_affected": ['09969']})
        var = GenotypesFilterDominant(ss).apply(self.variants).variants
        self.assertEqual(len(var), 0)

    def test_missing_group1(self):
        """An empty required group results in no variant passing."""
        ss = samples_selection_factory(db='test', groups={"affected": [], "not_affected": ['09969']})
        var = GenotypesFilterDominant(ss).apply(self.variants).variants
        self.assertEqual(len(var), 0)

    def test_missing_parents(self):
        """Missing the parents results in no variant passing."""
        ss = samples_selection_factory(db='test', groups={"affected": ['09818','09819']})
        var = GenotypesFilterDeNovo(ss).apply(self.variants).variants
        self.assertEqual(len(var), 0)


############################
#         ACTIVE           #
############################

#@unittest.skip('')
class TestActive(unittest.TestCase):
    def setUp(self):
        self.F = Family()

    def test_active(self):
        """Should return what is not ref/ref (1) in at least one of the selected samples."""
        genotypes = array(
            [[2,1, 2,1,1,1],
             [1,2, 2,2,1,1],
             [1,2, 2,2,1,1],
             [1,2, 2,2,1,1],
             [1,1, 2,2,1,1]], dtype=DTYPE)
        variants = VariantsCollection([Variant(variant_id=x+1) for x in range(len(genotypes))], db='test')
            # the db parameter should be ignored
            # pk needs to start at 0 to emulate the array indexing
        groups = {"affected": ["Mother"]}
        ss = SamplesSelection(self.F.ss.samples, groups)
        var = GenotypesFilterActive(ss).apply(variants, genotypes).variants
        self.assertEqual(len(var), 1)
        self.assertTrue(any([genotypes[v.pk][i] > 1 for i in [0]] for v in var))

        groups = {"affected": ["Mother", "Father"]}
        ss = SamplesSelection(self.F.ss.samples, groups)
        var = GenotypesFilterActive(ss).apply(variants, genotypes).variants
        self.assertEqual(len(var), 4)
        self.assertTrue(any([genotypes[v.pk][i] > 1 for i in [0,1]] for v in var))

        groups = {"affected": ["Dasha", "Lena"], "not_affected": ["Lesha"]}
        ss = SamplesSelection(self.F.ss.samples, groups)
        var = GenotypesFilterActive(ss).apply(variants, genotypes).variants
        self.assertEqual(len(var), 4)
        self.assertTrue(any([genotypes[v.pk][i] > 1 for i in [3,4,5]] for v in var))


############################
#        DOMINANT          #
############################

#@unittest.skip('')
class TestDominant(unittest.TestCase):
    def setUp(self):
        self.F = Family()
        self.genotypes = array(
                [[2,1, 2,2,1,1],  # X - from unaffected mother
                 [1,2, 2,2,1,1],  # V - from affected father
                 [1,2, 2,1,1,1],  # X - affected without the mutation
                 [1,2, 2,2,2,1],  # X - not affected with the mutation
                 [1,1, 2,1,1,1],  # X - de novo
                 [2,2, 4,1,1,1],  # X - recessive, both parents have it (unaffected)
                 [1,2, 2,2,1,1]], # V - Actually the only working situation
                dtype=DTYPE)
        self.variants = VariantsCollection([Variant(variant_id=x+1) for x in range(len(self.genotypes))], db='test')

    def test_dominant(self):
        """All affected must be carriers, all non affected must be non-carriers."""
        groups = {"affected": ["Father","Sasha","Dasha"], "not_affected": ["Mother","Lena","Lesha"]}
        ss = SamplesSelection(self.F.samples, groups)
        var = GenotypesFilterDominant(ss).apply(self.variants, self.genotypes).variants
        self.assertEqual(len(var), 2)
        for v in var:
            gts = self.genotypes[v.pk-1]
            self.assertEqual(gts[0], 1)         # mother
            self.assertGreaterEqual(gts[1], 2)  # father
            self.assertGreaterEqual(gts[2], 2)  # aff. Sasha
            self.assertGreaterEqual(gts[3], 2)  # aff. Dash
            self.assertEqual(gts[4], 1)         # Lesha
            self.assertEqual(gts[5], 1)         # Lena

    def test_noaffected(self):
        groups = {"affected": [], "not_affected": ["Lena"]}
        ss = SamplesSelection(self.F.samples, groups)
        var = GenotypesFilterDominant(ss).apply(self.variants, self.genotypes).variants
        self.assertEqual(len(var), 0)


############################
#        RECESSIVE         #
############################

#@unittest.skip('')
class TestRecessive(unittest.TestCase):
    def setUp(self):
        self.F = Family()

    def test_recessive(self):
        """All affected must be homozygous (4), the parents must be hererozygous,
        and all other not affected must be heterozygous or non-carriers."""
        genotypes = array(
            [[2,1, 4,2,1,1],  # X - Both parents must have it
             [2,2, 4,2,1,1],  # X - Affected but not homozygous
             [2,2, 4,4,1,1],  # V - OK
             [2,2, 4,4,4,1],  # X - Not affected homozygous
             [2,2, 4,4,2,1]], # V - Not affected carrier
            dtype=DTYPE)
        variants = VariantsCollection([Variant(variant_id=x+1) for x in range(len(genotypes))], db='test')
        groups = {"affected": ["Sasha","Dasha"], "not_affected": ["Mother","Father","Lena","Lesha"]}
        ss = SamplesSelection(self.F.samples, groups)
        var = GenotypesFilterRecessive(ss).apply(variants, genotypes).variants
        self.assertEqual(len(var), 2)
        for v in var:
            gts = genotypes[v.pk-1]
            self.assertEqual(gts[0], 2)
            self.assertEqual(gts[1], 2)
            self.assertEqual(gts[2], 4)
            self.assertEqual(gts[3], 4)
            self.assertLessEqual(gts[4], 2)
            self.assertLessEqual(gts[5], 2)


############################
#         DE NOVO          #
############################

#@unittest.skip('')
class TestDeNovo(unittest.TestCase):
    def setUp(self):
        self.F = Family()
        self.genotypes = array(
            [[2,1, 2,2,1,1],  # X - Mother carrier
             [1,2, 2,2,1,1],  # X - Father carrier
             [1,1, 2,2,1,1],  # V - OK
             [1,1, 2,2,1,2],  # X - Not affected mutant
             [1,1, 2,1,1,1],  # X - Affected non carrier
             [1,1, 2,2,1,1]], # V - Actually the only working situation
            dtype=DTYPE)
        self.variants = VariantsCollection([Variant(variant_id=x+1) for x in range(len(self.genotypes))], db='test')

    def test_denovo(self):
        groups = {"affected": ["Sasha","Dasha"], "not_affected": ["Mother","Father","Lena","Lesha"]}
        ss = SamplesSelection(self.F.samples, groups)
        var = GenotypesFilterDeNovo(ss).apply(self.variants, self.genotypes).variants
        self.assertEqual(len(var), 2)
        for v in var:
            gts = self.genotypes[v.pk-1]
            self.assertEqual(gts[0], 1)  # mother
            self.assertEqual(gts[1], 1)  # father
            self.assertEqual(gts[2], 2)  # Sasha
            self.assertEqual(gts[3], 2)  # Dasha
            self.assertEqual(gts[4], 1)  # Lesha
            self.assertEqual(gts[5], 1)  # Lena

    def test_parents_inactive(self):
        """Parents are inactive, so it should be shortcut and return no variant."""
        groups = {"affected": ["Sasha"], "not_affected": ["Lena"]}
        ss = SamplesSelection(self.F.samples, groups)
        var = GenotypesFilterDeNovo(ss).apply(self.variants, self.genotypes).variants
        self.assertEqual(len(var), 0)

    def test_parents_inactive_2(self):
        """Even if there is only one but we require 2."""
        groups = {"affected": ["Sasha"], "not_affected": ["Lena","Mother"]}
        ss = SamplesSelection(self.F.samples, groups)
        var = GenotypesFilterDeNovo(ss).apply(self.variants, self.genotypes).variants
        self.assertEqual(len(var), 0)


############################
#         X-LINKED         #
############################

#@unittest.skip('')
class TestXLinked(unittest.TestCase):
    """Test X-linked recessive case."""
    def setUp(self):
        self.F = Family()

    def test_both_parents_carriers_unaffected(self):
        """Both parents are carriers"""
        genotypes = array(
            [[2,2, 2,4,1,1],  # V - Both parents carriers, affected children have it
             [4,2, 2,4,1,1],  # X - Both parents carriers, mother carrier hom
             [2,2, 2,4,2,1],  # X - Both parents carriers, non-affected son carrier
             [2,2, 2,4,1,4],  # X - Both parents carriers, non-affected external female carrier hom
             [2,4, 2,4,1,2],  # X - Both parents carriers, mother is carrier hom (should be affected)
             [4,2, 2,4,1,2],  # X - Both parents carriers, father is carrier hom (can't be)
             [2,2, 2,2,1,1],  # X - Both parents carriers, affected daughter is carrier het only
             [2,2, 4,4,1,1]], # X - Both parents carriers, affected male is carrier hom
            dtype=DTYPE)
        variants = VariantsCollection([Variant(variant_id=x+1, chrom='chrX') for x in range(len(genotypes))], db='test')
        groups = {"affected": ["Father","Sasha","Dasha"], "not_affected": ["Mother","Lena","Lesha"]}
        ss = SamplesSelection(self.F.samples, groups)
        var = GenotypesFilterXLinked(ss).apply(variants, genotypes).variants
        self.assertEqual(len(var), 1)
        for v in var:
            gts = genotypes[v.pk-1]
            self.assertLessEqual(gts[0], 6)  # mother
            self.assertEqual(gts[1], 2)  # father
            self.assertEqual(gts[2], 2)  # Sasha
            self.assertEqual(gts[3], 4)  # Dasha
            self.assertEqual(gts[4], 1)  # Lesha
            self.assertLessEqual(gts[5], 3)  # Lena

    def test_father_only_carrier(self):
        """Only the father carries the variant - so he is affected."""
        variants = VariantsCollection([Variant(variant_id=1, chrom='chrX')], db='test')

        # X - Father carrier, mother not, daughter affected
        groups = {"affected": ["Father","Dasha"], "not_affected": ["Mother","Sasha","Lena","Lesha"]}
        ss = SamplesSelection(self.F.samples, groups)
        genotypes = array([[1,2, 1,4,1,1]],dtype=DTYPE)
        var = GenotypesFilterXLinked(ss).apply(variants, genotypes).variants
        self.assertEqual(len(var), 0)

        # X - Father carrier, mother not, son affected
        groups = {"affected": ["Father","Sasha"], "not_affected": ["Mother","Dasha","Lena","Lesha"]}
        ss = SamplesSelection(self.F.samples, groups)
        genotypes = array([[1,2, 2,1,1,1]],dtype=DTYPE)
        var = GenotypesFilterXLinked(ss).apply(variants, genotypes).variants
        self.assertEqual(len(var), 0)

    def test_mother_only_carrier(self):
        """Only the mother carries the variant. Father is unaffected."""
        variants = VariantsCollection([Variant(variant_id=1, chrom='chrX')], db='test')

        # X - Mother carrier, father not, affected daughter (cannot be, she needs 2 copies)
        groups = {"affected": ["Dasha"], "not_affected": ["Mother","Father","Sasha","Lena","Lesha"]}
        ss = SamplesSelection(self.F.samples, groups)
        genotypes = array([[2,1, 1,4,1,1]], dtype=DTYPE)
        var = GenotypesFilterXLinked(ss).apply(variants, genotypes).variants
        self.assertEqual(len(var), 0)

        # V - Mother carrier, father not, affected son carrier het
        groups = {"affected": ["Sasha"], "not_affected": ["Mother","Father","Dasha","Lena","Lesha"]}
        ss = SamplesSelection(self.F.samples, groups)
        genotypes = array([[2,1, 2,1,1,1]], dtype=DTYPE)
        var = GenotypesFilterXLinked(ss).apply(variants, genotypes).variants
        self.assertEqual(len(var), 1)

    def test_not_on_chrom_X(self):
        """Only variants on chrom X must pass"""
        genotypes = array([[2,2, 2,4,1,1]]*10, dtype=DTYPE)
        groups = {"affected": ["Father","Sasha","Dasha"], "not_affected": ["Mother","Lena","Lesha"]}
        ss = SamplesSelection(self.F.samples, groups)

        variants = VariantsCollection(
                [Variant(variant_id=x+1, chrom=('chrX' if x > 5 else 'chrU'))
                 for x in range(len(genotypes))], db='test')
        var = GenotypesFilterXLinked(ss).apply(variants, genotypes).variants
        self.assertEqual(len(var), 4)

        variants = VariantsCollection(
                [Variant(variant_id=x+1, chrom=('chrX' if x%2 else 'chrU'))
                 for x in range(len(genotypes))], db='test')
        var = GenotypesFilterXLinked(ss).apply(variants, genotypes).variants
        self.assertEqual(len(var), 5)

    @unittest.skip('Include into test db')
    def test_Xlinked_Lucie_ASMTL(self):
        """This gene has 2 X-linked variants"""
        db = 'lgueneau'
        ss = samples_selection_factory(db=db,
            groups = {'affected': ['09818','09819'], 'not_affected':['09960','09961']})
        qs = Variant.objects.using(db).filter(gene_symbol__in=['ASMTL','CSF2RA','PPP2R3B','TM4SF2'], chrom='chrX')
        # Using GenotypesFilterXLinked.apply()
        variants = variants_collection_factory(db=db, qs=qs)
        print(GenotypesFilterXLinked(ss).conditions_vector)
        var = GenotypesFilterXLinked(ss).apply(variants).variants
        self.assertEqual(len(var), 5)
        # Using FilterCollection.apply()
        fc = FiltersCollection([GenotypesFilterXLinked(ss)])
        var = fc.apply(initqs=qs, db=db).variants
        self.assertEqual(len(var), 5)

    @unittest.skip('Include into test db')
    def test_Xlinked_Norine_BMX(self):
        """This gene has no X-linked variant"""
        db = 'lgueneau'
        ss = samples_selection_factory(db=db,
            groups = {'affected': ['09818','09819'], 'not_affected':['09960','09961']})
        qs = Variant.objects.using(db).filter(gene_symbol__in=['BMX'], chrom='chrX')
        # Using GenotypesFilterXLinked.apply()
        variants = variants_collection_factory(db=db, qs=qs)
        var = GenotypesFilterXLinked(ss).apply(variants).variants
        self.assertEqual(len(var), 0)
        # Using FilterCollection.apply()
        fc = FiltersCollection([GenotypesFilterXLinked(ss)])
        var = fc.apply(initqs=qs, db=db).variants
        self.assertEqual(len(var), 0)


############################
#       COMPOUND HET       #
############################

#@unittest.skip('')
class TestCompoundHet(unittest.TestCase):
    def setUp(self):
        self.F = Family()
        groups = {"affected": ["Sasha","Dasha"], "not_affected": ["Mother","Father","Lesha","Lena"]}
        self.ss = SamplesSelection(self.F.samples, groups)
        # Most standard case:
        self.genotypes = array(
                [[2,1, 2,2, 1,1],   # mother and child carry var 1
                 [1,2, 2,2, 1,1]],  # father and child carry var 2
                dtype=DTYPE)
        self.variants = VariantsCollection([
            Variant(variant_id=1, start=1, gene_symbol='B'),  # mother contrib
            Variant(variant_id=2, start=2, gene_symbol='B'),  # father contrib
        ])

    def test_compound_normal_case(self):
        """Simple compound case, the only pair of variants should pass."""
        var = GenotypesFilterCompoundHeterozygous(self.ss).apply(self.variants, self.genotypes, parallel=False).variants
        self.assertEqual(len(var), 2)  # one pair

    def test_compound_normal_case_symmetric(self):
        """Simple compound case, the only pair of variants should pass."""
        genotypes = array([self.genotypes[1], self.genotypes[0]], dtype=DTYPE)
        var = GenotypesFilterCompoundHeterozygous(self.ss).apply(self.variants, genotypes, parallel=False).variants
        self.assertEqual(len(var), 2)  # one pair

    def test_compound_normal_case_parallel(self):
        """Simple compound case, the only pair of variants should pass."""
        var = GenotypesFilterCompoundHeterozygous(self.ss).apply(self.variants, self.genotypes, parallel=True).variants
        self.assertEqual(len(var), 2)  # one pair

    def test_compound_nogroups(self):
        """No active samples -> no compound"""
        ss = SamplesSelection(self.F.samples, {})
        f = GenotypesFilterCompoundHeterozygous(ss)
        self.assertTrue(f.shortcut)
        var = f.apply(self.variants, self.genotypes).variants
        self.assertEqual(len(var), 0)

    def test_compound_missing_group(self):
        """No affected samples -> no compound"""
        ss = SamplesSelection(self.F.samples, {"not_affected": ["Lena"]})
        f = GenotypesFilterCompoundHeterozygous(ss)
        self.assertTrue(f.shortcut)
        var = f.apply(self.variants, self.genotypes).variants
        self.assertEqual(len(var), 0)

    def test_compound_missing_parents(self):
        """No parents -> no compound"""
        ss = SamplesSelection(self.F.samples, {"affected": ["Mother", "Sasha"], "not_affected": ["Lena"]})
        f = GenotypesFilterCompoundHeterozygous(ss)
        self.assertTrue(f.shortcut)
        var = f.apply(self.variants, self.genotypes).variants
        self.assertEqual(len(var), 0)

    def test_compound_same_gene(self):
        """Compounds be on the same gene"""
        genotypes = array(
            [[2,1, 2,2, 1,1],
             [1,2, 2,2, 1,1],
             [1,2, 2,2, 1,1]], dtype=DTYPE)
        variants = VariantsCollection([
            Variant(variant_id=1, start=1, gene_symbol='B'),  # mother contrib
            Variant(variant_id=2, start=2, gene_symbol='B'),  # father contrib
            Variant(variant_id=3, start=2, gene_symbol='C'),  # X - not the same transcript
        ])
        var = GenotypesFilterCompoundHeterozygous(self.ss).apply(variants, genotypes).variants
        self.assertEqual(len(var), 2)  # not 1 because they are reported on 2 separate lines
        for v in var:
            gts = genotypes[v.pk]
            self.assertTrue((gts[0] == 1 and gts[1] == 2) or (gts[0] == 2 and gts[1] == 1))  # parents
            self.assertGreaterEqual(gts[2], 2)
            self.assertGreaterEqual(gts[3], 2)
            self.assertLessEqual(gts[4], 2)
            self.assertLessEqual(gts[5], 1)

    def test_compound_multiple_1(self):
        """There can be multiple combinations"""
        genotypes = array(
            [[2,1, 2,2, 1,1],
             [2,1, 2,2, 1,1],
             [1,2, 2,2, 1,1],
             [1,2, 2,2, 1,1],
             [1,2, 2,2, 1,1]], dtype=DTYPE)
        variants = VariantsCollection([
            Variant(variant_id=1, start=1, gene_symbol='B'),  # mother contrib 1
            Variant(variant_id=2, start=1, gene_symbol='B'),  # mother contrib 2
            Variant(variant_id=3, start=2, gene_symbol='B'),  # father contrib 1
            Variant(variant_id=4, start=3, gene_symbol='B'),  # father contrib 2
            Variant(variant_id=5, start=4, gene_symbol='B'),  # father contrib 3
        ])
        var = GenotypesFilterCompoundHeterozygous(self.ss).apply(variants, genotypes).variants
        self.assertEqual(len(var), 5)  # 6 pairs but 5 variants

    def test_compound_multiple_2(self):
        """Reference case for the following ones"""
        genotypes = array(
            [[2,1, 2,2, 1,1],
             [1,2, 2,2, 1,1],
             [1,2, 2,2, 1,1]], dtype=DTYPE)
        variants = VariantsCollection([
            Variant(variant_id=1, start=1, gene_symbol='B'),  # mother contrib
            Variant(variant_id=2, start=2, gene_symbol='B'),  # father contrib 1, not transmitted
            Variant(variant_id=3, start=3, gene_symbol='B'),  # father contrib 2, transmitted
        ])
        var = GenotypesFilterCompoundHeterozygous(self.ss).apply(variants, genotypes).variants
        self.assertEqual(len(var), 3)

    def test_compound_same_parent(self):
        """One of the affected gets a pair from the same parent: exclude"""
        genotypes = array(
            [[2,1, 2,1, 1,1],
             [1,2, 2,2, 1,1],
             [1,2, 2,2, 1,1],
             [1,2, 2,2, 1,1]], dtype=DTYPE)
        variants = VariantsCollection([
            Variant(variant_id=1, start=1, gene_symbol='B'),  # mother contrib   } }
            Variant(variant_id=2, start=2, gene_symbol='B'),  # father contrib 1 }    father + affected
            Variant(variant_id=3, start=3, gene_symbol='B'),  # father contrib 2   }  father + affected
            Variant(variant_id=4, start=4, gene_symbol='B'),  # father contrib 3
        ])
        var = GenotypesFilterCompoundHeterozygous(self.ss).apply(variants, genotypes).variants
        self.assertEqual(len(var), 0)

    def test_compound_healty_homozygous(self):
        """Unaffected homozygous: exclude (because it will affect both alleles)"""
        genotypes = array(
            [[2,1, 2,2, 1,1],
             [1,2, 2,2, 1,4],
             [1,2, 2,2, 1,1]], dtype=DTYPE)
        variants = VariantsCollection([
            Variant(variant_id=1, start=1, gene_symbol='B'),  # mother
            Variant(variant_id=2, start=2, gene_symbol='B'),  # father 1 + unaffected hom
            Variant(variant_id=3, start=3, gene_symbol='B'),  # father 2
        ])
        var = GenotypesFilterCompoundHeterozygous(self.ss).apply(variants, genotypes).variants
        self.assertEqual(len(var), 2)  # would be 3 but we exclude 1 variant -> 1 pair left

    def test_compound_unaffected_compound(self):
        """Unaffected compound: exclude (the disease is not due to a compound)"""
        genotypes = array(
            [[2,1, 2,2, 1,1],
             [2,1, 2,2, 2,1],
             [1,2, 2,2, 1,1],
             [1,2, 2,2, 2,1]], dtype=DTYPE)
        variants = VariantsCollection([
            Variant(variant_id=1, start=0, gene_symbol='B'),  # mother 1
            Variant(variant_id=2, start=1, gene_symbol='B'),  # mother 2 + unaffected 1
            Variant(variant_id=3, start=2, gene_symbol='B'),  # father 1
            Variant(variant_id=4, start=3, gene_symbol='B'),  # father 2 + unaffected 2
        ])
        var = GenotypesFilterCompoundHeterozygous(self.ss).apply(variants, genotypes).variants
        self.assertEqual(len(var), 2)  # would be 4, but here we exclude an entire pair (2 variants):
            # one of the ends of the unaffected pair must be non-deleterious,
            # so no affected pair containing one of them can have both alleles deficient.
            # Thus a single pair remains -> 2 variants.

    # Updated by the change that allows only one same compound for all affected samples.
    #@unittest.expectedFailure
    # To my opinion it is ok if different compound scenarios work in different affected samples
    # i.e. two samples can be affected but each one with a different compound pair.
    def test_compound_affected_nocompound(self):
        """Affected without the compound: exclude (the disease is not due to a compound).
        (!? When one affected has it but not the other, the disease cannot be due to this compound)."""
        genotypes = array(
            [[2,1, 2,2, 1,1],
             [1,2, 2,2, 1,1],
             [1,2, 2,1, 1,1]],
            dtype=DTYPE)
        variants = VariantsCollection([
            Variant(variant_id=1, start=1, gene_symbol='B'),  # } } father +  aff1  + aff2
            Variant(variant_id=2, start=2, gene_symbol='B'),  # } } mother + (aff1) + aff2
            Variant(variant_id=3, start=3, gene_symbol='B'),  # }   mother +  aff1
        ])
        var = GenotypesFilterCompoundHeterozygous(self.ss).apply(variants, genotypes).variants
        self.assertEqual(len(var), 2)  # would be 3, but we exclude 1 variant -> 1 pair left

    @unittest.expectedFailure
    # Actually now the genotype filters are always applied last, see FiltersCollection.list
    def test_compound_non_commutative(self):
        """The goal is to test the non-cummutativity of applying compound het then some other filter,
        or the contrary.
        Not certain about the final number, but at least it should go without an error."""
        variants = variants_collection_factory(db='test')
        ss = samples_selection_factory(db='test',
            groups = {'affected': ['09818','09819'], 'not_affected':['09960','09961']})

        filter_coll = variant_filters_collection_factory([
            ('filter', '=', 'PASS'),
            ('aaf_1kg_all', '<=', '0.01'),
            ('genotype', '=', 'compound_het'),
        ], ss)
        var = filter_coll.apply(variants).variants
        self.assertEqual(len(var), 13)

        filter_coll = variant_filters_collection_factory([
            ('genotype', '=', 'compound_het'),
            ('filter', '=', 'PASS'),
            ('aaf_1kg_all', '<=', '0.01'),
        ], ss)
        var = filter_coll.apply(variants).variants
        self.assertEqual(len(var), 0)

    def test_compound_Lucie_FNDC1(self):
        """These 2(3) variants are annotated on different transcripts of the same gene,
        and because of the group_by(transcript_id), the compound was not found.
        Check here that it is fixed.
        """
        ss = samples_selection_factory(db='test',
            groups = {'affected': ['101563','101591'], 'not_affected':['101564','101565']})
        variants = variants_collection_factory(db='test',
            qs=Variant.objects.using('test').filter(gene_symbol='FNDC1'))
        ## To select them directly:
        #variants = variants_collection_factory(
        #    Variants.objects.using('test').filter(start__in=['159653504','159653634']), db='test')
        var = GenotypesFilterCompoundHeterozygous(ss).apply(variants).variants
        self.assertEqual(len(var), 3)


############################
#       FROM REQUEST       #
############################

#@unittest.skip('')
class TestGenotypeFiltersFromRequest(unittest.TestCase):
    def setUp(self):
        self.variants = variants_collection_factory(db='test')
        self.genotypes = genotypes_service(db='test').genotypes

    def test_genotypes_filter_from_request_with_default_ss(self):
        """With no samples selection given, makes them from PED phenotype."""
        request = RequestFactory().get('', [('filter', 'genotype=dominant')])
        fc = variant_filters_from_request(request, db='test')
        gf = fc['genotype']
        self.assertIsInstance(gf, GenotypesFilterDominant)
        self.assertEqual(sorted(gf.ss.groups.keys()), ['affected','not_affected'])

    def test_genotypes_Nothing_filter_from_request_with_ss_from_request(self):
        """With a sound grouping passed by url."""
        samples = [('samples', 'A=09818,09819'), ('samples', 'B=09960,09961')]
        filters = [('filter', 'genotype=nothing')]
        request = RequestFactory().get('', samples + filters)
        fc = variant_filters_from_request(request, db='test')
        self.assertIsInstance(fc, FiltersCollection)
        self.assertTrue(len(fc) == len(filters))

        gf = fc['genotype']
        self.assertEqual(sorted(gf.ss.groups.keys()), ['A','B'])
        self.assertEqual(gf.name, 'genotype')
        self.assertEqual(gf.val, 'nothing')
        self.assertEqual(gf.op, '=')
        self.assertIsInstance(gf, GenotypesFilterDoNothing)

    #@unittest.skip('')
    def test_genotypes_Active_filter_from_request_with_ss_from_request(self):
        """With a sound grouping passed by url."""
        samples = [('samples', 'group1=09818,09819')]
        filters = [('filter', 'genotype=active')]
        request = RequestFactory().get('', samples + filters)
        fc = variant_filters_from_request(request, db='test')
        gf = fc['genotype']
        self.assertIsInstance(gf, GenotypesFilterActive)

        var = gf.apply(self.variants).variants  # no need for self.genotypes, it will be created on the fly
        for v in var:
            gts = self.genotypes[v.pk-1]
            self.assertTrue(gts[S09818] > 1 or gts[S09819] > 1)

    #@unittest.skip('')
    def test_genotypes_Dominant_filter_from_request_with_ss_from_request(self):
        """With a sound grouping passed by url."""
        samples = [('samples', 'not_affected=09960,09961'),
                   ('samples', 'affected=09818,09819')]
        filters = [('filter', 'genotype=dominant')]
        request = RequestFactory().get('', samples + filters)
        fc = variant_filters_from_request(request, db='test')
        gf = fc['genotype']
        self.assertIsInstance(gf, GenotypesFilterDominant)

        var = gf.apply(self.variants).variants
        for v in var:
            gts = self.genotypes[v.pk-1]
            self.assertGreater(gts[S09818], 1)
            self.assertGreater(gts[S09819], 1)
            self.assertEqual(gts[S09960], 1)
            self.assertEqual(gts[S09961], 1)


############################
#     CONDITIONS MERGE     #
############################

class TestMergeConditionsArray(unittest.TestCase):
    def setUp(self):
        self.f = GenotypesFilterDoNothing(samples_selection_factory(db='test'))

    def test_merge_conditions_array_replace(self):
        """Conditions are duplicated, remove the duplicates.
        First is hom ref, second in alt het, third is alt hom"""
        conds = [[0,1], [1,2], [2,4],
                 [0,1], [1,2], [2,4]]
        merged = merge_conditions_array(conds)
        self.assertEqual(merged, [(0,1), (1,2), (2,4)])

    def test_merge_conditions_array_contradictory(self):
        """The second one cannot be 2 (alt het) and 4 (alt hom) at the same time."""
        conds = [[0,1], [1,2], [2,4],
                 [0,1], [1,4], [2,4]]
        merged = merge_conditions_array(conds)
        self.assertEqual(merged, [(0,1), (1,0), (2,4)])

    def test_merge_conditions_array_augmented(self):
        """Carrier (6) < Carrier het (2), Not carrier hom (3) < Not carrier (1), etc."""
        conds = [[0,1], [1,2], [2,4], [3,2],
                 [0,1], [1,2], [2,4], [3,3],
                 [0,3], [1,6], [2,6], [3,7]]
        merged = merge_conditions_array(conds)
        self.assertEqual(merged, [(0,1), (1,2), (2,4), (3,2)])

    def test_merge_compound_case(self):
        """Real case, from compound het. (The first only is affected)."""
        c1 = [(2, 2), (1, 6), (0, 1), (5, 3), (3, 3), (4, 3), (0, 3), (1, 3)]
        c1_merged = merge_conditions_array(c1)
        self.assertEqual(c1_merged, [(0, 1), (1, 2), (2, 2), (3, 3), (4, 3), (5, 3)])

        c2 = [(2, 2), (1, 1), (0, 6), (5, 3), (3, 3), (4, 3), (0, 3), (1, 3)]
        c2_merged = merge_conditions_array(c2)
        self.assertEqual(c2_merged, [(0, 2), (1, 1), (2, 2), (3, 3), (4, 3), (5, 3)])

    def test_merge_compound_case2(self):
        """Real case, from compound het. (The first only is affected)."""
        c1 = [(3, 2), (1, 6), (0, 1), (5, 3), (3, 3), (4, 3), (0, 3), (1, 3)]
        c1_merged = merge_conditions_array(c1)
        self.assertEqual(c1_merged, [(0, 1), (1, 2), (3, 2), (4, 3), (5, 3)])

        c2 = [(3, 2), (1, 1), (0, 6), (5, 3), (3, 3), (4, 3), (0, 3), (1, 3)]
        c2_merged = merge_conditions_array(c2)
        self.assertEqual(c2_merged, [(0, 2), (1, 1), (3, 2), (4, 3), (5, 3)])



if __name__ == '__main__':
    unittest.main()

