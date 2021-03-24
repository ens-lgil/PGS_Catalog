from catalog.models import Score, Performance
from pgs_web import constants


class UpdateScoreAncestry:

    ancestry_cat = constants.ANCESTRY_MAPPINGS
    ancestry_cat_keys = ancestry_cat.keys()


    ancestry_keys = constants.ANCESTRY_LABELS.keys()

    extra_ancestry_cat = {
        "Multi-Ancestry (excluding European)": "MAO",
        "Multi-Ancestry (including European)": "MAE"
    }

    def __init__(self):
        self.scores = Score.objects.all().order_by('num')
        #self.scores = Score.objects.filter(num=739):


    def get_ancestry_code(self,anc):
        a_code = self.ancestry_cat['Other']
        if anc in self.ancestry_cat_keys:
            a_code = self.ancestry_cat[anc]
        elif ',' in anc:
            if 'European' in anc:
                a_code = self.extra_ancestry_cat["Multi-Ancestry (including European)"]
            else:
                a_code = self.extra_ancestry_cat["Multi-Ancestry (excluding European)"]
        return a_code


    def get_samples_ancestry_data(self,samples):
        data_ancestry = {}
        data_ancestry_total = 0
        for sample in samples:
            ancestry = sample.ancestry_broad.strip()
            sample_number = sample.sample_number
            anc_code = self.get_ancestry_code(ancestry)
            print(f'\t\t- {ancestry} ({anc_code}): {sample_number}')
            if not anc_code in data_ancestry:
                data_ancestry[anc_code] = sample_number
            else:
                data_ancestry[anc_code] += sample_number
            data_ancestry_total += sample_number
        # Simplify values
        if len(data_ancestry.keys())==1 and data_ancestry_total == 0:
            data_ancestry_total = 1
            for key,value in data_ancestry.items():
                data_ancestry[key] = 1
        return { 'data': data_ancestry, 'total': data_ancestry_total }


    def update_ancestry(self):

        for score in self.scores:
            # Get Variant selection ancestries
            score_ancestry_data = {}

            # variant_ancestry = {}
            # #variant_ancestry_total = 0
            # dev_ancestry = {}
            # #dev_ancestry_total = 0
            # eval_ancestry = {}
            #eval_ancestry_total = 0
            score_id = score.id
            print("# "+score_id+" #")

            print("\t> Variant:")
            samples_variant = score.samples_variants.all()
            score_ancestry_data['gwas'] = self.get_samples_ancestry_data(samples_variant)

            print("\t> Development:")
            samples_dev = score.samples_training.all()
            score_ancestry_data['dev'] = self.get_samples_ancestry_data(samples_dev)

            print("\t> Evaluation:")
            publication_samplesets_list = set()
            sampleset_sample_anc = {}
            data_eval_ancestry = {}
            data_eval_ancestry_total = 0
            # Performances
            for perf in Performance.objects.filter(score__id=score_id):
                sampleset = perf.sampleset
                sampleset_id = sampleset.id
                publication_id = perf.publication.id
                key_id = publication_id+'_'+sampleset_id
                if key_id in publication_samplesets_list:
                    continue
                publication_samplesets_list.add(key_id)
                print('\t ->'+publication_id+" | "+sampleset_id)
                # Samples
                for sample in sampleset.samples.all():
                    ancestry = sample.ancestry_broad.strip()
                    anc_code = self.get_ancestry_code(ancestry)
                    print(f'\t\t- {ancestry} ({anc_code}): {sample.sample_number}')
                    if key_id in sampleset_sample_anc.keys():
                        if not anc_code in sampleset_sample_anc[key_id]:
                            sampleset_sample_anc[key_id].append(anc_code)
                    else:
                        sampleset_sample_anc[key_id] = [anc_code]
                # Data update
                if len(sampleset_sample_anc[key_id]) > 1:
                    if 'EUR' in sampleset_sample_anc[key_id]:
                        anc_key = 'MAE'
                    else:
                        anc_key = 'MAO'
                else:
                    anc_key = sampleset_sample_anc[key_id][0]

                if not anc_key in data_eval_ancestry:
                    data_eval_ancestry[anc_key] = 0
                data_eval_ancestry[anc_key] += 1

                data_eval_ancestry_total += 1
            score_ancestry_data['eval'] = { 'data': data_eval_ancestry, 'total': data_eval_ancestry_total }



            anc_data = {}
            for type in ['gwas','dev','eval']:
                if score_ancestry_data[type]['data']:
                    anc_data[type] = {}
                    print(f'\t#### '+type.upper())
                    count_total = score_ancestry_data[type]['total']
                    for key, value in score_ancestry_data[type]['data'].items():
                        percent = "{:.1f}".format((value/count_total)*100)
                        print(f'\t>>>> PERCENT: {key} => {percent}%')
                        anc_data[type][key] = percent

        # if variant_ancestry:
        #     anc_data['gwas'] = {}
        #     print(f'\t#### GWAS')
        #     for key, value in variant_ancestry.items():
        #         percent = "{:.1f}".format((value/variant_ancestry_total)*100)
        #         print(f'\t>>>> PERCENT: {key} => {percent}%')
        #         anc_data['gwas'][key] = percent
        # if dev_ancestry:
        #     anc_data['dev'] = {}
        #     print(f'\t#### DEV')
        #     for key, value in dev_ancestry.items():
        #         percent = "{:.1f}".format((value/dev_ancestry_total)*100)
        #         print(f'\t>>>> PERCENT: {key} => {percent}%')
        #         anc_data['dev'][key] = percent
        # if data_eval_ancestry:
        #     anc_data['eval'] = {}
        #     print(f'\t#### EVAL')
        #     for key, value in data_eval_ancestry.items():
        #         percent = "{:.1f}".format((value/data_eval_ancestry_total)*100)
        #         print(f'\t>>>> PERCENT: {key} => {percent}%')
        #         anc_data['eval'][key] = percent
            score.ancestries = anc_data
            score.save()


################################################################################

def run():

    score_ancestry = UpdateScoreAncestry()
    score_ancestry.update_ancestry()
