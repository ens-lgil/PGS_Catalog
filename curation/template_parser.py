import pandas as pd
import re
import requests
#from psycopg2.extras import NumericRange
from catalog.models import *
from curation.parsers.cohort import CohortData
from curation.parsers.publication import PublicationData
from curation.parsers.score import ScoreData
from curation.parsers.sample import SampleData
from curation.parsers.performance import PerformanceData


class CurationTemplate():
    def __init__(self):
        self.file_loc = None
        self.parsed_publication = None
        self.parsed_scores = {}
        self.parsed_cohorts = {}
        self.parsed_samples_scores = []
        self.parsed_samples_testing = []
        self.parsed_performances = []
        self.table_mapschema = None
        self.spreadsheet_names = {}
        self.report = { 'error': {}, 'warning': {} }

    def get_spreadsheet_names(self):
        for s_name, s_content in self.table_mapschema.iterrows():
            # Fetch model
            s_model = s_content[1]
            if s_model not in self.spreadsheet_names:
                self.spreadsheet_names[s_model] = s_name


    def read_curation(self):
        '''ReadCuration takes as input the location of a study metadata file'''

        self.get_spreadsheet_names()

        loc_excel = self.file_loc
        if loc_excel != None:
            self.table_publication =  pd.read_excel(loc_excel, sheet_name=self.spreadsheet_names['Publication'], header=0, index_col=0)

            self.table_scores = pd.read_excel(loc_excel, sheet_name=self.spreadsheet_names['Score'], header=[0, 1], index_col=0)

            self.table_samples = pd.read_excel(loc_excel, sheet_name=self.spreadsheet_names['Sample'], header=0)
            
            # GWAS and Dev/Training Samples 
            self.table_samples_scores = self.table_samples[[x.startswith('Test') is False for x in self.table_samples.iloc[:, 1]]]
            # Index on columns "Score Name(s)" & "Study Stage"
            self.table_samples_scores.set_index(list(self.table_samples_scores.columns[[0, 1]]), inplace = True)
            
            # Testing (Evaluation) Samples 
            self.table_samples_testing = self.table_samples[[x.startswith('Test') for x in self.table_samples.iloc[:, 1]]]
            # Index on column "Sample Set ID"
            self.table_samples_testing.set_index(list(self.table_samples_testing.columns[[2]]), inplace=True)

            self.table_performances = pd.read_excel(loc_excel, sheet_name=self.spreadsheet_names['Performance'], header=[0,1], index_col=[0, 1])
            
            self.table_cohorts = pd.read_excel(loc_excel, sheet_name=self.spreadsheet_names['Cohort'], header=0, index_col=0)


    def extract_cohorts(self):
        spreadsheet_name = self.spreadsheet_names['Cohort']
        current_schema = self.table_mapschema.loc[spreadsheet_name].set_index('Column')
        for cohort_name, cohort_info in self.table_cohorts.iterrows():
            cohort_long_name = cohort_name
            for col, val in cohort_info.iteritems():
                if col in current_schema.index:
                    if pd.isnull(val) == False:
                        field = current_schema.loc[col, 'Field']
                        if field == 'name_full':
                            cohort_long_name = val
                            break
            parsed_cohort = CohortData(cohort_name,cohort_long_name)
            cohort_id = cohort_name.upper()
            if cohort_id in self.parsed_cohorts:
                self.report_warning(spreadsheet_name, f'Ambiguity found in the Cohort spreadsheet: the cohort ID "{cohort_name}" has been found more than once!')
            self.parsed_cohorts[cohort_id] = parsed_cohort


    def extract_publication(self):
        '''parse_pub takes a curation dictionary as input and extracts the relevant info from the sheet and EuropePMC'''
        pinfo = self.table_publication.iloc[0]
        c_doi = pinfo['doi']
        c_PMID = pinfo[0]
        publication = None

        # Check if this is already in the DB
        try:
            publication = Publication.objects.get(doi=c_doi)
            c_doi = publication.doi
            c_PMID = publication.PMID
            print("Publication found in the database")
        except Publication.DoesNotExist:
            print("New publication")

        parsed_publication = PublicationData(self.table_publication,c_doi,c_PMID,publication)
        
        if not publication:
            parsed_publication.get_publication_information()

        self.parsed_publication = parsed_publication


    def extract_scores(self):
        model = 'Score'
        spreadsheet_name = self.spreadsheet_names[model]
        current_schema = self.table_mapschema.loc[spreadsheet_name].set_index('Column')
        for score_name, score_info in self.table_scores.iterrows():
            parsed_score = ScoreData(score_name,self.parsed_publication.doi)
            for col, val in score_info.iteritems():
                if pd.isnull(val) is False:
                    # Map to schema
                    if col[1] in current_schema.index:
                        m, f = current_schema.loc[col[1]][:2]
                    elif col[0] in current_schema.index:
                        m, f = current_schema.loc[col[0]][:2]
                    else:
                        m = None

                    # Add to extract if it's the same model
                    if m == model:
                        if f == 'trait_efo':
                            efo_list = val.split(',')
                            parsed_score.add_data(f, efo_list)
                        else:
                            parsed_score.add_data(f, val)
            self.parsed_scores[score_name] = parsed_score


    def extract_samples(self):
        spreadsheet_name = self.spreadsheet_names['Sample']
        current_schema = self.table_mapschema.loc[spreadsheet_name].set_index('Column')

        # Extract data for training (GWAS + Score Development) sample
        for sample_id, sample_info in self.table_samples_scores.iterrows():
            sample_remapped = self.get_sample_data(sample_info,current_schema)

            # Parse from GWAS Catalog
            sample_keys = sample_remapped.data.keys()
            if 'sample_number' not in sample_keys:
                if 'source_GWAS_catalog' in sample_keys:
                    gwas_study = get_gwas_study(sample_remapped.data['source_GWAS_catalog'])
                    if gwas_study:
                        gwas_results = []
                        for gwas_ancestry in gwas_study:
                            c_sample = sample_remapped
                            for field, val in gwas_ancestry.items():
                                c_sample.add_data(field, val)
                            gwas_results.append(c_sample)
                        sample_remapped = gwas_results
                    else:
                        self.report_error(spreadsheet_name, f'Can\'t fetch the GWAS information for the study {sample_remapped["source_GWAS_catalog"]}')
                else:
                    self.report_error(spreadsheet_name, f'Missing GWAS Study ID (GCST ID) to fetch the sample information')
            if type(sample_remapped) != list:
                sample_remapped = [sample_remapped]
            self.parsed_samples_scores.append((sample_id, sample_remapped))

        # Extract data Testing samples
        for testset_name, testsets in self.table_samples_testing.groupby(level=0):
            results = []
            for sample_id, sample_info in testsets.iterrows():
                sample_remapped = self.get_sample_data(sample_info,current_schema)
                results.append(sample_remapped)
            self.parsed_samples_testing.append((testset_name, results))


    def extract_performances(self):
        spreadsheet_name = self.spreadsheet_names['Performance']
        current_schema = self.table_mapschema.loc[spreadsheet_name].set_index('Column')
        for p_key, performance_info in self.table_performances.iterrows():
            parsed_performance = PerformanceData(self.parsed_publication.doi)
            for col, val in performance_info.iteritems():
                if pd.isnull(val) == False:
                    m = None
                    if col[1] in current_schema.index:
                        m, f = current_schema.loc[col[1]][:2]
                    elif col[0] in current_schema.index:
                        m, f = current_schema.loc[col[0]][:2]

                    if m is not None:
                        if f.startswith('metric'):
                            try:
                                parsed_performance.add_metric(f, val)
                            except:
                                if ';' in str(val):
                                    for x in val.split(';'):
                                        parsed_performance.add_metric(f, x)
                                else:
                                    self.report_error(spreadsheet_name, f'Error parsing: {f} {val}')
                        else:
                            parsed_performance.add_data(f, val)
            self.parsed_performances.append((p_key,parsed_performance))


    def get_sample_data(self, sample_info, current_schema):
        ''' 
        Extract the sample data (gwas and dev/training)
        '''
        sample_remapped = SampleData()
        for c, val in sample_info.to_dict().items():
            if c in current_schema.index:
                if pd.isnull(val) == False:
                    f = current_schema.loc[c, 'Field']
                    if pd.isnull(f) == False:
                        if f == 'cohorts':
                            cohorts_list = []
                            for cohort in val.split(','):
                                cohort_id = cohort.upper()
                                if cohort_id in self.parsed_cohorts:
                                    cohorts_list.append(self.parsed_cohorts[cohort_id])
                                else:
                                    self.report_error(spreadsheet_name, f'Error: the sample cohort "{val}" cannot be found in the Cohort Refr. spreadsheet')
                            val = cohorts_list
                        elif f in ['sample_age', 'followup_time']:
                            val = sample_remapped.str2demographic(f, val)
                            
                        sample_remapped.add_data(f,val)
        return sample_remapped


    #=================================#
    #  Error/warning reports methods  #
    #=================================#

    def report_error(self, spreadsheet_name, msg):
        """
        Store the reported error.
        - spreadsheet_name: name of the spreadsheet (e.g. Publication Information)
        - msg: error message
        """
        if not spreadsheet_name in self.report['error']:
            self.report['error'][spreadsheet_name] = {}
        # Avoid duplicated message
        if not msg in self.report['error'][spreadsheet_name]:
            self.report['error'][spreadsheet_name][msg] = []
        # # Avoid duplicated line reports
        # if not row_id in self.report['error'][spreadsheet_name][msg]:
        #     self.report['error'][spreadsheet_name][msg].append(row_id)

    def report_warning(self, spreadsheet_name, msg):
        """
        Store the reported warning.
        - spreadsheet_name: name of the spreadsheet (e.g. Publication Information)
        - msg: warning message
        """
        if not spreadsheet_name in self.report['warning']:
            self.report['warning'][spreadsheet_name] = {}
        # Avoid duplicated message
        if not msg in self.report['warning'][spreadsheet_name]:
            self.report['warning'][spreadsheet_name][msg] = []




