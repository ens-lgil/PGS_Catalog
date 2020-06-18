from elasticsearch_dsl import Q
from search.documents.efo_trait import EFOTraitDocument
from search.documents.publication import PublicationDocument

class PGSSearch:
    fields = []      # fields that should be searched
    query = None     # query term(s)
    count = 0        # response count
    document = None  # ES document to use

    def search(self):
        query_settings = Q("multi_match", type="best_fields", query=self.query, fields=self.fields)
        #query_settings = Q("multi_match", type="best_fields",  operator="and", query=self.query, fields=self.fields)
        search_query = self.document.search().query(query_settings).extra(size=20)
        response = search_query.execute()
        self.count = len(response)
        return response


class EFOTraitSearch(PGSSearch):

    def __init__(self, query, include_children):
        self.query = query
        #self.fields = fields = ["id","label","synonyms","mapped_terms","traitcategory_set.label","traitcategory_set.parent","score_set.id","score_set.name"]
        self.fields = ["id^2","label^2","synonyms^2","mapped_terms","traitcategory_set.label","traitcategory_set.parent","score_set.id","score_set.name"]
        if include_children and include_children=="True":
            print("Children included")
            self.fields.append("trait_parents^2")
        self.document = EFOTraitDocument



class PublicationSearch(PGSSearch):

    def __init__(self, query):
        self.query = query
        self.fields = ["id","title^2","firstauthor^2","authors","pmid^2","doi^2","publication_score.id","publication_score.name"]
        self.document = PublicationDocument
