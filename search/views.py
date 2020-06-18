from django.shortcuts import render
from elasticsearch_dsl import Q
from search.documents.efo_trait import EFOTraitDocument
from search.documents.publication import PublicationDocument
from search.search import EFOTraitSearch, PublicationSearch

all_results_scores = {}

def search(request):
    global all_results_scores

    q = request.GET.get('q')
    trait_children = None
    #trait_children = request.GET.get('include_children')
    scores_count = 0
    efo_trait_count = 0
    publication_count = 0
    table_scores = None
    table_efo_traits = None
    table_publications = None
    all_results = None
    all_results_scores = {}

    if q:
        # EFO Traits
        efo_trait_search = EFOTraitSearch(q, trait_children)
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
        #'table_efo_traits': table_efo_traits,
        #'table_publications': table_publications,
        'all_results': all_results,
        #'all_results': sorted(all_results),
        #'scores_count': scores_count,
        'efo_traits_count': efo_trait_count,
        'publications_count': publication_count,
        'has_table': 1
    }
    return render(request, 'search/search.html', context)


def efo_traits_table(request, data):

    results = []
    icon = '<span class="mr-3" style="font-weight:bold;font-size:18px;background-color:#BE4A81;padding: 4px 9px;color: white;display: inline-block;vertical-align: middle;border-radius: 50%">T</span>'
    for d in data:
        desc = d.description
        if desc:
            desc = desc.replace("['",'').replace("']",'')
        else:
            desc = ''

        score_html =  score_mini_table(d.id, d.score_set)

        categories = ', '.join([x.label for x in d.traitcategory_set])
        hmtl_results =  '<div class="pgs_result efo_traits_entry mb-4" title='+str(d.meta.score)+'>'
        hmtl_results += '<div class="pgs_result_title clearfix">'
        hmtl_results += '  <h4 class="mt-0 mb-2 mr-3 float-left">'
        hmtl_results += '    '+icon+'<a href="/trait/{}">{}</a>'.format(d.id, d.label)
        hmtl_results += '  </h4>'
        hmtl_results += '  <div class="mt-0 mb-2 pl-3 mr-3 float-left">{}</div>'.format(categories)
        hmtl_results += '  <div class="pl-3 float-left">{}</div>'.format(d.id)
        hmtl_results += '</div>'
        hmtl_results += '<div class="more">{}</div>'.format(desc)
        hmtl_results += '<div class="mt-1">Associated PGS scores <span class="badge badge-pill badge-pgs">{}</span> {}</div>'.format(d.scores_count, score_html)
        hmtl_results += '</div>'
        results.append(hmtl_results)

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
    #for d in data:
    for idx, d in enumerate(data):

        score_html =  score_mini_table("pub_"+str(idx), d.publication_score)

        hmtl_results =  '<div class="pgs_result publications_entry mb-4" title='+str(d.meta.score)+'>'
        hmtl_results += '<div class="pgs_result_title"><h4 class="mt-0 mb-2">'+icon+'<a href="/publication/{}">{}</a></h4></div>'.format(d.id, d.title)
        hmtl_results += '<div class="pgs_result_content">{} et al. ({}) - {}'.format(d.firstauthor, d.pub_year, d.journal)
        hmtl_results += '<span class="ml-2 pl-2"><b>PMID</b>:{}</span>'.format( d.PMID)
        hmtl_results += '<span class="ml-2 pl-2"><b>doi</b>:{}</span></div>'.format(d.doi)
        hmtl_results += '<div class="mt-1">Associated PGS scores <span class="badge badge-pill badge-pgs">{}</span> {}</div>'.format(d.scores_count, score_html)
        hmtl_results += '</div>'
        results.append(hmtl_results)

        result_score = d.meta.score
        if result_score in all_results_scores:
            all_results_scores[result_score].append(hmtl_results)
        else:
            all_results_scores[result_score] = [hmtl_results]

    return results


def score_mini_table(id, scores):

    score_html =  '<a class="toggle_btn" id="{}_scores"><i class="fa fa-plus-circle"></i></a>'.format(id)
    score_html += '<div class="toggle_content" id="list_{}_scores" style="display:none">'.format(id)
    score_html += """<table class="table table-striped table_pgs_score_results mt-2">
      <thead class="thead-light">
        <tr><th>PGS ID</th><th>PGS Name</th></tr>
      </thead>
      <tbody>"""
    for score in scores:
        score_html += '<tr><td><a href="/score/{}">{}</a></td><td>{}</td></tr>'.format(score.id, score.id, score.name)
    score_html += '</tbody></table></div>'

    return score_html
