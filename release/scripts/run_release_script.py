import sys, os.path, shutil, glob
from datetime import date
import tarfile
from catalog.models import *
from release.scripts.CreateRelease import CreateRelease
from release.scripts.UpdateEFO import UpdateEFO
from release.scripts.GenerateBulkExport import PGSExportAllMetadata
from release.scripts.PGSExport import PGSExport
from release.scripts.PGSBuildFtp import PGSBuildFtp


def run(*args):
    """
        Main method executed by the Django command:
        `python manage.py runscript run_release_script`
    """
    if (len(args) == 0):
        print("ERROR: missing argument providing the path to the export directory")
        print("Please use the command line with: --script-args <path_to_the_export_directory>")
        exit()

    today = date.today()

    previous_release_date = get_previous_release_date()

    #--------------#
    #  DB release  #
    #--------------#
    print("# Start the database release")

    # Check that the publications are associated to at least a Score or a Performance Metric
    #check_publications_associations()

    # Check that the EFO Traits are associated to at least a Score or a Performance Metric
    #check_efotrait_associations()

    # Create release
    #call_create_release()

    # Update EFO data
    #call_efo_update()

    #---------------#
    #  FTP release  #
    #---------------#

    print("# Start the FTP release")

    debug = 0
    scores_db = Score.objects.all().order_by('num')
    new_ftp_dir = '{}/../new_ftp_content/'.format(args[0])
    create_pgs_directory(new_ftp_dir)

    archive_file_name = '{}/../pgs_ftp_{}.tar.gz'.format(args[0],today)
    scores_list_file = new_ftp_dir+'/pgs_scores_list.txt'

    # Generate file listing all the released Scores
    generate_scores_list_file(scores_list_file)

    # Generate all PGS metadata export files
    #call_generate_all_metadata_exports(args[0])

    # Generate PGS metadata export files for each released studies
    #call_generate_studies_metadata_exports(args[0],scores_db,debug)

    # Build FTP structure for metadata files
    #build_metadata_ftp(args[0],new_ftp_dir,scores_db,previous_release_date,debug)

    # Check that the new entries have a PGS directory
    check_new_data_entry_in_metadata(new_ftp_dir,today)

    # Build FTP structure for the bulk metadata files
    #build_bulk_metadata_ftp(args[0],new_ftp_dir,previous_release_date,debug)

    # Generates the compressed archive to be copied to the EBI Private FTP
    #tardir(new_ftp_dir, archive_file_name)




#-----------#
#  Methods  #
#-----------#

#####  DB methods  #####

def check_publications_associations():
    """ Check the publications associations """
    print("\t- Check the publications associations")

    publications = Publication.objects.all().order_by('num')
    pub_list = []

    for publication in publications:
        pub_id = publication.id
        is_associated = 0
        if Score.objects.filter(publication=publication):
            is_associated = 1
        elif Performance.objects.filter(publication=publication):
            is_associated = 1
        if not is_associated:
            pub_list.append(pub_id)

    if len(pub_list) > 0:
        print("ERROR: The following PGS publications are not associated to a Score or a Performance Metric:\n"+'\n'.join(pub_list))
        exit(1)
    else:
        print("Publications associations - OK: All the publications are associated to a Score or a Performance Metric!")


def check_efotrait_associations():
    """ Check the EFO Trait associations """
    print("\t- Check the EFO Trait associations")

    efo_traits = EFOTrait.objects.all().order_by('id')
    traits_list = []

    for efo_trait in efo_traits:
        trait_id = efo_trait.id
        is_associated = 0
        if Score.objects.filter(trait_efo__in=[efo_trait]):
            is_associated = 1
        elif Performance.objects.filter(phenotyping_efo__in=[efo_trait]):
            is_associated = 1
        if not is_associated:
            traits_list.append(trait_id)

    if len(traits_list) > 0:
        print("ERROR: The following PGS EFO Traits are not associated to a Score or a Performance Metric:\n"+'\n'.join(traits_list))
        exit(1)
    else:
        print("EFOTrait associations - OK: All the traits are associated to a Score or a Performance Metric!")


