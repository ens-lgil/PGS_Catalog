from django.urls import path
from django.views.generic.base import TemplateView

from . import views


urlpatterns = [
    path('', views.index, name='index'),

    # ex: /pgs/PGS000029/
    path('pgs/<str:pgs_id>/', views.pgs, name='PGS'),

    # ex: /publication/PGP000001/
    path('publication/<str:pub_id>/', views.pgp, name='Publication'),

    # ex: /trait/EFO_0000305/
    path('trait/<str:efo_id>/', views.efo, name='Polygenic Trait'),

    # ex: /sampleset/PSS000001/
    path('sampleset/<str:pss_id>/', views.pss, name='Sample Set'),

    # ex: /browse/{scores, traits, studies}/
    path('browse/<str:view_selection>/', views.browseby, name='Browse Scores'),

    # ex: /about/
    path('about/', views.AboutView.as_view(), name='About'),

    # ex: /docs/
    path('docs/', views.DocsView.as_view(), name='Documentation'),

    # ex: /downloads/
    path('downloads/', views.DownloadView.as_view(), name='Downloads'),

    # ex: /docs/
    path('search/', views.search, name='Search'),

    #ex: /template/current
    path('template/current', views.CurrentTemplateView.as_view(), name='Current Curation Template'),

    # Setup URL used to warmup the Django app in the Google App Engine
    path('_ah/warmup', views.warmup, name="Warmup"),

    # Setup robots.txt
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain"))
]

# Debug SQL queries
from django.conf import settings
if settings.DEBUG:
    from django.conf.urls import include, url  # For django versions before 2.0
    from django.urls import include  # For django versions from 2.0 and
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),

        # For django versions before 2.0:
        # url(r'^__debug__/', include(debug_toolbar.urls)),

    ] + urlpatterns
