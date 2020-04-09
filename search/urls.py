#from rest_framework.routers import SimpleRouter
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from .views import *

app_name = 'search'

#router = SimpleRouter()
#router.register(
#    prefix=r'',
#    base_name='search',
#    viewset=EFOTraitViewSet
#)


router = DefaultRouter()
books = router.register(r'efotraits',
                        EFOTraitDocumentView,
                        basename='efotraitdocument')

#urlpatterns = router.urls
urlpatterns = [
    url(r'^', include(router.urls)),
]
