from django.http import Http404
from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.conf import settings
from django.db.models.functions import Lower
from django.db.models import Q
import re

from .tables import *


def performance_disclaimer():
    return """<span class="pgs_note_title">Disclaimer: </span>
        The performance metrics are displayed as reported by the source studies.
        It is important to note that metrics are not necessarily comparable with
        each other. For example, metrics depend on the sample characteristics
        (described by the PGS Catalog Sample Set [PSS] ID), phenotyping, and
        statistical modelling. Please refer to the source publication for additional
        guidance on performance."""


def get_efo_traits_data():
    """ Generate the list of traits and trait categories in PGS."""
    data = []
    traits_list = []

    for category in TraitCategory.objects.all().prefetch_related('efotraits__score_set','efotraits__traitcategory_set').order_by('label'):
        cat_scores_count = 0
        cat_id = category.parent.replace(' ', '_')

        cat_traits = []

        for trait in category.efotraits.all():
            trait_scores_count = trait.scores_count
            if trait_scores_count == 0:
                continue
            cat_scores_count += trait_scores_count
            trait_entry = {
                "name": trait.label,
                "size": trait_scores_count,
                "id": trait.id
            }
            cat_traits.append(trait_entry)
            traits_list.append(trait)

        if cat_scores_count == 0:
            continue

        cat_traits.sort(key=lambda x: x["name"].lower())

        cat_data = {
          "name": category.label,
          "colour" : category.colour,
          "id" : cat_id,
          "size_g": cat_scores_count,
          "children": cat_traits
        }
        data.append(cat_data)

    traits_list.sort(key=lambda x: x.label)

    return [traits_list, data]


def index(request):
    current_release = Release.objects.values('date').order_by('-date').first()

    context = {
        'release' : current_release,
        'num_pgs' : Score.objects.count(),
        'num_traits' : EFOTrait.objects.count(),
        'num_pubs' : Publication.objects.count(),
        'has_ebi_icons' : 1
    }
    return render(request, 'catalog/index.html', context)


def browseby(request, view_selection):
    context = {}

    if view_selection == 'traits':
        efo_traits_data = get_efo_traits_data()
        table = Browse_TraitTable(efo_traits_data[0])
        context = {
            'view_name': 'Traits',
            'table': table,
            'data_chart': efo_traits_data[1],
            'has_chart': 1
        }
    elif view_selection == 'studies':
        context['view_name'] = 'Publications'
        table = Browse_PublicationTable(Publication.objects.all().prefetch_related('publication_score', 'publication_performance', 'publication_performance__score'), order_by="num")
        context['table'] = table
    elif view_selection == 'sample_set':
        context['view_name'] = 'Sample Sets'
        table = Browse_SampleSetTable(Sample.objects.filter(sampleset__isnull=False).prefetch_related('sampleset', 'cohorts'))
        context['table'] = table
    else:
        context['view_name'] = 'Polygenic Scores (PGS)'
        table = Browse_ScoreTable(Score.objects.select_related('publication').all().prefetch_related('trait_efo'), order_by="num")
        context['table'] = table

    context['has_table'] = 1

    return render(request, 'catalog/browseby.html', context)


