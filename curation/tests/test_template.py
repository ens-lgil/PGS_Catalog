from django.test import TestCase
from curation.tools import *
import os, gzip
import requests
import numpy as np

class TemplateTest(TestCase):
    """ Test the template """

    pgs_template_dir = 'pgs_template_dir'
    if os.environ[pgs_template_dir]:
        root_dir = os.environ[pgs_template_dir]
        if not root_dir.endswith('/'):
            root_dir += '/'
    else:
        print("Please provide an environment variable '"+pgs_template_dir+"'")
        exit(1)

    pgs_study_file = 'pgs_study_file'
    if os.environ[pgs_study_file]:
        study_file = os.environ[pgs_study_file]
    else:
        print("Please provide an environment variable '"+pgs_study_file+"'")
        exit(1)

    loc_curation2schema = root_dir+'templates/TemplateColumns2Models_v5.xlsx'
    curation2schema = pd.read_excel(loc_curation2schema, index_col = 0)

    loc_curation2schema_scoring = root_dir+'templates/ScoringFileSchema.xlsx'
    curation2schema_scoring = pd.read_excel(loc_curation2schema_scoring, index_col = 0)


    #loc_localGWAS = '../pgs_DBSourceFiles/local_GWASCatalog/'
    loc_localGWAS = root_dir+'local_GWASCatalog/'
    #gwas_studies, gwas_samples = load_GWAScatalog(loc_localGWAS, update = True)
    gwas_studies, gwas_samples = load_GWAScatalog(loc_localGWAS, update = False)
    gwas_studies.set_index('STUDY ACCESSION', inplace = True)
    gwas_samples.set_index('STUDY ACCESSION', inplace = True)
    gwas_samples = gwas_samples[gwas_samples['STAGE'] == 'initial'] # Get rid of replication studies

    study = CurationTemplate()

    saved_scores = {}
    testset_to_sampleset = {}
    samples_tested = []
    debug = False #True

    external_id_checked = {
        'DOI'  : {},
        'EFO'  : {},
        'GWAS' : {},
        'PMID' : {}
    }

    def parse_study_template(self):
        self.study.file_loc  = self.study_file
        self.study.read_curation()
        self.study.table_mapschema = self.curation2schema
        self.study.extract_publication()
        self.study.extract_scores()
        self.study.extract_samples(self.gwas_samples)
        self.study.extract_performances()


    def load_study_data(self):
        print("#----------#\n#  Scores  #\n#----------#")
        self.load_scores()
        print("\n#---------------------#\n#  Samples to Scores  #\n#---------------------#")
        self.link_samples_to_scores()
        print("\n#---------------#\n#  Sample Sets  #\n#---------------#")
        self.load_sample_sets()
        print("\n#-----------------------#\n#  Performance Metrics  #\n#-----------------------#")
        self.load_performance_metrics()


    def load_scores(self):
        # Scores
        for score_id, fields in self.study.parsed_scores.items():
            current_score = Score()
            score_db_id = next_scorenumber(Score)
            current_score.set_score_ids(score_db_id)
            for f, val in fields.items():
                if f == 'publication':
                    current_score.publication = Publication.objects.get(id = val)
                elif f == 'trait_efo':
                    efos_toadd = []
                    for tid in val:
                        try:
                            efo = EFOTrait.objects.get(id=tid)
                        except:
                            efo = EFOTrait(id=tid)
                            efo.parse_api()
                            efo.save()
                        efos_toadd.append(efo)
                else:
                    setattr(current_score, f, val)
            current_score.save()
            for efo in efos_toadd:
                current_score.trait_efo.add(efo)
            current_score.save()

            self.saved_scores[score_id] = current_score

            # Test Score
            print("SCORE ID: "+str(score_db_id)+" ("+score_id+")")
            self.score_test(current_score, score_db_id, len(efos_toadd))

    def link_samples_to_scores(self):

        # Attach Samples 2 Scores
        for x in self.study.parsed_samples_scores:
            scores = []
            for s in x[0][0].split(','):
                scores.append(self.saved_scores[s.strip()])
            samples = x[1]
            for current_score in scores:
                if type(samples) == dict:
                    samples = [samples]
                for fields in samples:
                    current_sample = Sample()
                    cohorts_toadd = []
                    for f, val in fields.items():
                        if f == 'cohorts':
                            for name_short, name_full in val:
                                try:
                                    cohort = Cohort.objects.get(name_short=name_short, name_full=name_full)
                                except:
                                    cohort = Cohort(name_short=name_short, name_full=name_full)
                                    cohort.save()
                                cohorts_toadd.append(cohort)
                        elif f in ['sample_age', 'followup_time']:
                            current_demographic = Demographic(**val)
                            current_demographic.save()
                            setattr(current_sample, f, current_demographic)
                        else:
                            setattr(current_sample, f, val)
                    current_sample.save()
                    for cohort in cohorts_toadd:
                        current_sample.cohorts.add(cohort)
                    if x[0][1] == 'GWAS/Variant associations':
                        current_score.samples_variants.add(current_sample)
                    elif x[0][1] == 'Score development':
                        current_score.samples_training.add(current_sample)
                    else:
                        print('ERROR: Unclear how to add samples')

                # Test Score Samples
                #print("Score to Sample | SCORE ID: "+str(current_score.id)+" ("+current_score.name+")")
                self.score_sample_test(current_score)


    def load_sample_sets(self):

        # Create testing sample sets
        self.testset_to_sampleset = {}
        for x in self.study.parsed_samples_testing:
            test_name, sample_list = x

            # Initialize the current SampleSet
            current_sampleset = SampleSet()
            current_sampleset.set_ids(next_PSS_num())
            current_sampleset.save()

            # Attach underlying sample(s) and their descriptions to the SampleSet
            for sample_desc in sample_list:
                current_sample = Sample()
                cohorts_toadd = []
                for f, val in sample_desc.items():
                    if f == 'cohorts':
                        for name_short, name_full in val:
                            try:
                                cohort = Cohort.objects.get(name_short=name_short, name_full=name_full)
                            except:
                                cohort = Cohort(name_short=name_short, name_full=name_full)
                                cohort.save()
                            cohorts_toadd.append(cohort)
                    elif f in ['sample_age', 'followup_time']:
                        current_demographic = Demographic(**val)
                        current_demographic.save()
                        setattr(current_sample, f, current_demographic)
                    else:
                        setattr(current_sample, f, val)
                current_sample.save()

                # Add cohort(s) to the sample
                for cohort in cohorts_toadd:
                    current_sample.cohorts.add(cohort)
                current_sample.save()

                # Add sample to the SampleSet
                current_sampleset.samples.add(current_sample)
            current_sampleset.save()
            self.testset_to_sampleset[test_name] = current_sampleset

            # Test Sample Set
            self.sampleset_test(current_sampleset)


    def load_performance_metrics(self):

        for x in self.study.parsed_performances:
            i, fields = x
            if i[0] in self.saved_scores:
                current_score = self.saved_scores[i[0]]
            else:
                current_score = Score.objects.get(id = i[0])
            related_SampleSet = self.testset_to_sampleset[i[1]]
            current_performance = Performance(publication=self.study.parsed_publication, score = current_score, sampleset = related_SampleSet)
            for f, val in fields.items():
                if f not in ['publication', 'metrics']:
                    setattr(current_performance, f, val)
            current_performance.set_performance_id(next_scorenumber(Performance))
            current_performance.save()
            # Parse metrics
            for m in fields['metrics']:
                current_metric = Metric(performance=current_performance)
                for f, val in m.items():
                    setattr(current_metric, f, val)
                current_metric.save()

            # Test Performance
            #print("Performance | PPM ID: "+str(current_performance.id)+" ( Score: "+str(current_score.id)+' - '+current_score.name+")")
            self.performance_test(current_performance)


    #-------------------------------#
    #  Model oriented test methods  #
    #-------------------------------#

    def score_test(self, score, score_id, count_efo):
        score_name = ''
        if score.name:
            score_name = " ("+str(score.name)+")"
        print("\t> Test Score - "+str(score.id)+score_name)

        # Instance
        self.assertIsInstance(score, Score)
        # Variables
        self.assertRegexpMatches(score.id, r'^PGS0*'+str(score_id)+'$')
        self.assertRegexpMatches(score.name, r'\w+')
        self.assertRegexpMatches(score.trait_reported, r'\w+')
        self.assertRegexpMatches(score.method_name, r'\w+')
        self.assertIsNotNone(score.method_params)
        self.assertRegexpMatches(score.method_params, r'\w+')
        self.assertIsInstance(score.variants_number, int)
        self.assertIsInstance(score.variants_interactions, int)
        self.assertRegexpMatches(score.variants_genomebuild, r'\w+')

        efo = score.trait_efo.all()
        self.assertEqual(len(efo), count_efo)

        if (score.publication):
            self.assertTrue(isinstance(score.publication, Publication))
            self.publication_test(score.publication)
        else:
            print("No Publication associated with the Score "+score.name+"!")

        if (score.trait_efo):
            efo_traits = score.trait_efo.all()
            self.assertGreater(len(efo_traits), 0)
            self.assertTrue(isinstance(efo_traits[0], EFOTrait))
            for efo_trait in efo_traits:
                self.efo_trait_test(efo_trait)
        else:
            print("No Publication associated with the Score "+score.name+"!")


    def publication_test(self, publication):
        title = ''
        if publication.title:
            title =  " ("+publication.title+")"
        print("\t> Test Publication - "+str(publication.id)+title)

        # Instance
        self.assertIsInstance(publication, Publication)
        # Variables
        self.assertRegexpMatches(publication.id, r'^PGP0*\d+$')
        self.assertRegexpMatches(publication.title, r'\w+')
        if publication.doi in self.external_id_checked['DOI']:
            self.assertTrue(self.external_id_checked['DOI'][publication.doi])
        else:
            self.assertRegexpMatches(publication.doi, r'\w+')
            self.assertTrue(self.check_doi(publication.doi))
        self.assertRegexpMatches(publication.journal, r'\w+')
        self.assertRegexpMatches(publication.firstauthor, r'\w+')
        self.assertRegexpMatches(publication.authors, r'\w+')
        #self.assertRegexpMatches(publication.date_publication, r'\d+')
        self.assertIsNotNone(publication.date_publication)

        if (publication.PMID):
            self.pmid_test(publication.PMID)


    def efo_trait_test(self, efo_trait):
        trait = ''
        if efo_trait.label:
            trait =  " ("+efo_trait.label+")"
        print("\t> Test EFO Trait - "+str(efo_trait.id)+trait)


        self.assertIsNotNone(efo_trait.id)
        # Check EFO exist
        if efo_trait.id in self.external_id_checked['EFO']:
            self.assertTrue(self.external_id_checked['EFO'][efo_trait.id])
        else:
            self.assertTrue(self.check_trait_in_efo(efo_trait.id))


    def performance_test(self, performance):
        print("\t> Test Performance - "+str(performance.id)+" (#"+str(performance.num)+")")

        # Instance
        self.assertIsInstance(performance, Performance)
        # Variables
        self.assertRegexpMatches(performance.id, r'^PPM0*\d+$')
        self.assertIsNotNone(performance.score)
        self.assertIsNotNone(performance.publication)
        #if (performance.phenotyping_efo):
        #    efo_traits = performance.phenotyping_efo.all()
        #    self.assertTrue(isinstance(efo_traits[0], EFOTrait))
        #    for efo_trait in efo_traits:
        #        self.efo_trait_test(efo_trait)
        self.assertRegexpMatches(performance.phenotyping_reported, r'\w+')
        if performance.covariates:
            self.assertRegexpMatches(performance.covariates, r'\w+')
        if performance.performance_comments:
            self.assertRegexpMatches(performance.performance_comments, r'\w+')

        # Metrics
        metrics = performance.performance_metric.all()
        self.assertGreater(len(metrics), 0)
        for metric in metrics:
            self.metric_test(metric)


    def score_sample_test(self, score):
        score_label = "Score: "+score.id+" ("+score.name+")"
        if (score.samples_variants):
            for sample in score.samples_variants.all():
                self.sample_test(sample, score_label)
        if (score.samples_training):
            for sample in score.samples_training.all():
                self.sample_test(sample, score_label)


    def sampleset_test(self, sampleset):
        print("\t> Test Sample Set - "+sampleset.id+" (#"+str(sampleset.num)+")")
        # Instance
        self.assertIsInstance(sampleset, SampleSet)
        # Variables
        self.assertRegexpMatches(sampleset.id, r'^PSS0*\d+$')
        samples = sampleset.samples.all()
        self.assertGreater(len(samples), 0)
        for sample in samples:
            self.sample_test(sample)


    def sample_test(self, sample, associated_id=None):
        # Check sample ID, to see if the object has already been tested
        if sample.id in self.samples_tested:
            return

        prefix = '\t-'
        association = ''
        if associated_id:
            association =  " | "+associated_id
            prefix = '>'
        print("\t"+prefix+" Test Sample - #"+str(sample.id)+association)

        # Instance
        self.assertIsInstance(sample, Sample)

        ## Numbers
        self.assertIsInstance(sample.sample_number, int)
        if sample.sample_cases:
            self.assertIsInstance(sample.sample_cases, int)
        if sample.sample_controls:
            self.assertIsInstance(sample.sample_controls, int)
        if sample.sample_percent_male:
            self.assertIsInstance(sample.sample_percent_male, float)

        ## Description
        if sample.phenotyping_free:
            self.assertRegexpMatches(sample.phenotyping_free, r'\w+')
        if sample.sample_age:
            self.demographic_test(sample.sample_age)
        if sample.followup_time:
            self.demographic_test(sample.followup_time)

        ## Ancestry
        self.assertRegexpMatches(sample.ancestry_broad, r'\w+')
        if sample.ancestry_free:
            self.assertRegexpMatches(sample.ancestry_free, r'\w+')
        if sample.ancestry_country:
            self.assertRegexpMatches(sample.ancestry_country, r'\w+')
        if sample.ancestry_additional:
            self.assertRegexpMatches(sample.ancestry_additional, r'\w+')

        ## Sources
        if sample.source_PMID:
            self.pmid_test(sample.source_PMID)
        if sample.source_GWAS_catalog:
            if sample.source_GWAS_catalog in self.external_id_checked['GWAS']:
                self.assertTrue(self.external_id_checked['GWAS'][sample.source_GWAS_catalog])
            else:
                self.assertRegexpMatches(sample.source_GWAS_catalog, r'^GCST\d+$')
                self.assertTrue(self.check_gwas_id(sample.source_GWAS_catalog))

        ## Cohorts
        for cohort in sample.cohorts.all():
            self.cohort_test(cohort)
        if sample.cohorts_additional:
            self.assertRegexpMatches(sample.cohorts_additional, r'\w+')

        # Store sample ID, to avoid testing the same object several times
        self.samples_tested.append(sample.id)


    def cohort_test(self, cohort):
        self.assertRegexpMatches(cohort.name_short, r'\w+')
        self.assertRegexpMatches(cohort.name_full, r'\w+')


    def metric_test(self, metric):
        self.assertRegexpMatches(metric.name, r'\w+')
        if metric.name_short:
            self.assertRegexpMatches(metric.name_short, r'\w+')
        self.assertIsNotNone(metric.estimate)
        self.assertIsInstance(metric.estimate, float)
        if metric.unit:
            self.assertRegexpMatches(metric.unit, r'\w+')
        if metric.ci:
            self.assertRegexpMatches(str(metric.ci), r'\[\d+\.?\d+\s?,\s?\d+\.?\d+\]')
        if metric.se:
            self.assertIsInstance(metric.se, float)


    def demographic_test(self, demographic):
        # Estimate
        if demographic.estimate:
            self.assertIsInstance(demographic.estimate, float)
            self.assertIsNotNone(demographic.estimate)
            self.assertRegexpMatches(demographic.estimate_type, r'\w+')
        # Range
        if demographic.range:
            self.assertRegexpMatches(str(demographic.range), r'\[\d+\.?\d+\s?,\s?\d+\.?\d+\]')
            self.assertRegexpMatches(demographic.range_type, r'\w+')
        # Variability
        if demographic.variability:
            self.assertIsInstance(demographic.variability, float)
            self.assertIsNotNone(demographic.variability)
            self.assertRegexpMatches(demographic.variability_type, r'\w+')
        self.assertRegexpMatches(demographic.unit, r'\w+')

        if not demographic.estimate and not demographic.range and not demographic.variability:
            print("\t\tMissing required data for 'sample_age' and/or 'followup_time'")


    def pmid_test(self, pmid):
        if pmid in self.external_id_checked['PMID']:
            self.assertTrue(self.external_id_checked['PMID'][pmid])
        else:
            self.assertRegexpMatches(str(pmid), r'^\d+$')
            self.assertTrue(self.check_pubmed_id(pmid))



    #--------------------#
    #  Main test method  #
    #--------------------#

    def test_curation_template(self):
        print("Run test_curation_template")
        self.parse_study_template()
        self.load_study_data()




    #-------------------#
    #  Utility methods  #
    #-------------------#

    def check_trait_in_efo(self, trait_id):
        response = requests.get('https://www.ebi.ac.uk/ols/api/ontologies/efo/terms?obo_id=%s'%trait_id.replace('_', ':'))
        status = response.status_code
        if (self.debug):
            print("\t> OLS STATUS: "+str(status))
        if status == 200:
            result = True
        elif status == 404:
            print("The trait ID: "+trait_id+" does not exist in EFO")
            result = False
        else:
            print("Issue with the OLS API: we can't check that the trait ID: "+trait_id+" exists in EFO")
            result = True
        self.external_id_checked['EFO'][trait_id] = result
        return result

    def check_pubmed_id(self, pmid_id):
        response = requests.get('https://pubmed.ncbi.nlm.nih.gov/%s'%pmid_id)
        status = response.status_code
        if (self.debug):
            print("\t> PubMed STATUS: "+str(status))
        if status == 200:
            result = True
        elif status == 404:
            print("The PubMed ID: "+pmid_id+" does not exist in PubMed")
            result = False
        else:
            print("Issue with the PubMed website: we can't check that the PubMed ID: "+pmid_id+" exists")
            result = True
        self.external_id_checked['PMID'][pmid_id] = result
        return result

    def check_doi(self, doi):
        response = requests.get('https://doi.org/api/handles/%s'%doi)
        status = response.status_code
        if (self.debug):
            print("\t> DOI STATUS: "+str(status))
        if status == 200:
            result = True
        elif status == 404:
            print("The DOI: "+doi+" does not exist")
            result = False
        else:
            print("Issue with the DOI server: we can't check that the DOI: "+doi+" exists")
            result = True
        self.external_id_checked['DOI'][doi] = result
        return result

    def check_gwas_id(self, gwas_id):
        response = requests.get('https://www.ebi.ac.uk/gwas/rest/api/studies/%s'%gwas_id)
        status = response.status_code
        if (self.debug):
            print("\t> GWAS STATUS: "+str(status))
        if status == 200:
            result = True
        elif status == 404:
            print("The GWAS Catalog Study ID: "+gwas_id+" does not exist")
            result = False
        else:
            print("Issue with the GWAS Catalog website: we can't check that the GWAS Study ID: "+gwas_id+" exists")
            result = True
        self.external_id_checked['GWAS'][gwas_id] = result
        return result
