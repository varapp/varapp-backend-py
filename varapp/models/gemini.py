# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Remove `managed = True` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin sqlcustom [app_label]'
# into your database.
from __future__ import unicode_literals

from django.db import models


## Gemini schema

class GeneDetailed(models.Model):
    uid = models.IntegerField(primary_key=True, blank=True)
    chrom = models.TextField(blank=True, null=True)
    gene = models.TextField(blank=True, null=True)
    is_hgnc = models.NullBooleanField()
    ensembl_gene_id = models.TextField(blank=True, null=True)
    transcript = models.TextField(blank=True, null=True)
    biotype = models.TextField(blank=True, null=True)
    transcript_status = models.TextField(blank=True, null=True)
    ccds_id = models.TextField(blank=True, null=True)
    hgnc_id = models.TextField(blank=True, null=True)
    entrez_id = models.TextField(blank=True, null=True)
    cds_length = models.TextField(blank=True, null=True)
    protein_length = models.TextField(blank=True, null=True)
    transcript_start = models.TextField(blank=True, null=True)
    transcript_end = models.TextField(blank=True, null=True)
    strand = models.TextField(blank=True, null=True)
    synonym = models.TextField(blank=True, null=True)
    rvis_pct = models.TextField(blank=True, null=True)  # This field type is a guess.
    mam_phenotype_id = models.TextField(blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'gene_detailed'

class GeneSummary(models.Model):
    uid = models.IntegerField(primary_key=True, blank=True)
    chrom = models.TextField(blank=True, null=True)
    gene = models.TextField(blank=True, null=True)
    is_hgnc = models.NullBooleanField()
    ensembl_gene_id = models.TextField(blank=True, null=True)
    hgnc_id = models.TextField(blank=True, null=True)
    transcript_min_start = models.TextField(blank=True, null=True)
    transcript_max_end = models.TextField(blank=True, null=True)
    strand = models.TextField(blank=True, null=True)
    synonym = models.TextField(blank=True, null=True)
    rvis_pct = models.TextField(blank=True, null=True)  # This field type is a guess.
    mam_phenotype_id = models.TextField(blank=True, null=True)
    in_cosmic_census = models.NullBooleanField()
    class Meta:
        managed = False
        db_table = 'gene_summary'

class Resources(models.Model):
    name = models.TextField(blank=True, null=True)
    resource = models.TextField(blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'resources'

class SampleGenotypeCounts(models.Model):
    sample_id = models.IntegerField(primary_key=True, blank=True)
    num_hom_ref = models.IntegerField(blank=True, null=True)
    num_het = models.IntegerField(blank=True, null=True)
    num_hom_alt = models.IntegerField(blank=True, null=True)
    num_unknown = models.IntegerField(blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'sample_genotype_counts'

class SampleGenotypes(models.Model):
    sample_id = models.IntegerField(primary_key=True, blank=True)
    gt_types = models.BinaryField(blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'sample_genotypes'

class Samples(models.Model):
    sample_id = models.IntegerField(primary_key=True, blank=True, null=False)
    family_id = models.TextField(blank=True, null=True)
    name = models.TextField(unique=True, blank=True, null=True)
    paternal_id = models.TextField(blank=True, null=True)
    maternal_id = models.TextField(blank=True, null=True)
    sex = models.TextField(blank=True, null=True)
    phenotype = models.TextField(blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'samples'


class Variants(models.Model):
    chrom = models.TextField(blank=True)
    start = models.IntegerField(blank=True, null=True, db_column='start')
    end = models.IntegerField(blank=True, null=True)
    variant_id = models.IntegerField(primary_key=True, blank=True)
    ref = models.TextField(blank=True)
    alt = models.TextField(blank=True)
    quality = models.FloatField(blank=True, null=True, db_column='qual')  # This field type is a guess.
    pass_filter = models.TextField(blank=True, db_column='filter')
    gts_blob = models.BinaryField(blank=True, null=True, db_column='gts')
    gt_types_blob = models.BinaryField(blank=True, null=True, db_column='gt_types')
    in_dbsnp = models.NullBooleanField()
    dbsnp = models.TextField(blank=True, db_column='rs_ids')
    clinvar_sig = models.TextField(blank=True)
    clinvar_disease_acc = models.TextField(blank=True)
    gerp_bp_score = models.FloatField(blank=True, null=True)  # This field type is a guess.
    gerp_element_pval = models.FloatField(blank=True, null=True)  # This field type is a guess.
    gene_symbol = models.TextField(blank=True, db_column='gene')
    transcript = models.TextField(blank=True)
    exon = models.TextField(blank=True)
    is_exonic = models.NullBooleanField()
    is_coding = models.NullBooleanField()
    is_lof = models.NullBooleanField()
    codon_change = models.TextField(blank=True)
    aa_change = models.TextField(blank=True)
    impact = models.TextField(blank=True)
    impact_so = models.TextField(blank=True)
    impact_severity = models.TextField(blank=True)
    polyphen_pred = models.TextField(blank=True)
    polyphen_score = models.FloatField(blank=True)
    sift_pred = models.TextField(blank=True, null=True)
    sift_score = models.FloatField(blank=True, null=True)
    read_depth = models.IntegerField(blank=True, null=True, db_column='depth')
    #strand_bias = models.FloatField(blank=True, null=True)
    rms_map_qual = models.FloatField(blank=True, null=True)
    qual_depth = models.FloatField(blank=True, null=True)
    allele_count = models.IntegerField(blank=True, null=True)
    cadd_raw = models.FloatField(blank=True, null=True)
    cadd_scaled = models.FloatField(blank=True, null=True)
    in_esp = models.NullBooleanField()
    in_1kg = models.NullBooleanField()
    in_exac = models.NullBooleanField()
    #aaf_esp_ea = models.DecimalField(blank=True, null=True, default=0)
    #aaf_esp_aa = models.DecimalField(blank=True, null=True, default=0)
    aaf_esp_all = models.DecimalField(blank=True, null=True, max_digits=7, decimal_places=2)
    #aaf_1kg_amr = models.DecimalField(blank=True, null=True, default=0)
    #aaf_1kg_eas = models.DecimalFieldd(blank=True, null=True, default=0)
    #aaf_1kg_sas = models.DecimalField(blank=True, null=True, default=0)
    #aaf_1kg_afr = models.DecimalField(blank=True, null=True, default=0)
    #aaf_1kg_eur = models.DecimalField(blank=True, null=True, default=0)
    aaf_1kg_all = models.DecimalField(blank=True, null=True, max_digits=7, decimal_places=2)
    aaf_exac_all = models.DecimalField(blank=True, null=True, max_digits=7, decimal_places=2)
    aaf_max_all = models.DecimalField(blank=True, null=True, db_column='max_aaf_all', max_digits=7, decimal_places=2)
    #info = models.BinaryField(blank=True, null=True)
    type = models.TextField(blank=True)
    #sub_type = models.TextField(blank=True)

### Manually added ###

    allele_freq = models.FloatField(blank=True, null=True, db_column='AF')
    base_qual_rank_sum = models.FloatField(blank=True, null=True, db_column='BaseQRankSum')
    fisher_strand_bias = models.FloatField(blank=True, null=True, db_column='FS')
    map_qual_rank_sum = models.FloatField(blank=True, null=True, db_column='MQRankSum')
    read_pos_rank_sum = models.FloatField(blank=True, null=True, db_column='ReadPosRankSum')
    strand_bias_odds_ratio = models.FloatField(blank=True, null=True, db_column='SOR')
    #GQ_MEAN = models.FloatField(blank=True, null=True)
    #GQ_STDDEV = models.FloatField(blank=True, null=True)
    #VQSLOD = models.FloatField(blank=True, null=True)

### VEP custom fields ###

    hgvsp = models.TextField(blank=True, db_column='vep_hgvsp')
    hgvsc = models.TextField(blank=True, db_column='vep_hgvsc')

    def __str__(self):
        return "<Variant {}:{}>".format(self.chrom, self.start)

    class Meta:
        managed = False
        db_table = 'variants'


class VcfHeader(models.Model):
    vcf_header = models.TextField(blank=True)
    class Meta:
        managed = False
        db_table = 'vcf_header'

class Version(models.Model):
    version = models.TextField(blank=True)
    class Meta:
        managed = False
        db_table = 'version'
