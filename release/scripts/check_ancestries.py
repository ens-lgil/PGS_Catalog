from catalog.models import Score, Performance
from pgs_web import constants

# "African American or Afro-Caribbean",
# "African American or Afro-Caribbean, Asian unspecified"
# "African unspecified"
# "Asian unspecified"
# "East Asian"
# "European"
# "European "
# "European, African American or Afro-Caribbean, Hispanic or Latin American"
# "European, African American or Afro-Caribbean, Hispanic or Latin American, South Asian"
# "European, African unspecified"
# "European, African unspecified, East Asian, Hispanic or Latin American"
# "European, African unspecified, Hispanic or Latin America, East Asian, South Asian"
# "European, African unspecified, Hispanic or Latin American, East Asian, South Asian"
# "European, African unspecified, South Asian, East Asian, NR"
# "European, Hispanic or Latin American, African unspecified"
# "European, NR"
# "European, Other"
# "European, South Asian, African unspecified, East Asian, NR"
# "European, South Asian, NR"
# "Greater Middle Eastern (Middle Eastern, North African or Persian)"
# "Hispanic or Latin American"
# "NR"
# "NR, Hispanic or Latin American, African unspecified, Asian unspecified"
# "Not reported"
# "Other"
# "Other admixed ancestry"
# "South Asian"
# "South Asian, South East Asian, East Asian"
# "South East Asian"
# "Sub-Saharan African"
# "Sub-Saharan African, African American or Afro-Caribbean"

ancestry_cat = constants.ANCESTRY_MAPPINGS
ancestry_cat_keys = ancestry_cat.keys()


ancestry_keys = constants.ANCESTRY_LABELS.keys()

extra_ancestry_cat = {
    "Multi-Ancestry (excluding European)": "MAO",
    "Multi-Ancestry (including European)": "MAE"
}

def get_ancestry_code(anc):
    a_code = ancestry_cat['Other']
    if anc in ancestry_cat_keys:
        a_code = ancestry_cat[anc]
    elif ',' in anc:
        if 'European' in anc:
            a_code = extra_ancestry_cat["Multi-Ancestry (including European)"]
        else:
            a_code = extra_ancestry_cat["Multi-Ancestry (excluding European)"]
    return a_code


def run():

    #for score in Score.objects.filter(num=739):
    for score in Score.objects.all():
        # Get Variant selection ancestries
        variant_ancestry = {}
        variant_ancestry_total = 0
        dev_ancestry = {}
        dev_ancestry_total = 0
        eval_ancestry = {}
        eval_ancestry_total = 0
        score_id = score.id
        print("# "+score_id+" #")
        print("\t> Variant:")
        for sample in score.samples_variants.all():
            ancestry = sample.ancestry_broad.strip()
            sample_number = sample.sample_number
            anc_code = get_ancestry_code(ancestry)
            print(f'\t\t- {ancestry} ({anc_code}): {sample_number}')
            if not anc_code in variant_ancestry:
                variant_ancestry[anc_code] = sample_number
            else:
                variant_ancestry[anc_code] += sample_number
            variant_ancestry_total += sample_number
        if len(variant_ancestry)==1 and variant_ancestry_total == 0:
            variant_ancestry_total = 1
            for key,value in variant_ancestry.items():
                variant_ancestry[key] = 1

        print("\t> Development:")
        for sample in score.samples_training.all():
            ancestry = sample.ancestry_broad.strip()
            sample_number = sample.sample_number
            anc_code = get_ancestry_code(ancestry)
            print(f'\t\t- {ancestry} ({anc_code}): {sample_number}')
            if not anc_code in dev_ancestry:
                dev_ancestry[anc_code] = sample_number
            else:
                dev_ancestry[anc_code] += sample_number
            dev_ancestry_total += sample_number
        if len(dev_ancestry)==1 and dev_ancestry_total == 0:
            dev_ancestry_total = 1
            for key,value in dev_ancestry.items():
                dev_ancestry[key] = 1

        print("\t> Evaluation:")
        publication_samplesets_list = set()
        performances = Performance.objects.filter(score__id=score_id)
        sampleset_sample_anc = {}
        for perf in performances:
            sampleset = perf.sampleset
            sampleset_id = sampleset.id
            publication_id = perf.publication.id
            key_id = publication_id+'_'+sampleset_id
            if key_id in publication_samplesets_list:
                continue
            publication_samplesets_list.add(key_id)
            print('\t ->'+publication_id+" | "+sampleset_id)
            for sample in sampleset.samples.all():
                ancestry = sample.ancestry_broad.strip()
                #sample_number = sample.sample_number
                anc_code = get_ancestry_code(ancestry)
                print(f'\t\t- {ancestry} ({anc_code}): {sample_number}')
                if key_id in sampleset_sample_anc.keys():
                    if not anc_code in sampleset_sample_anc[key_id]:
                        sampleset_sample_anc[key_id].append(anc_code)
                else:
                    sampleset_sample_anc[key_id] = [anc_code]
                # if not anc_code in eval_ancestry:
                #     eval_ancestry[anc_code] = 1 #sample_number
                # else:
                #     eval_ancestry[anc_code] += 1 #sample_number
                # eval_ancestry_total += 1 #sample_number
            if len(sampleset_sample_anc[key_id]) > 1:
                has_eur = 0
                for anc in sampleset_sample_anc[key_id]:
                    if anc == 'EUR':
                        has_eur = 1
                if has_eur == 1:
                    if 'MAE' in eval_ancestry:
                        eval_ancestry['MAE'] += 1
                    else:
                        eval_ancestry['MAE'] = 1
                else:
                    if 'MAO' in eval_ancestry:
                        eval_ancestry['MAO'] += 1
                    else:
                        eval_ancestry['MAO'] = 1
            else:
                anc_key = sampleset_sample_anc[key_id][0]
                if anc_key in eval_ancestry:
                    eval_ancestry[anc_key] += 1
                else:
                    eval_ancestry[anc_key] = 1
            eval_ancestry_total += 1
        # if len(eval_ancestry)==1 and eval_ancestry_total == 0:
        #     eval_ancestry_total = 1
        #     for key,value in eval_ancestry.items():
        #         eval_ancestry[key] = 1



        anc_data = {}
        if variant_ancestry:
            anc_data['gwas'] = {}
            print(f'\t#### GWAS')
            for key, value in variant_ancestry.items():
                percent = "{:.1f}".format((value/variant_ancestry_total)*100)
                print(f'\t>>>> PERCENT: {key} => {percent}%')
                anc_data['gwas'][key] = percent
        if dev_ancestry:
            anc_data['dev'] = {}
            print(f'\t#### DEV')
            for key, value in dev_ancestry.items():
                percent = "{:.1f}".format((value/dev_ancestry_total)*100)
                print(f'\t>>>> PERCENT: {key} => {percent}%')
                anc_data['dev'][key] = percent
        if eval_ancestry:
            anc_data['eval'] = {}
            print(f'\t#### EVAL')
            for key, value in eval_ancestry.items():
                percent = "{:.1f}".format((value/eval_ancestry_total)*100)
                print(f'\t>>>> PERCENT: {key} => {percent}%')
                anc_data['eval'][key] = percent
        score.ancestries = anc_data
        score.save()
