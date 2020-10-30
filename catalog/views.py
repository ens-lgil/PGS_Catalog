import os
from django.http import Http404
from django.shortcuts import render,redirect
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.conf import settings
from django.db.models import Prefetch
from django.db.models.functions import Lower

from benchmark.models import BM_EFOTrait
from .tables import *


generic_attributes =[ 'curation_notes','publication__title','publication__PMID','publication__authors','publication__curation_status','publication__curation_notes','publication__date_released']
pgs_defer = {
    'generic': generic_attributes,
    'perf'   : [*generic_attributes,'date_released','score__curation_notes','score__date_released']
}
pgs_prefetch = {
    'trait': Prefetch('trait_efo', queryset=EFOTrait.objects.only('id','label').all()),
    'perf' : ['score__publication', 'phenotyping_efo', 'sampleset__samples', 'sampleset__samples__sampleset', 'sampleset__samples__sample_age', 'sampleset__samples__followup_time', 'sampleset__samples__cohorts', 'performance_metric'],
    'publication_score': Prefetch('publication_score', queryset=Score.objects.only('id', 'publication').all()),
    'publication_performance': Prefetch('publication_performance', queryset=Performance.objects.only('id', 'publication', 'score').all().prefetch_related(Prefetch('score', queryset=Score.objects.only('id', 'publication').all()))),
}

def disclaimer_formatting(content):
    return '<div class="clearfix"><div class="mt-2 float_left pgs_note pgs_note_2"><div><span>Disclaimer: </span>{}</div></div></div>'.format(content)

def performance_disclaimer():
    return disclaimer_formatting("""The performance metrics are displayed as reported by the source studies.
        It is important to note that metrics are not necessarily comparable with
        each other. For example, metrics depend on the sample characteristics
        (described by the PGS Catalog Sample Set [PSS] ID), phenotyping, and
        statistical modelling. Please refer to the source publication for additional
        guidance on performance.""")

def score_disclaimer(publication_url):
    return disclaimer_formatting("""The original published polygenic score is unavailable.
    The authors have provided an alternative polygenic for the Catalog.
    Please note some details and performance metrics may differ from the <a href="https://doi.org/{}">publication</a>.""".format(publication_url))


def get_efo_traits_data():
    """ Generate the list of traits and trait categories in PGS."""
    data = []
    # Use set() to avoid duplication when an entry belongs to several categories
    traits_list = set()
    for category in TraitCategory.objects.all().prefetch_related('efotraits__associated_scores','efotraits__traitcategory').order_by('label'):
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
            # Traits table
            traits_list.add(trait)

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

    traits_list = list(traits_list)
    traits_list.sort(key=lambda x: x.label)

    return [traits_list, data]


def index(request):
    current_release = Release.objects.values('date').order_by('-date').first()

    traits_count = EFOTrait.objects.count()

    context = {
        'release' : current_release,
        'num_pgs' : Score.objects.count(),
        'num_traits' : traits_count,
        'num_pubs' : Publication.objects.count(),
        'num_benchmarks': BM_EFOTrait.objects.using('benchmark').count(),
        'has_ebi_icons' : 1
    }
    if settings.PGS_ON_CURATION_SITE=='True':
        released_traits = set()
        for score in Score.objects.filter(date_released__isnull=False).prefetch_related('trait_efo'):
            for efo in score.trait_efo.all():
                released_traits.add(efo.id)
        released_traits_count = len(list(released_traits))
        trait_diff = traits_count - released_traits_count
        if trait_diff != 0:
            context['num_traits_not_released'] = trait_diff
        context['num_pgs_not_released']  = Score.objects.filter(date_released__isnull=True).count()
        context['num_pubs_not_released'] = Publication.objects.filter(date_released__isnull=True).count()

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
        publication_defer = ['authors','curation_status','curation_notes','date_released']
        publication_prefetch_related = [pgs_prefetch['publication_score'], pgs_prefetch['publication_performance']]
        publications = Publication.objects.defer(*publication_defer).all().prefetch_related(*publication_prefetch_related)
        table = Browse_PublicationTable(publications, order_by="num")
        context = {
            'view_name': 'Publications',
            'table': table,
            'has_chart': 1
        }
    elif view_selection == 'sample_set':
        context['view_name'] = 'Sample Sets'
        table = Browse_SampleSetTable(Sample.objects.filter(sampleset__isnull=False).prefetch_related('sampleset', 'cohorts'))
        context['table'] = table
    else:
        context['view_name'] = 'Polygenic Scores (PGS)'
        score_only_attributes = ['id','name','publication','trait_efo','trait_reported','variants_number','publication__id','publication__date_publication','publication__journal','publication__firstauthor']
        table = Browse_ScoreTable(Score.objects.only(*score_only_attributes).select_related('publication').all().prefetch_related(pgs_prefetch['trait']), order_by="num")
        context['table'] = table

    context['has_table'] = 1

    return render(request, 'catalog/browseby.html', context)


