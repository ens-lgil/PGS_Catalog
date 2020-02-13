from django.http import Http404
from django.shortcuts import render
from django.views.generic import TemplateView
import re

from .tables import *


####################################################
##################### TESTS ########################
####################################################

def charts(request):

    # Scores per trait
    scores_per_trait = {}
    efo_per_trait = {}
    for trait in EFOTrait.objects.all():
        label = trait.label
        scores_per_trait[label] = trait.scores_count
        efo_per_trait[label] = trait.id

    traits_list = []
    efo_list = []
    score_counts_list = []
    score_counts_category = {}
    for trait, count in sorted(scores_per_trait.items()):
        efo_list.append(efo_per_trait[trait])
        traits_list.append(trait+" ("+str(count)+")")
        score_counts_list.append(count)

        if re.search("cancer", trait) or re.search("carcinoma", trait):
            if "cancer" in score_counts_category:
                score_counts_category["cancer"] = score_counts_category["cancer"] + count
            else:
                score_counts_category["cancer"] = count
        elif re.search("diabetes", trait):
            if "diabetes" in score_counts_category:
                score_counts_category["diabetes"] = score_counts_category["diabetes"] + count
            else:
                score_counts_category["diabetes"] = count
        elif re.search("heart", trait) or re.search("artery", trait) or re.search("fibrillation", trait):
            if "heart disease" in score_counts_category:
                score_counts_category["heart disease"] = score_counts_category["heart disease"] + count
            else:
                score_counts_category["heart disease"] = count
        else:
            score_counts_category[trait] = count

    colours_list = get_colours_list(len(traits_list))

    colours_list_cat = get_colours_list(len(score_counts_category.keys()))

    index = 0
    colours_legend = []
    for trait in traits_list:
        tuple = (trait,efo_list[index],colours_list[index])
        colours_legend.append(tuple)
        index = index + 1

    index = 0
    colours_legend_cat = []
    traits_list_cat = []
    counts_per_category = []
    for cat in sorted(score_counts_category.keys()):
        tuple = (cat,colours_list_cat[index])
        colours_legend_cat.append(tuple)
        traits_list_cat.append(cat)
        counts_per_category.append(score_counts_category[cat])
        index = index + 1

    # Variants per PGS
    variants_per_score_cat = {}
    for score in Score.objects.all():
        variants = str(score.variants_number);
        unit_size = len(variants)
        upper_unit = "1"
        for i in range(0,unit_size):
            upper_unit = upper_unit + '0'
        if upper_unit in variants_per_score_cat:
            variants_per_score_cat[upper_unit] = variants_per_score_cat[upper_unit] + 1
        else:
            variants_per_score_cat[upper_unit] = 1

    var_colours_list = get_colours_list(len(variants_per_score_cat.keys()))

    counts_per_var_cat = []
    var_cat_list = []
    for var_cat in sorted(variants_per_score_cat.keys()):
        var_cat_formatted = format(int(var_cat), ",")
        var_cat_list.append("Under "+var_cat_formatted+" variants ("+str(variants_per_score_cat[var_cat])+")")
        counts_per_var_cat.append(variants_per_score_cat[var_cat])

    context = {
        'scores_per_trait'    : [traits_list,score_counts_list,efo_list,colours_list,colours_legend],
        'scores_per_category' : [traits_list_cat,counts_per_category,colours_list_cat,colours_legend_cat],
        'var_per_pgs'         : [var_cat_list,counts_per_var_cat,var_colours_list]
    }
    return render(request, 'catalog/charts.html', context)


def random_colours():
    r = random.randint(0,255)
    g = random.randint(0,255)
    b = random.randint(0,255)
    return "rgb(" + str(r) + "," + str(g) + "," + str(b) + ")";

def get_colours_list(number):
    colours_list = ['rgb(230, 25, 75)', 'rgb(60, 180, 75)', 'rgb(255, 225, 25)', 'rgb(0, 130, 200)', 'rgb(245, 130, 48)', 'rgb(145, 30, 180)', 'rgb(70, 240, 240)', 'rgb(240, 50, 230)', 'rgb(210, 245, 60)', 'rgb(250, 190, 190)', 'rgb(0, 128, 128)', 'rgb(230, 190, 255)', 'rgb(170, 110, 40)', 'rgb(255, 250, 200)', 'rgb(128, 0, 0)', 'rgb(170, 255, 195)', 'rgb(128, 128, 0)', 'rgb(255, 215, 180)', 'rgb(0, 0, 128)', 'rgb(128, 128, 128)']
    number_of_colours_to_add = number - len(colours_list)
    if (number_of_colours_to_add > 0):
        for c in range(0,number):
            colour = random_colours()
            if colour in colours_list:
                loop_max = 0
                while colour in colours_list or loop_max<10:
                    colour = random_colours()
                loop_max = 0
            colours_list.append(colour)

    return colours_list

