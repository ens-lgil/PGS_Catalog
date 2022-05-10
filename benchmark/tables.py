import django_tables2 as tables
from django.conf import settings
from django.utils.html import format_html
from .models import *
from catalog.tables import Browse_ScoreTable


page_size = "50"

class Column_format_html(tables.Column):
    def render(self, value):
        return format_html(value)

class Column_sample_merged(tables.Column):
    def render(self, value):
        return format_html(value)

class Column_cohorts(tables.Column):
    def render(self, value):
        qdict = {}
        qlist = []
        for c in value:
            r = format_html('<span title="{}" class="pgs_helptip">{}</span>', c.name_full, c.name_short)
            qdict[c.name_short] = r
        for k in sorted (qdict):
            qlist.append(qdict[k])
        if len(qlist) > 5:
            div_id = get_random_string(10)
            html_list = '<a class="toggle_table_btn pgs_btn_plus" id="'+div_id+'" title="Click to expand/collapse the list">'+str(len(qlist))+' cohorts</a>'
            html_list = html_list+'<div class="toggle_list" id="list_'+div_id+'">'
            html_list = html_list+"<ul><li>"+'</li><li><span class="only_export">,</span>'.join(qlist)+'</li></ul></div>'
            return format_html(html_list)
        else:
            return format_html(', '.join(qlist))

class Column_ancestries(tables.Column):
    def render(self, value):
        vlist = []
        for val in sorted (value):
            vlist.append(val)
        if len(vlist) > 5:
            div_id = get_random_string(10)
            html_list = '<a class="toggle_table_btn pgs_btn_plus" id="'+div_id+'" title="Click to expand/collapse the list">'+str(len(vlist))+' ancestries</a>'
            html_list = html_list+'<div class="toggle_list" id="list_'+div_id+'">'
            html_list = html_list+"<ul><li>"+'</li><li><span class="only_export">,</span>'.join(vlist)+'</li></ul></div>'
            return format_html(html_list)
        else:
            return format_html(', '.join(vlist))


class BM_SampleTable(tables.Table):
    '''Table on PGS page - displays information about the GWAS samples used'''
    ancestry_broad = tables.Column(accessor='ancestry_broad', verbose_name='Ancestry', orderable=False)
    sample_sex = tables.Column(accessor='sample_sex', verbose_name='Sex', orderable=False)
    sample_merged = Column_sample_merged(accessor='display_samples_for_table', verbose_name='Sample Numbers', orderable=False)
    #sources = Column_joinlist(accessor='display_sources', verbose_name='Study Identifiers', orderable=False)
    #sample_ancestry = Column_ancestry(accessor='display_ancestry', verbose_name='Sample Ancestry', orderable=False)

    class Meta:
        model = BM_Sample
        attrs = {
            "data-show-columns" : "false",
            "data-export-options" : '{"fileName": "pgs_cohort_sample_data"}',
            "data-sort-name" : "ancestry_broad",
            'data-search' : "false",
            'data-filter-control': "false",
            'data-show-export' : "false"
        }
        fields = [
            'ancestry_broad', 'sample_sex', 'sample_merged'
        ]
        template_name = 'catalog/pgs_catalog_django_table.html'


    def render_sources(self, value):
        l = []
        if 'GCST' in value:
            l.append('GWAS Catalog: <a href="https://www.ebi.ac.uk/gwas/studies/{}">{}</a>'.format(value['GCST'], value['GCST']))
        if 'PMID' in value and value['PMID']:
            l.append('EuropePMC: <a href="https://europepmc.org/search?query={}">{}</a>'.format(value['PMID'], value['PMID']))
        return format_html('<br>'.join(l))


class BM_Browse_ScoreTable(Browse_ScoreTable):
    class Meta:
        attrs = {
            "id": "bm_scores_table",
            "data-show-columns" : "false",
            "data-sort-name" : "id",
            "data-page-size" : page_size,
            "data-export-options" : '{"fileName": "pgs_scores_data"}',
            'data-search' : "false",
            'data-filter-control': "false"
        }
        fields = [
            'id',
            'publication',
            'trait_reported',
            'trait_efo',
            'variants_number',
            'ancestries',
            'ftp_link'
        ]
        template_name = 'catalog/pgs_catalog_django_table.html'


class BM_Browse_Benchmarking(tables.Table):
    '''Table on PGS page - displays information about the GWAS samples used'''
    label_link = Column_format_html(accessor='display_label', verbose_name='Ontology Trait Label', orderable=True)
    id = tables.Column(accessor='id', verbose_name='Ontology Trait ID', orderable=False)
    scores = tables.Column(accessor='count_scores', verbose_name='Polygenic Score(s)', orderable=False)
    cohorts = Column_cohorts(accessor='cohorts_list', verbose_name='Cohort(s)', orderable=False)
    ancestries = Column_ancestries(accessor='ancestries_list', verbose_name='Ancestry Group(s)', orderable=False)
    #sources = Column_joinlist(accessor='display_sources', verbose_name='Study Identifiers', orderable=False)
    #sample_ancestry = Column_ancestry(accessor='display_ancestry', verbose_name='Sample Ancestry', orderable=False)

    class Meta:
        model = BM_EFOTrait
        attrs = {
            "data-show-columns" : "false",
            "data-export-options" : '{"fileName": "pgs_benchmark_data"}',
            'data-search' : "true",
            "data-page-size" : page_size,
            "data-sort-name" : "display_label",
            'data-filter-control': "true",
            'data-show-export' : "true"
        }
        fields = [
            'label_link', 'id', 'scores', 'cohorts', 'ancestries'
        ]
        template_name = 'catalog/pgs_catalog_django_table.html'


class BM_data(tables.Table):
    pgs_id = tables.Column(accessor='pgs_id', verbose_name='PGS ID', orderable=True)
    cohort = tables.Column(accessor='cohort', verbose_name='Cohort', orderable=True)
    ancestry = tables.Column(accessor='ancestry', verbose_name='Ancestry', orderable=True)
    sex = tables.Column(accessor='sex', verbose_name='Sex', orderable=True)
    performance_metric = tables.Column(accessor='performance_metric', verbose_name='Performance Metric', orderable=False)
    sample_data = Column_format_html(accessor='sample_data', verbose_name='Sample Numbers', orderable=True)

    class Meta:
        attrs = {
            "data-export-options" : '{"fileName": "pgs_benchmark_table_data"}',
            'data-search' : "true",
            "data-page-size" : page_size,
            "data-sort-name" : "pgs_id",
            'data-filter-control': "true",
            'data-show-export' : "true"
        }
        fields = [
            'pgs_id', 'cohort', 'ancestry', 'sex', 'performance_metric','sample_data'
        ]
        template_name = 'catalog/pgs_catalog_django_table.html'

    def render_pgs_id(self, value):
        return format_html(f'<a href="/score/{value}">{value}</a>')
