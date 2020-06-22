import os, requests
from requests.exceptions import HTTPError
import json
import time
from elasticsearch import Elasticsearch
#from elasticsearch import helpers
from catalog.models import EFOTrait, TraitCategory

parents_index   = "parents_test"
efo_trait_index = "efo_trait"
efo_trait_index_tmp = "efo_trait_tmp"
policy_name   = "efo_trait_parents"
pipeline_name = "efo_trait_update"

efo_parents_list = {}
#es_root_url = 'http://127.0.0.1:9200/'
es_root_url = os.environ['ELASTICSEARCH_URL_ROOT']
exclude_terms = ['disposition', 'experimental factor', 'material property', 'Thing']

def get_efo_parents(trait):
    """ Fetch EFO information from an EFO ID, using the OLS REST API """
    trait_id = trait.id
    ols_url = 'https://www.ebi.ac.uk/ols/api/ontologies/efo/terms/http%253A%252F%252Fwww.ebi.ac.uk%252Fefo%252F{}/ancestors'
    response = requests.get(ols_url.format(trait_id))
    response_json = response.json()
    efo_parents_list[trait_id] = []
    if '_embedded' in response_json:
        response = response_json['_embedded']['terms']
        if len(response) > 0:
            for parent in response:
                parent_label = parent['label']
                if not parent_label in exclude_terms:
                    suffix = ''
                    #if parent['short_form'].startswith("EFO"):
                    #    suffix = " | EFO"
                    #efo_parents_list[trait_id].append(parent_label+suffix)
                    efo_parents_list[trait_id].append(parent_label)
        else:
            print("The script can't retrieve the parents of the trait '"+trait.label+"' ("+trait_id+"): the API returned "+str(len(response))+" results.")
    else:
        print("  >> WARNING: Can't find parents for the trait '"+trait_id+"'.")

def add_data_to_parents_index(es):
    """ Populate the parent traits index """
    print("Add data to parents_index")
    for trait in efo_parents_list.keys():
        es.create(
            index = parents_index,
            id = trait,
            body = { "id" : trait, "parents" : efo_parents_list[trait] }
        )


def enrich_efo_trait_index(es):
    """ Add the parent traits via the ingest pipeline """
    print("Enrich efo_trait index")
    count = 1
    data = []
    bulk_data = ''
    for trait in efo_parents_list.keys():
        #time.sleep(2.5)
        ##if count >= 70:
        ##    time.sleep(2)
        ##    #count = 0
        ##else:
        ##    time.sleep(1.5)
        print(str(count)+" - Enrich trait: "+trait)
        # Get content of trait document
        source = es.get_source(
            index = efo_trait_index,
            id = trait
        )
        source['trait_parents'] = efo_parents_list[trait]

        source_string = json.dumps(source)
        source_string_one_line = source_string.replace("\n",'')
        if bulk_data != '':
            bulk_data += '\n'
        bulk_data += '{ "index" : { "_index" : "'+efo_trait_index_tmp+'", "_id" : "'+trait+'" } }\n'+source_string_one_line

        # Delete trait document
        #es.delete(
        #    index = efo_trait_index,
        #    id = trait
        #)
        # Recreate trait document with pipeline
        #es.create(
        #    index = efo_trait_index_tmp,
        #    id = trait,
        #    body = source,
        #    pipeline = pipeline_name
        #)
        count += 1
    #es.bulk(body=json.dumps(data), index=efo_trait_index_tmp)
    #print(bulk_data)
    #es.bulk(body=bulk_data, index=efo_trait_index_tmp, pipeline=pipeline_name)
    efo_mapping = es.indices.get_mapping(efo_trait_index)
    es.indices.create(index=efo_trait_index_tmp, ignore=400, body=json.dumps(efo_mapping))
    es.bulk(body=bulk_data, index=efo_trait_index_tmp, refresh=True)
    #helpers.bulk(es,data)


