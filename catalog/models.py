from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.postgres.fields import DecimalRangeField

class Publication(models.Model):
    """Class for publications with PGS"""
    # Stable identifiers
    num = models.IntegerField('PGS Publication/Study (PGP) Number', primary_key=True)
    id = models.CharField('PGS Publication/Study (PGP) ID', max_length=30)

    date_released = models.DateField('PGS Release Date', null=True)

    # Key information (also) in the spreadsheet
    doi = models.CharField('digital object identifier (doi)', max_length=100)
    PMID = models.IntegerField('PubMed ID (PMID)', null=True)
    journal = models.CharField('Journal Name', max_length=100)
    firstauthor = models.CharField('First Author', max_length=50)

    # Information extracted from EuropePMC
    authors = models.TextField('Authors')
    title = models.TextField('Title')
    date_publication = models.DateField('Publication Date')

    # Curation information
    CURATION_STATUS_CHOICES = [
        ('C',  'Curated'),
        ('ID', 'Curated - insufficient data'),
        ('IP', 'Curation in Progress'),
        ('AW', 'Awaiting Curation')
    ]
    curation_status = models.CharField(max_length=2,
                            choices=CURATION_STATUS_CHOICES,
                            default='AW',
                            verbose_name='Curation Status'
                            )
    curation_notes = models.TextField('Curation Notes', default='')

    # Methods
    def __str__(self):
        return ' | '.join([self.id, self.firstauthor])

    class Meta:
        get_latest_by = 'num'

    def set_publication_ids(self, n):
        self.num = n
        self.id = 'PGP' + str(n).zfill(6)

    def is_published(self):
        return self.PMID != None

    @property
    def scores_count(self):
        return Score.objects.filter(publication=self).count()

    @property
    def scores_evaluated(self):
        performances = Performance.objects.filter(publication=self)
        return len(performances.values('score').distinct())

    def parse_EuropePMC(self, doi=None, PMID=None):
        '''Function to get the citation information from the EuropePMC API'''
        import requests

        payload = {'format': 'json'}
        if doi != None:
            payload['query'] = 'doi:' + doi
        elif type(PMID) == int:
            payload['query'] = ['ext_id:' + str(PMID)]
        else:
            print('Please retry with a valid doi or PMID')

        if 'query' in payload:
            r = requests.get('https://www.ebi.ac.uk/europepmc/webservices/rest/search', params=payload)
            r = r.json()
            r = r['resultList']['result'][0]

            self.doi = r['doi']
            self.firstauthor = r['authorString'].split(',')[0]
            self.authors = r['authorString']
            self.title = r['title']
            self.date_publication = r['firstPublicationDate']

            if r['pubType'] == 'preprint':
                self.journal=r['bookOrReportDetails']['publisher']
            else:
                self.journal=r['journalTitle']
                if 'pmid' in r:
                    self.PMID=r['pmid']


class Cohort(models.Model):
    """Class to describe cohorts used in samples"""
    name_short = models.CharField('Cohort(Short Name)', max_length=100)
    name_full = models.CharField('Cohort', max_length=1000)

    def __str__(self):
        return self.name_short


class EFOTrait(models.Model):
    '''Class to hold information related to controlled trait vocabulary
    (mainly to link multiple EFO to a single score)'''
    id = models.CharField('Experimental Factor Ontology ID (EFO_ID)', max_length=30, primary_key=True)
    label = models.CharField('EFO Label', max_length=500)
    description = models.TextField('EFO Description')
    url = models.CharField('EFO URL', max_length=500)

    def parse_api(self):
        import requests
        response = requests.get('https://www.ebi.ac.uk/ols/api/ontologies/efo/terms?obo_id=%s'%self.id.replace('_', ':'))
        response = response.json()['_embedded']['terms']
        if len(response) == 1:
            response = response[0]
            self.label = response['label']
            self.url = response['iri']

            # Make description
            try:
                desc = response['obo_definition_citation'][0]
                str_desc = desc['definition']
                for x in desc['oboXrefs']:
                    if x['database'] != None:
                        if x['id'] != None:
                            str_desc += ' [{}: {}]'.format(x['database'], x['id'])
                        else:
                            str_desc += ' [{}]'.format(x['database'])
                self.description = str_desc
            except:
                self.description = response['description']

    def __str__(self):
        return '%s | %s '%(self.id, self.label)

    @property
    def display_label(self):
        return '<a href="../../trait/%s">%s</a>'%(self.id, self.label)

    def display_id_url(self):
        return '<a href="%s">%s</a><span class="only_export">: %s</span>'%(self.url, self.id, self.url)

    @property
    def scores_count(self):
        return Score.objects.filter(trait_efo=self).count()


