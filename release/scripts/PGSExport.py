import sys, os.path, tarfile
import pandas as pd
import hashlib
from catalog.models import *

class PGSExport:

    #---------------#
    # Configuration #
    #---------------#

    fields_to_include = {
        'EFOTrait':
            [
                'id',
                'label',
                'description',
                'url'
            ],
        'Sample':
            [
                'associated_score',
                'study_stage',
                'sample_number',
                'sample_cases',
                'sample_controls',
                'sample_percent_male',
                'sample_age_formatted',
                'ancestry_broad',
                'ancestry_free',
                'ancestry_country',
                'ancestry_additional',
                'phenotyping_free',
                'followup_time_formatted',
                'source_GWAS_catalog',
                'source_PMID',
                'cohorts_list',
                'cohorts_additional'
            ],
        'SampleSet':
            [
                'id'
            ],
        'Score':
            [
                'id',
                'name',
                'trait_reported',
                'trait_label',
                'trait_id',
                'method_name',
                'method_params',
                'variants_genomebuild',
                'variants_number',
                'variants_interactions',
                'pub_id',
                'pub_pmid_label',
                'pub_doi_label',
                'flag_asis',
                'ftp_scoring_file',
                'license'
            ],
        'Performance':
            [
                'id',
                'score',
                'sampleset',
                'pub_id',
                'phenotyping_reported',
                'covariates',
                'performance_comments',
                'pub_pmid_label',
                'pub_doi_label'
            ],
        'Publication':
            [
                'id',
                'firstauthor',
                'title',
                'journal',
                'date_publication',
                'authors',
                'doi',
                'PMID'
            ]
    }

    extra_fields_to_include = {
        'ftp_scoring_file': 'FTP link',
        'trait_label': 'Mapped Trait(s) (EFO label)',
        'trait_id'   : 'Mapped Trait(s) (EFO ID)',
        'pub_id'         : 'PGS Publication (PGP) ID',
        'pub_pmid_label' : 'Publication (PMID)',
        'pub_doi_label'  : 'Publication (doi)',
        'cohorts_list' : 'Cohort(s)',
        'associated_score' : 'Polygenic Score (PGS) ID',
        'study_stage' : 'Stage of PGS Development',
        'sample_age_formatted' : 'Sample Age',
        'followup_time_formatted': 'Followup Time'
    }

    # Metrics
    other_metric_key = 'Other Metric'
    other_metric_label = other_metric_key+'(s)'
    metrics_type = ['HR','OR','β','AUROC','C-index',other_metric_label]
    metrics_header = {
        'HR': 'Hazard Ratio (HR)',
        'OR': 'Odds Ratio (OR)',
        'β': 'Beta',
        'AUROC': 'Area Under the Receiver-Operating Characteristic Curve (AUROC)',
        'C-index': 'Corcordance Statistic (C-index)',
        other_metric_key: other_metric_label
    }

    def __init__(self,filename):
        self.filename = filename
        self.pgs_list = []
        self.writer   = pd.ExcelWriter(filename, engine='xlsxwriter')
        self.spreadsheets_conf = {
            'scores'     : ('Scores', self.create_scores_spreadsheet),
            'perf'       : ('Performance Metrics', self.create_performance_metrics_spreadsheet),
            'samplesets' : ('Evaluation Sample Sets', self.create_samplesets_spreadsheet),
            'samples_development': ('Score Development Samples', self.create_samples_development_spreadsheet),
            'publications': ('Publications', self.create_publications_spreadsheet),
            'efo_traits': ('EFO Traits', self.create_efo_traits_spreadsheet)
        }
        self.spreadsheets_list = [
            'scores', 'perf', 'samplesets', 'samples_development', 'publications', 'efo_traits'
        ]

    def set_pgs_list(self, pgs_list):
        """ List the PGS IDs used to generate the metadata files """
        if isinstance(pgs_list, list):
            self.pgs_list = pgs_list
        else:
            print('Error: '+str(pgs_list)+" is not a list")


    def save(self):
        """ Close the Pandas Excel writer and output the Excel file """
        self.writer.save()


    def generate_sheets(self, csv_prefix):
        """ Generate the differents sheets """

        if (len(self.spreadsheets_conf.keys()) != len(self.spreadsheets_list)):
            print("Size discrepancies between the dictionary 'spreadsheets' and the list 'spreadsheets_ordering'.")
            exit()
        if (csv_prefix == ''):
            print("CSV prefix, for the individual CSV spreadsheet is empty. Please, provide a prefix!")
            exit()

        for spreadsheet_name in self.spreadsheets_list:
            spreadsheet_label = self.spreadsheets_conf[spreadsheet_name][0]
            try:
                data = self.spreadsheets_conf[spreadsheet_name][1]()
                self.generate_sheet(data, spreadsheet_label)
                print("Spreadsheet '"+spreadsheet_label+"' done")
                self.generate_csv(data, csv_prefix, spreadsheet_label)
                print("CSV '"+spreadsheet_label+"' done")
            except:
                print("Issue to generate the spreadsheet '"+spreadsheet_label+"'")
                exit()


    def generate_sheet(self, data, sheet_name):
        """ Generate the Pandas dataframe and insert it as a spreadsheet into to the Excel file """
        try:
            # Create a Pandas dataframe.
            df = pd.DataFrame(data)
            # Convert the dataframe to an XlsxWriter Excel object.
            df.to_excel(self.writer, index=False, sheet_name=sheet_name)
        except NameError:
            print("Spreadsheet generation: At least one of the variables is not defined")
        except:
            print("Spreadsheet generation: There is an issue with the data of the spreadsheet '"+str(sheet_name)+"'")


    def generate_csv(self, data, prefix, sheet_name):
        """ Generate the Pandas dataframe and create a CSV file """
        try:
            # Create a Pandas dataframe.
            df = pd.DataFrame(data)
            # Convert the dataframe to an XlsxWriter Excel object.
            sheet_name = sheet_name.lower().replace(' ', '_')
            csv_filename = prefix+"_metadata_"+sheet_name+".csv"
            df.to_csv(csv_filename, index=False)
        except NameError:
            print("CSV generation: At least one of the variables is not defined")
        except:
            print("CSV generation: There is an issue with the data of the type '"+str(sheet_name)+"'")


    def generate_tarfile(self, output_filename, source_dir):
        """ Generate a tar.gz file from a directory """
        with tarfile.open(output_filename, "w:gz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))


    def get_column_labels(self, classname, exception_field=None, exception_classname=None):
        """ Fetch the column labels from the Models """
        model_fields = [f.name for f in classname._meta.fields]
        model_labels = {}

        classname_string = classname.__name__

        for field_name in self.fields_to_include[classname_string]:
            label = None
            if field_name in model_fields:
                label = classname._meta.get_field(field_name).verbose_name
            elif exception_field and field_name in exception_field:
                exception_field_name = 'id'
                label = exception_classname._meta.get_field(exception_field_name).verbose_name
            elif field_name in self.extra_fields_to_include:
                label = self.extra_fields_to_include[field_name]
            else:
                print("Error: the field '"+field_name+"' can't be found for the class "+classname_string)

            if label:
                model_labels[field_name] = label
        return model_labels


    def not_in_extra_fields_to_include(self,column):
        if column not in self.extra_fields_to_include.keys():
            return True
        else:
            return False


    def create_md5_checksum(self, md5_filename='md5_checksum.txt', blocksize=4096):
        """ Returns MD5 checksum for the generated file. """

        md5 = hashlib.md5()
        try:
            file = open(self.filename, 'rb')
            with file:
                for block in iter(lambda: file.read(blocksize), b""):
                    md5.update(block)
        except IOError:
            print('File \'' + self.filename + '\' not found!')
            return None
        except:
            print("Error: the script couldn't generate a MD5 checksum for '" + self.filename + "'!")
            return None

        md5file = open(md5_filename, 'w')
        md5file.write(md5.hexdigest())
        md5file.close()
        print("MD5 checksum file '"+md5_filename+"' has been generated.")


    #---------------------#
    # Spreadsheet methods #
    #---------------------#

    def create_scores_spreadsheet(self):
        """ Score spreadsheet """

        # Fetch column labels an initialise data dictionary
        score_labels = self.get_column_labels(Score)
        scores_data = {}
        for label in list(score_labels.values()):
            scores_data[label] = []

        scores = []
        if len(self.pgs_list) == 0:
            scores = Score.objects.all().order_by('id')
        else:
            scores = Score.objects.filter(id__in=self.pgs_list).order_by('id')


        for score in scores:
            # Publication
            scores_data[score_labels['pub_id']].append(score.publication.id)
            scores_data[score_labels['pub_pmid_label']].append(score.publication.PMID)
            scores_data[score_labels['pub_doi_label']].append(score.publication.doi)
            # FTP link
            scores_data[score_labels['ftp_scoring_file']].append(score.ftp_scoring_file)
            # Mapped Traits
            trait_labels = []
            trait_ids = []
            for trait in score.trait_efo.all():
                trait_labels.append(trait.label)
                trait_ids.append(trait.id)
            scores_data[score_labels['trait_label']].append(', '.join(trait_labels))
            scores_data[score_labels['trait_id']].append(', '.join(trait_ids))

            # Load the data into the dictionnary
            # e.g. column is "id":
            # `getattr` generates the perf.score method call
            # The following code is actually run:
            # scores_data[score_labels['id']].append(score.id)
            for column in score_labels.keys():
                if self.not_in_extra_fields_to_include(column):
                    object_method_name = getattr(score, column)
                    scores_data[score_labels[column]].append(object_method_name)

        return scores_data


    def create_performance_metrics_spreadsheet(self, pgs_list=[]):
        """ Performance Metrics spreadsheet """

        metrics_header = self.metrics_header
        metrics_type = self.metrics_type
        other_metric_label = self.other_metric_label

        # Fetch column labels an initialise data dictionary
        score_field = 'score'
        perf_labels = self.get_column_labels(Performance, exception_field=score_field, exception_classname=Score)
        perf_data = {}
        for label in list(perf_labels.values()):
            perf_data[label] = []

        # Addtional fields

        # Metrics
        for m_header in metrics_header:
            full_header = metrics_header[m_header]
            perf_data[full_header]  = []


        performances = []
        if len(self.pgs_list) == 0:
            performances = Performance.objects.all().order_by('id')
        else:
            for pgs_id in self.pgs_list:
                score = Score.objects.get(id__exact=pgs_id)
                score_performances = Performance.objects.filter(score=score)
                for score_perf in score_performances:
                    if score_perf not in performances:
                        performances.append(score_perf)
            performances = list(performances)
            performances.sort(key=lambda x: x.id, reverse=False)

        for perf in performances:
            # Publication
            perf_data[perf_labels['pub_id']].append(perf.publication.id)
            perf_data[perf_labels['pub_pmid_label']].append(perf.publication.PMID)
            perf_data[perf_labels['pub_doi_label']].append(perf.publication.doi)

            # Metrics
            metrics_data = {}
            for m_header in list(metrics_header.values()):
                metrics_data[m_header] = ""
            # Effect sizes
            effect_sizes_list = perf.effect_sizes_list
            if effect_sizes_list:
                for metric in effect_sizes_list:
                    if metric[0][1] in metrics_type:
                        m_header = metrics_header[metric[0][1]]
                        metrics_data[m_header] = metric[1]
            # Classification metrics
            class_acc_list = perf.class_acc_list
            if class_acc_list:
                for metric in class_acc_list:
                    if metric[0][1] in metrics_type:
                        m_header = metrics_header[metric[0][1]]
                        metrics_data[m_header] = metric[1]
            # Other metrics
            othermetrics_list = perf.othermetrics_list
            if othermetrics_list:
                for metric in othermetrics_list:
                    m_data = metric[0][1]+" = "+metric[1]
                    if metrics_data[other_metric_label] == '':
                        metrics_data[other_metric_label] = m_data
                    else:
                        metrics_data[other_metric_label] = metrics_data[other_metric_label]+", "+m_data

            for m_header in list(metrics_header.values()):
                perf_data[m_header].append(metrics_data[m_header])

            # Load the data into the dictionnary
            # e.g. column is "score":
            # `getattr` generates the perf.score method call
            # The following code is actually run:
            # perf_data[perf_labels['score']].append(perf.score)
            for column in perf_labels.keys():
                if self.not_in_extra_fields_to_include(column):
                    # Exception for the score entry
                    if column == score_field:
                        object_method_name = perf.score.id
                    else:
                        object_method_name = getattr(perf, column)

                    perf_data[perf_labels[column]].append(object_method_name)
        return perf_data


    def create_samplesets_spreadsheet(self, pgs_list=[]):
        """ Sample Sets spreadsheet """

        # Fetch column labels an initialise data dictionary
        object_labels = self.get_column_labels(SampleSet)
        object_data = {}
        for label in list(object_labels.values()):
            object_data[label] = []

        # Sample
        sample_object_labels = self.get_column_labels(Sample)
        # Remove the "study_stage" column for this spreadsheet
        del sample_object_labels['study_stage']
        for label in list(sample_object_labels.values()):
            object_data[label] = []


        samplesets = []
        if len(self.pgs_list) == 0:
            samplesets = SampleSet.objects.all().prefetch_related('samples')
        else:
            for pgs_id in self.pgs_list:
                score = Score.objects.get(id__exact=pgs_id)
                score_performances = Performance.objects.filter(score=score)
                for score_perf in score_performances:
                    sampleset = SampleSet.objects.get(id__exact=score_perf.sampleset)
                    if sampleset not in samplesets:
                        samplesets.append(sampleset)

            samplesets = list(samplesets)
            samplesets.sort(key=lambda x: x.id, reverse=False)

        for pss in samplesets:
            performances = Performance.objects.filter(sampleset=pss)
            scores_ids = {}
            for performance in performances:
                scores_ids[performance.score.id] = 1
            scores = ', '.join(scores_ids.keys())
            for sample in pss.samples.all():
                object_data[sample_object_labels['associated_score']].append(scores)
                object_data[sample_object_labels['cohorts_list']].append(', '.join([c.name_short for c in sample.cohorts.all()]))
                object_data[sample_object_labels['sample_age_formatted']].append(self.format_demographic_data(sample.sample_age))
                object_data[sample_object_labels['followup_time_formatted']].append(self.format_demographic_data(sample.followup_time))

                for sample_column in sample_object_labels.keys():
                    if self.not_in_extra_fields_to_include(sample_column):
                        sample_object_method_name = getattr(sample, sample_column)
                        object_data[sample_object_labels[sample_column]].append(sample_object_method_name)

                for column in object_labels.keys():
                    if self.not_in_extra_fields_to_include(column):
                        object_method_name = getattr(pss, column)
                        object_data[object_labels[column]].append(object_method_name)
        return object_data



    def create_samples_development_spreadsheet(self):
        """ Samples used for score development (GWAS and/or training) spreadsheet """

        # Fetch column labels an initialise data dictionary
        object_labels = self.get_column_labels(Sample)
        object_data = {}
        for label in list(object_labels.values()):
            object_data[label] = []

        # Get the relevant scores
        if len(self.pgs_list) == 0:
            scores = Score.objects.all().order_by('id')
        else:
            scores = Score.objects.filter(id__in=self.pgs_list).order_by('id')

        #Loop through Scores to output their samples:
        for score in scores:
            for study_stage, stage_name in [('samples_variants', 'Source of Variant Associations (GWAS)'),
                                            ('samples_training','Score Development/Training')]:
                if study_stage == 'samples_variants':
                    samples = score.samples_variants.all()
                elif study_stage == 'samples_training':
                    samples = score.samples_training.all()

                if len(samples) > 0:
                    for sample in samples:
                        object_data[object_labels['associated_score']].append(score.id)
                        object_data[object_labels['study_stage']].append(stage_name)
                        object_data[object_labels['sample_age_formatted']].append(self.format_demographic_data(sample.sample_age))
                        object_data[object_labels['followup_time_formatted']].append(self.format_demographic_data(sample.followup_time))

                        for column in object_labels.keys():
                            if self.not_in_extra_fields_to_include(column):
                                object_method_name = getattr(sample, column)
                                object_data[object_labels[column]].append(object_method_name)

                        object_data[object_labels['cohorts_list']].append(', '.join([c.name_short for c in sample.cohorts.all()]))

        return object_data


    def create_publications_spreadsheet(self):
        """ Publications spreadsheet """

        # Fetch column labels an initialise data dictionary
        object_labels = self.get_column_labels(Publication)
        object_data = {}
        for label in list(object_labels.values()):
            object_data[label] = []

        publications = []
        if len(self.pgs_list) == 0:
            publications = Publication.objects.all().order_by('id')
        else:
            scores = Score.objects.filter(id__in=self.pgs_list).order_by('id')
            for score in scores:
                # Score publication
                score_publication = score.publication
                if score_publication not in publications:
                    publications.append(score_publication)

                # Performance publication
                score_performances = Performance.objects.filter(score=score)
                for score_perf in score_performances:
                    perf_publication = score_perf.publication
                    if perf_publication not in publications:
                        publications.append(perf_publication)

            publications = list(publications)
            publications.sort(key=lambda x: x.id, reverse=False)

        for publi in publications:

            for column in object_labels.keys():
                if self.not_in_extra_fields_to_include(column):
                    object_method_name = getattr(publi, column)
                    object_data[object_labels[column]].append(object_method_name)

        return object_data


    def create_efo_traits_spreadsheet(self):
        """ EFO traits spreadsheet """

        # Fetch column labels an initialise data dictionary
        object_labels = self.get_column_labels(EFOTrait)
        object_data = {}
        for label in list(object_labels.values()):
            object_data[label] = []

        traits = []
        if len(self.pgs_list) == 0:
            traits = EFOTrait.objects.all().order_by('label')
        else:
            scores = Score.objects.filter(id__in=self.pgs_list).order_by('id')
            for score in scores:
                score_traits = score.trait_efo
                for score_trait in score_traits.all():
                    if score_trait not in traits:
                        traits.append(score_trait)

        for trait in traits:
            for column in object_labels.keys():
                if self.not_in_extra_fields_to_include(column):
                    object_method_name = getattr(trait, column)
                    object_data[object_labels[column]].append(object_method_name)

        return object_data


    def format_demographic_data(self, demographic):
        """ Combine the different elements of the Demographic model within 1 line """
        data = []
        if demographic:
            # Extract and format demographic data
            estimate = demographic.format_estimate()
            if not estimate:
                estimate = demographic.format_range()
            variability = demographic.format_variability()

            # Add formatted data
            if estimate:
                data.append(estimate)
            if variability:
                data.append(variability)
            if data:
                data.append(demographic.format_unit())
        if data:
            return ';'.join(data)
        return ''
