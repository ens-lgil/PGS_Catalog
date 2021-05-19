# import gzip
# import pandas as pd
# import numpy as np
from curation.imports.curation import CurationImport
from curation.config import *
# from catalog.models import *


# class StudyImport():

#     data_obj = [
#         ('performance', 'num', Performance),
#         ('sampleset', 'num', SampleSet),
#         ('sample', 'id', Sample)
#     ]

#     data_ids = {
#         'performance': [],
#         'sampleset': [],
#         'sample': []
#     }

#     study_scores = {}
#     existing_scores = []

#     import_warnings = []
#     failed_data_import = []
#     has_failed = False

#     def __init__(self, study_data, studies_dir, steps_count, curation_schema):
#         self.study_name = study_data['name']

#         self.study_path = f'{studies_dir}/{self.study_name}'

#         self.study_license = None
#         if 'license' in study_data:
#             self.study_license = study_data['license']

#         self.study_status = None
#         if 'status' in study_data:
#             self.study_status = study_data['status']

#         self.steps_count = steps_count

#         self.curation_schema = curation_schema


#     def print_title(self):
#         # Print current study name
#         title = f'Study: {self.study_name}'
#         border = '===='
#         for i in range(len(title)):
#             border += '=' 
#         print(f'\n\n{border}\n# Study: {self.study_name} #\n{border}')
#         if self.study_status:
#             print(f'Curation status: {self.study_status}\n')


#     def parse_curation_data(self):
#         ## Parsing ##
#         print(f'==> Step 1/{self.steps_count}: Parsing study data')

#         self.study = CurationTemplate()
#         self.study.file_loc  = f'{self.study_path}/{self.study_name}.xlsx'
#         self.study.table_mapschema = self.curation_schema
#         self.study.read_curation()
#         # Extract data from the different spreadsheets
#         self.study.extract_cohorts()
#         self.study.extract_publication(self.study_status)
#         self.study.extract_scores(self.study_license)
#         self.study.extract_samples()
#         self.study.extract_performances()

    
#     def import_curation_data(self):
#         ## Import ##
#         print('\n----------------------------------\n')
#         print(f'==> Step 2/{self.steps_count}: Importing study data')

#         self.import_publication_model()
#         self.import_score_models()
#         self.import_gwas_dev_samples()
#         self.remove_existing_performance_metrics()
#         self.import_samplesets()
#         self.import_performance_metrics()

#         # Print import warnings 
#         if len(self.import_warnings):
#             print('\n>>>> Import information <<<<')
#             print('  - '+'\n  - '.join(self.import_warnings))

#         # Remove entries if the import failed
#         if len(self.failed_data_import):
#             self.has_failed = True
#             print('\n**** ERROR: Import failed! ****')
#             print('  - '+'\n  - '.join(self.failed_data_import))
#             for obj in self.data_obj:
#                 ids = self.data_ids[obj[0]]
#                 if len(ids):
#                     col_condition = obj[1] + '__in'
#                     obj[2].objects.filter(**{ col_condition: ids}).delete()
#                     print(f'  > DELETED {obj[0]} (column "{obj[1]}") : {ids}')
#             return False
#         return True


#     def import_publication_model(self):#, publication_model=Publication):
#         if self.study.parsed_publication.model:
#             self.study_publication = self.study.parsed_publication.model
#         else:
#             try:
#                 self.study_publication = Publication.objects.get(**self.study.parsed_publication.data)
#             except Publication.DoesNotExist:
#                 self.study_publication = self.study.parsed_publication.create_publication_model()
#                 # Set publication curation status
#                 if not self.study_status:
#                     self.study_publication.curation_status = default_curation_status
#                     self.study_publication.save()


#     def import_score_models(self, current_publication):#, score_model=Score):
#         for score_id, score_data in self.study.parsed_scores.items():
#             # Check if score already exist
#             try:
#                 current_score = Score.objects.get(name=score_data.data['name'],publication__id=self.study_publication.id)
#                 self.import_warnings.append(f'Existing Score: {current_score.id} ({score_id})')
#                 self.existing_scores.append(current_score.id)
#             except Score.DoesNotExist:
#                 current_score = score_data.create_score_model(self.study_publication)
#                 self.import_warnings.append(f'New Score: {current_score.id} ({score_id})')
#             self.study_scores[score_id] = current_score


