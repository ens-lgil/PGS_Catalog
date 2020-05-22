from django.test import TestCase
from curation.tools import *
import os, gzip
import requests
import numpy as np

class TemplateTest(TestCase):
    """ Test the template """

    loc_curation2schema = '~/Workspace/datafiles/templates/TemplateColumns2Models_v5.xlsx'
    curation2schema = pd.read_excel(loc_curation2schema, index_col = 0)

    loc_curation2schema_scoring = '~/Workspace/datafiles/templates/ScoringFileSchema.xlsx'
    curation2schema_scoring = pd.read_excel(loc_curation2schema_scoring, index_col = 0)


    #loc_localGWAS = '../pgs_DBSourceFiles/local_GWASCatalog/'
    loc_localGWAS = '~/Workspace/datafiles/local_GWASCatalog/'
    #gwas_studies, gwas_samples = load_GWAScatalog(loc_localGWAS, update = True)
    gwas_studies, gwas_samples = load_GWAScatalog(loc_localGWAS, update = False)
    gwas_studies.set_index('STUDY ACCESSION', inplace = True)
    gwas_samples.set_index('STUDY ACCESSION', inplace = True)
    gwas_samples = gwas_samples[gwas_samples['STAGE'] == 'initial'] # Get rid of replication studies

    study = CurationTemplate()

    saved_scores = {}
    testset_to_sampleset = {}
    debug = True

    def parse_study_template(self, study_name):
        self.study.file_loc  = '~/Workspace/datafiles/SourceFiles/{}/{}.xlsx'.format(study_name,study_name)
        self.study.read_curation()
        self.study.table_mapschema = self.curation2schema
        self.study.extract_publication()
        self.study.extract_scores()
        self.study.extract_samples(self.gwas_samples)
        self.study.extract_performances()


    def load_study_data(self):
        self.load_scores()
        self.link_samples_to_scores()
        self.load_sample_sets()
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
                print("Score to Sample | SCORE ID: "+str(current_score.id)+" ("+current_score.name+")")
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


    #-------------------------------#
    #  Model oriented test methods  #
    #-------------------------------#

    def score_test(self, score, score_id, count_efo):
        print("> Test Score")
        # Instance
        self.assertIsInstance(score, Score)
        # Variables
        self.assertRegexpMatches(score.id, r'^PGS0*'+str(score_id)+'$')
        self.assertIsNotNone(score.name)
        efo = score.trait_efo.all()
        self.assertEqual(len(efo), count_efo)

        if (score.publication):
            self.assertTrue(isinstance(score.publication, Publication))
            self.publication_test(score.publication)
        else:
            print("No Publication associated with the Score "+score.name+"!")

        if (score.trait_efo):
            efo_traits = score.trait_efo.all()
            self.assertTrue(isinstance(efo_traits[0], EFOTrait))
            for efo_trait in efo_traits:
                self.efo_trait_test(efo_trait)
        else:
            print("No Publication associated with the Score "+score.name+"!")


    def publication_test(self, publication):
        print("> Test Publication")
        self.assertRegexpMatches(publication.id, r'^PGP0*\d+$')
        self.assertIsNotNone(publication.title)
        self.assertIsNotNone(publication.doi)
        self.assertTrue(self.check_doi(publication.doi))
        self.assertIsNotNone(publication.journal)
        self.assertIsNotNone(publication.firstauthor)
        self.assertIsNotNone(publication.authors)
        self.assertIsNotNone(publication.date_publication)

        if (publication.PMID):
            self.assertIsInstance(publication.PMID, int)
            self.assertTrue(self.check_pubmed_id(publication.PMID))


    def efo_trait_test(self, efo_trait):
        print("> Test EFO Trait")
        self.assertIsNotNone(efo_trait.id)
        # Check EFO exist
        self.assertTrue(self.check_trait_in_efo(efo_trait.id))


    def score_sample_test(self, score):
        if (score.samples_variants):
            for sample in score.samples_variants.all():
                self.assertIsInstance(sample, Sample)
                self.assertIsNotNone(sample.sample_number)
                if sample.source_PMID:
                    self.assertTrue(self.check_pubmed_id(sample.source_PMID))
                if sample.source_GWAS_catalog:
                    self.assertTrue(self.check_gwas_id(sample.source_GWAS_catalog))
        if (score.samples_training):
            for sample in score.samples_training.all():
                self.assertIsInstance(sample, Sample)
                self.assertIsNotNone(sample.sample_number)
                if sample.source_PMID:
                    self.assertTrue(self.check_pubmed_id(sample.source_PMID))

    #--------------------#
    #  Main test method  #
    #--------------------#

    def test_curation_template(self):
        print("Run test_curation_template")
        self.parse_study_template('HoLe2016')
        self.load_study_data()


    #-------------------#
    #  Utility methods  #
    #-------------------#

    def check_trait_in_efo(self, trait_id):
        response = requests.get('https://www.ebi.ac.uk/ols/api/ontologies/efo/terms?obo_id=%s'%trait_id.replace('_', ':'))
        status = response.status_code
        if (self.debug):
            print("> OLS STATUS: "+str(status))
        if status == 200:
            return True
        elif status == 404:
            print("The trait ID: "+trait_id+" does not exist in EFO")
            return False
        else:
            print("Issue with the OLS API: we can't check that the trait ID: "+trait_id+" exists in EFO")
            return True

    def check_pubmed_id(self, pmid_id):
        response = requests.get('https://pubmed.ncbi.nlm.nih.gov/%s'%pmid_id)
        status = response.status_code
        if (self.debug):
            print("> PubMed STATUS: "+str(status))
        if status == 200:
            return True
        elif status == 404:
            print("The PubMed ID: "+pmid_id+" does not exist in PubMed")
            return False
        else:
            print("Issue with the PubMed website: we can't check that the PubMed ID: "+pmid_id+" exists")
            return True

    def check_doi(self, doi):
        response = requests.get('https://doi.org/api/handles/%s'%doi)
        status = response.status_code
        if (self.debug):
            print("> DOI STATUS: "+str(status))
        if status == 200:
            return True
        elif status == 404:
            print("The DOI: "+doi+" does not exist")
            return False
        else:
            print("Issue with the DOI server: we can't check that the DOI: "+doi+" exists")
            return True

    def check_gwas_id(self, gwas_id):
        response = requests.get('https://www.ebi.ac.uk/gwas/rest/api/studies/%s'%gwas_id)
        status = response.status_code
        if (self.debug):
            print("> GWAS STATUS: "+str(status))
        if status == 200:
            return True
        elif status == 404:
            print("The GWAS Catalog Study ID: "+gwas_id+" does not exist")
            return False
        else:
            print("Issue with the GWAS Catalog website: we can't check that the GWAS Study ID: "+gwas_id+" exists")
            return True
