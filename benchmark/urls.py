from django.urls import path
from django.views.generic.base import TemplateView

from . import views

urlpatterns = [
    # ex: /test/EFO_0005842/
    path('benchmark/', views.bm_index, name='Benchmark'),
    path('benchmark/<str:trait_id>/', views.benchmark, name='Benchmark')
]
