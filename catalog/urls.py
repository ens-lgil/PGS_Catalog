import django
from django.urls import path

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

    # ex: /cohort/1/
    path('cohort/<str:cohort_short_name>_<str:cohort_id>/', views.cohort, name='Cohort'),

    # ex: /gwas/GCST001937/
    path('gwas/<str:gcst_id>/', views.gwas_gcst, name='NHGRI-GWAS Catalog Study'),

    # ex: /browse/{scores, traits, studies}/
    path('browse/<str:view_selection>/', views.browseby, name='Browse Scores'),

    # ex: /about/
    path('about/', views.AboutView.as_view(), name='About'),

    # ex: /docs/
    path('docs/', views.DocsView.as_view(), name='Documentation'),

    # ex: /releases/
    path('releases/', views.releases, name='Releases'),

    # ex: /downloads/
    path('downloads/', views.DownloadView.as_view(), name='Downloads'),

    # Test charts
    path('charts/', views.charts, name='Charts tests'),
]
