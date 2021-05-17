import re

class GenericData():

    # Needed for parsing confidence intervals
    insquarebrackets = re.compile('\\[([^)]+)\\]')
    interval_format = r'^\-?\d+.?\d*\s\-\s\-?\d+.?\d*$'
    inparentheses = re.compile(r'\((.*)\)')

    def __init__(self):
        self.model = None
        self.data = {}
        self.report = { 'error': {}, 'warning': {} }


    def add_data(self, field, value):
        if type(value) == str:# and not re.match('^\d+\.?\d+$', str(value)):
            value = value.strip()
        self.data[field] = value


    def next_id_number(self, model):
        assigned = 1
        if len(model.objects.all()) != 0:
            assigned = model.objects.latest().pk + 1
        return assigned


    def add_report(self, type, spreadsheet_name, msg):
        """
        Store the reported error/warning.
        - type: type of report (e.g. error, warning)
        - spreadsheet_name: name of the spreadsheet (e.g. Publication Information)
        - msg: error message
        """
        if type in ['error', 'warning']:
            if not spreadsheet_name in self.report[type]:
                self.report[type][spreadsheet_name] = set()
            self.report[type][spreadsheet_name].add(msg)
        else:
            print('ERROR: Can\'t find the report category "{type}"!')


    def report_error(self, spreadsheet_name, msg):
        """
        Store the reported error.
        - spreadsheet_name: name of the spreadsheet (e.g. Publication Information)
        - msg: error message
        """
        self.add_report('error', spreadsheet_name, msg)


    def report_warning(self, spreadsheet_name, msg):
        """
        Store the reported warning.
        - spreadsheet_name: name of the spreadsheet (e.g. Publication Information)
        - msg: warning message
        """
        self.add_report('warning', spreadsheet_name, msg)