def get_lighter_colour(rgb_colour):
    """ Generate a slightly lighter colour/tint from the RGB provided """
    tint_factor = 0.9
    currentRGB = re.match(r"rgb\((\d+)\,\s?(\d+)\,\s?(\d+)",rgb_colour)
    newRGB = []
    for i in range(1,4):
        currentC = currentRGB.group(i)
        newC = round(255 - (255 - int(currentC)) * tint_factor)
        print("> "+str(currentC)+" | "+str(newC))
        if (newC > 255):
            newC = 255
        newRGB.append(str(newC))
    return "rgb("+', '.join(newRGB)+")"




####################################################
####################################################

def performance_disclaimer():
    return """<span class="pgs_note_title">Disclaimer: </span>
        The performance metrics are displayed as reported by the source studies.
        It is important to note that metrics are not necessarily comparable with
        each other.For example, metrics depend on the sample characteristics
        (described by the PGS Catalog Sample Set [PSS] ID), phenotyping, and
        statistical modelling. Please refer to the source publication for additional
        guidance on performance."""


def traits_chart_data():
    data = []

    for category in TraitCategory.objects.all():
        cat_name   = category.label
        cat_colour = category.colour
        cat_scores_count = category.count_scores
        cat_id = category.parent.replace(' ', '_')

        cat_traits = []

        for trait in category.efotraits.all():
            trait_id = trait.id
            trait_name = trait.label
            trait_scores_count = trait.scores_count
            trait_entry = {"name": trait_name, "size": trait_scores_count, "id": trait_id}
            cat_traits.append(trait_entry)

        cat_data = {
          "name": cat_name,
          "colour" : cat_colour,
          "id" : cat_id,
          "size_g": cat_scores_count,
          "children": cat_traits
        }
        data.append(cat_data)

    return data

def index(request):
    current_release = Release.objects.order_by('-date').first()

    context = {
        'release' : current_release,
        'num_pgs' : Score.objects.count(),
        'num_traits' : EFOTrait.objects.count(),
        'num_pubs' : Publication.objects.count()
    }
    return render(request, 'catalog/index.html', context)

def browseby(request, view_selection):
    context = {}

    if view_selection == 'traits':
        context['view_name'] = 'Traits'
        r = Score.objects.all().values('trait_efo').distinct()
        l = []
        for x in r:
            l.append(x['trait_efo'])
        table = Browse_TraitTable(EFOTrait.objects.filter(id__in=l), order_by="label")
        context = {
            'table': table,
            'data_chart': traits_chart_data(),
            'has_chart': 1
        }
    elif view_selection == 'studies':
        context['view_name'] = 'Publications'
        table = Browse_PublicationTable(Publication.objects.all(), order_by="num")
        context['table'] = table
    elif view_selection == 'sample_set':
        context['view_name'] = 'Sample Sets'
        table = Browse_SampleSetTable(Sample.objects.filter(sampleset__isnull=False))
        context['table'] = table
    elif view_selection == 'cohorts':
        context['view_name'] = 'Cohorts'
        table = Browse_CohortTable(Cohort.objects.all(), order_by="name_short")
        context['table'] = table
    else:
        context['view_name'] = 'Polygenic Scores'
        table = Browse_ScoreTable(Score.objects.all(), order_by="num")
        context['table'] = table

    context['has_table'] = 1

    return render(request, 'catalog/browseby.html', context)