#     def import_gwas_dev_samples(self):
#         ''' Sample - GWAS and Dev/Training Samples and attach them the associated Scores '''
#         try:
#             for x in self.study.parsed_samples_scores:
#                 scores = []
#                 for s in x[0][0].split(','):
#                     if s.strip() in self.study_scores:
#                         scores.append(self.study_scores[s.strip()])
#                     else:
#                         self.import_warnings.append(f'{s.strip()} is not found in the saved scores list!!!')
#                 samples = x[1]
#                 for current_score in scores:
#                     for sample in samples:
#                         sample_model_exist = False
#                         if current_score.id in self.existing_scores:
#                             sample_model_exist = sample.sample_model_exist()
#                         if not sample_model_exist:
#                             current_sample = sample.create_sample_model()
#                             #self.data_ids['sample'].append(current_sample.id)
#                             if x[0][1] == 'GWAS/Variant associations':
#                                 current_score.samples_variants.add(current_sample)
#                             elif x[0][1] == 'Score development':
#                                 current_score.samples_training.add(current_sample)
#                             else:
#                                 self.import_warnings.append('ERROR: Unclear how to add samples')
#                         else:
#                             self.import_warnings.append(f'Sample "{x[0][0]}" ({x[0][1]}) already exist in the Database')
#         except Exception as e:
#             self.failed_data_import.append(f'GWAS & Dev/Testing Sample: {e}')


#     def remove_existing_performance_metrics(self):
#         # Check if the Performance Metrics already exist in the DB
#         # If they exist, we delete them (including the associated SampleSet and Samples)
#         try:
#             data2delete = {'performance': set(), 'sampleset': set(), 'sample': set()}
#             for x in self.study.parsed_performances:
#                 i, performance = x
#                 # Find Score from the Score spreadsheet
#                 if i[0] in self.study_scores:
#                     current_score = self.study_scores[i[0]]
#                 # Find existing Score in the database (e.g. PGS000001)
#                 else:
#                     try:
#                         current_score = Score.objects.get(id__iexact=i[0])
#                     except Score.DoesNotExist:
#                         self.failed_data_import.append(f'Performance Metric: can\'t find the Score {i[0]} in the database')
#                         continue
#                 performances = Performance.objects.filter(publication=self.study_publication, score=current_score)
                
#                 for performance in performances:
#                     sampleset = performance.sampleset
#                     samples = sampleset.samples.all()
#                     # Store the objects to delete
#                     data2delete['performance'].add(performance)
#                     data2delete['sampleset'].add(sampleset)
#                     for sample in samples:
#                         data2delete['sample'].add(sample)
#             # Delete stored objects
#             for data_type in ('performance','sampleset','sample'):
#                 data_list = list(data2delete[data_type])
#                 self.import_warnings.append(f'DELETE existing {data_type}(s) [ids]: {", ".join([str(x.id) for x in data_list])}')
#                 for entry in data_list:
#                     entry.delete()

#         except Exception as e:
#             self.failed_data_import.append(f'Check existing Performance Metric: {e}')


#     def import_samplesets(self):
#          # Test (Evaluation) Samples and Sample Sets
#         self.study_samplesets = {}
#         try:
#             for x in self.study.parsed_samples_testing:
#                 test_name, sample_list = x

#                 samples_for_sampleset = []

#                 # Create samples
#                 for sample_test in sample_list:
#                     sample_model = sample_test.create_sample_model()
#                     self.data_ids['sample'].append(sample_model.id)
#                     samples_for_sampleset.append(sample_model)
                    
#                 # Initialize the current SampleSet
#                 sampleset_model = SampleSet()
#                 sampleset_model.set_ids(next_PSS_num())
#                 sampleset_model.save()
#                 self.data_ids['sampleset'].append(sampleset_model.num)

