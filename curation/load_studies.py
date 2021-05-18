import os, gzip
import pandas as pd
import numpy as np
from curation.template_parser import *
from curation.config import *
from catalog.models import Score



def global_report(study_names_list, failed_studies):
    ''' Global reports of the studies import '''
    studies_count = len(study_names_list)
    import_success = studies_count - len(failed_studies.keys())
    print('\n=======================================================\n')
    print('#------------------------#')
    print('# End of script - Report #')
    print('#------------------------#')
    print(f'Successful imports: {import_success}/{studies_count}')
    if failed_studies:
        print(f'Failed imports:')
        for study,error_type in failed_studies.items():
            print(f'- {study}: {error_type}')
    print('\n')


def create_scoringfileheader(cscore, score_model=Score):
    '''Function to extract score & publication information for the PGS Catalog Scoring File commented header'''

    pub = cscore.publication
    lines = [
        '### PGS CATALOG SCORING FILE - see www.pgscatalog.org/downloads/#dl_ftp for additional information',
        '## POLYGENIC SCORE (PGS) INFORMATION',
        f'# PGS ID = {cscore.id}',
        f'# PGS Name = {cscore.name}',
        f'# Reported Trait = {cscore.trait_reported}',
        f'# Original Genome Build = {cscore.variants_genomebuild}',
        f'# Number of Variants = {cscore.variants_number}',
        '## SOURCE INFORMATION',
        f'# PGP ID = {pub.id}',
        f'# Citation = {pub.firstauthor} et al. {pub.journal} ({pub.pub_year}). doi:{pub.doi}'
    ]

    try:
        if cscore.license != score_model._meta.get_field('license')._get_default():
            ltext = cscore.license.replace('\n', ' ')     # Make sure there are no new-lines that would screw up the commenting
            lines.append('# LICENSE = {}'.format(ltext))  # Append to header
    except Exception as e:
        print(f'Exception: {e}')
    return lines


curation2schema = pd.read_excel(template_schema, index_col=0)
curation2schema_scoring = pd.read_excel(scoring_schema, index_col=0)

data_obj = [
    ('performance', 'num', Performance),
    ('sampleset', 'num', SampleSet),
    ('sample', 'id', Sample)
]

if skip_scorefiles == False:
    steps_count = 3 
else:
    steps_count = 2

failed_studies = {}

