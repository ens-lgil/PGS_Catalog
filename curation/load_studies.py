import os, gzip
import numpy as np
from curation.template_parser import *
from curation.config import *
from catalog.models import Score


curation2schema = pd.read_excel(template_schema, index_col=0)
curation2schema_scoring = pd.read_excel(scoring_schema, index_col=0)

data_obj = [
    ('metric', 'id', Metric),
    ('performance', 'num', Performance),
    ('sampleset', 'num', SampleSet),
    ('sampleset', 'id', Sample)
]

#Loop through studies to be included/loaded
for study_name in study_names_list:
    # Print current study name
    title = f'Study: {study_name}'
    border = '===='
    for i in range(len(title)):
       border += '=' 
    print(f'\n\n{border}\n# Study: {study_name} #\n{border}')

    current_study = CurationTemplate()
    current_study.file_loc  = f'{studies_dir}/{study_name}/{study_name}.xlsx'
    current_study.table_mapschema = curation2schema
    current_study.read_curation()
    # Extract data from the different spreadsheets
    current_study.extract_cohorts()
    current_study.extract_publication()
    current_study.extract_scores()
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
            print("\t# Spreadsheet '"+spreadsheet+"'")
            for msg in warning_report[spreadsheet]:
                print('\t- '+msg)
        print('\n')

    # List the reported error(s)
    if current_study.report['error']:
        print("\n### Reported error(s) ###\n")
        error_report = current_study.report['error']
        for spreadsheet in error_report:
            print("\t# Spreadsheet '"+spreadsheet+"'")
            for msg in error_report[spreadsheet]:
                print('\t- '+msg)
        continue
        print('\n')
    
    # Exit for debugging
    #continue
    #exit(0)

    saved_scores = {}
    existing_scores = []
    import_warnings = []


    ## Publication ##
    current_publication = current_study.parsed_publication.create_publication_model()


    ## Score ##
    for score_id, score_data in current_study.parsed_scores.items():
        # Check if score already exist
        try:
            current_score = Score.objects.get(name=score_data.data['name'],publication__id=current_publication.id)
            import_warnings.append(f'Existing Score: {current_score.id} ({score_id})')
            existing_scores.append(current_score.id)
        except Score.DoesNotExist:
            current_score = score_data.create_score_model()
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


    # Test (Evaluation) Samples and Sample Sets
    testset_to_sampleset = {}
    try:
        for x in current_study.parsed_samples_testing:
            test_name, sample_list = x

            samples_for_sampleset = []

            # Create samples
            for sample_desc in sample_list:
                current_sample = sample_desc.create_sample_model()
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
            for metric in Metric.objects.filter(performance__id=current_performance.id):
                data_ids['metric'].append(metric.id)
            data_ids['performance'].append(current_performance.num)
    except Exception as e:
        failed_data_import.append(f'Performance Metric: {e}')


    # Update publication curation status
    current_publication.curation_status = 'C'
    current_publication.save()

    # Print import warnings 
    if len(import_warnings):
        print('>>>> Import warnings <<<<')
        print('- '+'\n- '.join(import_warnings))
        print('\n')

    # Remove entries if the import failed
    if len(failed_data_import):
        print('*************************')
        print('* ERROR: Import failed! *')
        print('*************************')
        print('- '+'\n- '.join(failed_data_import))
        for obj in data_obj:
            ids = data_ids[obj[0]]
            col_condition = obj[1] + '__in'
            print(f'DELETE {obj} : {ids}')
            obj[2].objects.filter(**{ col_condition: ids}).delete()
        print('\n')


    ## Scoring file ##
    # Read the PGS and re-format with header information
    if skip_scorefiles == False:
        for score_id, current_score in saved_scores.items():
            try:
                loc_scorefile = f'{studies_dir}/{study_name}/raw_scores/{score_id}.txt'
                #print('reading scorefile: {}', loc_scorefile)
                df_scoring = pd.read_table(loc_scorefile, dtype='str', engine = 'python')
                # Check that columns are in the schema
                column_check = [x in curation2schema_scoring.index for x in df_scoring.columns]
                if all(column_check):
                    header = create_scoringfileheader(current_score)

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

                    # Reorganize columns according to schema
                    corder = []
                    for x in curation2schema_scoring.index:
                        if x in df_scoring.columns:
                            corder.append(x)
                    df_scoring = df_scoring[corder]

                    with gzip.open('ScoringFiles/{}.txt.gz'.format(current_score.id), 'w') as outf:
                        outf.write('\n'.join(header).encode('utf-8'))
                        outf.write('\n'.encode('utf-8'))
                        outf.write(df_scoring.to_csv(sep='\t', index=False).encode('utf-8'))
                else:
                    badmaps = []
                    for i, v in enumerate(column_check):
                        if v == False:
                            badmaps.append(df_scoring.columns[i])
                    print('Error in {} ! bad columns: {}', loc_scorefile, badmaps)
            except:
                print('ERROR reading scorefile: {}', loc_scorefile)



def create_scoringfileheader(cscore):
    """Function to extract score & publication information for the PGS Catalog Scoring File commented header"""
    pub = cscore.publication
    lines = [
        '### PGS CATALOG SCORING FILE - see www.pgscatalog.org/downloads/#dl_ftp for additional information',
        '## POLYGENIC SCORE (PGS) INFORMATION',
        '# PGS ID = {}'.format(cscore.id),
        '# PGS Name = {}'.format(cscore.name),
        '# Reported Trait = {}'.format(cscore.trait_reported),
        '# Original Genome Build = {}'.format(cscore.variants_genomebuild),
        '# Number of Variants = {}'.format(cscore.variants_number),
        '## SOURCE INFORMATION',
        '# PGP ID = {}'.format(pub.id),
        '# Citation = {} et al. {} ({}). doi:{}'.format(pub.firstauthor, pub.journal, pub.date_publication.strftime('%Y'), pub.doi)
    ]
    if cscore.license != Score._meta.get_field('license')._get_default():
        ltext = cscore.license.replace('\n', ' ')     # Make sure there are no new-lines that would screw up the commenting
        lines.append('# LICENSE = {}'.format(ltext))  # Append to header
    return lines