#                 # Add sample(s) to the SampleSet
#                 for sample in samples_for_sampleset:
#                     sampleset_model.samples.add(sample_model)
#                     sampleset_model.save()

#                 self.study_samplesets[test_name] = sampleset_model
#         except Exception as e:
#             self.failed_data_import.append(f'SampleSet & Evaluation Sample: {e}')


#     def import_performance_metrics(self):
#         ## Performance Metrics ##
#         try:
#             for x in self.study.parsed_performances:
#                 i, performance = x
#                 # Find Score from the Score spreadsheet
#                 if i[0] in self.study_scores:
#                     current_score = self.study_scores[i[0]]
#                 # Find existing Score in the database (e.g. PGS000001)
#                 else:
#                     try:
#                         current_score = Score.objects.get(id__iexact=i[0])
#                     except Score.DoesNotExist:
#                         self.failed_data_import.append(f'Performance Metric: can\'t find the Score {i[0]} in the database')
#                         continue

#                 related_SampleSet = self.study_samplesets[i[1]]

#                 study_performance = performance.create_performance_model(publication=self.study_publication, score=current_score, sampleset=related_SampleSet)
#                 self.import_warnings.append(f'New Performance Metric: {study_performance.id} & new Sample Set: {study_performance.sampleset.id}')

#                 self.data_ids['performance'].append(study_performance.num)
#         except Exception as e:
#             self.failed_data_import.append(f'Performance Metric: {e}')



# class ScoringFileUpdate():

#     def __init__(self, score, study_path, new_scoring_dir, score_file_schema):
#         self.score = score
#         self.score_file_path = f'{study_path}/raw_scores'
#         self.new_score_file_path = new_scoring_dir
#         self.score_file_schema = score_file_schema



#     def create_scoringfileheader(cscore):
#         '''Function to extract score & publication information for the PGS Catalog Scoring File commented header'''

#         pub = cscore.publication
#         lines = [
#             '### PGS CATALOG SCORING FILE - see www.pgscatalog.org/downloads/#dl_ftp for additional information',
#             '## POLYGENIC SCORE (PGS) INFORMATION',
#             f'# PGS ID = {cscore.id}',
#             f'# PGS Name = {cscore.name}',
#             f'# Reported Trait = {cscore.trait_reported}',
#             f'# Original Genome Build = {cscore.variants_genomebuild}',
#             f'# Number of Variants = {cscore.variants_number}',
#             '## SOURCE INFORMATION',
#             f'# PGP ID = {pub.id}',
#             f'# Citation = {pub.firstauthor} et al. {pub.journal} ({pub.pub_year}). doi:{pub.doi}'
#         ]

#         try:
#             if cscore.license != Score._meta.get_field('license')._get_default():
#                 ltext = cscore.license.replace('\n', ' ')     # Make sure there are no new-lines that would screw up the commenting
#                 lines.append('# LICENSE = {}'.format(ltext))  # Append to header
#         except Exception as e:
#             print(f'Exception: {e}')
#         return lines


#     def update_scoring_file(self):
#         failed_update = False
#         try:
#             score_id = self.score.id
#             loc_scorefile = f'{self.score_file_path}/{score_id}.txt'
#             df_scoring = pd.read_table(loc_scorefile, dtype='str', engine = 'python')
#             column_check = True
#             for x in df_scoring.columns:
#                 if not x in self.score_file_schema.index:
#                     column_check = False
#                     print(f'{x} not in index')
#                     break
#             # Check that columns are in the schema
#             #column_check = [x in curation2schema_scoring.index for x in df_scoring.columns]
#             #if all(column_check):
#             if column_check == True:
#                 # Get new header
#                 header = self.create_scoringfileheader(self.score)