class Demographic(models.Model):
    estimate = models.FloatField(verbose_name='Estimate (value)', null=False, default=0)
    estimate_type = models.CharField(verbose_name='Estimate (type)', max_length=100, null=False, default='mean') #e.g. mean, median, mode
    unit = models.TextField(verbose_name='Unit', max_length=100, null=True)
    ci = DecimalRangeField(verbose_name='95% Confidence Interval', null=True)
    range = DecimalRangeField(verbose_name='Range', null=True)
    se = models.FloatField(verbose_name='Standard Error', null=True)


class Sample(models.Model):
    """Class to describe samples used in variant associations and PGS training/testing"""

    # Sample Information
    ## Numbers
    sample_number = models.IntegerField('Number of Individuals', validators=[MinValueValidator(1)])
    sample_cases = models.IntegerField('Number of Cases', null=True)
    sample_controls = models.IntegerField('Number of Controls', null=True)
    sample_percent_male = models.FloatField('Percent of Participants Who are Male', validators=[MinValueValidator(0), MaxValueValidator(100)], null=True)
    sample_age = models.OneToOneField(Demographic, on_delete=models.CASCADE,related_name='ages_of', null=True)

    ## Description
    phenotyping_free = models.TextField('Detailed Phenotype Description')
    followup_time = models.OneToOneField(Demographic, on_delete=models.CASCADE,related_name='followuptime_of', null=True)

    ## Ancestry
    ancestry_broad = models.CharField('Broad Ancestry Category', max_length=100)
    ancestry_free = models.TextField('Ancestry (e.g. French, Chinese)', null=True)
    ancestry_country = models.TextField('Country of Recruitment', null=True)
    ancestry_additional = models.TextField('Additional Ancestry Description', null=True)

    ## Cohorts/Sources
    source_GWAS_catalog = models.CharField('GWAS Catalog Study ID (GCST...)', max_length=20)
    source_PMID = models.CharField('Source PubMed ID (PMID)', max_length=20)
    cohorts = models.ManyToManyField(Cohort, verbose_name='Cohort(s)')
    cohorts_additional = models.TextField('Additional Sample/Cohort Information', null=True)

    def __str__(self):
        s = 'Sample: {}'.format(str(self.pk))

        #Check if any PGS
        ids = self.associated_PGS()
        if len(ids) > 0:
            s += ' | {}'.format(' '.join(ids))
        # Check if any PSS
        ids = self.associated_PSS()
        if len(ids) > 0:
            s += ' | {}'.format(' '.join(ids))
        return s

    def associated_PGS(self):
        ids = set()
        for x in self.score_variants.all().values():
            ids.add(x['id'])
        for x in self.score_training.all().values():
            ids.add(x['id'])
        ids = list(ids)
        ids.sort()
        return list(ids)

    def associated_PSS(self):
        ids = set()
        for x in self.sampleset.all().values():
            ids.add(x['id'])
        ids = list(ids)
        ids.sort()
        return list(ids)

    def list_cohortids(self):
        return [x.name_full for x in self.cohorts.all()]

    @property
    def display_sampleset(self):
        return SampleSet.objects.get(samples__in=[self])

    @property
    def display_samples(self):
        sinfo = ['{:,} individuals'.format(self.sample_number)]
        if self.sample_cases != None:
            sstring = '[ {:,} cases'.format(self.sample_cases)
            if self.sample_controls != None:
                sstring += ', {:,} controls]'.format(self.sample_controls)
            else:
                sstring += ']'
            sinfo.append(sstring)
        if self.sample_percent_male != None:
            sinfo.append('%s %% Male samples'%str(round(self.sample_percent_male,2)))
        return sinfo

    @property
    def display_sample_number_total(self):
        ssinfo = '{:,} individuals'.format(self.sample_number)
        return ssinfo

    @property
    def display_sample_number_detail(self):
        sinfo = []
        if self.sample_cases != None:
            sinfo.append('{:,} cases'.format(self.sample_cases))
            if self.sample_controls != None:
                sinfo.append('{:,} controls'.format(self.sample_controls))
        if self.sample_percent_male != None:
            sinfo.append('%s %% Male samples'%str(round(self.sample_percent_male,2)))
        return sinfo

    @property
    def display_sample_category_number(self):
        categories = []
        numbers = []
        if self.sample_cases != None:
            #sinfo['Cases'] = self.sample_cases
            categories.append("Cases")
            numbers.append(self.sample_cases)
            if self.sample_controls != None:
                #sinfo['Controls'] = self.sample_controls
                categories.append('Controls')
                numbers.append(self.sample_controls)
        return [categories,numbers]

    @property
    def display_sample_gender_percentage(self):
        categories = []
        numbers = []
        if self.sample_percent_male != None:
            percent_male = round(self.sample_percent_male,2)
            categories = ["% Male", "% Female"]
            numbers    = [percent_male, round(100-percent_male,2)]
        return [categories,numbers]


    @property
    def display_sources(self):
        d = {}
        if self.source_GWAS_catalog.startswith('GCST'):
            d['GCST'] = self.source_GWAS_catalog
        if self.source_PMID != None:
            d['PMID'] = self.source_PMID
        return d

    @property
    def display_ancestry(self):
        if self.ancestry_free in ['NR', '', None]:
            return self.ancestry_broad
        else:
            return '{}<br/>({})'.format(self.ancestry_broad, self.ancestry_free)

    @property
    def display_ancestry_inline(self):
        if self.ancestry_free in ['NR', '', None]:
            return self.ancestry_broad
        else:
            return '{} ({})'.format(self.ancestry_broad, self.ancestry_free)


