import re
from psycopg2.extras import NumericRange
from curation.parsers.generic import GenericData
from curation.parsers.demographic import DemographicData
from catalog.models import Sample

class SampleData(GenericData):

    # def __init__(self):
    #     self.sample = None


    # def get_demographic(self, field, val):
    #     demographic_val = self.str2demographic(field,val)
    #     self.add_data(field, demographic_val)


    def str2demographic(self, field, val, spreadsheet_name):
        unit_regex = "([-+]?\d*\.\d+|\d+) ([a-zA-Z]+)"
        current_demographic = DemographicData(field,val)
        if type(val) == float:
            current_demographic.add_data('estimate', val)
        else:
            # Split by ; in case of multiple sub-fields
            l = val.split(';')
            for x in l:
                values = x.split('=')
                if len(values) == 2:
                    name = values[0].strip()
                    value = values[1].strip()
                else:
                    prefix_msg = f'Wrong format in the column \'{field}\''
                    if len(values) > 2:
                        prefix_msg = f'Too many values in the column \'{field}\''
                    self.report_error(spreadsheet_name, f'{prefix_msg}. Format expected: \'name=value_or_interval unit\' (e.g. median=5.2 years).')
                    continue

                # Check if it contains a range item
                matches = self.insquarebrackets.findall(value)
                if len(matches) == 1:
                    if re.search(self.interval_format, matches[0]):
                        range_match = tuple(map(float, matches[0].split(' - ')))
                        current_demographic.add_data('range', NumericRange(lower=range_match[0], upper=range_match[1], bounds='[]'))
                    else:
                        self.report_error(spreadsheet_name, f'Data Range for the value "{value}" is not in the expected format (e.g. \'1.00 [0.80 - 1.20]\')')
                    current_demographic.add_data('range_type', name)
                else:
                    if name.lower().startswith('m'):
                        current_demographic.add_data('estimate_type', name)
                        with_units = re.match(unit_regex, value, re.I)
                        if with_units:
                            items = with_units.groups()
                            estimate = items[0]
                            current_demographic.add_data('unit', items[1])
                        else:
                            estimate = value
                        current_demographic.add_data('estimate', estimate)

                    elif name.lower().startswith('s'):
                        current_demographic.add_data('variability_type', name)
                        with_units = re.match(unit_regex, value, re.I)
                        if with_units:
                            items = with_units.groups()
                            variability = items[0]
                            current_demographic.add_data('unit', items[1])
                        else:
                            variability = value
                        current_demographic.add_data('variability', variability)
        #print(val, current_demographic)
        return current_demographic

    def sample_model_exist(self):
        sample_data = {}
        for field, val in self.data.items():
            if field not in ['cohorts','sample_age', 'followup_time']:
                sample_data[field] = val
        samples = Sample.objects.filter(**sample_data)
        if len(samples) != 0:
            return True
        else: 
            return False

    # def sample_model_exist(self):
    #     sample_data = {}
    #     for field, val in self.data.items():
    #         if field not in ['cohorts','sample_age', 'followup_time']:
    #             sample_data[field] = val
    #     samples = Sample.objects.filter(**sample_data)
    #     matching_sample = None
    #     print(f'# Check sample_model_exist')
    #     if len(samples) != 0:
    #         sample_count = 0
    #         for sample in samples:
    #             sample_count += 1
    #             print(f'+ Sample {sample_count}')
    #             # Check cohorts
    #             if self.data['cohorts']:
    #                 sample_cohorts = [x.name_short for x in sample.cohorts]
    #                 print(f'  > Sample cohorts {sample_cohorts}')
    #                 cohort_match = 0
    #                 for cohort in self.data['cohorts']:
    #                     print(f'  > SampleData: {cohort}')
    #                     if cohort.name in sample_cohorts:
    #                         cohort_match += 1
    #                 if cohort_match != len(self.data['cohorts']):
    #                     continue
    #                 print("Cohorts match!")
    #             # Check sample_age
    #             if self.data['sample_age']:
    #                 print(f'  > Check sample_age')
    #                 if sample.sample_age:
    #                     sample_data_age = self.data['sample_age']
    #                     identical_sample_age = True
    #                     for key, val in sample_data_age.items():
    #                         if sample_data_age[key] != sample.sample_age[key]:
    #                             identical_sample_age = False
    #                             break
    #                     if not identical_sample_age:
    #                         continue
    #                 else:
    #                     continue
    #             # Check followup_time
    #             if self.data['followup_time']:
    #                 print(f'  > Check followup_time')
    #                 if sample.followup_time:
    #                     sample_data_time = self.data['followup_time']
    #                     identical_sample_time = True
    #                     for key, val in sample_data_time.items():
    #                         if sample_data_time[key] != sample.followup_time[key]:
    #                             identical_sample_time = False
    #                             break
    #                     if not identical_sample_time:
    #                         continue
    #                 else:
    #                     continue
    #             print(f'Sample for evaluation already exist: {self.data}')
    #             matching_sample = sample
    #     return matching_sample


    def create_sample_model(self):
        self.model = Sample()
        cohorts = []
        for field, val in self.data.items():
            if field == 'cohorts':
                # Stored as list of CohortData
                for cohort_data in val:
                    cohort = cohort_data.create_cohort_model()
                    cohorts.append(cohort)
            elif field in ['sample_age', 'followup_time']:
                current_demographic = val.create_demographic_model()
                setattr(self.model, field, current_demographic)
            else:
                setattr(self.model, field, val)
        #setattr(self.model, 'id', self.next_id_number(Sample))
        self.model.save()

        # Need to create the Sample object first (with an ID)
        for cohort in cohorts:
            self.model.cohorts.add(cohort)
        self.model.save()

        return self.model