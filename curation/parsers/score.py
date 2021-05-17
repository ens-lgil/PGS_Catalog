from curation.parsers.generic import GenericData
from catalog.models import Score, EFOTrait


class ScoreData(GenericData):

    def __init__(self,score_name):
        GenericData.__init__(self)
        self.name = score_name
        self.data = {'name': score_name}


    def create_score_model(self,publication):
        self.model = Score()
        self.model.set_score_ids(self.next_id_number(Score))
        for field, val in self.data.items():
            if field == 'trait_efo':
                efo_traits = []
                for trait_id in val:
                    trait_id = trait_id.replace(':','_')
                    try:
                        efo = EFOTrait.objects.get(id__iexact=trait_id)
                    except EFOTrait.DoesNotExist:
                        efo = EFOTrait(id=trait_id)
                        efo.parse_api()
                        efo.save()
                    efo_traits.append(efo)
            else:
                setattr(self.model, field, val)
        # Associate a Publication
        self.model.publication = publication
        self.model.save()

        for efo in efo_traits:
            self.model.trait_efo.add(efo)
        self.model.save()

        return self.model