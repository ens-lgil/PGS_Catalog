import re, math
from django.http import Http404
from django.shortcuts import render,redirect
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.db.models import Prefetch
from .models import *
from .tables import *
from catalog.models import Score, EFOTrait
from catalog.views import ancestry_legend
from catalog import common

bm_db = 'benchmark'

pgs_prefetch = {
    'trait': Prefetch('trait_efo', queryset=EFOTrait.objects.only('id','label').all()),
}

def benchmark_data(efotrait):

    global bm_db

    chart_data = {
        'cohorts' : [],
        'ancestry_groups': [],
        'pgs_ids': {},
        'ancestries': {},
        'sexes': {},
        'data': {}
    }

    cohort_max_sample = {}

    # Number of decimals to round the estimate
    decimals = 3

    #metric_to_exp = ['Hazard Ratio', 'Odds Ratio']

    # Performances
    performances = BM_Performance.objects.using(bm_db).select_related('sample','cohort','efotrait').filter(efotrait=efotrait).prefetch_related('performance_metric')

    for performance in performances:
        cohort_name = performance.cohort.name_short
        pgs_id = performance.score_id
        # Sample data
        sample = performance.sample
        sample_number = sample.sample_number
        sample_cases = sample.sample_cases
        sample_cases_percent =  sample.sample_cases_percent
        sample_controls = sample.sample_controls
        ancestry = sample.ancestry_broad
        sex = sample.sample_sex

        # Cohorts
        if not cohort_name in chart_data['cohorts']:
            chart_data['cohorts'].append(cohort_name)

        # Ancestry groups
        if not ancestry in chart_data['ancestry_groups']:
            chart_data['ancestry_groups'].append(ancestry)

        # Sample numbers
        if not cohort_name in cohort_max_sample:
            cohort_max_sample[cohort_name] = {}
        if not ancestry in cohort_max_sample[cohort_name]:
            cohort_max_sample[cohort_name][ancestry] = {}
        if not 'num' in cohort_max_sample[cohort_name][ancestry]:
            cohort_max_sample[cohort_name][ancestry]['num'] = sample_number
        if cohort_max_sample[cohort_name][ancestry]['num'] <= sample_number:
            cohort_max_sample[cohort_name][ancestry]['num'] = sample_number
            cohort_max_sample[cohort_name][ancestry]['display'] = sample.display_samples_for_table(True)

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
                'anc': ancestry,
                'y': round(estimate, decimals)
            }

            if lower_e and upper_e:
                entry['eb'] = round(lower_e, decimals)
                entry['et'] = round(upper_e, decimals)

            # Sample
            for key in ['s_num','s_cases','s_cases_p','s_ctrls']:
                entry[key] = ''
            entry['s_num'] = f'{sample_number:,}'
            if sample_cases:
                entry['s_cases'] = f'{sample_cases:,}'
            if sample_cases_percent:
                entry['s_cases_p'] = sample_cases_percent
            if sample_controls:
                entry['s_ctrls'] = f'{sample_controls:,}'

            chart_data['data'][cohort_name][metric_name][sex].append(entry)

    # Sort ancestry_groups
    chart_data['ancestry_groups'] = sort_ancestries(chart_data['ancestry_groups'])

    # Sort each cohort ancestries
    for cohort in chart_data['ancestries']:
        chart_data['ancestries'][cohort] = sort_ancestries(chart_data['ancestries'][cohort])

    # Prepare the data for the Cohort(s) display
    cohort_ancestry_sample = {}
    for cohort in cohort_max_sample:
        if not cohort in cohort_ancestry_sample:
            cohort_ancestry_sample[cohort] = []
            #c_ancestries = sorted(cohort_max_sample[cohort].keys())
            c_ancestries = sort_ancestries(cohort_max_sample[cohort].keys())
            for ancestry in c_ancestries:
                entry = {'name': ancestry, 'display': cohort_max_sample[cohort][ancestry]['display']}
                cohort_ancestry_sample[cohort].append(entry)

    return chart_data, cohort_ancestry_sample


def sort_ancestries(ancestry_list):
    ancestry_list = sorted(ancestry_list)
    eu_ancestry = 'European'
    aa_ancestry = 'African'
    if eu_ancestry in ancestry_list:
        ancestry_list.remove(eu_ancestry)
        ancestry_list.insert(0,eu_ancestry)
    if aa_ancestry in ancestry_list:
        ancestry_list.remove(aa_ancestry)
        ancestry_list.append(aa_ancestry)
    return ancestry_list


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

    pgs_data, cohort_max_sample = benchmark_data(efotrait)

    # Benchmark data table
    data_list = []
    row_id = 0
    for cohort in pgs_data['data'].keys():
        for metric_name in pgs_data['data'][cohort].keys():
            for sex in pgs_data['data'][cohort][metric_name].keys():
                for entry in pgs_data['data'][cohort][metric_name][sex]:
                    row = {
                        'cohort':cohort,
                        'performance_metric': f"{metric_name}: {entry['y']}",
                        'ancestry': entry['anc'],
                        'sex': sex,
                        'pgs_id': entry['pgs'],
                        'sample_data': display_samples_for_table(entry['s_num'],entry['s_cases'], entry['s_ctrls'],row_id)
                    }
                    row_id += 1
                    data_list.append(row)
    table_data = BM_data(data_list)

    # Scores table
    scores = set()

    cohorts = pgs_data['pgs_ids'].keys()
    for cohort in cohorts:
        for score in pgs_data['pgs_ids'][cohort]:
            scores.add(score)

    score_only_attributes = ['id','name','publication','trait_efo','trait_reported','variants_number','publication__id','publication__date_publication','publication__journal','publication__firstauthor']
    table_scores = BM_Browse_ScoreTable(Score.objects.only(*score_only_attributes).select_related('publication').filter(id__in=list(scores)).prefetch_related(pgs_prefetch['trait']), order_by="num")

    # Cohort table(s)
    bm_cohorts = BM_Cohort.objects.using('benchmark').filter(name_short__in=cohorts).prefetch_related('cohort_sample').distinct()

    cohort_data = {}
    for bm_cohort in bm_cohorts:
        cohort_name = bm_cohort.name_short
        if not cohort_name in cohort_data:
            ancestry_max_sample = cohort_max_sample[cohort_name]
            cohort_data[cohort_name] = {
                'name': bm_cohort.name_full,
                'ancestries': ancestry_max_sample
            }


    context = {
        'trait': efotrait,
        'pgs_data': pgs_data,
        'table_data': table_data,
        'table_scores': table_scores,
        'cohorts': cohort_data,
        'ancestry_legend': ancestry_legend(),
        'has_table': 1,
        'has_chart': 1,
        'is_benchmark': 1
    }
    return render(request, 'benchmark/benchmark.html', context)


def display_samples_for_table(sample_number,sample_cases,sample_controls,row_id):
    div_id = "sample_"+str(row_id)
    sstring = ''
    if sample_cases:
        sstring += f'<div><a class="toggle_table_btn pgs_btn_plus pgs_helptip" id="{div_id}" title="Click to show/hide the details">{sample_number} individuals</a></div>'
        sstring += f'<div class="toggle_list" id="list_{div_id}">'
        sstring += f'<ul>\n<li>{sample_cases} cases</li>\n'
        if sample_controls != None:
            sstring += f'<li>{sample_controls} controls</li>\n'
        sstring += '</ul>'
        sstring += '</div>'
    else:
        sstring += sample_number
    return sstring
