from curation.parsers.generic import GenericData
from catalog.models import Demographic

class DemographicData(GenericData):

    def __init__(self,type,value):
        GenericData.__init__(self)
        self.type = type.strip()
        self.value = value

    def create_demographic_model(self):
        self.model = Demographic(**self.data)
        self.model.save()
        return self.model