def pgs(request, pgs_id):
    try:
        score = Score.objects.get(id__exact=pgs_id)
    except Score.DoesNotExist:
        raise Http404("Polygenic Score (PGS): \"{}\" does not exist".format(pgs_id))

    pub = score.publication
    citation = format_html(' '.join([pub.firstauthor, '<i>et al. %s</i>'%pub.journal, '(%s)' % pub.date_publication.strftime('%Y')]))
    citation = format_html('<a target="_blank" href=https://doi.org/{}>{}</a>', pub.doi, citation)
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
    pquery = Performance.objects.filter(score=score)
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
        pub = Publication.objects.get(id__exact=pub_id)
    except Publication.DoesNotExist:
        raise Http404("Publication: \"{}\" does not exist".format(pub_id))
    context = {
        'publication' : pub,
        'performance_disclaimer': performance_disclaimer(),
        'has_table': 1
    }

    #Display scores that were developed by this publication
    related_scores = Score.objects.filter(publication=pub)
    if related_scores.count() > 0:
        table = Browse_ScoreTable(related_scores)
        context['table_scores'] = table

    #Get PGS evaluated by the PGP
    pquery = Performance.objects.filter(publication=pub)

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
        trait = EFOTrait.objects.get(id__exact=efo_id)
    except EFOTrait.DoesNotExist:
        raise Http404("Trait: \"{}\" does not exist".format(efo_id))

    related_scores = Score.objects.filter(trait_efo=efo_id)
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
    pquery = Performance.objects.filter(score__in=related_scores)
    table = PerformanceTable_PubTrait(pquery)
    context['table_performance'] = table

    pquery_samples = set()
    for q in pquery:
        for sample in q.samples():
            pquery_samples.add(sample)

    table = SampleTable_performance(pquery_samples)
    context['table_performance_samples'] = table

    return render(request, 'catalog/efo.html', context)


def gwas_gcst(request, gcst_id):
    try:
        samples = Sample.objects.filter(source_GWAS_catalog__exact=gcst_id).distinct()
    except Sample.DoesNotExist:
        raise Http404("PGS Sample with the NHGRI-GWAS Catalog ID: \"{}\" does not exist".format(gcst_id))

    related_scores = Score.objects.filter(samples_variants__in=samples).distinct()

    context = {
        'gwas_id': gcst_id,
        'table_scores' : Browse_ScoreTable(related_scores),
        'table_samples' : SampleTable_variants_details(samples),
        'has_table': 1
    }

    return render(request, 'catalog/gwas_gcst.html', context)


def pss(request, pss_id):
    try:
        sample_set = SampleSet.objects.get(id__exact=pss_id)
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


def cohort(request, cohort_short_name, cohort_id):
    try:
        cohort = Cohort.objects.get(id=cohort_id,name_short=cohort_short_name)
    except Cohort.DoesNotExist:
        raise Http404("Cohort: \"{}\" with the id \"{}\" does not exist".format(cohort_short_name,cohort_id))

    context = {
        'cohort': cohort,
        'has_table': 1
    }

    samples = Sample.objects.filter(cohorts__in=[cohort])
    context['table_samples'] = SampleTable_performance(samples)

    # PGS sources
    scores_eval = Score.objects.filter(samples_variants__in=samples)
    if len(scores_eval) > 0:
        context['table_scores_eval'] = Browse_ScoreTable(scores_eval)

    # PGS training
    scores_training = Score.objects.filter(samples_training__in=samples)
    if len(scores_training) > 0:
        context['table_scores_training'] = Browse_ScoreTable(scores_training)

    # PGS performance
    sample_sets = SampleSet.objects.filter(samples__in=samples)
    perfs = Performance.objects.filter(sampleset__in=sample_sets)
    score_perfs_dict = {}
    for perf in perfs:
        score_perfs_dict[perf.score] = 1
    scores_perf = list(score_perfs_dict.keys())
    if len(scores_perf) > 0:
        context['table_scores_perf'] = Browse_ScoreTable(scores_perf)

    return render(request, 'catalog/cohort.html', context)


def releases(request):
    releases_list = Release.objects.order_by('-date')

    # TEST - start #
    import datetime
    from random import randrange

    month = 1
    day = 5
    year = 2019

    release_data = []

    total_score = 0
    total_perf = 0
    total_publi = 0

    for test in range(0,20):
        score = randrange(10)
        perf = randrange(10)
        publi = randrange(10)
        date = datetime.datetime(year,month,day)

        if (test%2):
            month += 1
        day += 1

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
    # TEST - end #

    context = {
        'releases_list': releases_list,
        'releases_data': release_data,
        'has_table': 1,
        'has_chart': 1

    }
    return render(request, 'catalog/releases.html', context)

class AboutView(TemplateView):
    template_name = "catalog/about.html"

class DocsView(TemplateView):
    template_name = "catalog/docs.html"

class DownloadView(TemplateView):
    template_name = "catalog/download.html"
