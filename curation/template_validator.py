import os
import argparse

def main():
    script_desc = '''
    Validate and test PGS templates.
    Run it from the root of the repository and use a command like this:
    python curation/template_validator.py -f <path_to_template_file> --dir <path_to_root_dir_for_schema/template/gwas>
    '''

    dir_help = '''
    The root directory of the templates files and schema.
    For instance, the structure should be like:
    <dir>/templates/TemplateColumns2Models_v5.xlsx,
    <dir>/templates/ScoringFileSchema.xlsx,
    <dir>/local_GWASCatalog/
    '''

    argparser = argparse.ArgumentParser(description=script_desc)
    argparser.add_argument("-f", help='The path to the PGS template file to be validated - Excel spreadsheet (.xlsx)', required=True)
    argparser.add_argument("--dir", help=dir_help, required=True)

    args = argparser.parse_args()

    template_root_dir = args.dir
    if not template_root_dir.endswith('/'):
        template_root_dir += '/'

    # Check study root directory exists
    if not os.path.isdir(template_root_dir):
        print("Directory '"+template_root_dir+"' can't be found")
        exit(1)

    # Check study file exists
    study_file = args.f
    if not os.path.isfile(study_file):
        print("File '"+study_file+"' can't be found")
        exit(1)

    os.environ['pgs_study_file'] = study_file
    os.environ['pgs_template_dir'] = template_root_dir
    os.system('python manage.py test curation/tests/')


if __name__ == '__main__':
    main()
