from elasticsearch_dsl import Q
from search_2.documents.efo_trait import EFOTraitDocument
from search_2.documents.publication import PublicationDocument

class PGSSearch:
    fields = []      # fields that should be searched
    query = None     # query term(s)
    count = 0        # response count
    document = None  # ES document to use

    def search(self):
        query_settings = Q("multi_match", query=self.query, fields=self.fields)
        search_query = self.document.search().query(query_settings)
        response = search_query.execute()
        self.count = len(response)
        return response


class EFOTraitSearch(PGSSearch):

    def __init__(self, query):
        self.query = query
        #self.fields = fields = ["id","label","synonyms","mapped_terms","traitcategory_set.label","traitcategory_set.parent","score_set.id","score_set.name"]
        self.fields = fields = ["id","label","synonyms","mapped_terms","traitcategory_set.label","traitcategory_set.parent","score_set.id","score_set.name","trait_parents.parents"]
        self.document = EFOTraitDocument



class PublicationSearch(PGSSearch):

    def __init__(self, query):
        self.query = query
        self.fields = fields = ["id","title","firstauthor","authors","pmid","doi","publication_score.id","publication_score.name"]
        self.document = PublicationDocument
