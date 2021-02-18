from catalog.models import Score, Performance

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

ancestry_cat = {
    "African American or Afro-Caribbean": "AFR",
    "African unspecified" : "AFR",
    "East Asian": "EAS",
    "European": "EUR",
    "Hispanic or Latin American": "AMR",
    "South Asian": "SAS",
    "South East Asian": "EAS",
    "Sub-Saharan African": "AFR",
    "Sub-Saharan African, African American or Afro-Caribbean": "AFR",
    "Other": "OTH",
    "NR": "NR" # Not reported
}
ancestry_cat_keys = ancestry_cat.keys()

extra_ancestry_cat = {
    "Multi-Ancestry (excluding European)": "MA",
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

    #for score in Score.objects.filter(num__lte=20):
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
        performances = Performance.objects.filter(score__id=score_id)
        for perf in performances:
            sampleset = perf.sampleset
            for sample in sampleset.samples.all():
                ancestry = sample.ancestry_broad.strip()
                sample_number = sample.sample_number
                anc_code = get_ancestry_code(ancestry)
                print(f'\t\t- {ancestry} ({anc_code}): {sample_number}')
                if not anc_code in eval_ancestry:
                    eval_ancestry[anc_code] = sample_number
                else:
                    eval_ancestry[anc_code] += sample_number
                eval_ancestry_total += sample_number
        if len(eval_ancestry)==1 and eval_ancestry_total == 0:
            eval_ancestry_total = 1
            for key,value in eval_ancestry.items():
                eval_ancestry[key] = 1


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
