from django.shortcuts import render
from elasticsearch_dsl import Q
from search.documents.efo_trait import EFOTraitDocument
from search.documents.publication import PublicationDocument
from search.search import EFOTraitSearch, PublicationSearch

all_results_scores = {}

def search(request):
    global all_results_scores

    q = request.GET.get('q')
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
        'all_results': all_results,
        'efo_traits_count': efo_trait_count,
        'publications_count': publication_count,
        'has_table': 1
    }
    return render(request, 'search/search.html', context)


def efo_traits_table(request, data):

    results = []
    icon = '<span class="result_facet_type result_facet_type_1 mr-3"></span>'
    for d in data:
        desc = d.description
        if desc:
            desc = desc.replace("['",'').replace("']",'')
        else:
            desc = ''

        score_html =  score_mini_table(d.id, d.score_set)

        categories = ', '.join([x.label for x in d.traitcategory_set])
        hmtl_results =  '<div class="pgs_result efo_traits_entry mb-4" title='+str(d.meta.score)+'>'
        hmtl_results += '<div class="pgs_result_title">'
        hmtl_results += '  <h4 class="mt-0 mb-2 mr-4">'
        hmtl_results += '    '+icon+'<a href="/trait/{}">{}</a>'.format(d.id, d.label)
        hmtl_results += '  </h4>'
        hmtl_results += '  <div class="pgs_result_subtitles">'
        hmtl_results += '    <div class="mr-3">{}</div>'.format(categories)
        hmtl_results += '    <div>{}</div>'.format(d.id)
        hmtl_results += '  </div>'
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
    icon = '<span class="result_facet_type result_facet_type_2 mr-3"></span>'
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