#=======================#
#  Independent methods  #
#=======================#

def get_gwas_study(gcst_id):
    """
    Get the GWAS Study information related to the PGS sample.
    Check that all the required data is available
    > Parameter:
        - gcst_id: GWAS Study ID (e.g. GCST010127)
    > Return: list of dictionnaries (1 per ancestry)
    """
    gwas_rest_url = 'https://www.ebi.ac.uk/gwas/rest/api/studies/'
    response = requests.get(f'{gwas_rest_url}{gcst_id}')
    response_data = response.json()
    study_data = []
    if response_data:
        try:
            source_PMID = response_data['publicationInfo']['pubmedId']
            for ancestry in response_data['ancestries']:

                if ancestry['type'] != 'initial':
                    continue

                ancestry_data = { 'source_PMID': source_PMID }
                ancestry_data['sample_number'] = ancestry['numberOfIndividuals']

                # ancestry_broad
                for ancestralGroup in ancestry['ancestralGroups']:
                    if not 'ancestry_broad' in ancestry_data:
                        ancestry_data['ancestry_broad'] = ''
                    else:
                        ancestry_data['ancestry_broad'] += ','
                    ancestry_data['ancestry_broad'] += ancestralGroup['ancestralGroup']
                # ancestry_free
                for countryOfOrigin in ancestry['countryOfOrigin']:
                    if countryOfOrigin['countryName'] != 'NR':
                        if not 'ancestry_free' in ancestry_data:
                            ancestry_data['ancestry_free'] = ''
                        else:
                            ancestry_data['ancestry_free'] += ','
                        ancestry_data['ancestry_free'] += countryOfOrigin['countryName']

                # ancestry_country
                for countryOfRecruitment in ancestry['countryOfRecruitment']:
                    if countryOfRecruitment['countryName'] != 'NR':
                        if not 'ancestry_country' in ancestry_data:
                            ancestry_data['ancestry_country'] = ''
                        else:
                            ancestry_data['ancestry_country'] += ','
                        ancestry_data['ancestry_country'] += countryOfRecruitment['countryName']
                # ancestry_additional
                # Not found in the REST API

                study_data.append(ancestry_data)
        except:
            print(f'Error: can\'t fetch GWAS results for {gcst_id}')
    return study_data


def next_PSS_num():
    r = SampleSet.objects.last()
    if r == None:
        return 1
    else:
        return r.num + 1
