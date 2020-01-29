import requests
from catalog.models import Sample

def get_gwas_info(gcst_id):
    """ Fetch the GWAS study datafrom a GCST ID, using the GWAS REST API """
    response = requests.get('https://www.ebi.ac.uk/gwas/rest/api/studies/%s'%gcst_id)
    response_json = response.json()
    if response_json:
        print("# "+gcst_id+": ")
        pmid = response_json['publicationInfo']['pubmedId']

        #Parse a new row of the Samples table for each model
        for ancestry in response_json['ancestries']:
            if ancestry['type'] != "initial":
                continue

            #Create Sample model
            current_sample = {'source_GWAS_catalog' : gcst_id,'source_PMID' : pmid}

            current_sample['phenotyping_free'] = response_json['diseaseTrait']['trait']
            current_sample['sample_number'] = ancestry['numberOfIndividuals']

            ancestry_broad_list = []
            for ancestral_group in ancestry['ancestralGroups']:
                ancestry_broad_list.append(ancestral_group['ancestralGroup'])
            current_sample['ancestry_broad'] = ', '.join(ancestry_broad_list)

            ancestry_country_list = []
            for country in ancestry['countryOfRecruitment']:
                ancestry_country_list.append(country['countryName'])
            current_sample['ancestry_country'] = ', '.join(ancestry_country_list)
            print(current_sample)


def run():
    """ Update the EFO entries and add/update the Trait categories (from GWAS Catalog)."""
    for sample in Sample.objects.all():
        if sample.source_GWAS_catalog:
            get_gwas_info(sample.source_GWAS_catalog)
