import requests
from elasticsearch import Elasticsearch
from catalog.models import EFOTrait, TraitCategory

parents_index   = "parents_test"
efo_trait_index = "efo_trait"
policy_name   = "efo_trait_parents"
pipeline_name = "efo_trait_update"

efo_parents_list = {}
es_root_url = 'http://127.0.0.1:9200/'
exclude_terms = ['disposition', 'experimental factor', 'material property', 'Thing']

def get_efo_parents(trait):
    """ Fetch EFO information from an EFO ID, using the OLS REST API """
    trait_id = trait.id
    ols_url = 'https://www.ebi.ac.uk/ols/api/ontologies/efo/terms/http%253A%252F%252Fwww.ebi.ac.uk%252Fefo%252F{}/ancestors'
    response = requests.get(ols_url.format(trait_id))
    response = response.json()['_embedded']['terms']
    efo_parents_list[trait_id] = []
    if len(response) > 0:
        for parent in response:
            parent_label = parent['label']
            if not parent_label in exclude_terms:
                suffix = ''
                if parent['short_form'].startswith("EFO"):
                    suffix = " | EFO"
                #efo_parents_list[trait_id].append(parent_label+suffix)
                efo_parents_list[trait_id].append(parent_label)
    else:
        print("The script can't retrieve the parents of the trait '"+trait.label+"' ("+trait_id+"): the API returned "+str(len(response))+" results.")


def add_data_to_parents_index(es):
    """ Populate the parent traits index """
    for trait in efo_parents_list.keys():
        es.create(
            index = parents_index,
            id = trait,
            body = { "id" : trait, "parents" : efo_parents_list[trait] }
        )


def enrich_efo_trait_index(es):
    """ Add the parent traits via the ingest pipeline """

    for trait in efo_parents_list.keys():
        # Get content of trait document
        source = es.get_source(
            index = efo_trait_index,
            id = trait
        )
        # Delete trait document
        es.delete(
            index = efo_trait_index,
            id = trait
        )
        # Recreate trait document with pipeline
        es.create(
            index = efo_trait_index,
            id = trait,
            body = source,
            pipeline = pipeline_name
        )


def create_parents_index(es):
    """ Create temporary index to store the traits parents. """

    if not es.indices.exists(index=parents_index):
        response = es.indices.create(
            index = parents_index,
            body = {
                "settings": {"number_of_shards": 1},
                "mappings": {
                  "properties": {
                    "id":  { "type": "text"  },
                    "parents":   { "type": "text"  }
                  }
                }
            }
        )
        if not 'acknowledged' in response:
            print("ERROR: Can't create new index")
        elif not response['acknowledged']:
            print("ERROR: The index creation failed:\n"+response)
    else:
        print("Index '"+parents_index+"' already exists: no need to create it")


def delete_parents_index(es):
    """ Delete temporary index storing the traits parents. """
    es.indices.delete(parents_index)


def create_policy(es):
    """ Create enrich policy for the efo_trait index, using the trait parents index. """
    try:
        es.enrich.get_policy(name=policy_name)
    except:
        # Create enrich policy
        es.enrich.put_policy(
            name = policy_name,
            body = {
                "match": {
                    "indices": ["parents_test"],
                    "match_field": "id",
                    "enrich_fields": ["parents"]
                }
            }
        )
    # Execute enrich policy
    es.enrich.execute_policy(policy_name)


def create_ingest_pipeline(es):

    es.ingest.put_pipeline(
        id = pipeline_name,
        body = {
          "description" : "Enriching user details to messages",
          "processors" : [
            {
              "enrich" : {
                "policy_name": policy_name,
                "field" : "id",
                "target_field": "trait_parents",
                "max_matches": "1"
              }
            },
            {
              "remove": {
                "field": "trait_parents.id"
              }
                }
         ]
        }
    )


def prepare_enrich_data():

    response = requests.get('https://www.ebi.ac.uk/gwas/rest/api/parentMapping/%s'%trait_id)
    response_json = response.json()


def run(*args):
    """ Get all EFO parents of the EFO entries."""

    try:
        es = Elasticsearch(['http://localhost:9200'])
        print("Connected")
    except Exception as ex:
        print("Connection error:", ex)


    create_parents_index(es)
    create_policy(es)
    create_ingest_pipeline(es)

    #for trait in EFOTrait.objects.all():
    for trait in EFOTrait.objects.all()[:5]: # Only for tests
        #trait_id = trait.id
        #trait_label = trait.label
        #trait_desc = trait.description
        #print("# "+trait_id+" | "+trait_label)
        get_efo_parents(trait)

    add_data_to_parents_index(es)
    enrich_efo_trait_index(es)
    delete_parents_index(es)

    for entry in efo_parents_list:
        print(entry+":\n  - "+'\n  - '.join(efo_parents_list[entry]))
