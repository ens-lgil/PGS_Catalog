import pandas as pd
from curation.imports.study import StudyImport
from curation.imports.scoring_file import ScoringFileUpdate


class CurationImport():

    failed_studies = {}

    def __init__(self, data_path, studies_list, curation_status_by_default, skip_scoringfiles):
        self.curation2schema = pd.read_excel(data_path['template_schema'], index_col=0)
        self.curation2schema_scoring = pd.read_excel(data_path['scoring_schema'], index_col=0)

        self.studies_list = studies_list
        self.studies_path = data_path['studies_dir']
        self.new_scoring_path = data_path['scoring_dir']
        self.skip_scoringfiles = skip_scoringfiles

        self.curation_status_by_default = curation_status_by_default

        self.steps_count = 2
        if self.skip_scoringfiles == False:
            self.steps_count = 3 


    def global_report(self):
        ''' Global reports of the studies import '''
        studies_count = len(self.studies_list)
        import_success = studies_count - len(self.failed_studies.keys())
        print('\n=======================================================\n')
        print('#------------------------#')
        print('# End of script - Report #')
        print('#------------------------#')
        print(f'Successful imports: {import_success}/{studies_count}')
        if self.failed_studies:
            print(f'Failed imports:')
            for study,error_type in self.failed_studies.items():
                print(f'- {study}: {error_type}')
        print('\n')


    def run_curation_import(self):
        for study_data in self.studies_list:
            # Metadata import
            study_import = StudyImport(study_data, self.studies_path, self.curation2schema, self.curation_status_by_default)
            study_import.print_title()

            print(f'Content: {"|".join(study_import.import_warnings)}')

            ## Parsing ##
            print(f'==> Step 1/{self.steps_count}: Parsing study data')
            study_import.parse_curation_data()

            ## Import ##
            print('\n----------------------------------\n')
            print(f'==> Step 2/{self.steps_count}: Importing study data')
            study_import.import_curation_data()

            if study_import.has_failed:
                self.failed_studies[study_import.study_name] = 'import error'
            else:
                # Scoring files
                if self.skip_scoringfiles == False:

                    print('\n----------------------------------\n')
                    print(f'==> Step 3/{self.steps_count}: Add header to the Scoring file(s)')
                    if study_import.study_scores:
                        for score_id, score in study_import.study_scores.items():
                            scoring_file_update = ScoringFileUpdate(score,study_import.study_path,self.new_scoring_path,self.curation2schema_scoring)
                            is_failed = scoring_file_update.update_scoring_file()
                            if is_failed == True:
                                self.failed_studies[study_import.study_name] = 'scoring file error'
                    else:
                        print("  > No scores for this study")
        self.global_report()
