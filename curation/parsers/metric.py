from curation.parsers.generic import GenericData
from catalog.models import Metric

class MetricData(GenericData):

    # Type of metric
    type_choices = {
        'other' : 'Other Metric',
        'beta'  : 'Effect Size',
        'class' : 'Classification Metric'
    }
    # Metric method
    name_common = {
        'OR': ('Odds Ratio', 'OR'),
        'HR': ('Hazard Ratio', 'HR'),
        'AUROC': ('Area Under the Receiver-Operating Characteristic Curve', 'AUROC'),
        'Cindex': ('Concordance Statistic', 'C-index'),
        'R2': ('Proportion of the variance explained', 'R²'),
    }

    def __init__(self,type,name,value):
        GenericData.__init__(self)
        self.name = name.strip()
        self.type = type.strip()
        self.value = value
        self.data = {'type': self.type_choices[type]}


    def set_names(self):
        if self.name in self.name_common:
            self.add_data('name', self.name_common[self.name][0])
            self.add_data('name_short', self.name_common[self.name][1])
        elif (self.type == 'beta') and (self.name == 'other'):
            self.add_data('name','Beta')
            self.add_data('name_short','β')
        else:
            self.name, self.value = self.value.split('=')
            self.name = self.name.strip()
            self.add_data('name', self.name)
            # if self.name.lower().startswith('beta'):
            #     self.add_data('name_short', 'β')
            # elif self.name.lower().startswith('odds ratio'):
            #     self.add_data('name_short', 'OR')

        if not 'name_short' in self.data and len(self.name) <= 10:
            self.add_data('name_short', self.name)

    
    def create_metric_model(self,performance):
        self.model = Metric(**self.data)
        self.model.performance = performance
        self.model.save()
        return self.model