curation_directories = {
    'template_schema': './curation/templates/TemplateColumns2Models_v6a.xlsx',
    'scoring_schema': './curation/templates/ScoringFileSchema.xlsx',
    'studies_dir': '/Users/lg10/Workspace/datafiles/SourceFiles/test_DBSourceFiles_May142021/',
    'scoring_dir': '/Users/lg10/Workspace/datafiles/SourceFiles/ScoringFiles/'
}

study_names_list = [
    #{ 'name': 'Wang2020' },
    #{ 'name': 'Johnson2015' },
    { 'name': 'Darst2021' },
    { 'name': 'Dron2021' , 'license': 'Not the default license'},
    { 'name': 'Fahed2020_Penetrance' },
    #{ 'name': 'Fahed2020_Test' },
    { 'name': 'Tam2021_PreSub', 'status': 'E' }
]

default_curation_status = 'IP'

skip_scorefiles = False