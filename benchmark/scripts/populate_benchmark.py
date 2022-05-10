import os, sys, math
from catalog.models import EFOTrait_Ontology
from benchmark.models import *

bm_db = 'benchmark'
efo_id = 'EFO_0005842'

# ICDs (Codings)
icds = {
    'ICD9: 153.0': 'Malignant neoplasm of hepatic flexure',
    'ICD9: 153.1': 'Malignant neoplasm of transverse colon',
    'ICD9: 153.2': 'Malignant neoplasm of descending colon',
    'ICD9: 153.3': 'Malignant neoplasm of sigmoid colon',
    'ICD9: 153.4': 'Malignant neoplasm of cecum',
    'ICD9: 153.5': 'Malignant neoplasm of appendix vermiformis',
    'ICD9: 153.6': 'Malignant neoplasm of hepatic flexure',
    'ICD9: 153.7': 'Malignant neoplasm of splenic flexure',
    'ICD9: 153.8': 'Malignant neoplasm of other specified sites of large intestine',
    'ICD9: 153.9': 'Malignant neoplasm of colon, unspecified site',
    'ICD9: 154.0': 'Malignant neoplasm of rectosigmoid junction',
    'ICD9: 154.1': 'Malignant neoplasm of rectum',
    'ICD9: 154.8': 'Malignant neoplasm of other sites of rectum, rectosigmoid junction, and anus',
	'ICD10: C18.0': 'Malignant neoplasm of cecum',
    'ICD10: C18.1': 'Malignant neoplasm of appendix',
    'ICD10: C18.2': 'Malignant neoplasm of ascending colon',
    'ICD10: C18.3': 'Malignant neoplasm of hepatic flexure',
    'ICD10: C18.4': 'Malignant neoplasm of transverse colon',
    'ICD10: C18.5': 'Malignant neoplasm of splenic flexure',
    'ICD10: C18.6': 'Malignant neoplasm of descending colon',
    'ICD10: C18.7': 'Malignant neoplasm of sigmoid colon',
    'ICD10: C18.8': 'Malignant neoplasm of overlapping sites of colon',
    'ICD10: C18.9': 'Malignant neoplasm of colon, unspecified',
    'ICD10: C19': 'Malignant neoplasm of rectosigmoid junction',
    'ICD10: C20': 'Malignant neoplasm of rectum',
    'ICD10: C21.8': 'Malignant neoplasm of overlapping sites of rectum, anus and anal canal'
}

metric_label = {
    'DeltaC': 'Delta-C-index',
    'deltaAUROC': 'DeltaAUROC'
}

metric_info = {
    'HR': 'Hazard Ratio',
    'OR': 'Odds Ratio',
    'Delta-C-index': 'Δ C-index (PRS+covariates vs. covariates alone)',
    'DeltaAUROC': 'Δ AUROC (PRS+covariates vs. covariates alone)',
    'DeltaR2': 'Δ R2'
}

traits_to_skip = [
    'DBP_highest',
    'DBP_median',
    'DBP_latest',
    'Glaucoma_CALIBER',
    'Obesity',
    'SBP_highest',
    'SBP_median',
    'SBP_latest'
]


def get_efo_trait(trait_label):
    try:
        bm_trait = BM_EFOTrait.objects.using(bm_db).get(label=trait_label)
    except BM_EFOTrait.DoesNotExist:
        try:
            trait = EFOTrait_Ontology.objects.get(label=trait_label)
        except EFOTrait_Ontology.DoesNotExist:
            print("Can't find the trait '"+trait_label+"' in the PGS Catalog DB (EFOTrait_Ontology)!")
            exit(1)

        bm_trait = BM_EFOTrait.objects.using(bm_db).create(
            id=trait.id,
            label=trait.label,
            description=trait.description,
            #synonyms=trait.synonyms,
            #mapped_terms=trait.mapped_terms
        )
    return bm_trait



skip_independent=1

if skip_independent==0:
    print("Import independent data")
    # ICDs
    for icd in icds:
        icd_type = (icd.split(':'))[0]
        BM_Coding.objects.using(bm_db).create(
            id=icd,
            label=icds[icd],
            type=icd_type
        )

    # Trait
    bm_efotrait = BM_EFOTrait.objects.using(bm_db).create(
        id=efo_id,
        label='Colorectal cancer',
        description='A primary or metastatic malignant neoplasm that affects the colon or rectum. Representative examples include carcinoma, lymphoma, and sarcoma. [NCIT: C4978]'
    )
    for icd in icds:
        bm_icd = BM_Coding.objects.using(bm_db).get(id=icd)
        bm_efotrait.phenotype_structured.add(bm_icd)


    # Cohort
    BM_Cohort.objects.using(bm_db).create(
        name_short='UKB',
        name_full='UK Biobank'
    )
    BM_Cohort.objects.using(bm_db).create(
        name_short='G&H',
        name_full='Genes & Health'
    )
    BM_Cohort.objects.using(bm_db).create(
        name_short='EstBB',
        name_full='Estonian Biobank'
    )


data_structure = {}

print("Read/parse data file")

data_filepaths = [
    '/Users/lg10/Documents/PGS/Data/MergedPerformanceMetrics_LongForm_edited.csv',
    #'/Users/lg10/Documents/PGS/Data/benchmark_data_UKB_example.csv',
    #'/Users/lg10/Documents/PGS/Data/CRC_EB.csv',
];

trait_efo = {}
current_trait = ''