def pgs(request, pgs_id):
    try:
        score = Score.objects.select_related('publication').prefetch_related('trait_efo','samples_variants','samples_training').get(id__exact=pgs_id)
    except Score.DoesNotExist:
        raise Http404("Polygenic Score (PGS): \"{}\" does not exist".format(pgs_id))

    pub = score.publication
    citation = format_html(' '.join([pub.firstauthor, '<i>et al. %s</i>'%pub.journal, '(%s)' % pub.date_publication.strftime('%Y')]))
    citation = format_html('<a target="_blank" href="https://doi.org/{}">{}</a>', pub.doi, citation)
    context = {
        'pgs_id' : pgs_id,
        'score' : score,
        'citation' : citation,
        'performance_disclaimer': performance_disclaimer(),
        'efos' : score.trait_efo.all(),
        'num_variants_pretty' : '{:,}'.format(score.variants_number),
        'has_table': 1
    }

    # Extract and display Sample Tables
    if score.samples_variants.count() > 0:
        table = SampleTable_variants(score.samples_variants.all())
        context['table_sample_variants'] = table
    if score.samples_training.count() > 0:
        table = SampleTable_training(score.samples_training.all())
        context['table_sample_training'] = table

    # Extract + display Performance + associated samples
    pquery = Performance.objects.select_related('score', 'publication').filter(score=score).prefetch_related('score__publication', 'phenotyping_efo', 'sampleset__samples', 'sampleset__samples__sampleset', 'sampleset__samples__sample_age', 'sampleset__samples__followup_time', 'sampleset__samples__cohorts', 'performance_metric')
    table = PerformanceTable(pquery)
    table = PerformanceTable(pquery)
    context['table_performance'] = table

    pquery_samples = set()
    for q in pquery:
        for sample in q.samples():
            pquery_samples.add(sample)

    table = SampleTable_performance(pquery_samples)
    context['table_performance_samples'] = table

    return render(request, 'catalog/pgs.html', context)


def pgp(request, pub_id):
    try:
        pub = Publication.objects.prefetch_related('publication_score', 'publication_performance').get(id__exact=pub_id)
    except Publication.DoesNotExist:
        raise Http404("Publication: \"{}\" does not exist".format(pub_id))
    context = {
        'publication' : pub,
        'performance_disclaimer': performance_disclaimer(),
        'has_table': 1
    }

    #Display scores that were developed by this publication
    related_scores = pub.publication_score.all().prefetch_related('trait_efo', 'publication')
    if related_scores.count() > 0:
        table = Browse_ScoreTable(related_scores)
        context['table_scores'] = table

    #Get PGS evaluated by the PGP
    pquery = pub.publication_performance.select_related('publication','score').all().prefetch_related('score__publication', 'phenotyping_efo', 'sampleset__samples', 'sampleset__samples__sampleset', 'sampleset__samples__sample_age', 'sampleset__samples__followup_time', 'sampleset__samples__cohorts', 'performance_metric')

    # Check if there any of the PGS are externally developed + display their information
    external_scores = set()
    for perf in pquery:
        if perf.score not in related_scores:
            external_scores.add(perf.score)
    if len(external_scores) > 0:
        table = Browse_ScoreTable(external_scores)
        context['table_evaluated'] = table

    #Find + table the evaluations
    table = PerformanceTable_PubTrait(pquery)
    context['table_performance'] = table

    pquery_samples = set()
    for q in pquery:
        for sample in q.samples():
            pquery_samples.add(sample)

    table = SampleTable_performance(pquery_samples)
    context['table_performance_samples'] = table

    context['has_table'] = 1
    return render(request, 'catalog/pgp.html', context)


def efo(request, efo_id):
    try:
        trait = EFOTrait.objects.prefetch_related('score_set').get(id__exact=efo_id)
    except EFOTrait.DoesNotExist:
        raise Http404("Trait: \"{}\" does not exist".format(efo_id))

    related_scores = trait.score_set.select_related('publication').all().prefetch_related('trait_efo')
    context = {
        'trait': trait,
        'performance_disclaimer': performance_disclaimer(),
        'table_scores' : Browse_ScoreTable(related_scores),
        'has_table': 1
    }

    # Check if there are multiple descriptions
    try:
        desc_list = eval(trait.description)
        if type(desc_list) == list:
            context['desc_list'] = desc_list
    except:
        pass

    #Find the evaluations of these scores
    pquery = Performance.objects.select_related('publication','score').filter(score__in=related_scores).prefetch_related('score__publication', 'phenotyping_efo', 'sampleset__samples', 'sampleset__samples__sampleset', 'sampleset__samples__sample_age', 'sampleset__samples__followup_time', 'sampleset__samples__cohorts', 'performance_metric')
    table = PerformanceTable_PubTrait(pquery)
    context['table_performance'] = table

    pquery_samples = set()
    for q in pquery:
        for sample in q.samples():
            pquery_samples.add(sample)

    table = SampleTable_performance(pquery_samples)
    context['table_performance_samples'] = table

    return render(request, 'catalog/efo.html', context)


