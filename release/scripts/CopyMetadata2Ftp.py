import sys, os, shutil, glob
import hashlib
import requests
import urllib
from catalog.models import *
from ftplib import FTP

# 1 - Get list of PGS scores + scoring files paths

# 2 - Compare scoring files
#     a) PGS directory doesn't exist
#       - Create required PGS directories
#       - Copy scoring file to FTP
#     b) PGS directory exist
#       - Compare md5 between new and current file.
#       - If different, create archive with the current file (use previous release date?)
#         and copy new file
#

# 3 - Compare metadata files (in a separate script ?)
#     a) Metadata files not on FTP
#       - Create metadata directories if needed
#       - Copy metadata files to FTP
#     b) Metadata files already on FTP
#       - Compare md5 between new and current file.
#       - If different, create archive with the current files (use previous release date?)
#         and copy new files

ftp_path = 'pub/databases/spot/pgs/scores/'
all_meta_file = 'pgs_all_metadata.txt.gz'

def get_ftp_score_md5(pgs_id):
    """ Check that all the PGSs have a corresponding Scoring file in the PGS FTP. """

    ftp = FTP('ftp.ebi.ac.uk')     # connect to host, default port
    ftp.login()                    # user anonymous, passwd anonymous@

    m = hashlib.md5()
    if pgs_id == all:
        ftp.retrbinary('RETR %s' % ftp_path+all_meta_file, m.update)
    else:
        ftp.retrbinary('RETR %s' % ftp_path+pgs_id+'/Metadata/'+pgs_id+'_metadata.txt.gz', m.update)

    return m.hexdigest()


def get_ftp_metadata_file(filename,new_filename):
    """ Download Scoring file from the PGS FTP. """

    if pgs_id == all:
        path = ftp_path
    else:
        path = ftp_path+pgs_id+'/Metadata/'

    ftp = FTP('ftp.ebi.ac.uk')     # connect to host, default port
    ftp.login()                    # user anonymous, passwd anonymous@
    ftp.cwd(path)
    ftp.retrbinary("RETR " + filename, open(new_filename, 'wb').write)
    ftp.quit()


def get_md5_checksum(filename, blocksize=4096):
    """ Returns MD5 checksum for the given file. """

    md5 = hashlib.md5()
    try:
        file = open(filename, 'rb')
        with file:
            for block in iter(lambda: file.read(blocksize), b""):
                md5.update(block)
    except IOError:
        print('File \'' + self.filename + '\' not found!')
        return None
    except:
        print("Error: the script couldn't generate a MD5 checksum for '" + self.filename + "'!")
        return None

    return md5.hexdigest()


def run():

    temp_ftp_dir    = '/Users/lg10/Workspace/datafiles/temp_ftp/'
    temp_scores_dir = '/Users/lg10/Workspace/datafiles/scores/'

    # Prepare the temporary FTP directory to copy/download all the PGS Scores
    if not os.path.isdir(temp_ftp_dir):
        try:
            os.mkdir(temp_ftp_dir,  0o755)
        except OSError:
            print ("Creation of the directory %s failed" % temp_ftp_dir)
            exit()

    releases = Release.objects.all().order_by('-date')
    previous_release = str(releases[1].date)

    # 1 - Get list of PGS scores + metadata files paths

    #for score in Score.objects.exclude(date_released__isnull=True):
    for score in Score.objects.all().order_by('num'):
        pgs_id = score.id
        meta_file = pgs_id+'_metadata.txt.gz'
        meta_file_xls = pgs_id+'_metadata.xslx'

        # For test only
        if pgs_id == "PGS000011":
            break

        # Build temporary FTP structure for the PGS Metadata
        pgs_main_dir = temp_ftp_dir+pgs_id
        meta_file_dir = pgs_main_dir+'/Metadata/'
        if not os.path.isdir(meta_file_dir):
            try:
                os.mkdir(pgs_main_dir, 0o755)
                os.mkdir(meta_file_dir, 0o755)
            except OSError:
                print ("Creation of the directory %s and/or %s failed" % (pgs_main_dir, meta_file_dir))
                exit()

        # 2 - Compare metadata files
        new_file_md5_checksum = get_md5_checksum(temp_scores_dir+meta_file)
        ftp_file_md5_checksum = get_ftp_metadata_md5(pgs_id)

        # 2 a) - New published Score (PGS directory doesn't exist)
        if not ftp_file_md5_checksum:
            shutil.copy2(temp_scores_dir+meta_file, meta_file_dir+meta_file)
            shutil.copy2(temp_scores_dir+meta_file_xls, meta_file_dir+meta_file_xls)
            for file in glob.glob(r+temp_scores_dir+'*.csv'):
                shutil.copy2(temp_scores_dir+file, meta_file_dir+file)

        # 2 b) - PGS directory exist (Updated Metadata)
        elif new_file_md5_checksum != ftp_file_md5_checksum:
            meta_archives = meta_file_dir+'archived_versions/'
            meta_archives_file = meta_archives+pgs_id+'_'+previous_release+'.txt.gz'
            meta_archives_file_xls = meta_archives+pgs_id+'_'+previous_release+'.xlsx'
            if not os.path.isdir(meta_archives):
                try:
                    os.mkdir(meta_archives, 0o755)
                except OSError:
                    print ("Creation of the directory %s failed" % meta_archives)
                    exit()

            # Need to get all the metadata files (zip only ?), rename and copy them to the archive
            get_ftp_metadata_file(meta_file, meta_archives_file)
            shutil.copy2(temp_scores_dir+meta_file, meta_file_dir+meta_file)
            get_ftp_metadata_file(meta_file_xls, meta_archives_file_xls)
            shutil.copy2(temp_scores_dir+meta_file_xls, meta_file_dir+meta_file_xls)