def pgs(request, pgs_id):
    # If ID in lower case, redirect with the ID in upper case
    if not pgs_id.isupper():
        return redirect_with_upper_case_id(request, '/score/', pgs_id)

    template_html_file = 'pgs.html'

    try:
        score = Score.objects.defer(*pgs_defer['generic']).select_related('publication').prefetch_related('trait_efo','samples_variants','samples_training').get(id__exact=pgs_id)
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
    if not score.flag_asis:
        context['score_disclaimer'] = score_disclaimer(score.publication.doi)

    # Extract and display Sample Tables
    if score.samples_variants.count() > 0:
        table = SampleTable_variants(score.samples_variants.all())
        context['table_sample_variants'] = table
    if score.samples_training.count() > 0:
        table = SampleTable_training(score.samples_training.all())
        context['table_sample_training'] = table

    # Extract + display Performance + associated samples
    pquery = Performance.objects.defer(*pgs_defer['perf']).select_related('score', 'publication').filter(score=score).prefetch_related(*pgs_prefetch['perf'])
    table = PerformanceTable(pquery)
    table.exclude = ('score')
    context['table_performance'] = table

    pquery_samples = set()
    for q in pquery:
        for sample in q.samples():
            pquery_samples.add(sample)

    table = SampleTable_performance(pquery_samples)
    context['table_performance_samples'] = table

    return render(request, 'catalog/'+template_html_file, context)


def redirect_with_upper_case_id(request, dir, id):
    id = id.upper()
    response = redirect(dir+str(id), permanent=True)
    return response


def redirect_pgs_to_score(request, pgs_id):
    response = redirect_with_upper_case_id(request, '/score/', pgs_id)
    return response


def pgp(request, pub_id):
    # If ID in lower case, redirect with the ID in upper case
    if not pub_id.isupper():
        return redirect_with_upper_case_id(request, '/publication/', pub_id)

    template_html_file = 'pgp.html'
    try:
        pub = Publication.objects.prefetch_related('publication_score', 'publication_performance').get(id__exact=pub_id)
    except Publication.DoesNotExist:
        raise Http404("Publication: \"{}\" does not exist".format(pub_id))
    context = {
        'publication' : pub,
        'performance_disclaimer': performance_disclaimer(),
        'has_table': 1
    }

    # Display scores that were developed by this publication
    related_scores = pub.publication_score.defer(*pgs_defer['generic']).select_related('publication').all().prefetch_related(pgs_prefetch['trait'])
    if related_scores.count() > 0:
        table = Browse_ScoreTable(related_scores)
        context['table_scores'] = table

    #Get PGS evaluated by the PGP
    pquery = pub.publication_performance.defer(*pgs_defer['perf']).select_related('publication','score').all().prefetch_related(*pgs_prefetch['perf'], 'score__trait_efo')

    # Check if there any of the PGS are externally developed + display their information
    external_scores = set()
    for perf in pquery:
        perf_score = perf.score
        if perf_score not in related_scores:
            external_scores.add(perf_score)
    if len(external_scores) > 0:
        table = Browse_ScoreTable(external_scores)
        context['table_evaluated'] = table

    #Find + table the evaluations
    table = PerformanceTable(pquery)
    context['table_performance'] = table

    pquery_samples = set()
    for q in pquery:
        for sample in q.samples():
            pquery_samples.add(sample)

    table = SampleTable_performance(pquery_samples)
    context['table_performance_samples'] = table

    context['has_table'] = 1
    return render(request, 'catalog/'+template_html_file, context)


