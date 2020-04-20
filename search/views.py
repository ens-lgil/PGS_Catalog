from django.shortcuts import render
from search.documents.efo_trait import EFOTraitDocument
from search.documents.publication import PublicationDocument
from search.documents.score import ScoreDocument

#from search.tables import *

def search(request):

    q = request.GET.get('q')
    scores_count = 0
    efo_traits_count = 0
    publications_count = 0
    if q:
        # Scores
        scores = ScoreDocument.search().query("multi_match", query=q, fields=["id","name","publication.title","publication.doi","publication.authors","trait_efo.id","trait_efo.label","trait_efo.synonyms","trait_efo.mapped_terms"])
        scores_count = scores.count()
        scores_all = scores.scan()
        # EFO Traits
        efo_traits = EFOTraitDocument.search().query("multi_match", query=q, fields=["id","label","synonyms","mapped_terms","traitcategory_set.label","traitcategory_set.parent"])
        efo_traits_count = efo_traits.count()
        efo_traits_all = efo_traits.scan()
        # Publications
        publications = PublicationDocument.search().query("multi_match", query=q, fields=["id","title","doi","authors"])
        publications_count = publications.count()
        publications_all = publications.scan()

        #print("COUNT:"+str(scores_count))
        table_scores = scores_table(request, scores_all)
        table_efo_traits = efo_traits_table(request, efo_traits_all)
        table_publications = publications_table(request, publications_all)
    context = {
        'table_scores': table_scores,
        'table_efo_traits': table_efo_traits,
        'table_publications': table_publications,
        'scores_count': scores_count,
        'efo_traits_count': efo_traits_count,
        'publications_count': publications_count,
        'has_table': 1
    }
    return render(request, 'search/search.html', context)


def scores_table(request, data):

    attrs = 'data-show-columns="true" data-sort-name="id"'
    #attrs = 'data-show-columns="true" data-sort-name="id" data-page-size="50"'
    fields = [
        { 'key': 'id', 'label': "ID" },
        { 'key': 'name', 'label': "Name" },
        { 'key': 'variants_number', 'label': "Number of variants" },
        { 'key': 'trait_efo.label', 'label': "Trait (ontology term label)", 'multi': '1' },
        { 'key': 'publication.firstauthor', 'label': 'Publication author' },
        { 'key': 'publication.title', 'label': 'Publication' }
    ]
    tags = []
    multi_tags = set()
    for column in fields:
        tags.append(column['key'])
        if 'multi' in column:
            multi_tags.add(column['key'])

    formatted_data = []
    for d in sorted(data, key=lambda x: x.id):
        #print("DATA: "+str(d))
        my_data = []
        for t in tags:
            keys = t.split('.')
            if len(keys) == 1:
                my_data.append(d[t])
            else:
                if t in multi_tags:
                    content = []
                    for item in d[keys[0]]:
                        content.append(item[keys[1]])
                    my_data.append(', '.join(content))
                else:
                    my_data.append(d[keys[0]][keys[1]])
        formatted_data.append(my_data)

    context = {'attrs': attrs, 'fields': fields, 'table_data': formatted_data}
    render_html = render(request, 'search/pgs_catalog_result_table.html', context)

    return render_html.content.decode("utf-8")
    #return render(request, 'search/pgs_catalog_result_table.html', context)


def efo_traits_table(request, data):

    attrs = 'data-show-columns="true" data-sort-name="label"'
    #attrs = 'data-show-columns="true" data-sort-name="id" data-page-size="50"'
    fields = [
        { 'key': 'label', 'label': "Trait (ontology term label)" },
        { 'key': 'id', 'label': "Trait Identifier (Experimental Factor Ontology ID)" },
        #{ 'key': 'traitcategory.label', 'label': 'Trait Category' }
    ]

    tags = []
    for column in fields:
        tags.append(column['key'])

    formatted_data = []
    for d in sorted(data, key=lambda x: x.label.lower()):
        my_data = []
        for t in tags:
            keys = t.split('.')
            if len(keys) == 1:
                my_data.append(d[t])
            else:
                #print("MULTI ("+t+"): "+keys[0]+" | "+keys[1])
                my_data.append(d[keys[0]][keys[1]])
        formatted_data.append(my_data)

    context = {'attrs': attrs, 'fields': fields, 'table_data': formatted_data}
    render_html = render(request, 'search/pgs_catalog_result_table.html', context)

    return render_html.content.decode("utf-8")


def publications_table(request, data):

    attrs = 'data-show-columns="true" data-sort-name="id"'
    #attrs = 'data-show-columns="true" data-sort-name="id" data-page-size="50"'
    fields = [
        { 'key': 'id', 'label': "PGS Publication/Study (PGP) ID" },
        { 'key': 'title', 'label': "Title" },
        { 'key': 'firstauthor', 'label': 'Publication author' },
        { 'key': 'doi', 'label': "Digital object identifier (doi)"},
        { 'key': 'PMID', 'label': "PubMed ID (PMID)" }
    ]

    tags = []
    for column in fields:
        tags.append(column['key'])

    formatted_data = []
    for d in sorted(data, key=lambda x: x.id):
        my_data = []
        for t in tags:
            keys = t.split('.')
            if len(keys) == 1:
                my_data.append(d[t])
            else:
                #print("MULTI ("+t+"): "+keys[0]+" | "+keys[1])
                my_data.append(d[keys[0]][keys[1]])
        formatted_data.append(my_data)

    context = {'attrs': attrs, 'fields': fields, 'table_data': formatted_data}
    render_html = render(request, 'search/pgs_catalog_result_table.html', context)

    return render_html.content.decode("utf-8")
