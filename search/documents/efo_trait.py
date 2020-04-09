from django.conf import settings
from django_elasticsearch_dsl import Document, Index, fields
from elasticsearch_dsl import analyzer

from catalog.models import EFOTrait, TraitCategory

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
class EFOTraitDocument(Document):
    """EFOTrait elasticsearch document"""

    id = fields.TextField(attr='id')
    label = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField(analyzer='keyword'),
            'suggest': fields.CompletionField()
        }
    )
    synonyms = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField(analyzer='keyword'),
        }
    )
    mapped_terms = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField(analyzer='keyword'),
        }
    )
    traitcategory_set = fields.ObjectField(
        properties={
            'label': fields.TextField(
                analyzer=html_strip,
                fields={
                    'raw': fields.TextField(analyzer='keyword'),
                    'suggest': fields.CompletionField()
                }
            ),
            'parent': fields.TextField(
                analyzer=html_strip,
                fields={
                    'raw': fields.TextField(analyzer='keyword'),
                }
            )
        }
    )

    class Django(object):
        """Inner nested class Django."""

        model = EFOTrait  # The model associate with this Document
        related_models = [TraitCategory]

    def get_instances_from_related(self, traitcategory_instance):
        return traitcategory_instance.efo_traits.all()
