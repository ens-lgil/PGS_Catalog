import re

class GenericData():

    # Needed for parsing confidence intervals
    insquarebrackets = re.compile('\\[([^)]+)\\]')
    interval_format = r'^\-?\d+.?\d*\s\-\s\-?\d+.?\d*$'
    inparentheses = re.compile(r'\((.*)\)')

    def __init__(self):
        self.model = None
        self.data = {}

    def add_data(self, field, value):
        if type(value) == str:# and not re.match('^\d+\.?\d+$', str(value)):
            value = value.strip()
        self.data[field] = value

    def next_id_number(self, model):
        assigned = 1
        if len(model.objects.all()) != 0:
            assigned = model.objects.latest().pk + 1
        return assigned
