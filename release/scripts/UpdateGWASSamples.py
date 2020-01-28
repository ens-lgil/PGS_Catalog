import requests
from catalog.models import Sample

def get_gwas_info(gcst_id):
    """ Fetch the GWAS study datafrom a GCST ID, using the GWAS REST API """
    response = requests.get('https://www.ebi.ac.uk/gwas/rest/api/studies/%s'%gcst_id)
    response_json = response.json()
    if response_json:
        sample_number = 0
        ancestry_broad = ''
        ancestry_country = ''
        phenotyping_free = response_json['diseaseTrait']['trait']
        pmid = response_json['publicationInfo']['pubmedId']
        for ancestry in response_json['ancestries']:
            if ancestry['type'] != "initial":
                continue

            sample_number = ancestry['numberOfIndividuals']
            ancestry_broad_list = []
            for ancestral_group in ancestry['ancestralGroups']:
                ancestry_broad_list.append(ancestral_group['ancestralGroup'])
            ancestry_broad = ', '.join(ancestry_broad_list)

            ancestry_country_list = []
            for country in ancestry['countryOfRecruitment']:
                ancestry_country_list.append(country['countryName'])
            ancestry_country = ', '.join(ancestry_country_list)

        print("# "+gcst_id+": ")
        print("\tSamples: "+str(sample_number))
        print("\tAncestry_broad: "+ancestry_broad)
        print("\tAncestry_country: "+ancestry_country)
        print("\tPhenotyping_free: "+phenotyping_free)
        print("\tPmid: "+str(pmid))


def run():
    """ Update the EFO entries and add/update the Trait categories (from GWAS Catalog)."""
    for sample in Sample.objects.all():
        if sample.source_GWAS_catalog:
            get_gwas_info(sample.source_GWAS_catalog)