class Score(models.Model):
    """Class for individual Polygenic Score (PGS)"""
    # Stable identifiers
    num = models.IntegerField('Polygenic Score (PGS) Number', primary_key=True)
    id = models.CharField('Polygenic Score (PGS) ID', max_length=30)

    name = models.CharField('PGS Name', max_length=100)

    # Curation/release information
    date_released = models.DateField('PGS Catalog Release Date', null=True)
    curation_notes = models.TextField('Curation Notes', default='')

    # Links to related models
    publication = models.ForeignKey(Publication, on_delete=models.PROTECT, verbose_name='PGS Publication (PGP) ID')
    ## Contributing Samples
    samples_variants = models.ManyToManyField(Sample, verbose_name='Source of Variant Associations (GWAS)', related_name='score_variants')
    samples_training = models.ManyToManyField(Sample, verbose_name='Score Development/Training', related_name='score_training')

    # Trait information
    trait_reported = models.TextField('Reported Trait')
    trait_additional = models.TextField('Additional Trait Information', null=True)
    trait_efo = models.ManyToManyField(EFOTrait, verbose_name='Mapped Trait(s) (EFO terms)')

    # PGS Development/method details
    method_name = models.TextField('PGS Development Method')
    method_params = models.TextField('PGS Development Details/Relevant Parameters')

    variants_number = models.IntegerField('Number of Variants', validators=[MinValueValidator(1)])
    variants_interactions = models.IntegerField('Number of Interaction Terms', default=0)
    variants_genomebuild = models.CharField('Original Genome Build', max_length=10, default='NR')

    # Methods
    def __str__(self):
        return ' | '.join([self.id, self.name, '(%s)' % self.publication.__str__()])

    def set_score_ids(self, n):
        self.num = n
        self.id = 'PGS' + str(n).zfill(6)

    class Meta:
        get_latest_by = 'num'

    # Score file FTP addresses
    @property
    def link_filename(self):
        filename = self.id + '.txt.gz'
        return filename

    @property
    def list_traits(self):
        l = [] # tuples (id, label)
        for t in self.trait_efo.values():
            l.append((t['id'], t['label']))
        return(l)

class SampleSet(models.Model):
    # Stable identifiers for declaring a set of related samples
    num = models.IntegerField('PGS Sample Set (PSS) Number', primary_key=True)
    id = models.CharField('PGS Sample Set (PSS) ID', max_length=30)

    # Link to the description of the sample(s) in the other table
    samples = models.ManyToManyField(Sample, verbose_name='Sample Set Descriptions', related_name='sampleset')

    def __str__(self):
        return self.id

    def set_ids(self, n):
        self.num = n
        self.id = 'PSS' + str(n).zfill(6)

    @property
    def samples_ancestry(self):
        ancestry_list = []
        for sample in self.samples.all():
            ancestry = sample.display_ancestry_inline
            if ancestry not in ancestry_list:
                ancestry_list.append(ancestry)
        if len(ancestry_list) > 0:
            return ', '.join(ancestry_list)
        else:
            return '-'

    @property
    def count_samples(self):
        return len(self.samples.all())

    @property
    def count_performances(self):
        return len(Performance.objects.filter(sampleset_id=self.num))