def efo(request, efo_id):
    # If ID in lower case, redirect with the ID in upper case
    # If ID with ':', redirect using the ID with '_'
    if not efo_id.isupper() or ':' in efo_id:
        efo_id = efo_id.replace(':','_')
        return redirect_with_upper_case_id(request, '/trait/', efo_id)

    exclude_children = False
    include_children = request.GET.get('include_children');
    if include_children:
        if include_children.lower() == 'false':
            exclude_children = True

    try:
        ontology_trait = EFOTrait_Ontology.objects.prefetch_related('scores_direct_associations','scores_child_associations','child_traits').get(id__exact=efo_id)
    except EFOTrait_Ontology.DoesNotExist:
        raise Http404("Trait: \"{}\" does not exist".format(efo_id))

    # Get list of PGS Scores
    related_direct_scores = ontology_trait.scores_direct_associations.defer(*pgs_defer['generic']).select_related('publication').all().prefetch_related(pgs_prefetch['trait'])
    related_child_scores = ontology_trait.scores_child_associations.defer(*pgs_defer['generic']).select_related('publication').all().prefetch_related(pgs_prefetch['trait'])
    if exclude_children:
        related_scores = related_direct_scores
    else:
        related_scores = list(related_direct_scores) + list(related_child_scores)
        related_scores.sort(key=lambda x: x.id)

    context = {
        'trait': ontology_trait,
        'trait_id_with_colon': ontology_trait.id.replace('_', ':'),
        'trait_scores_direct_count': len(related_direct_scores),
        'trait_scores_child_count': len(related_child_scores),
        'performance_disclaimer': performance_disclaimer(),
        'table_scores': Browse_ScoreTable(related_scores),
        'include_children': False if exclude_children else True,
        'has_table': 1
    }

    # Check if there are multiple descriptions
    try:
        desc_list = eval(ontology_trait.description)
        if type(desc_list) == list:
            context['desc_list'] = desc_list
    except:
        pass


    # Find the evaluations of these scores
    pquery = Performance.objects.defer(*pgs_defer['perf']).select_related('publication','score').filter(score__in=related_scores).prefetch_related(*pgs_prefetch['perf'])

    table = PerformanceTable(pquery)
    context['table_performance'] = table

    pquery_samples = set()
    for q in pquery:
        for sample in q.samples():
            pquery_samples.add(sample)

    table = SampleTable_performance(pquery_samples)
    context['table_performance_samples'] = table

    return render(request, 'catalog/efo.html', context)


def gwas_gcst(request, gcst_id):
    # If ID in lower case, redirect with the ID in upper case
    if not gcst_id.isupper():
        return redirect_with_upper_case_id(request, '/gwas/', gcst_id)

    samples = Sample.objects.filter(source_GWAS_catalog__exact=gcst_id).distinct()
    if len(samples) == 0:
        raise Http404("No PGS Samples are associated with the NHGRI-GWAS Catalog Study: \"{}\"".format(gcst_id))

    related_scores = Score.objects.defer(*pgs_defer['generic']).select_related('publication').filter(samples_variants__in=samples).prefetch_related(pgs_prefetch['trait']).distinct()
    if len(related_scores) == 0:
        raise Http404("No PGS Scores are associated with the NHGRI-GWAS Catalog Study: \"{}\"".format(gcst_id))

    context = {
        'gwas_id': gcst_id,
        'performance_disclaimer': performance_disclaimer(),
        'table_scores' : Browse_ScoreTable(related_scores),
        'has_table': 1
    }

    pquery = Performance.objects.defer(*pgs_defer['perf']).select_related('publication','score').filter(score__in=related_scores).prefetch_related(*pgs_prefetch['perf'])
    table = PerformanceTable(pquery)
    context['table_performance'] = table

    pquery_samples = set()
    for q in pquery:
        for sample in q.samples():
            pquery_samples.add(sample)

    table = SampleTable_performance(pquery_samples)
    context['table_performance_samples'] = table

    return render(request, 'catalog/gwas_gcst.html', context)


def pss(request, pss_id):
    # If ID in lower case, redirect with the ID in upper case
    if not pss_id.isupper():
        return redirect_with_upper_case_id(request, '/sampleset/', pss_id)

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

    related_performance = Performance.objects.defer(*pgs_defer['perf']).select_related('score', 'publication').filter(sampleset=sample_set).prefetch_related('score__publication', 'score__trait_efo', 'sampleset', 'phenotyping_efo', 'performance_metric')
    if related_performance.count() > 0:
        # Scores
        related_scores = [x.score for x in related_performance]
        table_scores = Browse_ScoreTable(related_scores)
        context['table_scores'] = table_scores
        # Display performance metrics associated with this sample set
        table_performance = PerformanceTable(related_performance)
        table_performance.exclude = ('sampleset')
        context['table_performance'] = table_performance
        context['performance_disclaimer'] = performance_disclaimer()

    return render(request, 'catalog/pss.html', context)

