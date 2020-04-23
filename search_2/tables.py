import django_tables2 as tables
#from django.conf import settings
from django.utils.html import format_html
from .documents.score import ScoreDocument
#from django.utils.crypto import get_random_string

relative_path = '../..'
publication_path = relative_path+'/publication'
trait_path = relative_path+'/trait'

#class Column_joinlist(tables.Column):
#    def render(self, value):
#        values = smaller_in_bracket('<br/>'.join(value))
#        return format_html(values)

#class Column_shorten_text_content(tables.Column):
#    def render(self, value):
#        return format_html('<span class="more">'+value+'</span>')

#class Column_format_html(tables.Column):
#    def render(self, value):
#        return format_html(value)


class ScoreResultTable(tables.Table):
    '''Table to browse Scores (PGS) results in the PGS Catalog'''
    #list_traits = tables.Column(accessor='list_traits', verbose_name='Mapped Trait(s)\n(Ontology)', orderable=False)
    #ftp_link = tables.Column(accessor='link_filename', verbose_name=format_html('PGS Scoring File (FTP Link)'), orderable=False)

    relative_path = '../..'

    class Meta(object):
        model = ScoreDocument
        attrs = {
            "data-show-columns" : "true",
            "data-sort-name" : "id",
            "data-page-size" : "50"
        }
        fields = [
            'id',
            'name',
            'publication',
        ]
        template_name = 'search/pgs_catalog_django_table.html'

    #def render_id(self, value):
    #    global relative_path
    #    return format_html('<a href='+self.relative_path+'/pgs/{}>{}</a>', value, value)

    #def render_publication(self, value):
    #    citation = format_html(' '.join([value.id, '<br/><small><i class="fa fa-angle-double-right"></i>', value.firstauthor, '<i>et al.</i>', value.journal, '(%s)'%value.date_publication.strftime('%Y'), '</small>']))
    #    return format_html('<a href="'+publication_path+'/{}">{}</a>', value.id, citation)

    #def render_list_traits(self, value):
    #    l = []
    #    for x in value:
    #        l.append('<a href=../../trait/{}>{}</a>'.format(x[0], x[1]))
    #    return format_html('<br>'.join(l))

    #def render_ftp_link(self, value):
    #    id = value.split('.')[0]
    #    ftp_link = settings.USEFUL_URLS['PGS_FTP_ROOT']+'/scores/{}/ScoringFiles/{}'.format(id, value)
    #    return format_html('<a class="pgs_no_icon_link file_link" href="{}" title="Download PGS Scoring File (variants, weights)" download><i class="fa fa-file-text"></i></a><span class="only_export">{}</span>', ftp_link, ftp_link)

    #def render_variants_number(self, value):
    #    return '{:,}'.format(value)