#                 #Check if weight_type in columns
#                 if 'weight_type' in df_scoring.columns:
#                     if all(df_scoring['weight_type']):
#                         val = df_scoring['weight_type'][0]
#                         if val == 'OR':
#                             df_scoring = df_scoring.rename({'effect_weight' : 'OR'}, axis='columns').drop(['weight_type'], axis=1)
#                 if 'effect_weight' not in df_scoring.columns:
#                     if 'OR' in df_scoring.columns:
#                         df_scoring['effect_weight'] = np.log(pd.to_numeric(df_scoring['OR']))
#                         df_scoring['weight_type'] = 'log(OR)'
#                     elif 'HR' in df_scoring.columns:
#                         df_scoring['effect_weight'] = np.log(pd.to_numeric(df_scoring['HR']))
#                         df_scoring['weight_type'] = 'log(HR)'

#                 # Reorganize columns according to schema
#                 corder = []
#                 for x in self.score_file_schema.index:
#                     if x in df_scoring.columns:
#                         corder.append(x)

#                 df_scoring = df_scoring[corder]
#                 with gzip.open(f'{self.new_score_file_path}/{score_id}.txt.gz', 'w') as outf:
#                     outf.write('\n'.join(header).encode('utf-8'))
#                     outf.write('\n'.encode('utf-8'))
#                     outf.write(df_scoring.to_csv(sep='\t', index=False).encode('utf-8'))

#             else:
#                 badmaps = []
#                 for i, v in enumerate(column_check):
#                     if v == False:
#                         badmaps.append(df_scoring.columns[i])
#                 #failed_studies[study_name] = 'scoring file error'
#                 failed_update = True
#                 print(f'ERROR in {loc_scorefile} ! bad columns: {badmaps}')
#         except:
#             #failed_studies[study_name] = 'scoring file error'
#             failed_update = True
#             print(f'ERROR reading scorefile: {loc_scorefile}')
#         return failed_update



# class CurationImport():

#     failed_studies = {}

#     def __init__(self, data_path, studies_list, skip_scoringfiles):
#         self.curation2schema = pd.read_excel(data_path['template_schema'], index_col=0)
#         self.curation2schema_scoring = pd.read_excel(data_path['scoring_schema'], index_col=0)
#         self.studies_list = studies_list
#         self.studies_path = data_path['studies_dir']
#         self.new_scoring_path = data_path['scoring_dir']

#         self.steps_count = 2
#         if skip_scoringfiles == False:
#             self.steps_count = 3 


#     def global_report(self):
#         ''' Global reports of the studies import '''
#         studies_count = len(self.study_names_list)
#         import_success = studies_count - len(self.failed_studies.keys())
#         print('\n=======================================================\n')
#         print('#------------------------#')
#         print('# End of script - Report #')
#         print('#------------------------#')
#         print(f'Successful imports: {import_success}/{studies_count}')
#         if self.failed_studies:
#             print(f'Failed imports:')
#             for study,error_type in self.failed_studies.items():
#                 print(f'- {study}: {error_type}')
#         print('\n')


#     def run_curation_import(self):
#         for study_data in self.studies_list:
#             # Metadata import
#             study_import = StudyImport(study_data,self.steps_count,self.curation2schema,self.studies_path)
#             study_import.print_title()
#             study_import.parse_curation_data()
#             study_import.import_curation_data()

#             if study_import.has_failed:
#                 self.failed_studies[study_import.study_name] = 'import error'
#             else:
#                 # Scoring files
#                 if self.skip_scoringfiles == False:
#                     print('\n----------------------------------\n')
#                     print(f'==> Step 3/{self.steps_count}: Add header to the Scoring file(s)')
#                     for score_id, score in study_import.study_scores.items():
#                         scoring_file_update = ScoringFileUpdate(score,study_import.study_path,self.new_scoring_path,self.curation2schema_scoring)
#                         is_failed = scoring_file_update.update_scoring_file()
#                         if is_failed == True:
#                             self.failed_studies[study_import.study_name] = 'scoring file error'
#         self.global_report()



# Main script
#def main():
curation_import = CurationImport(curation_directories, study_names_list, default_curation_status, skip_scorefiles)
curation_import.run_curation_import()
