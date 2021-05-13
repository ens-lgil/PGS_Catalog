from curation.parsers.generic import GenericData
from catalog.models import Score, Publication, EFOTrait


class ScoreData(GenericData):

    def __init__(self,score_name,publication_doi):
        GenericData.__init__(self)
        self.name = score_name
        self.data = {'name': score_name, 'publication': publication_doi}


    def create_score_model(self):

        self.model = Score()
        self.model.set_score_ids(self.next_id_number(Score))
        for field, val in self.data.items():
            if field == 'publication':
                self.model.publication = Publication.objects.get(doi = val)
            elif field == 'trait_efo':
                efo_traits = []
                for trait_id in val:
                    try:
                        efo = EFOTrait.objects.get(id=trait_id)
                    except EFOTrait.DoesNotExist:
                        efo = EFOTrait(id=trait_id)
                        efo.parse_api()
                        efo.save()
                    efo_traits.append(efo)
            else:
                setattr(self.model, field, val)
        self.model.save()

        for efo in efo_traits:
            self.model.trait_efo.add(efo)
        self.model.save()

        return self.model