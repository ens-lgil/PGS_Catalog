from django.test import TestCase
from catalog.models import *


class EFOTraitTest(TestCase):
    """ Test the EFOTrait model """

    def create_efo_trait(self, efo_id="EFO_0000249"):
        return EFOTrait.objects.create(id=efo_id)

    def test_efo_trait(self):
        efo_trait = self.create_efo_trait()
        self.assertTrue(isinstance(efo_trait, EFOTrait))
        efo_trait.parse_api()
        self.assertIsNotNone(efo_trait.label)
        self.assertIsNotNone(efo_trait.url)
        self.assertIsNotNone(efo_trait.description)


class PerformanceTest(TestCase):
    """ Test the Performance model """

    def create_perfomance(self, num):
        pubtest = PublicationTest()
        pub = pubtest.create_publication_by_doi(num=num)
        return Performance.objects.create(num=num, publication_id=pub.num)

    #def test_performance(self):
    #    id = 1
    #    performance = self.create_perfomance(id)
    #    performance.set_performance_id(id)
    #    self.assertTrue(isinstance(performance, Performance))
    #    self.assertEqual(performance.id, 'PPM000001')


class PublicationTest(TestCase):
    """ Test the Publication model """

    def create_publication_by_doi(self, num, date="2018-10-01", id="10.1016/j.jacc.2018.07.079"):
        return Publication.objects.create(num=num, date_publication=date, doi=id)

    def create_publication_by_pmid(self, num, date="2015-04-08", id=25855707):
        return Publication.objects.create(num=num, date_publication=date, PMID=id)

    def test_publication(self):
        id = 1
        pub_doi = self.create_publication_by_doi(id)
        pub_doi.set_publication_ids(id)
        self.assertTrue(isinstance(pub_doi, Publication))
        self.assertEqual(pub_doi.id, 'PGP000001')

        id = 2
        pub_pmid = self.create_publication_by_pmid(id)
        pub_pmid.set_publication_ids(id)
        self.assertTrue(isinstance(pub_pmid, Publication))
        self.assertEqual(pub_pmid.id, 'PGP000002')


class SampleTest(TestCase):
    """ Test the Sample model """

    def create_sample(self, sample_number=10):
        return Sample.objects.create(sample_number=sample_number)

    def test_sample(self):
        id = 1
        sample = self.create_sample()
        self.assertTrue(isinstance(sample, Sample))
        self.assertEqual(sample.pk, id)


class SampleSetTest(TestCase):
    """ Test the SampleSet model """

    def create_sampleset(self, num):
        return SampleSet.objects.create(num=num)

    def test_sampleset(self):
        id = 1
        sampleset = self.create_sampleset(id)
        sampleset.set_ids(id)
        self.assertTrue(isinstance(sampleset, SampleSet))
        self.assertEqual(sampleset.id, 'PSS000001')



class ScoreTest(TestCase):
    """ Test the Score model """

    def create_score(self, num, var_number=10):
        pubtest = PublicationTest()
        pub = pubtest.create_publication_by_doi(num=num)
        return Score.objects.create(num=num, variants_number=var_number,publication_id=pub.num)

    def test_score(self):
        id = 1
        score = self.create_score(id)
        score.set_score_ids(id)
        self.assertTrue(isinstance(score, Score))
        self.assertEqual(score.id, 'PGS000001')
