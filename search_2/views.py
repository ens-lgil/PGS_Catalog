from django.shortcuts import render
from elasticsearch_dsl import Q
from search_2.documents.efo_trait import EFOTraitDocument
from search_2.documents.publication import PublicationDocument
from search_2.search import EFOTraitSearch, PublicationSearch

all_results_scores = {}

def search(request):
    global all_results_scores

    q = request.GET.get('q')
    scores_count = 0
    efo_traits_count = 0
    publications_count = 0
    table_scores = None
    table_efo_traits = None
    table_publications = None
    all_results = None
    all_results_scores = {}

    if q:
        # EFO Traits
        efo_trait_search = EFOTraitSearch(q)
        efo_trait_results = efo_trait_search.search()
        efo_trait_count = efo_trait_search.count

        # Publications
        publication_search = PublicationSearch(q)
        publication_results = publication_search.search()
        publication_count = publication_search.count

        table_efo_traits = efo_traits_table(request, efo_trait_results)
        table_publications = publications_table(request, publication_results)
        if all_results_scores:
            all_results = []
            for score in sorted(all_results_scores, reverse=True):
                for result in all_results_scores[score]:
                    all_results.append(result)


    context = {
        'query': q,
        #'table_scores': table_scores,
        'table_efo_traits': table_efo_traits,
        'table_publications': table_publications,
        'all_results': all_results,
        #'all_results': sorted(all_results),
        #'scores_count': scores_count,
        'efo_traits_count': efo_trait_count,
        'publications_count': publication_count,
        'has_table': 1
    }
    return render(request, 'search_2/search.html', context)


def efo_traits_table(request, data):

    results = []
    icon = '<span class="mr-3" style="font-weight:bold;font-size:18px;background-color:#BE4A81;padding: 4px 9px;color: white;display: inline-block;vertical-align: middle;border-radius: 50%">T</span>'
    for d in data:
        desc = d.description
        desc = desc.replace("['",'').replace("']",'')
        categories = ', '.join([x.label for x in d.traitcategory_set])
        hmtl_results = '<div class="mb-4" style="padding:8px 12px;border:1px solid #333;border-radius:5px" title='+str(d.meta.score)+'>'
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
        print(d.id+': '+d.label)

        result_score = d.meta.score
        if result_score in all_results_scores:
            all_results_scores[result_score].append(hmtl_results)
        else:
            all_results_scores[result_score] = [hmtl_results]

    return results


def publications_table(request, data):

    results = []
    doi_url = 'https://doi.org/'
    pubmed_url = 'https://www.ncbi.nlm.nih.gov/pubmed/'
    icon = '<span class="mr-3" style="font-weight:bold;font-size:18px;background-color:#f58f22;padding: 4px 8.5px;color: white;display: inline-block;vertical-align: middle;border-radius: 50%">P</span>'
    for d in data:
        hmtl_results = '<div class="mb-4" style="padding:8px 12px;border:1px solid #333;border-radius:5px" title='+str(d.meta.score)+'>'
        hmtl_results += '<h4 class="mt-0 mb-2">'+icon+'<a style="border:none;color:#007C82" href="/publication/{}">{}</a></h4>'.format(d.id, d.title)
        hmtl_results += '<div>{} et al. ({}) - {}'.format(d.firstauthor, d.pub_year, d.journal)
        hmtl_results += '<span class="ml-2 pl-2" style="border-left:1px solid #BE4A81"><b>PMID</b>:{}</span>'.format( d.PMID)
        hmtl_results += '<span class="ml-2 pl-2" style="border-left:1px solid #BE4A81"><b>doi</b>:{}</span></div>'.format(d.doi)
        hmtl_results += '<div class="mt-1">Associated PGS scores <span class="badge badge-pill badge-pgs">{}</span></div>'.format(d.scores_count)
        hmtl_results += '</div>'
        results.append(hmtl_results)

        result_score = d.meta.score
        if result_score in all_results_scores:
            all_results_scores[result_score].append(hmtl_results)
        else:
            all_results_scores[result_score] = [hmtl_results]

    return results
