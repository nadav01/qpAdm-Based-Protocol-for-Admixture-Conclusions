import argparse
import pandas as pd
from collections import defaultdict
import os
import csv

parser = argparse.ArgumentParser("Nadav's Protocol")
parser.add_argument("tsvfiles", help="The tsv files to be parsed. give list of files as string without spaces: MAIN_RUN_FILE,VALIDATION_FILE_[MISSING_SOURCE_POPULATION_NAME], ... , VALIDATION_FILE_[MISSING_SOURCE_POPULATION_NAME]. Should be located in the same directory.", type=str)
parser.add_argument("tpop", help="Comma seperated list of target population names", type=str)
parser.add_argument("sources", help="Give list of sources as string without spaces: Anatolia_N,Armenia_ChL,Steppe_MLBA,Tunisia_N,Megiddo_MLBA_original", type=str)
parser.add_argument("references", help="Give a comma seperated list of references of the main run as string without spaces", type=str)
parser.add_argument("tail_prob_threshold", help="The lower bound of tail probability for accepting models", type=float)
parser.add_argument("pval_threshold", help="The bound of pvalue for accepting models", type=float)
args = parser.parse_args()

tsvfiles = args.tsvfiles.lower().split(',')
target_pop_list = args.tpop.lower().split(',')
tail_prob_threshold = args.tail_prob_threshold
pval_threshold = args.pval_threshold
SOURCES = args.sources.lower().split(',')
_references = args.references.lower()
comments = defaultdict(lambda: '')

protocol_summary = [] # list of lists, every list is a row: target_pop  %   %   %...

