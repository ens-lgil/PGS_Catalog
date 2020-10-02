import re, math
from django.http import Http404
from django.shortcuts import render,redirect
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.conf import settings
from django.db.models import Prefetch
from .models import *
from .tables import *
from catalog.models import Score, EFOTrait


bm_db = 'benchmark'

pgs_prefetch = {
    'trait': Prefetch('trait_efo', queryset=EFOTrait.objects.only('id','label').all()),
}

def benchmark_data(efotrait):

    global bm_db

    chart_data = {
        'cohorts' : [],
        'pgs_ids': {},
        'ancestries': {},
        'sexes': {},
        'data': {}
    }

    #metric_to_exp = ['Hazard Ratio', 'Odds Ratio']

    # Performances
    performances = BM_Performance.objects.using(bm_db).select_related('sample','cohort','efotrait').filter(efotrait=efotrait).prefetch_related('performance_metric')

    for performance in performances:
        cohort_name = performance.cohort.name_short
        pgs_id = performance.score_id
        ancestry = performance.sample.ancestry_broad
        sex = performance.sample.sample_sex

        # Cohorts
        if not cohort_name in chart_data['cohorts']:
            chart_data['cohorts'].append(cohort_name)

        # PGS IDs
        chart_data = add_global_data(chart_data, cohort_name, pgs_id, 'pgs_ids')

        # Ancestries
        chart_data = add_global_data(chart_data, cohort_name, ancestry, 'ancestries')

        # Sex types
        chart_data = add_global_data(chart_data, cohort_name, sex, 'sexes')

        # Main data (metric)
        if not cohort_name in chart_data['data']:
            chart_data['data'][cohort_name] = {}

        #print(cohort_name+" - "+ancestry+" - "+sex+" - "+pgs_id)

        for metric in performance.performance_metric.all():
            metric_name = metric.name
            estimate = metric.estimate
            ci = metric.ci
            lower_e = upper_e = None
            if ci:
                pattern = re.compile("^\[(.+),\s(.+)\]$")
                m = re.match(pattern,str(ci))
                lower_e = float(m.group(1))
                upper_e = float(m.group(2))

            if not metric_name in chart_data['data'][cohort_name]:
                chart_data['data'][cohort_name][metric_name] = {}
            if not sex in chart_data['data'][cohort_name][metric_name]:
                chart_data['data'][cohort_name][metric_name][sex] = []

            #if metric_name in metric_to_exp:
            #    estimate = data2exp(estimate)
            #    if lower_e and upper_e:
            #        lower_e = data2exp(lower_e)
            #        upper_e = data2exp(upper_e)

            entry = {
                'pgs': pgs_id,
                'grpName': ancestry,
                'y': estimate
            }
            if lower_e and upper_e:
                entry['eb'] = lower_e
                entry['et'] = upper_e
            chart_data['data'][cohort_name][metric_name][sex].append(entry)

    return chart_data


def add_global_data(data, cohort_name, entry_name, data_type):
    if not cohort_name in data[data_type]:
        data[data_type][cohort_name] = [entry_name]
    elif not entry_name in data[data_type][cohort_name]:
        data[data_type][cohort_name].append(entry_name)

    return data

#def data2exp(value):
#    return round(math.exp(float(value)), 4)


def bm_index(request):
    context = {}

    bm_traits = BM_EFOTrait.objects.using('benchmark').all().prefetch_related('efotrait_performance', 'efotrait_performance__cohort', 'efotrait_performance__sample');

    #for bm_trait in bm_traits:
    #    print("TRAIT: "+bm_trait.id)
    #    bm_perfs = BM_Performance.objects.using("benchmark").filter(efotrait=bm_trait).order_by('id')
    #    print(str(bm_perfs))

    table_bms = BM_Browse_Benchmarking(bm_traits)
    context = {
        'table_bm': table_bms,
        'has_table': 1,
        'is_benchmark': 1
    }
    return render(request, 'benchmark/index.html', context)


def benchmark(request, trait_id):

    efotrait = BM_EFOTrait.objects.using('benchmark').prefetch_related('phenotype_structured').get(id=trait_id)

    pgs_data = benchmark_data(efotrait)

    scores = set()

    cohorts = pgs_data['pgs_ids'].keys()
    for cohort in cohorts:
        for score in pgs_data['pgs_ids'][cohort]:
            scores.add(score)

    score_only_attributes = ['id','name','publication','trait_efo','trait_reported','variants_number','publication__id','publication__date_publication','publication__journal','publication__firstauthor']
    table_scores = BM_Browse_ScoreTable(Score.objects.only(*score_only_attributes).select_related('publication').filter(id__in=list(scores)).prefetch_related(pgs_prefetch['trait']), order_by="num")


    bm_cohorts = BM_Cohort.objects.using('benchmark').filter(name_short__in=cohorts).prefetch_related('cohort_sample').distinct()

    cohort_data = {}
    for bm_cohort in bm_cohorts:
        cohort_name = bm_cohort.name_short
        if not cohort_name in cohort_data:
            table_samples = BM_SampleTable(bm_cohort.cohort_sample.all())
            cohort_data[cohort_name] = {
                'table': table_samples,
                'name': bm_cohort.name_full
            }
    context = {
        'trait': efotrait,
        'pgs_data': pgs_data,
        'table_scores': table_scores,
        'cohorts': cohort_data,
        'has_table': 1,
        'has_chart': 1,
        'is_benchmark': 1
    }
    return render(request, 'benchmark/benchmark.html', context)