def call_create_release():
    """ Create a new PGS Catalog release """
    print("\t- Create a new PGS Catalog release")

    lastest_release = Release.objects.latest('date').date

    release = CreateRelease()
    release.update_data_to_release()
    new_release = release.create_new_release()

    # Just a bunch of prints
    print("Latest release: "+str(lastest_release))
    print("New release: "+str(new_release.date))
    print("Number of new Scores: "+str(new_release.score_count))
    print(', '.join(release.new_scores.keys()))
    print("Number of new Publications: "+str(new_release.publication_count))
    print("Number of new Performances: "+str(new_release.performance_count))

    if new_release.score_count == 0 or new_release.publication_count == 0 or new_release.performance_count == 0:
        print("Error: at least one of the main components (Score, Publication or Performance Metrics) hasn't a new entry this release")
        exit(1)


def call_efo_update():
    """ Update the EFO entries and add/update the Trait categories (from GWAS Catalog)."""
    print("\t- Update the EFO entries and add/update the Trait categories (from GWAS Catalog)")
    efo_update = UpdateEFO()
    efo_update.launch_efo_updates()


#####  FTP methods  #####

def generate_scores_list_file(scores_file):
    """ Generate file listing all the released Scores """
    print("\t- Generate file listing all the released Scores")
    released_scores = Score.objects.filter(date_released__isnull=False).order_by('num')
    file = open(scores_file, 'w')
    for score in released_scores:
        file.write(score.id+'\n')
    file.close()


def call_generate_all_metadata_exports(dirpath):
    """ Generate all PGS metadata export files """
    print("\t- Generate all PGS metadata export files")

    datadir = dirpath+"all_metadata/"
    filename = datadir+'pgs_all_metadata.xlsx'

    csv_prefix = datadir+'pgs_all'

    if not os.path.isdir(datadir):
        try:
            os.mkdir(datadir)
        except OSError:
            print ("Creation of the directory %s failed" % datadir)

    if not os.path.isdir(datadir):
        print("Can't create a directory for the metadata ("+datadir+")")
        exit(1)

    # Create export object
    pgs_export = PGSExportAllMetadata(filename)

    # Info/readme spreadsheet
    pgs_export.create_readme_spreadsheet()

    # Build the spreadsheets
    pgs_export.generate_sheets(csv_prefix)

    # Close the Pandas Excel writer and output the Excel file.
    pgs_export.save()

    # Create a md5 checksum for the spreadsheet
    pgs_export.create_md5_checksum()

    # Generate a tar file of the study data
    pgs_export.generate_tarfile(dirpath+"pgs_all_metadata.tar.gz",datadir)


def call_generate_studies_metadata_exports(dirpath,scores,debug):
    """ Generate PGS metadata export files for each released studies """
    print("\t- Generate PGS metadata export files for each released studies")

    if debug:
        pgs_ids_list = []
        for i in range(1,debug+1):
            num = i < 10 and '0'+str(i) or str(i)
            pgs_ids_list.append('PGS0000'+num)
    else:
        pgs_ids_list = [  x.id for x in scores ]

    for pgs_id in pgs_ids_list:

        print("\n# PGS "+pgs_id)

        pgs_dir = dirpath+pgs_id
        study_dir = pgs_dir+"/Metadata/"
        csv_prefix = study_dir+pgs_id

        # Check / create PGS directory
        if not os.path.isdir(pgs_dir):
            try:
                os.mkdir(pgs_dir)
            except OSError:
                print ("Creation of the directory %s failed" % pgs_dir)

        # Check / create PGS metadata directory
        if os.path.isdir(pgs_dir) and not os.path.isdir(study_dir):
            try:
                os.mkdir(study_dir)
            except OSError:
                print ("Creation of the directory %s failed" % study_dir)

        if not os.path.isdir(study_dir):
            print("Can't create a directory for the study "+pgs_id)
            break

        filename = study_dir+pgs_id+"_metadata.xlsx"

        # Create export object
        pgs_export = PGSExport(filename)
        pgs_export.set_pgs_list([pgs_id])

        # Build the spreadsheets
        pgs_export.generate_sheets(csv_prefix)

        # Close the Pandas Excel writer and output the Excel file.
        pgs_export.save()

        # Generate a tar file of the study data
        pgs_export.generate_tarfile(dirpath+pgs_id+"_metadata.tar.gz",study_dir)


