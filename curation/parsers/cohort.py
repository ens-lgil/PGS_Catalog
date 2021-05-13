from curation.parsers.generic import GenericData
from catalog.models import Cohort

class CohortData(GenericData):

    def __init__(self,name,name_long):
        GenericData.__init__(self)
        self.name = name.strip()
        self.name_long = name_long.strip()
        self.cohort_tuple = (self.name,self.name_long)

    def check_cohort(self):
        try:
            cohort = Cohort.objects.get(name_short__iexact=self.name, name_full__iexact=self.name_long)
            self.model = cohort
            print(f'Cohort {self.name} found in the DB')
        except Cohort.DoesNotExist:
            self.model = None
            try:
                cohort = Cohort.objects.get(name_short__iexact=self.name)
                print(f'A existing cohort has been found in the DB with the ID {self.name}. However the long name differs.')
            except Cohort.DoesNotExist:
                self.model = None

    def create_cohort_model(self):
        self.model, created = Cohort.objects.get_or_create(
                        name_short=self.name, name_full=self.name_long
                    )
        self.model.save()
        return self.model
