
FILTER_CLASS_QUALITY = 'quality'
FILTER_CLASS_PATHOGENICITY = 'pathogenicity'
FILTER_CLASS_LOCATION = 'location'
FILTER_CLASS_FREQUENCY = 'frequency'
FILTER_CLASS_IMPACT = 'impact'
FILTER_CLASS_GENOTYPE = 'genotype'

# Correspondance between our names and gemini column names
TRANSLATION = {'pass_filter':'filter', 'quality':'qual', 'fisher_strand_bias':'FS',
               'strand_bias_odds_ratio':'sor', 'base_qual_rank_sum':'BaseQRankSum',
               'map_qual_rank_sum':'MQRankSum', 'read_pos_rank_sum':'ReadPosRankSum',
               }


################
# Filter names #
################

# The category determines how stats are calculated,
# i.e. the format of the Stats object that is sent to the frontend.

# static values
ENUM_FILTER_NAMES = ['impact', 'pass_filter', 'polyphen_pred', 'sift_pred', 'type']
TRUE_FALSE_ANY_FILTER_NAMES = ['in_dbsnp', 'in_1kg', 'in_esp', 'in_exac', 'is_exonic', 'is_coding']
# 0 to 1, diff. meanings
ZERO_ONE_FILTER_NAMES = ['polyphen_score', 'sift_score']
# 0 to 1, null has freq=0
FREQUENCY_FILTER_NAMES = ['aaf_1kg_all', 'aaf_esp_all', 'aaf_exac_all', 'aaf_max_all']
# 0 to 1, null has pval=1
PVALUE_FILTER_NAMES = [] #['gerp_element_pval']
# unbound
CONTINUOUS_FILTER_NAMES = ['quality', 'cadd_raw', 'cadd_scaled', 'gerp_bp_score',
                           'qual_depth', 'fisher_strand_bias', 'strand_bias_odds_ratio', 'rms_map_qual',
                           'base_qual_rank_sum', 'map_qual_rank_sum', 'read_pos_rank_sum']

# Put together
DISCRETE_FILTER_NAMES = ENUM_FILTER_NAMES + TRUE_FALSE_ANY_FILTER_NAMES
NUMERIC_FILTER_NAMES = CONTINUOUS_FILTER_NAMES + FREQUENCY_FILTER_NAMES + PVALUE_FILTER_NAMES
ALL_VARIANT_FILTER_NAMES = ENUM_FILTER_NAMES + TRUE_FALSE_ANY_FILTER_NAMES + CONTINUOUS_FILTER_NAMES + \
                           ZERO_ONE_FILTER_NAMES + FREQUENCY_FILTER_NAMES + PVALUE_FILTER_NAMES


#################
# Filter values #
#################
GENOTYPE_FILTER_NAMES = ['active','dominant','recessive','de_novo','compound_het']