def build_metadata_ftp(dirpath,dirpath_new,scores,previous_release,debug):
    """ Generates PGS specific metadata files (PGS by PGS) """
    print("\t- Generates PGS specific metadata files (PGS by PGS)")
    temp_data_dir = dirpath
    temp_ftp_dir  = dirpath_new+'/scores/'

    # Prepare the temporary FTP directory to copy/download all the PGS Scores
    create_pgs_directory(dirpath_new)
    create_pgs_directory(temp_ftp_dir)

    # Create temporary archive directory
    tmp_archive = dirpath+'/pgs_archives/'
    if os.path.isdir(tmp_archive):
        shutil.rmtree(tmp_archive,ignore_errors=True)
    create_pgs_directory(tmp_archive)

    # 1 - Add metadata for each PGS Score
    for score in scores:
        pgs_id = score.id

        # For test only
        if debug and score.num == debug:
            break

        file_suffix = '_metadata.xlsx'
        pgs_ftp = PGSBuildFtp(pgs_id, file_suffix, 'metadata')

        meta_file_tar = pgs_id+'_metadata'+pgs_ftp.meta_file_extension
        meta_file_xls = pgs_id+file_suffix

        # Build temporary FTP structure for the PGS Metadata
        pgs_main_dir = temp_ftp_dir+pgs_id
        create_pgs_directory(pgs_main_dir)
        meta_file_dir = pgs_main_dir+'/Metadata/'
        create_pgs_directory(meta_file_dir)

        temp_meta_dir = temp_data_dir+"/"+pgs_ftp.pgs_id+"/Metadata/"

        # 2 - Compare metadata files
        new_file_md5_checksum = pgs_ftp.get_md5_checksum(temp_meta_dir+meta_file_xls)
        ftp_file_md5_checksum = pgs_ftp.get_ftp_data_md5()

        # 2 a) - New published Score (PGS directory doesn't exist)
        if not ftp_file_md5_checksum:
            # Copy new files
            shutil.copy2(temp_meta_dir+meta_file_xls, meta_file_dir+meta_file_xls)
            shutil.copy2(temp_data_dir+meta_file_tar, meta_file_dir+meta_file_tar)
            for file in glob.glob(temp_meta_dir+'*.csv'):
                csv_filepath = file.split('/')
                filename = csv_filepath[-1]
                shutil.copy2(file, meta_file_dir+filename)

        # 2 b) - PGS directory exist (Updated Metadata)
        elif new_file_md5_checksum != ftp_file_md5_checksum:
            # Fetch and Copy tar file from FTP
            meta_archives_path = tmp_archive+pgs_id+'_metadata'
            meta_archives_file_tar = pgs_id+'_metadata_'+previous_release+pgs_ftp.meta_file_extension
            meta_archives_file = tmp_archive+'/'+meta_archives_file_tar
            # Fetch and Copy tar file to the archive
            pgs_ftp.get_ftp_file(meta_file_tar,meta_archives_file)

            if meta_archives_file.endswith(pgs_ftp.meta_file_extension):
                tar = tarfile.open(meta_archives_file, 'r')
                tar.extractall(meta_archives_path)
                tar.close()
            else:
                print("Error: can't extract the file '"+meta_archives_file+"'!")
                exit(1)

            # Copy CSV files and compare them with the FTP ones
            has_difference = False
            for csv_file in glob.glob(temp_meta_dir+'*.csv'):
                csv_filepath = csv_file.split('/')
                filename = csv_filepath[-1]
                # Copy CSV file to the metadata directory
                shutil.copy2(csv_file, meta_file_dir+filename)

                # Compare CSV files
                ftp_csv_file = meta_archives_path+'/'+filename
                if os.path.exists(ftp_csv_file):
                    new_csv = pgs_ftp.get_md5_checksum(csv_file)
                    ftp_csv = pgs_ftp.get_md5_checksum(ftp_csv_file)
                    if new_csv != ftp_csv:
                        has_difference = True
                else:
                    has_difference = True

            # Copy other new files
            shutil.copy2(temp_meta_dir+meta_file_xls, meta_file_dir+meta_file_xls)
            shutil.copy2(temp_data_dir+meta_file_tar, meta_file_dir+meta_file_tar)

            # Archive metadata from previous release
            if has_difference:
                meta_archives = meta_file_dir+'archived_versions/'
                create_pgs_directory(meta_archives)
                # Copy tar file to the archive
                shutil.copy2(meta_archives_file, meta_archives+meta_archives_file_tar)


