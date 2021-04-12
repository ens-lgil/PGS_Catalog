from django.utils.html import format_html
from pgs_web import constants


def individuals_format(value, use_icon=None):
    html = '{:,} individuals'.format(value)
    if use_icon:
        html = f'<i class="fa fa-user"></i> {html}'
    return format_html(html)