#Loop through studies to be included/loaded
for study_data in study_names_list:

    study_name = study_data['name']

    study_license = None
    if 'license' in study_data:
        study_license = study_data['license']

    study_status = None
    if 'status' in study_data:
        study_status = study_data['status']

    # Print current study name
    title = f'Study: {study_name}'
    border = '===='
    for i in range(len(title)):
        border += '=' 
    print(f'\n\n{border}\n# Study: {study_name} #\n{border}')
    if study_status:
        print(f'Curation status: {study_status}\n')

    ## Parsing ##
    print(f'==> Step 1/{steps_count}: Parsing study data')

    current_study = CurationTemplate()
    current_study.file_loc  = f'{studies_dir}/{study_name}/{study_name}.xlsx'
    current_study.table_mapschema = curation2schema
    current_study.read_curation()
    # Extract data from the different spreadsheets
    current_study.extract_cohorts()
    current_study.extract_publication(study_status)
    current_study.extract_scores(study_license)
    current_study.extract_samples()
    current_study.extract_performances()

    
    data_ids = {
        'metric': [],
        'performance': [],
        'sampleset': [],
        'sample': []
    }
    failed_data_import = []

    # List the reported warning(s)
    if current_study.report['warning']:
        print("\n/!\ Reported warning(s) /!\ \n")
        warning_report = current_study.report['warning']
        for spreadsheet in warning_report:
            print("  # Spreadsheet '"+spreadsheet+"'")
            for msg in list(warning_report[spreadsheet]):
                print('    - '+msg)
        print('\n')

    # List the reported error(s)
    if current_study.report['error']:
        print("\n### Reported error(s) ###\n")
        error_report = current_study.report['error']
        for spreadsheet in error_report:
            print("  # Spreadsheet '"+spreadsheet+"'")
            for msg in list(error_report[spreadsheet]):
                print('    - '+msg)
        failed_studies[study_name] = 'parsing error'
        continue
    
    # Exit for debugging
    #continue


    ## Import ##
    print('\n----------------------------------\n')
    print(f'==> Step 2/{steps_count}: Importing study data')

    saved_scores = {}
    existing_scores = []
    import_warnings = []


    ## Publication ##
    if current_study.parsed_publication.model:
        current_publication = current_study.parsed_publication.model
    else:
        try:
            current_publication = Publication.objects.get(**current_study.parsed_publication.data)
        except Publication.DoesNotExist:
            current_publication = current_study.parsed_publication.create_publication_model()


    ## Score ##
    for score_id, score_data in current_study.parsed_scores.items():
        # Check if score already exist
        try:
            current_score = Score.objects.get(name=score_data.data['name'],publication__id=current_publication.id)
            import_warnings.append(f'Existing Score: {current_score.id} ({score_id})')
            existing_scores.append(current_score.id)
        except Score.DoesNotExist:
            current_score = score_data.create_score_model(current_publication)
            import_warnings.append(f'New Score: {current_score.id} ({score_id})')
        saved_scores[score_id] = current_score


    ## Sample ##
    # GWAS and Dev/Training Sample and attach them to Scores
    try:
        for x in current_study.parsed_samples_scores:
            scores = []
            for s in x[0][0].split(','):
                if s.strip() in saved_scores:
                    scores.append(saved_scores[s.strip()])
                else:
                    import_warnings.append(f'{s.strip()} is not found in the saved scores list!!!')
            samples = x[1]
            for current_score in scores:
                for sample in samples:
                    sample_model_exist = False
                    if current_score.id in existing_scores:
                        sample_model_exist = sample.sample_model_exist()
                    if not sample_model_exist:
                        current_sample = sample.create_sample_model()
                        data_ids['sample'].append(current_sample.id)
                        if x[0][1] == 'GWAS/Variant associations':
                            current_score.samples_variants.add(current_sample)
                        elif x[0][1] == 'Score development':
                            current_score.samples_training.add(current_sample)
                        else:
                            import_warnings.append('ERROR: Unclear how to add samples')
                    else:
                        import_warnings.append(f'Sample "{x[0][0]}" ({x[0][1]}) already exist in the Database')
    except Exception as e:
        failed_data_import.append(f'GWAS & Dev/Testing Sample: {e}')


    # Check if the Performance Metrics already exist in the DB
    # If they exist, we delete them (including the associated SampleSet and Samples)
    try:
        data2delete = {'performance': set(), 'sampleset': set(), 'sample': set()}
        for x in current_study.parsed_performances:
            i, performance = x
            # Find Score from the Score spreadsheet
            if i[0] in saved_scores:
                current_score = saved_scores[i[0]]
            # Find existing Score in the database (e.g. PGS000001)
            else:
                try:
                    current_score = Score.objects.get(id__iexact=i[0])
                except Score.DoesNotExist:
                    failed_data_import.append(f'Performance Metric: can\'t find the Score {i[0]} in the database')
                    continue
            performances = Performance.objects.filter(publication=current_publication, score=current_score)
            
            for performance in performances:
                sampleset = performance.sampleset
                samples = sampleset.samples.all()
                # Store the objects to delete
                data2delete['performance'].add(performance)
                data2delete['sampleset'].add(sampleset)
                for sample in samples:
                    data2delete['sample'].add(sample)
        # Delete stored objects
        for data_type in ('performance','sampleset','sample'):
            data_list = list(data2delete[data_type])
            import_warnings.append(f'DELETE existing {data_type}(s) [ids]: {", ".join([str(x.id) for x in data_list])}')
            for entry in data_list:
                entry.delete()

    except Exception as e:
        failed_data_import.append(f'Check existing Performance Metric: {e}')


    # Test (Evaluation) Samples and Sample Sets
    testset_to_sampleset = {}
    try:
        for x in current_study.parsed_samples_testing:
            test_name, sample_list = x

            samples_for_sampleset = []

            # Create samples
            for sample_test in sample_list:
                current_sample = sample_test.create_sample_model()
                data_ids['sample'].append(current_sample.id)
                samples_for_sampleset.append(current_sample)
                
            # Initialize the current SampleSet
            current_sampleset = SampleSet()
            current_sampleset.set_ids(next_PSS_num())
            current_sampleset.save()
            data_ids['sampleset'].append(current_sampleset.num)

            # Add sample(s) to the SampleSet
            for sample in samples_for_sampleset:
                current_sampleset.samples.add(current_sample)
                current_sampleset.save()

            testset_to_sampleset[test_name] = current_sampleset
    except Exception as e:
        failed_data_import.append(f'SampleSet & Evaluation Sample: {e}')


    ## Performance Metrics ##
    try:
        for x in current_study.parsed_performances:
            i, performance = x
            # Find Score from the Score spreadsheet
            if i[0] in saved_scores:
                current_score = saved_scores[i[0]]
            # Find existing Score in the database (e.g. PGS000001)
            else:
                try:
                    current_score = Score.objects.get(id__iexact=i[0])
                except Score.DoesNotExist:
                    failed_data_import.append(f'Performance Metric: can\'t find the Score {i[0]} in the database')
                    continue

            related_SampleSet = testset_to_sampleset[i[1]]

            current_performance = performance.create_performance_model(publication=current_publication, score=current_score, sampleset=related_SampleSet)
            import_warnings.append(f'New Performance Metric: {current_performance.id} & new Sample Set: {current_performance.sampleset.id}')

            data_ids['performance'].append(current_performance.num)
    except Exception as e:
        failed_data_import.append(f'Performance Metric: {e}')


    # Set publication curation status
    if not study_status:
        current_publication.curation_status = default_curation_status
        current_publication.save()

    # Print import warnings 
    if len(import_warnings):
        print('\n>>>> Import information <<<<')
        print('  - '+'\n  - '.join(import_warnings))

    # Remove entries if the import failed
    if len(failed_data_import):
        failed_studies[study_name] = 'import error'
        print('\n**** ERROR: Import failed! ****')
        print('  - '+'\n  - '.join(failed_data_import))
        for obj in data_obj:
            ids = data_ids[obj[0]]
            if len(ids):
                col_condition = obj[1] + '__in'
                obj[2].objects.filter(**{ col_condition: ids}).delete()
                print(f'  > DELETED {obj[0]} (column "{obj[1]}") : {ids}')
        continue


    #==============#
    # Scoring file #
    #==============#
    # Read the PGS and re-format with header information
    if skip_scorefiles == False:
        print('\n----------------------------------\n')
        print(f'==> Step 3/{steps_count}: Add header to the Scoring file(s)')
        for score_id, current_score in saved_scores.items():
            try:
                print('Step 0')
                loc_scorefile = f'{studies_dir}/{study_name}/raw_scores/{score_id}.txt'
                df_scoring = pd.read_table(loc_scorefile, dtype='str', engine = 'python')
                column_check = True
                print('Step 0a')
                for x in df_scoring.columns:
                    if not x in curation2schema_scoring.index:
                        column_check = False
                        print(f'{x} not in index')
                        break
                # Check that columns are in the schema
                #column_check = [x in curation2schema_scoring.index for x in df_scoring.columns]
                #if all(column_check):
                print('Step 0b')
                if column_check == True:
                    print('Step 1a')
                    header = create_scoringfileheader(current_score)
                    print('Step 1b')
                    #Check if weight_type in columns
                    if 'weight_type' in df_scoring.columns:
                        if all(df_scoring['weight_type']):
                            val = df_scoring['weight_type'][0]
                            if val == 'OR':
                                df_scoring = df_scoring.rename({'effect_weight' : 'OR'}, axis='columns').drop(['weight_type'], axis=1)
                    if 'effect_weight' not in df_scoring.columns:
                        if 'OR' in df_scoring.columns:
                            df_scoring['effect_weight'] = np.log(pd.to_numeric(df_scoring['OR']))
                            df_scoring['weight_type'] = 'log(OR)'
                        elif 'HR' in df_scoring.columns:
                            df_scoring['effect_weight'] = np.log(pd.to_numeric(df_scoring['HR']))
                            df_scoring['weight_type'] = 'log(HR)'
                    print('Step 2')
                    # Reorganize columns according to schema
                    corder = []
                    for x in curation2schema_scoring.index:
                        if x in df_scoring.columns:
                            corder.append(x)
                    print('Step 3')
                    df_scoring = df_scoring[corder]
                    with gzip.open(f'{scoring_dir}/{current_score.id}.txt.gz', 'w') as outf:
                        outf.write('\n'.join(header).encode('utf-8'))
                        outf.write('\n'.encode('utf-8'))
                        outf.write(df_scoring.to_csv(sep='\t', index=False).encode('utf-8'))
                    print('Step 4')
                else:
                    badmaps = []
                    for i, v in enumerate(column_check):
                        if v == False:
                            badmaps.append(df_scoring.columns[i])
                    failed_studies[study_name] = 'scoring file error'
                    print(f'ERROR in {loc_scorefile} ! bad columns: {badmaps}')
            except:
                failed_studies[study_name] = 'scoring file error'
                print(f'ERROR reading scorefile: {loc_scorefile}')

# Global reports
global_report(study_names_list, failed_studies)

