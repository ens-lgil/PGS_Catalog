from django.shortcuts import render
from elasticsearch_dsl import Q
from search_2.documents.efo_trait import EFOTraitDocument
from search_2.documents.publication import PublicationDocument

def search(request):

    q = request.GET.get('q')
    scores_count = 0
    efo_traits_count = 0
    publications_count = 0
    table_scores = None
    table_efo_traits = None
    table_publications = None
    if q:
        # Scores
        #score_query = Q("multi_match", query=q, fields=["id","name","publication.title","publication.doi","publication.authors","trait_efo.id","trait_efo.label","trait_efo.synonyms","trait_efo.mapped_terms"])
        #scores = ScoreDocument.search().query(score_query)
        #scores_count = scores.count()
        #scores_all = scores.scan()
        # EFO Traits
        efo_trait_query = Q("multi_match", query=q, fields=["id","label","synonyms","mapped_terms","traitcategory_set.label","traitcategory_set.parent","score_set.id","score_set.name"])
        efo_traits = EFOTraitDocument.search().query(efo_trait_query)
        efo_traits_count = efo_traits.count()
        efo_traits_all = efo_traits.scan()
        # Publications
        publication_query = Q("multi_match", query=q, fields=["id","title","doi","authors","publication_score.id","publication_score.name"])
        publications = PublicationDocument.search().query(publication_query)
        publications_count = publications.count()
        publications_all = publications.scan()

        #print("COUNT:"+str(scores_count))
        #table_scores = scores_table(request, scores_all)
        table_efo_traits = efo_traits_table(request, efo_traits_all)
        table_publications = publications_table(request, publications_all)
        all_results = table_efo_traits + table_publications

    context = {
        'query': q,
        #'table_scores': table_scores,
        'table_efo_traits': table_efo_traits,
        'table_publications': table_publications,
        'all_results': sorted(all_results),
        #'scores_count': scores_count,
        'efo_traits_count': efo_traits_count,
        'publications_count': publications_count,
        'has_table': 1
    }
    return render(request, 'search_2/search.html', context)


def efo_traits_table(request, data):

    results = []
    icon = '<span class="mr-3" style="font-weight:bold;font-size:18px;background-color:#BE4A81;padding: 4px 9px;color: white;display: inline-block;vertical-align: middle;border-radius: 50%">T</span>'
    for d in sorted(data, key=lambda x: x.label.lower()):
        desc = d.description
        desc = desc.replace("['",'').replace("']",'')
        categories = ', '.join([x.label for x in d.traitcategory_set])
        hmtl_results = '<div class="mb-4" style="padding:8px 12px;border:1px solid #333;border-radius:5px">'
        hmtl_results += '<div class="clearfix">'
        hmtl_results += '  <h4 class="mt-0 mb-2 pr-3 mr-3 float-left" style="border-right:1px solid #BE4A81">'
        hmtl_results += '    '+icon+'<a style="border:none;color:#007C82" href="/trait/{}">{}</a>'.format(d.id, d.label)
        hmtl_results += '  </h4>'
        hmtl_results += '  <div class="mt-0 mb-2 pr-3 mr-3 float-left" style="line-height:28px;vertical-align:middle;border-right:1px solid #BE4A81">{}</div>'.format(categories)
        hmtl_results += '  <div class="float-left" style="line-height:28px;vertical-align:middle">{}</div>'.format(d.id)
        hmtl_results += '</div>'
        hmtl_results += '<div class="more">{}</div>'.format(desc)
        hmtl_results += '<div class="mt-1">Associated PGS scores <span class="badge badge-pill badge-pgs">{}</span></div>'.format(d.scores_count)
        hmtl_results += '</div>'
        results.append(hmtl_results)

    return results


def publications_table(request, data):

    results = []
    doi_url = 'https://doi.org/'
    pubmed_url = 'https://www.ncbi.nlm.nih.gov/pubmed/'
    icon = '<span class="mr-3" style="font-weight:bold;font-size:18px;background-color:#f58f22;padding: 4px 8.5px;color: white;display: inline-block;vertical-align: middle;border-radius: 50%">P</span>'
    for d in sorted(data, key=lambda x: x.title.lower()):
        hmtl_results = '<div class="mb-4" style="padding:8px 12px;border:1px solid #333;border-radius:5px">'
        hmtl_results += '<h4 class="mt-0 mb-2">'+icon+'<a style="border:none;color:#007C82" href="/publication/{}">{}</a></h4>'.format(d.id, d.title)
        hmtl_results += '<div>{} et al. ({}) - {}'.format(d.firstauthor, d.pub_year, d.journal)
        hmtl_results += '<span class="ml-2 pl-2" style="border-left:1px solid #BE4A81"><b>PMID</b>:{}</span>'.format( d.PMID)
        hmtl_results += '<span class="ml-2 pl-2" style="border-left:1px solid #BE4A81"><b>doi</b>:{}</span></div>'.format(d.doi)
        hmtl_results += '<div class="mt-1">Associated PGS scores <span class="badge badge-pill badge-pgs">{}</span></div>'.format(d.scores_count)
        hmtl_results += '</div>'
        results.append(hmtl_results)

    return results