class Performance(models.Model):
    """Class to hold performance/accuracy metrics for a PGS and a set of samples"""
    # Key identifiers
    num = models.IntegerField('PGS Performance Metric (PPM) Number', primary_key=True)
    id = models.CharField('PGS Performance Metric (PPM) ID', max_length=30)

    # Curation information
    date_released = models.DateField('PGS Catalog Release Date', null=True)
    curation_notes = models.TextField('Curation Notes', default='')

    # Links to related objects
    score = models.ForeignKey(Score, on_delete=models.CASCADE,
                              verbose_name='Evaluated Score') # PGS that the metrics are associated with
    phenotyping_efo = models.ManyToManyField(EFOTrait, verbose_name='Mapped Trait(s) (EFO)')
    sampleset = models.ForeignKey(SampleSet, on_delete=models.PROTECT,
                                  verbose_name='PGS Sample Set (PSS)') # Samples used for evaluation
    publication = models.ForeignKey(Publication, on_delete=models.PROTECT,
                                    verbose_name='Peformance Source') # Study that reported performance metrics

    # [Links to Performance metrics are made by ForeignKey in Metrics table, previously they were parameterized here]
    phenotyping_reported = models.CharField('Reported Trait', max_length=200)
    covariates = models.TextField('Covariates Included in PGS Model')
    performance_comments = models.TextField('PGS Performance: Other Relevant Information')

    def __str__(self):
        return '%s | %s -> %s'%(self.id, self.score.id, self.sampleset.id)

    class Meta:
        get_latest_by = 'num'

    def set_performance_id(self, n):
        self.num = n
        self.id = 'PPM' + str(n).zfill(6)\

    def samples(self):
        """ Method working as a shortcut to fetch all the samples related to the sampleset  """
        return list(self.sampleset.samples.all())

    @property
    def display_trait(self):
        d = {}
        if self.phenotyping_reported != '':
            d['reported'] = self.phenotyping_reported
        if self.phenotyping_efo.distinct().count() > 0:
            d['efo'] = self.phenotyping_efo.distinct()
        return d

    @property
    def effect_sizes_list(self):
        metrics = Metric.objects.filter(performance=self, type ='Effect Size')
        if len(metrics) > 0:
            l=[]
            for m in metrics:
                l.append((m.name_tuple(), m.display_value()))
            return l
        else:
            return None

    @property
    def class_acc_list(self):
        metrics = Metric.objects.filter(performance=self, type ='Classification Metric')
        if len(metrics) > 0:
            l=[]
            for m in metrics:
                l.append((m.name_tuple(), m.display_value()))
            return l
        else:
            return None

    @property
    def othermetrics_list(self):
        metrics = Metric.objects.filter(performance=self, type='Other Metric')
        if len(metrics) > 0:
            l = []
            for m in metrics:
                l.append((m.name_tuple(), m.display_value()))
            return l
        else:
            return None

    @property
    def publication_withexternality(self):
        '''This function checks whether the evaluation is internal or external to the score development paper'''
        p = self.publication
        info = [' '.join([p.id, '<br/><small>', p.firstauthor, '<i>et al.</i>', '(%s)' % p.date_publication.strftime('%Y'), '</small>']), self.publication.id]

        if self.publication == self.score.publication:
            info.append('D')
        else:
            info.append('E')

        return '|'.join(info)


class Metric(models.Model):
    """Class to hold metric type, name, value and confidence intervals of a performance metric"""
    performance = models.ForeignKey(Performance, on_delete=models.CASCADE, verbose_name='PGS Performance Metric (PPM)')

    TYPE_CHOICES = [
        ('ES', 'Effect Size'),
        ('CM', 'Classification Metric'),
        ('OM', 'Other Metric')
    ]
    type = models.CharField(max_length=40,
        choices=TYPE_CHOICES,
        default='Other Metric',
    )

    name = models.CharField(verbose_name='Performance Metric Name', max_length=100, null=False) # ex: "Odds Ratio"
    name_short = models.CharField(verbose_name='Performance Metric Name (Short)', max_length=10, null=True) # ex: "OR"

    estimate = models.FloatField(verbose_name='Estimate', null=False)
    unit = models.TextField(verbose_name='Units of the effect size', max_length=100, blank = False)
    ci = DecimalRangeField(verbose_name='95% Confidence Interval', null=True)
    se = models.FloatField(verbose_name='Standard error of the effect', null=True)

    def __str__(self):
        if self.ci != None:
            s = '{} {}'.format(self.estimate, self.ci)
        else:
            s = '{}'.format(self.estimate)

        if (self.name_short):
            return '%s (%s): %s'%(self.name, self.name_short, s)
        else:
            return '%s: %s'%(self.name, s)

    def display_value(self):
        if self.ci != None:
            s = '{} {}'.format(self.estimate, self.ci)
        else:
            s = '{}'.format(self.estimate)
        return s

    def name_tuple(self):
        if self.name_short is None:
            return (self.name, self.name)
        else:
            return (self.name, self.name_short)


class Release(models.Model):
    """Class to store and manipulate the releases information"""
    id = models.IntegerField('Internal release ID', primary_key=True)
    date = models.DateField("Release date", null=False)
    score_count =  models.IntegerField('Number of new PGS scores released', default=0)
    performance_count = models.IntegerField('Number of new PGS Performance metrics released', default=0)
    publication_count = models.IntegerField('Number of new PGS Publication released', default=0)
    notes = models.TextField(verbose_name='Release notes', max_length=600, blank=True)

    def __str__(self):
        return str(self.date)
