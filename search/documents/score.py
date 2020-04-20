from django.conf import settings
from django_elasticsearch_dsl import Document, Index, fields
from elasticsearch_dsl import analyzer

from catalog.models import Score, Publication, EFOTrait

# Name of the Elasticsearch index
INDEX = Index(settings.ELASTICSEARCH_INDEX_NAMES[__name__])

# See Elasticsearch Indices API reference for available settings
INDEX.settings(
    number_of_shards=1,
    number_of_replicas=1
)

html_strip = analyzer(
    'html_strip',
    tokenizer="standard",
    filter=["lowercase", "stop", "snowball"],
    char_filter=["html_strip"]
)

@INDEX.doc_type
class ScoreDocument(Document):
    """Score elasticsearch document"""

    id = fields.TextField(attr='id')
    name = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField(analyzer='keyword'),
        }
    )
    variants_number = fields.IntegerField()
    publication = fields.ObjectField(
        properties={
            'title': fields.TextField(
                analyzer=html_strip,
                fields={
                    'raw': fields.TextField(analyzer='keyword'),
                }
            ),
            'PMID': fields.IntegerField(),
            'firstauthor': fields.TextField(
                analyzer=html_strip,
                fields={
                    'raw': fields.TextField(analyzer='keyword'),
                }
            ),
            'authors': fields.TextField(
                analyzer=html_strip,
                fields={
                    'raw': fields.TextField(analyzer='keyword'),
                }
            ),
            'doi': fields.TextField(
                analyzer=html_strip,
                fields={
                    'raw': fields.TextField(analyzer='keyword'),
                }
            )
        }
    )
    trait_efo = fields.ObjectField(
        properties={
            'id': fields.TextField(attr='id'),
            'label': fields.TextField(
                analyzer=html_strip,
                fields={
                    'raw': fields.TextField(analyzer='keyword'),
                }
            ),
            'synonyms': fields.TextField(
                analyzer=html_strip,
                fields={
                    'raw': fields.TextField(analyzer='keyword'),
                }
            ),
            'mapped_terms': fields.TextField(
                analyzer=html_strip,
                fields={
                    'raw': fields.TextField(analyzer='keyword'),
                }
            )
        }
    )

    class Django(object):
        """Inner nested class Django."""

        model = Score  # The model associate with this Document
        related_models = [Publication,EFOTrait]

        def get_instances_from_related(self, publication_instance):
            return publication_instance.publication_score.all()