def releases(request):

    release_data = []
    pub_per_year_data = { 'all': [] }

    total_score = 0
    total_perf = 0
    total_publi = 0
    max_score = 0
    max_publi = 0
    max_perf = 0
    max_width = 100

    ## Publications distribution
    # All publications
    pub_per_year = {}
    publications = Publication.objects.all()
    for publication in publications:
        year = publication.pub_year
        if year in pub_per_year:
            pub_per_year[year] += 1
        else:
            pub_per_year[year] = 1

    for p_year in sorted(pub_per_year.keys()):
        pub_per_year_item = { 'year': p_year, 'count': pub_per_year[p_year] }
        pub_per_year_data['all'].append(pub_per_year_item)

    # Sepatate the "Released" and "Not released" Publications
    nr_publications = Publication.objects.filter(date_released__isnull=True)
    if len(nr_publications) > 0:
        nr_pub_per_year = {}
        for nr_publication in nr_publications:
            year = nr_publication.pub_year
            if year in nr_pub_per_year:
                nr_pub_per_year[year] += 1
            else:
                nr_pub_per_year[year] = 1
        pub_per_year_data['nr'] = []
        for p_year in sorted(nr_pub_per_year.keys()):
            pub_per_year_item = { 'year': p_year, 'count': nr_pub_per_year[p_year] }
            pub_per_year_data['nr'].append(pub_per_year_item)

        r_publications = Publication.objects.exclude(date_released__isnull=True)
        if len(r_publications) > 0:
            r_pub_per_year = {}
            for r_publication in r_publications:
                year = r_publication.pub_year

                if year in r_pub_per_year:
                    r_pub_per_year[year] += 1
                else:
                    r_pub_per_year[year] = 1
            pub_per_year_data['r'] = []
            for p_year in sorted(r_pub_per_year.keys()):
                pub_per_year_item = { 'year': p_year, 'count': r_pub_per_year[p_year] }
                pub_per_year_data['r'].append(pub_per_year_item)

    # Get max data
    releases_list = Release.objects.order_by('date')
    for release in releases_list:
        score = release.score_count
        perf  = release.performance_count
        publi = release.publication_count
        if score > max_score:
            max_score = score
        if publi > max_publi:
            max_publi = publi
        if perf > max_perf:
            max_perf = perf

    for release in releases_list:
        score = release.score_count
        perf  = release.performance_count
        publi = release.publication_count
        date  = release.date

        release_item = {
                        'date': date.strftime('%d/%m/%y'),
                        'score_count': score,
                        'performance_count': perf,
                        'publication_count': publi,
                        'total_score_count': total_score,
                        'total_performance_count': total_perf,
                        'total_publication_count': total_publi,
                       }
        total_score += score
        total_perf += perf
        total_publi += publi

        release_data.append(release_item)

    context = {
        'releases_list': releases_list.order_by('-date'),
        'releases_data': release_data,
        'pub_per_year_data': pub_per_year_data,
        'max_score': max_score,
        'max_publi': max_publi,
        'max_perf': max_perf,
        'has_table': 1,
        'has_chart_js': 1
    }
    return render(request, 'catalog/releases.html', context)


def upload_metadata(request):
    context = {}
    from django.core.files.storage import default_storage
    if request.method == 'POST' and request.FILES['myfile']:
        file_name = request.FILES['myfile'].name
        file_content = request.FILES['myfile'].read()
        file = default_storage.open(file_name, 'w')
        file.write(file_content)
        file.close()
        context['uploaded_file'] = True
        context['filename'] = file_name

    return render(request, 'catalog/upload.html', context)


class AboutView(TemplateView):
    template_name = "catalog/about.html"

class DocsView(TemplateView):
    template_name = "catalog/docs.html"

class DownloadView(TemplateView):
    template_name = "catalog/download.html"

class ReportStudyView(TemplateView):
    template_name = "catalog/report_study.html"

class CurrentTemplateView(RedirectView):
    url = settings.USEFUL_URLS['TEMPLATEGoogleDoc_URL']

class CurationDocView(RedirectView):
    url = settings.USEFUL_URLS['CurationGoogleDoc_URL']


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
