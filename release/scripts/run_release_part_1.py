import sys, os.path
from release.scripts.CreateRelease import CreateRelease
from release.scripts.UpdateEFO import *
from release.scripts.UpdateGWASSamples import *
from catalog.models import *

def run():

    # Create release
    call_create_release()

    # Update EFO data
    call_efo_update()

    # Update/add GWAS data
    #call_gwas_update()


def call_create_release():
    """ Create release """

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

    # Scores
    scores_direct = Score.objects.filter(date_released__isnull=True)

    # Performances
    perfs_direct = Performance.objects.filter(date_released__isnull=True)

    print("Number of new Scores (direct fetch): "+str(scores_direct.count()))
    print("Number of new Performances (direct fetch): "+str(perfs_direct.count()))

    release.check_ftp()


def call_efo_update():
    """ Update the EFO entries and add/update the Trait categories (from GWAS Catalog)."""
    for trait in EFOTrait.objects.all():
        update_efo_info(trait)
        update_efo_category_info(trait)


def call_gwas_update():
    """ Update the GWAS study entries."""
    for sample in Sample.objects.all():
        if sample.source_GWAS_catalog:
            get_gwas_info(sample.source_GWAS_catalog)
