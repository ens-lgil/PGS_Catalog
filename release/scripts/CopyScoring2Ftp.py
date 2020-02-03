import sys, os, shutil
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

ftp_path = 'pub/databases/spot/pgs/ScoringFiles_formatted/'
#ftp_path = 'pub/databases/spot/pgs/scores/'

def get_ftp_score_md5(pgs_id):
    """ Check that all the PGSs have a corresponding Scoring file in the PGS FTP. """

    ftp = FTP('ftp.ebi.ac.uk')     # connect to host, default port
    ftp.login()                    # user anonymous, passwd anonymous@

    m = hashlib.md5()
    ftp.retrbinary('RETR %s' % ftp_path+pgs_id+'.txt.gz', m.update)
    #ftp.retrbinary('RETR %s' % ftp_path+pgs_id+'/'+pgs_id+'.txt.gz', m.update)

    return m.hexdigest()


def get_ftp_score_file(pgs_id,new_filename):
    """ Download Scoring file from the PGS FTP. """

    path = ftp_path
    #path = 'pub/databases/spot/pgs/scores/'+pgs_id+'/'
    filename = pgs_id+'.txt.gz'

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

    # 1 - Get list of PGS scores + scoring files paths

    #for score in Score.objects.exclude(date_released__isnull=True):
    for score in Score.objects.all().order_by('num'):
        pgs_id = score.id
        score_file = pgs_id+'.txt.gz'

        # For test only
        if pgs_id == "PGS000011":
            break

        # Build temporary FTP structure for the PGS Score
        scoring_main_dir = temp_ftp_dir+pgs_id
        scoring_file_dir = scoring_main_dir+'/ScoringFiles/'
        if not os.path.isdir(scoring_file_dir):
            try:
                os.mkdir(temp_ftp_dir+pgs_id, 0o755)
                os.mkdir(scoring_file_dir, 0o755)
            except OSError:
                print ("Creation of the directory %s and/or %s failed" % (scoring_main_dir, scoring_file_dir))
                exit()

        # 2 - Compare scoring files
        new_file_md5_checksum = get_md5_checksum(temp_scores_dir+score_file)
        ftp_file_md5_checksum = get_ftp_score_md5(pgs_id)

        # 2 a) - New published Score (PGS directory doesn't exist)
        if not ftp_file_md5_checksum:
            shutil.copy2(temp_scores_dir+score_file, scoring_file_dir+score_file)
        # 2 b) - PGS directory exist (Updated Score)
        elif new_file_md5_checksum != ftp_file_md5_checksum:
            scoring_archives = scoring_file_dir+'archived_versions/'
            scoring_archives_file = scoring_archives+pgs_id+'_'+previous_release+'.txt.gz'
            if not os.path.isdir(scoring_archives):
                try:
                    os.mkdir(scoring_archives, 0o755)
                except OSError:
                    print ("Creation of the directory %s failed" % scoring_archives)
                    exit()

            get_ftp_score_file(pgs_id, scoring_archives_file)
            shutil.copy2(temp_scores_dir+score_file, scoring_file_dir+score_file)