def build_bulk_metadata_ftp(dirpath,dirpath_new,previous_release,debug):
    """ Generates the global metadata files (the ones containing all the PGS metadata) """
    print("\t- Generates the global metadata files (the ones containing all the PGS metadata)")

    temp_data_dir = dirpath
    temp_ftp_dir = dirpath_new+'/metadata/'

    # Prepare the temporary FTP directory to copy/download all the PGS Scores
    create_pgs_directory(dirpath_new)
    create_pgs_directory(temp_ftp_dir)

    pgs_ftp = PGSBuildFtp('all', '', 'metadata')

    meta_file = pgs_ftp.all_meta_file
    meta_file_xls = meta_file.replace('.tar.gz', '.xlsx')

    # Copy new metadata
    shutil.copy2(temp_data_dir+meta_file, temp_ftp_dir+meta_file)
    shutil.copy2(temp_data_dir+'all_metadata/'+meta_file_xls, temp_ftp_dir+meta_file_xls)

    for file in glob.glob(temp_data_dir+'all_metadata/*.csv'):
        csv_filepath = file.split('/')
        filename = csv_filepath[-1]
        shutil.copy2(file, temp_ftp_dir+filename)

    # Archiving metadata from previous release
    meta_archives_file = meta_file.replace('.tar.gz', '_'+previous_release+'.tar.gz')

    meta_archives_dir = temp_ftp_dir+'previous_releases/'
    create_pgs_directory(meta_archives_dir)

    previous_release_date = previous_release.split('-')
    meta_year_archives_dir = meta_archives_dir+previous_release_date[0]+'/'
    create_pgs_directory(meta_year_archives_dir)

    pgs_ftp.get_ftp_file(meta_file,meta_year_archives_dir+meta_archives_file)


def get_previous_release_date():
    """ Fetch the previous release date (i.e. the release date of the current live database) """
    releases = Release.objects.all().order_by('-date')
    return str(releases[1].date)


def check_new_data_entry_in_metadata(dirpath_new,release_date):
    """ Check that the metadata directory for the new Scores and Performance Metrics exists """
    scores_dir = dirpath_new+'/scores/'

    # Score(s)
    missing_score_dir = set()
    for score in Score.objects.filter(date_released=release_date).order_by('num'):
        score_id = score.id
        if not os.path.isdir(scores_dir+score_id):
            missing_score_dir.add(score_dir)
    # Performance Metric(s)
    missing_perf_dir = set()
    for perf in Performance.objects.select_related('score').filter(date_released=release_date).order_by('score__id'):
        score_id = perf.score.id
        if not os.path.isdir(scores_dir+score_id):
            missing_perf_dir.add(score_dir)

    if len(missing_score_dir) != 0 or len(missing_perf_dir) != 0:
        if len(missing_score_dir) != 0:
            print("/!\ Missing PGS directories for the new entry(ies):\n - "+'\n - '.join(list(missing_score_dir)))
        if len(missing_perf_dir) != 0:
            print("/!\ Missing PGS directories for the new associated Performance Metric entry(ies):\n - "+'\n - '.join(list(missing_perf_dir)))
        exit(1)
    else:
        print("OK - No missing PGS directory for the new  entry(ies)")



def create_pgs_directory(path):
    """ Creates directory for a given PGS """
    if not os.path.isdir(path):
        try:
            os.mkdir(path, 0o755)
        except OSError:
            print ("Creation of the directory %s failed" % path)
            exit()


def tardir(path, tar_name):
    """ Generates a tarball of the new PGS FTP metadata files """
    with tarfile.open(tar_name, "w:gz") as tar_handle:
        for root, dirs, files in os.walk(path):
            for file in files:
                tar_handle.add(os.path.join(root, file))