def pss(request, pss_id):
    try:
        sample_set = SampleSet.objects.prefetch_related('samples', 'samples__cohorts', 'samples__sample_age', 'samples__followup_time').get(id__exact=pss_id)
    except SampleSet.DoesNotExist:
        raise Http404("Sample Set: \"{}\" does not exist".format(pss_id))

    table_cohorts = []
    samples_list = sample_set.samples.all()
    for sample in samples_list:
        # Cohort
        if sample.cohorts.count() > 0:
            table = CohortTable(sample.cohorts.all(), order_by="name_short")
            table_cohorts.append(table)
        else:
            table_cohorts.append('')

    sample_set_data = zip(samples_list, table_cohorts)
    context = {
        'pss_id': pss_id,
        'sample_count': range(len(samples_list)),
        'sample_set_data': sample_set_data,
        'has_table': 1,
        'has_chart': 1
    }
    return render(request, 'catalog/pss.html', context)


class AboutView(TemplateView):
    template_name = "catalog/about.html"

class DocsView(TemplateView):
    template_name = "catalog/docs.html"

class DownloadView(TemplateView):
    template_name = "catalog/download.html"

class CurrentTemplateView(RedirectView):
    url = settings.USEFUL_URLS['TEMPLATEGoogleDoc_URL']


def get_query_search(query=None):
    queryset = {
        "scores" : set(),
        "publications" : set(),
        "efo_traits" : set()
    }
    queries = query.split(" ")

    for q in queries:
        scores = Score.objects.select_related('publication').filter(
            Q(id__icontains=q) | Q(name__icontains=q) |
            Q(publication__title__icontains=q) | Q(publication__firstauthor__icontains=q) |
            Q(trait_efo__id__icontains=q) | Q(trait_efo__label__icontains=q)
        ).prefetch_related('trait_efo').distinct()
        for score in scores:
            queryset["scores"].add(score)

        efo_traits = EFOTrait.objects.filter(
            Q(id__icontains=q) | Q(label__icontains=q) | Q(synonyms__icontains=q) | Q(mapped_terms__icontains=q) |
            Q(traitcategory__label__icontains=q) | Q(traitcategory__parent__icontains=q)
        ).prefetch_related('traitcategory_set').distinct()
        for efo_trait in efo_traits:
            queryset["efo_traits"].add(efo_trait)

        publications = Publication.objects.filter(
            Q(title__icontains=q) | Q(firstauthor__icontains=q)
        ).prefetch_related('publication_score', 'publication_performance', 'publication_performance__score').distinct()
        for publication in publications:
            queryset["publications"].add(publication)

    return(queryset)


def search(request):
    context = {}
    query = ""

    if request.GET:
        query = request.GET['q']
        context['query'] = str(query)
    if query:
        results = get_query_search(query)
        scores = list(results["scores"])
        publications = list(results["publications"])
        efo_traits = list(results["efo_traits"])
        #scores = sorted(get_query_search(query),key=Score.id)
        context['scores_count'] = len(scores)
        context['efo_traits_count'] = len(efo_traits)
        context['publications_count'] = len(publications)

        if scores:
            table_scores = Browse_ScoreTable(scores)
            context['table_scores'] = table_scores

        if efo_traits:
            table_efo_traits = Browse_TraitTable(efo_traits)
            context['table_efo_traits'] = table_efo_traits

        if publications:
            table_publications = Browse_PublicationTable(publications)
            context['table_publications'] = table_publications

    context['has_table'] = 1

    return render(request, 'catalog/search.html', context)


# Method used for the App Engine warmup
def warmup(request):
    """
    Provides default procedure for handling warmup requests on App
    Engine. Just add this view to your main urls.py.
    """
    import importlib
    from django.http import HttpResponse
    for app in settings.INSTALLED_APPS:
        for name in ('urls', 'views', 'models'):
            try:
                importlib.import_module('%s.%s' % (app, name))
            except ImportError:
                pass
    content_type = 'text/plain; charset=utf-8'
    return HttpResponse("Warmup done.", content_type=content_type)
