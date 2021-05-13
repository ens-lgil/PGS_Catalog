import re
from psycopg2.extras import NumericRange
from curation.parsers.generic import GenericData
from curation.parsers.metric import MetricData
from catalog.models import Performance

class PerformanceData(GenericData):

    def __init__(self,publication_doi):
        GenericData.__init__(self)
        self.data = {'publication': publication_doi, 'metrics': []}


    def add_metric(self, field, val):
        metric = self.str2metric(field, val)
        self.data['metrics'].append(metric)


    def str2metric(self, field, val):
        _, ftype, fname = field.split('_')

        #print(f'ftype: {ftype} | fname: {fname} | _: {_}')

        current_metric = MetricData(ftype,fname,val)
        current_metric.set_names()
        val = current_metric.value

        # Parse out the confidence interval and estimate
        if type(current_metric.value) == float:
            current_metric.add_data('estimate', current_metric.value)
        else:
            # Check if SE is reported
            matches_parentheses = self.inparentheses.findall(val)
            if len(matches_parentheses) == 1:
                val = val.split('(')[0].strip()
                # Check extra character/data after the parenthesis
                extra = val.strip().split(')')
                if len(extra) > 1:
                    print(f'{spread_sheet_name}: Extra information detected after the parenthesis for: {val}')
                try:
                    current_metric.add_data('estimate', float(val))
                except:
                    val, unit = val.split(" ", 1)
                    current_metric.add_data('estimate', float(val))
                    current_metric.add_data('unit', unit)
                current_metric.add_data('se', matches_parentheses[0])
            # Extract interval
            else:
                try:
                    current_metric.add_data('estimate', float(val.split(' [')[0]))
                    # Check extra character/data after the brackets
                    extra = val.strip().split(']')
                    #print(f'{current_metric.data}')
                    if len(extra) > 1:
                        # Check if second part has content
                        if (extra[1] != ''):
                            print(f'{spread_sheet_name}: Extra information detected after the interval for: "{val}"')
                except:
                    #self.report_error(spread_sheet_name,row_id,f'Can\'t extract the estimate value from ({val})')
                    print(f'{spread_sheet_name}: Can\'t extract the estimate value from ({val})')
                    current_metric.add_data('estimate', val)
                
                matches_square = self.insquarebrackets.findall(val)
                if len(matches_square) == 1:
                    if re.search(self.interval_format, matches_square[0]):
                        ci_match = tuple(map(float, matches_square[0].split(' - ')))
                        current_metric.add_data('ci', NumericRange(lower=ci_match[0], upper=ci_match[1], bounds='[]'))
                        min_ci = float(ci_match[0])
                        max_ci = float(ci_match[1])
                        estimate = float(current_metric.data['estimate'])
                        # Check that the estimate is within the interval
                        if not min_ci <= estimate <= max_ci:
                            #self.report_error(spread_sheet_name,f'The estimate value ({estimate}) is not within its the confidence interval [{min_ci} - {max_ci}]')
                            print(f'{spread_sheet_name}: The estimate value ({estimate}) is not within its the confidence interval [{min_ci} - {max_ci}]')
                    else:
                        #self.report_error(spread_sheet_name,f'Confidence interval "{val}" is not in the expected format (e.g. "1.00 [0.80 - 1.20]")')
                        print(f'{spread_sheet_name}: Confidence interval "{val}" is not in the expected format (e.g. "1.00 [0.80 - 1.20]")')
            # Update the value
            current_metric.value = val

        return current_metric


    def create_performance_model(self, publication, score, sampleset):
        self.model = Performance(publication=publication, score=score, sampleset=sampleset)
        self.model.set_performance_id(self.next_id_number(Performance))
        for field, val in self.data.items():
            if field not in ['publication','score','sampleset','metrics']:
                setattr(self.model, field, val)
        self.model.save()
        
        # Create associated Metric objects
        for metric in self.data['metrics']:
            metric.create_metric_model(self.model)