for target_pop in target_pop_list:
    valid_models_in_base_run = 'Yes'
    total_num_of_contained_compact_models = 0
    changed_classification_due_to_questionable_models_counter = 0
    print(target_pop)

    conclusions = defaultdict(lambda: '')
    conclusions["source population"] = "conclusions"
    output_files = []

    for file in tsvfiles:
        df = pd.read_csv(file, sep='\t', skiprows=1) # skipping the first 2 rows
        sources = SOURCES.copy()
        references = _references
        if 'validation' in file.lower():
            filename = file.split('.')[0].lower()
            for source in sources:
                if source in filename:
                    sources.remove(source)
                    references = references + ',' + source

        NUM_OF_SOURCES = len(sources)

        models = []
        for i in range(len(df)):
            if df.iloc[i].iloc[0].lower() == target_pop:
                models.append(df.iloc[i][1:-1])

        models_dict = {}


        # creating the participating string for all the models ('1' means the pop is participating, '0' otherwise)
        for model in models:
            m_string = ''
            pops = model[1:NUM_OF_SOURCES+1]
            for p in pops:
                if p != 0:
                    m_string += '1'
                else:
                    m_string += '0'
            models_dict[m_string] = model


        # calculating p-values for all the models
        for mstring in models_dict.keys():
            model = models_dict[mstring]
            i = 0
            for pop in mstring:
                if pop == '0':
                    i += 1
                    continue
                else:
                    new_mstring = mstring[:i] + '0' + mstring[i+1:]
                    if new_mstring == '0' * NUM_OF_SOURCES:
                        i += 1
                        continue
                    if new_mstring in models_dict.keys():
                        new_model = models_dict[new_mstring]
                        pval = new_model[1 + i + 2 + NUM_OF_SOURCES]
                        models_dict[mstring][1 + i + 2 + NUM_OF_SOURCES] = pval
                    i += 1

        valid_models = []
        FEASIBILITY_STATUS = 0
        TAIL_PROB = 1 + NUM_OF_SOURCES
        for model in models_dict.values():
            if model[FEASIBILITY_STATUS] and model[TAIL_PROB] > tail_prob_threshold:
                valid_models.append(model)

        # Compact Models
        compact_models = []

        for model in valid_models:
            add = True
            for i in range(NUM_OF_SOURCES):
                _add = True

                if model[1 + i] != 0: # the examined population is participating
                    pval = model[1 + i + 2 + NUM_OF_SOURCES]
                    _add = pval < pval_threshold

                else: # the examined population is not participating
                    pval = model[1 + i + 2 + NUM_OF_SOURCES]
                    _add = pval > pval_threshold

                add = add and _add

            if add:
                compact_models.append(model)

        # After finishing the above iteration, we will perform a final iteration over the compact models - for every
        # compact model, we will check if there is another compact model whose participating populations are contained in the
        # participating populations of the examined compact model. If there is such a model, the examined model will be
        # unmarked as a compact model and marked as a contained compact model.

        contained_compact_models = []

        for model in compact_models:
            m_string = ''
            pops = model[1:NUM_OF_SOURCES + 1]
            for p in pops:
                if p != 0:
                    m_string += '1'
                else:
                    m_string += '0'
            for model2 in compact_models:
                m2_string = ''
                pops2 = model2[1:NUM_OF_SOURCES + 1]
                for p in pops2:
                    if p != 0:
                        m2_string += '1'
                    else:
                        m2_string += '0'

                # check if m2_pops <= m_pops, if yes delete it
                contained = True
                for i in range(NUM_OF_SOURCES):
                    if int(m2_string[i]) <= int(m_string[i]):
                        continue
                    else:
                        contained = False
                        break
                if contained:
                    if m2_string != m_string: # if it is not the same model
                        contained_compact_models.append(model)
                        break

        # unmarking as compact
        for cm in contained_compact_models:
            compact_models.remove(cm)


        # iterate again over all of the valid models - if there is a valid model V such that there is no compact model whose
        # participating populations are contained in the set of participating populations of V, mark V as questionably compact
        questionable_models = []

        for model in valid_models:
            m_string = ''
            pops = model[1:NUM_OF_SOURCES + 1]
            for p in pops:
                if p != 0:
                    m_string += '1'
                else:
                    m_string += '0'
            contained = False
            for cmodel in compact_models:
                m2_string = ''
                cpops = cmodel[1:NUM_OF_SOURCES + 1]
                for p in cpops:
                    if p != 0:
                        m2_string += '1'
                    else:
                        m2_string += '0'

                # check if m2_pops <= m_pops, if yes delete it
                _contained = True
                for i in range(NUM_OF_SOURCES):
                    if int(m2_string[i]) <= int(m_string[i]):
                        continue
                    else:
                        _contained = False
                        break
                contained = contained or _contained
                if contained:
                    break
            if not contained:
                questionable_models.append(model)
                break

        contributing_populations = []
        non_contributing_populations = []
        ambiguous = []

        number_of_changed_classification_due_to_questionable_models = 0

        for i in range(NUM_OF_SOURCES):
            clear_sig = True
            clear_insig = True

            for model in (compact_models + contained_compact_models):
                if model[1 + i] != 0:
                    clear_insig = False
                else:
                    clear_sig = False

            for model in questionable_models:
                if model[1 + i] != 0:
                    if clear_insig:
                        number_of_changed_classification_due_to_questionable_models += 1
                    clear_insig = False
                else:
                    if clear_sig:
                        number_of_changed_classification_due_to_questionable_models += 1
                    clear_sig = False

            if clear_sig:
                contributing_populations.append(sources[i])
            if clear_insig:
                non_contributing_populations.append(sources[i])
            if (not clear_sig) and (not clear_insig):
                ambiguous.append(sources[i])

        comment = ""
        if len(valid_models) == 0:
            contributing_populations = []
            non_contributing_populations = []
            ambiguous = []
            comment = "NO VALID MODELS"

        # Output
        run_name = ' '.join(file.split('.')[0].lower().split('_'))
        if 'validation' in file:
            comments[references.split(',')[-1]] = comment
            changed_classification_due_to_questionable_models_counter += number_of_changed_classification_due_to_questionable_models

            run_name += ' in reference set'
        titles_strings = ["RUN", "Target sample", "Source populations", "Reference populations", "Thresholds", "contributing populations",
                          "non-contributing populations", "ambiguous populations", "number of valid models",
                          "number of compact models", "number of questionable models",
                          "number of changed classification due to questionable models", "number of compact models that contain a compact model", "comment"]
        values = [run_name, target_pop, ", ".join(sources), references, "tail_prob="+str(tail_prob_threshold)+", p_value="+str(pval_threshold),
                  ", ".join(contributing_populations), ", ".join(non_contributing_populations), ", ".join(ambiguous),
                  len(valid_models), len(compact_models), len(questionable_models),
                  number_of_changed_classification_due_to_questionable_models, len(contained_compact_models), comment]

        df_data = dict(zip(titles_strings, values))
        output = pd.DataFrame(df_data, index=[0])
        output.to_csv("protocol_output_" + target_pop + "_" + file.split('.')[0] + ".csv")
        output_files.append("protocol_output_" + target_pop + "_" + file.split('.')[0] + ".csv")

        classifications = {}
        classifications["valid models"] = "classification"
        for model in valid_models:
            if str(model) in [str(x) for x in compact_models]:
                classifications[str(model)] = 'Compact'
            elif str(model) in [str(x) for x in contained_compact_models]:
                classifications[str(model)] = 'Compact that Contain a Compact'
            elif str(model) in [str(x) for x in questionable_models]:
                classifications[str(model)] = 'Questionably Compact'
            else:
                classifications[str(model)] = 'Not Compact'

        # output valid models classifications file
        df_data_cl = classifications
        output_cl = pd.DataFrame(df_data_cl, index=[0])
        output_cl.to_csv("protocol_valid_models_classifications_" + target_pop + "_" + file + ".csv")
        output_files.append("protocol_valid_models_classifications_" + target_pop + "_" + file + ".csv")

        total_num_of_contained_compact_models += len(contained_compact_models)

        # updating conclusions
        for source in sources:
            conc = file.split('.')[0] + ': '
            if source in contributing_populations:
                conc += 'Contributing\n'
            elif source in non_contributing_populations:
                conc += 'Non-Contributing\n'
            elif source in ambiguous:
                conc += 'Ambiguous\n'
            else:
                continue
            conclusions[source] += conc

    # output conclusions file
    df_data_co = conclusions
    output_co = pd.DataFrame(df_data_co, index=[0])
    output_co.to_csv("protocol_conclusions_" + target_pop + ".csv")
    output_files.append("protocol_conclusions_" + target_pop + ".csv")

    # summary line
    percentages = []
    _comment = ''
    _total_num_of_runs = 0
    for source in SOURCES:
        conc = conclusions[source]
        vec = [conc.count(' Contributing'), conc.count('Ambiguous'), conc.count('Non-')]
        num_of_runs = conc.count('\n')
        _total_num_of_runs = max([_total_num_of_runs, num_of_runs])
        str_row = ''
        if num_of_runs == 0:
            #str_row += 'No valid models when participating\nas a source population'
            str_row += "--"
            percentages.append(str_row)
            continue
        """
        str_row += ('Contributing: ' + str(round(conc.count(' Contributing')/num_of_runs, 4)*100) + "%\n"
                           + 'Non-Contributing: ' + str(round(conc.count('Non-')/num_of_runs, 4)*100) + "%\n"
                           + 'Ambiguous: ' + str(round(conc.count('Ambiguous')/num_of_runs, 4)*100) + "%\n"
                           + 'based on ' + str(num_of_runs) + ' runs')
        """
        if comments[source] == "NO VALID MODELS":
            if len(str_row) > 1:
                str_row += '\n'
            #str_row += 'No valid models when participating\nas a reference population'
            vec.append(0)
        if comments[source] != "NO VALID MODELS":
            vec.append(1)

        # Calculating contribution score
        _contri = (conc.count(' Contributing') * (1/(2*num_of_runs)))
        _non_contri = -1 * (conc.count('Non-') * (1/(2*num_of_runs)))
        _valid_coef = -0.5
        if comments[source] == "NO VALID MODELS":
            _valid_coef = 0.5 # if there are not valid models when in reference it stretengh its contribution
        total_contribution_score = _contri + _non_contri + _valid_coef
        #str_row += '\nContribution score: ' + str(round(total_contribution_score, 4))
        vec.append(round(total_contribution_score, 2))
        str_row += str(vec)[1:-1]
        percentages.append(str_row)
    _comment = str(changed_classification_due_to_questionable_models_counter)
    protocol_summary.append([target_pop] + percentages + [valid_models_in_base_run] + [str(_total_num_of_runs)] + [str(total_num_of_contained_compact_models)] + [_comment])

    fout = open("Protocol_Report_" + target_pop + ".csv", "a")
    for file in output_files:
        for line in open(file):
            fout.write(line)
        fout.write("\n")
    fout.close()

    for file in output_files:
        os.remove(file)

# Protocol_Conclusions_Summary
# first row is the sources, first column are the targets
fout = open("Protocol_Summary" + ".csv", "a")
write_outfile = csv.writer(fout)
columns = ['target'] + SOURCES + ['valid models\nin base run?'] + ['total # of runs'] + ['# of compact that\ncontain a compact'] + ['# of changed classifications\ndue to questionable models']
write_outfile.writerow(columns)
for line in protocol_summary:
    write_outfile.writerow(line)
fout.close()

# Color Summary

summary_csv = pd.read_csv("Protocol_Summary.csv")

def _color_cell(c):
    try:
        val = float(c.split(' ')[-1])
        if val >= 0.25:
            return 'background-color: green'
        if val <= -0.25:
            return 'background-color: red'
        return 'background-color: yellow'
    except:
        return ''


summary_csv.style.applymap(_color_cell).to_excel('Protocol_Summary_Colored.xlsx', index=False, engine='openpyxl')