for file in data_filepaths:
    print("# Parse file: "+file)
    with open(file) as fp:
        # First line, to skip
        line = fp.readline()
        while line:
            line = fp.readline()
            if line:
                line_content = line.strip()
                data = line_content.split(',')
                trait    = data[0]
                pgs_id   = data[1]
                ancestry = data[2]
                metric   = data[3]
                estimate = data[4]
                lower_e  = data[5]
                upper_e  = data[6]
                sample_number   = int(float(data[7]))
                sample_cases    = data[8]
                sample_controls = data[9]
                sample_number_male   = data[10]
                sample_cases_male    = data[11]
                sample_controls_male = data[12]
                cohort = data[13]

                # Trait
                if trait in traits_to_skip:
                    continue;
                if trait != current_trait:
                    current_trait = trait
                    print("# Import benchmark for the trait '"+trait+"'")

                if trait in trait_efo:
                    bm_trait = trait_efo[trait]
                else:
                    bm_trait = get_efo_trait(trait)
                    trait_efo[trait] = bm_trait

                # Sample
                sex_type = 'Both'
                #if sample_number == sample_number_male:
                #    sex_type = "Male"
                #elif sample_number_male == 0:
                if sample_number_male == 0:
                    sex_type = "Female"

                if sample_cases == '':
                    if sample_controls:
                        sample_cases = sample_number - int(float(sample_controls))
                    sample_cases = 0
                if sample_controls == '':
                    if sample_cases:
                        sample_controls = sample_number - int(float(sample_cases))
                    else:
                        sample_controls = 0
                if sample_number_male == '':
                    sample_number_male = 0
                if sample_cases_male == '':
                    sample_cases_male = 0
                if sample_controls_male == '':
                    sample_controls_male = 0

                sample_cases    = int(float(sample_cases))
                sample_controls = int(float(sample_controls))
                sample_number_male   = int(float(sample_number_male))
                sample_cases_male    = int(float(sample_cases_male))
                sample_controls_male = int(float(sample_controls_male))

                # Fetch BM_Cohort
                bm_cohort = BM_Cohort.objects.using(bm_db).get(name_short=cohort)

                # Check if BM_Sample exist (cohort, ancestry, sex)
                try:
                    bm_sample = BM_Sample.objects.using(bm_db).get(
                        cohort=bm_cohort,
                        ancestry_broad=ancestry,
                        sample_sex=sex_type,
                        sample_number=sample_number,
                        sample_cases=sample_cases,
                        sample_controls=sample_controls
                    )
                except BM_Sample.DoesNotExist:
                    BM_Sample.objects.using(bm_db).create(
                        cohort=bm_cohort,
                        ancestry_broad=ancestry,
                        sample_sex=sex_type,
                        sample_number=sample_number,
                        sample_cases=sample_cases,
                        sample_controls=sample_controls
                    )
                    bm_sample = BM_Sample.objects.using(bm_db).get(
                        cohort=bm_cohort,
                        ancestry_broad=ancestry,
                        sample_sex=sex_type,
                        sample_number=sample_number,
                        sample_cases=sample_cases,
                        sample_controls=sample_controls
                    )

                # Get BM_Sample ID
                sample_id = bm_sample.id

                # Convert HR and OR data to e based exponential
                #if (metric == 'HR' or metric == 'OR') and cohort == ukb_cohort:
                #    estimate = round(math.exp(float(estimate)), 4)
                #    if lower_e and upper_e:
                #        lower_e = round(math.exp(float(lower_e)), 4)
                #        upper_e = round(math.exp(float(upper_e)), 4)


                # Create structure: Cohort -> BM_Sample ID -> Trait -> Score ID -> Metric -> Data value
                if not cohort in data_structure:
                    data_structure[cohort] = {}
                if not sample_id in data_structure[cohort]:
                    data_structure[cohort][sample_id] = {}
                if not trait in data_structure[cohort][sample_id]:
                    data_structure[cohort][sample_id][trait] = {}
                if not pgs_id in data_structure[cohort][sample_id][trait]:
                    data_structure[cohort][sample_id][trait][pgs_id] = {}
                #print(str(data_structure[cohort][sample_id][pgs_id]))

                if lower_e and upper_e:
                    data_structure[cohort][sample_id][trait][pgs_id][metric] = { 'estimate': estimate, 'ci': '['+str(lower_e)+', '+str(upper_e)+']' }
                else:
                    data_structure[cohort][sample_id][trait][pgs_id][metric] = { 'estimate': estimate }


print("Populate the BM_Performance and BM_Metric tables")

# Once we have all the structures, generate the BM_performance
for cohort in data_structure:
    bm_cohort = BM_Cohort.objects.using(bm_db).get(name_short=cohort)
    for sample_id in data_structure[cohort]:
        bm_sample = BM_Sample.objects.using(bm_db).get(id=sample_id)
        for trait in data_structure[cohort][sample_id]:
            bm_efotrait = trait_efo[trait]
            # Performances
            for pgs_id in data_structure[cohort][sample_id][trait]:
                performance = BM_Performance.objects.using(bm_db).create(
                    score_id=pgs_id,
                    sample=bm_sample,
                    cohort=bm_cohort,
                    efotrait=bm_efotrait
                )
                performance_id = performance.id
                # Metricsc
                # For each Data value, generate the corresponding BM_Metric
                for metric in data_structure[cohort][sample_id][trait][pgs_id]:
                    estimate = data_structure[cohort][sample_id][trait][pgs_id][metric]['estimate']
                    ci=None
                    if 'ci' in data_structure[cohort][sample_id][trait][pgs_id][metric]:
                        ci = data_structure[cohort][sample_id][trait][pgs_id][metric]['ci']

                    short_name = metric
                    if metric in metric_label:
                        short_name = metric_label[metric]
                    long_name = short_name
                    if short_name in metric_info:
                        long_name = metric_info[short_name]

                    BM_Metric.objects.using(bm_db).create(
                        performance_id=performance_id,
                        name=long_name,
                        name_short=short_name,
                        estimate=estimate,
                        ci=ci
                    )