def clone_efo_trait_index(es):

    print("Prepare index '"+efo_trait_index_tmp+"':")
    print("- Make index '"+efo_trait_index+"' read only")
    es.indices.put_settings(body = { "index": { "blocks.write": True } }, index = efo_trait_index)
    print("- Clone index '"+efo_trait_index+"' into '"+efo_trait_index_tmp+"'")
    es.indices.clone(efo_trait_index, efo_trait_index_tmp)
    print("- Make indexes ''"+efo_trait_index+"' and '"+efo_trait_index_tmp+"' writtable")
    es.indices.put_settings(body = { "index": { "blocks.write": False } }, index = efo_trait_index)
    es.indices.put_settings(body = { "index": { "blocks.write": False } }, index = efo_trait_index_tmp)
    print("- Delete documents from '"+efo_trait_index_tmp+"'")
    es.delete_by_query(
        index=efo_trait_index_tmp,
        body={ "query": { "match_all": {} } }
    )
    print("- Update mapping of '"+efo_trait_index_tmp+"'")
    es.indices.put_mapping(
        index=efo_trait_index_tmp,
        body={
            "properties": {
                "trait_parents":
                {
                    "type" : "text",
                    "fields" : {
                        "raw" : {
                            "type" : "text",
                            "analyzer" : "keyword"
                        }
                    }
                }
            }
        }
    )

def clone_new_efo_trait_index(es):
    print("Clone tmp index '"+efo_trait_index_tmp+"' into '"+efo_trait_index+"':")
    print("- Delete index '"+efo_trait_index+"'")
    es.indices.delete(efo_trait_index)
    print("- Make index '"+efo_trait_index_tmp+"' read only")
    es.indices.put_settings(body = { "index": { "blocks.write": True } }, index = efo_trait_index_tmp)
    print("- Clone index '"+efo_trait_index_tmp+"' into '"+efo_trait_index+"'")
    es.indices.clone(efo_trait_index_tmp, efo_trait_index)
    print("- Delete index '"+efo_trait_index_tmp+"'")
    es.indices.delete(efo_trait_index_tmp)


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
    print("Cleanup - delete temporary index '"+parents_index+"'.")
    es.indices.delete(parents_index)


def create_policy(es):
    """ Create enrich policy for the efo_trait index, using the trait parents index. """
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
          "description" : "Enriching traits with parent terms",
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

def count_index_documents(es,index):
    return es.count(index=index)

def run(*args):
    """ Get all EFO parents of the EFO entries."""
    print("SERVER: "+str(es_root_url))
    try:
        es = Elasticsearch([es_root_url], timeout=20)
        print("Connected")
    except Exception as ex:
        print("Connection error:", ex)

    #efo_mapping = es.indices.get_mapping(efo_trait_index)
    #print(efo_mapping[efo_trait_index])
    #es.indices.create(index=efo_trait_index_tmp, body=json.dumps(efo_mapping[efo_trait_index]))


    clone_efo_trait_index(es)

    #create_parents_index(es)
    # Number of documents in main index
    efo_trait_index_count = count_index_documents(es,efo_trait_index)

    for trait in EFOTrait.objects.all():
    #for trait in EFOTrait.objects.all()[:5]: # Only for tests
        trait_id = trait.id
        trait_label = trait.label
        trait_desc = trait.description
        print("# "+trait_id+" | "+trait_label)
        get_efo_parents(trait)

    #add_data_to_parents_index(es)
    #create_policy(es)
    #create_ingest_pipeline(es)

    enrich_efo_trait_index(es)

    # Number of documents in main index
    efo_trait_index_tmp_count = count_index_documents(es,efo_trait_index_tmp)

    if efo_trait_index_count == efo_trait_index_tmp_count:
        clone_new_efo_trait_index(es)
    else:
        print("The number of documents in the indexes '{}' and '{}' are different ({} vs {})".format(efo_trait_index,efo_trait_index_tmp,efo_trait_index_count,efo_trait_index_tmp_count))
    #delete_parents_index(es)

    #for entry in efo_parents_list:
    #    print(entry+":\n  - "+'\n  - '.join(efo_parents_list[entry]))
