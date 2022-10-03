############################################
# multi_test_template.py
# ----------------------
# Generic script for tunning multiple qpAdm tests.
# Need to copy over and replace the following attributes:
# REPLACE_WITH_DATASET_PATH - path of data set (path of file, not including ind/geno/snp extension)
# REPLACE_WITH_LIST_OF_TARGET_POPS    - python list of target pop ids
# REPLACE_WITH_LIST_OF_REFERENCE_POPS -python list of reference pop ids
# REPLACE_WITH_LIST_OF_SOURCE_POPS    -python list of source pop ids
############################################

import itertools, json, sys, os
from datetime import datetime

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = "/home/igronau/projects/phoenician/methods/adna-scripts"
PACKAGES = os.path.join(BASE_DIR, 'packages')
# print(BASE_DIR , PACKAGES)
sys.path.append(BASE_DIR)
sys.path.append(PACKAGES)

from lib.DataSet import DataSet
#from lib.QpAdmRunner import QpAdmRunnerBuilder

import tempfile
import math
import json

from scipy import stats
from prettytable import PrettyTable

from lib.utils import write_par_file, write_pop_file
from lib.AdmixTools import AdmixTools

class QpAdmRunnerBuilder:

    def __init__(self, dataset, admix_tools=None):
        self.dataset = dataset
        self.admix_tools = admix_tools or AdmixTools()

    def BuildQpAdmRunner(self, left_pops, right_pops):
        return QpAdmRunner(self.dataset, left_pops, right_pops, self.admix_tools)

class QpAdmRunner:

    def __init__(self, dataset, left_pops, right_pops, admix_tools):
        self.dataset = dataset
        self.left_pops = left_pops
        self.right_pops = right_pops
        self.admix_tools = admix_tools

    def run_test(self, output_format, additional_params=[]):
        qpadm_raw_log = self.execute_qpadm(additional_params)
        if output_format == 'full':
            return qpadm_raw_log
        try:
            json_results = self.parse_qpadm_log(qpadm_raw_log)
        except Exception as e:
            print(e)
            print(qpadm_raw_log)
            raise e
        self.get_p_value_for_nested_models(json_results)
        if output_format == 'short':
            return self.get_short_summary(json_results)
        return json.dumps(json_results, indent=4, sort_keys=True)

    def execute_qpadm(self, additional_params):
        qpadm_raw_log = ''
        with tempfile.NamedTemporaryFile() as par_file, tempfile.NamedTemporaryFile() as l_pop_file, tempfile.NamedTemporaryFile() as r_pop_file:
            qpadm_params = self.get_qpadm_params(l_pop_file.name, r_pop_file.name, additional_params)
            write_par_file(qpadm_params, par_file.name, force=True)
            write_pop_file(self.left_pops, l_pop_file.name, force=True)
            write_pop_file(self.right_pops, r_pop_file.name, force=True)
            qpadm_raw_log = self.admix_tools.run_qpadm(par_file.name)

        return qpadm_raw_log

    # all snps is provided through additional params if needed
    def get_qpadm_params(self, l_pop_file, r_pop_file, additional_params=[]):
        params = {
            'genotypename': self.dataset.get_geno_file(),
            'snpname': self.dataset.get_snp_file(),
            'indivname': self.dataset.get_ind_file(),
            'popleft':  l_pop_file,
            'popright': r_pop_file,
            'details': 'YES',
            'maxrank': '7'
        }

        for param in additional_params:
            params[param[0]] = param[1]
        return params


    def parse_qpadm_log(self, qpadm_log):
        if len(self.left_pops) == 2:
            return self.parse_qpadm_single_source_log(qpadm_log)
        results = []
        lines = qpadm_log.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if line.endswith('...') and i < len(lines):
                lines[i+1] = line.replace('...','') + lines[i+1]
                del lines[i]
        # index = [idx for idx, s in enumerate(lines) if s.startswith('summ: ')][0] + 3
        index = [idx for idx, s in enumerate(lines) if s.strip().startswith('fixed pat ')][0] + 1
        number_of_lines = int(math.pow(2, len(self.left_pops) -1))
        data_lines = lines[index:index + number_of_lines -1]
        for data_line in data_lines:
            line_summary = self.parse_summary_line(data_line)
            results.append(line_summary)
        return results

    def parse_qpadm_single_source_log(self, qpadm_log):
        results = []
        lines = qpadm_log.split('\n')
        for line in lines:
            if line.startswith('f4rank: 0'):
                parsed_line = line.split()
                summary = {
                    'participating_pops': [self.left_pops[1]],
                    'pops': {}
                }
                summary['pops'][self.left_pops[1]] = {
                    'participated': True,
                    'proportion': 1
                }
                summary['tail_probability'] = parsed_line[7]
                summary['chisq'] = parsed_line[5]
                summary['dof'] = parsed_line[3]
                summary['feasible'] = True
                results.append(summary)
        return results


    def parse_summary_line(self, summary_line):
        values = summary_line.split()
        # print(summary_line)
        # print(values)
        summary = {
            'participating_pops': [],
            'pops': {}
        }
        for index, pop_code in enumerate(values[0]): # values[0] is the code for which population participate 000 - all participated
            participated = pop_code == '0'
            if participated:
                summary['participating_pops'].append(self.left_pops[index + 1])
                proportion = values[5 + index]
            else:
                proportion = 'N/A'
            summary['pops'][self.left_pops[index + 1]] = {
                'participated': participated,
                'proportion': proportion
            }
        summary['tail_probability'] = values[4]
        summary['chisq'] = values[3]
        summary['dof'] = values[2]
        summary['feasible'] = len(values) == 4 + len(self.left_pops)
        # summary['parent_models'] = []
        # summary['nested_p_parent_models'] = []
        return summary

    def get_p_value_for_nested_models(self, qpadm_results):
        parent_model = None
        for pop_summary in qpadm_results:
            if len(pop_summary['participating_pops']) - len(pop_summary['pops']) == 0: #the parent model is the one where all the populations are participating
                parent_model = pop_summary
        if not parent_model: # TODO throw an exception
            return
        
        for pop_summary1 in qpadm_results:
            pop_summary1['parent_models'] = []
            for pop_summary2 in qpadm_results:
                if len(pop_summary1['participating_pops']) - len(pop_summary2['participating_pops']) == -1 and set(pop_summary1['participating_pops']) <= set(pop_summary2['participating_pops']):
                    pop_summary1['parent_models'].append(pop_summary2)

        for pop_summary in qpadm_results:
            pop_summary['nested_p_parent_models'] = [0] * len(pop_summary['pops'])
            chisq_diff = float(pop_summary['chisq']) - float(parent_model['chisq'])
            dof_diff = int(pop_summary['dof']) - int(parent_model['dof'])
            pop_summary['nested_p_value'] = 1 - stats.chi2.cdf(chisq_diff, dof_diff)
            #i = 0
            for pop_summary2 in qpadm_results:
                if pop_summary2 in pop_summary['parent_models']:
                    chisq_diff = float(pop_summary['chisq']) - float(pop_summary2['chisq'])
                    dof_diff = int(pop_summary['dof']) - int(pop_summary2['dof'])
                    missing_pop = [p for p in pop_summary2['participating_pops'] if p not in pop_summary['participating_pops']]
                    i = sources_all.index(missing_pop[0])
                    pop_summary['nested_p_parent_models'][i] = 1 - stats.chi2.cdf(chisq_diff, dof_diff)
                    #i += 1



    def get_short_summary(self, qpadm_results):
        table = PrettyTable()
        field_names = ['number of populations', 'feasible', 'chisq',  'dof']
        pops = self.left_pops[1:]
        field_names.extend(pops)
        field_names.extend(['tail probability', 'nested p-value'])
        nested_string = 'nested_p_with_'
        for p in pops:
            field_names.extend([nested_string + str(p)])
        table.field_names = field_names
        for model_summary in qpadm_results:
            number_of_populations = len(model_summary['participating_pops'])
            feasible = model_summary['feasible']
            chisq = model_summary['chisq']
            dof = model_summary['dof']
            proportions = [model_summary['pops'][pop]['proportion'] for pop in pops]
            tail_probability = model_summary['tail_probability']
            nested_p_value = model_summary['nested_p_value']
            nested_p_parent_models = model_summary['nested_p_parent_models']
            row = [number_of_populations, feasible, chisq, dof]
            row.extend(proportions)
            row.extend([tail_probability, nested_p_value])
            row.extend(nested_p_parent_models)
            table.add_row(row)
        return table.get_string()


from lib.utils import load_settings

from prettytable import PrettyTable
from prettytable import MSWORD_FRIENDLY

dataset_name = 'REPLACE_WITH_DATASET_PATH'
targets      = REPLACE_WITH_LIST_OF_TARGET_POPS
references   = REPLACE_WITH_LIST_OF_REFERENCE_POPS
sources_all  = REPLACE_WITH_LIST_OF_SOURCE_POPS
move_src_to_ref = MOVE_SRC_TO_REF

def get_qpadm_test_cases():
    tests = []
    if not move_src_to_ref:
        tests.append((list(sources_all), references ))
        return tests

    for i in range(1,1+len(sources_all)):
        for test_sources in itertools.combinations(sources_all, i):
            test_additional_refs = [item for item in sources_all if item not in test_sources]
            tests.append((list(test_sources), references + test_additional_refs))
            #tests.append( (list(test_sources), references) )
    return tests


def run_qpadm_test(dataset, left_pops, right_pops):
    qpadm_runner = QpAdmRunnerBuilder(dataset).BuildQpAdmRunner(left_pops, right_pops)
    additional_params = [('allsnps', 'YES')]
    print("Running test for ",left_pops, datetime.now().strftime("%H:%M:%S"))
    sys.stdout.flush()
    test_result = qpadm_runner.run_test('JSON', additional_params)
    return json.loads(test_result)


def get_short_summary(target, references, qpadm_results):
    table = PrettyTable()
    field_names = ['target', 'numpops', 'feasible', 'chisq',  'dof']
    pops = sources_all
    field_names.extend(pops)
    field_names.extend(['prob', 'nested-p'])
    nested_string = 'nested_p_with_'
    for p in pops:
        field_names.extend([nested_string + str(p)])
    table.field_names = field_names
    # for target in targets:
    # for qpadm_results in multi_qpadm_results:
    for model_summary in qpadm_results:
        number_of_populations = len(model_summary['participating_pops'])
        feasible = model_summary['feasible']
        chisq = model_summary['chisq']
        dof = model_summary['dof']
        proportions = [model_summary['pops'][pop]['proportion'] if pop in model_summary['pops'] and model_summary['pops'][pop]['proportion']!= 'N/A' else 'REF' if pop in references else 0 for pop in pops]
        tail_probability = model_summary['tail_probability']
        nested_p_value = model_summary['nested_p_value']
        nested_p_parent_models = model_summary['nested_p_parent_models']
        row = [target, number_of_populations, feasible, chisq, dof]
        row.extend(proportions)
        row.extend([tail_probability, nested_p_value])
        row.extend(nested_p_parent_models)
        table.add_row(row)
    #table.add_row(['-----' for field_name in field_names])
    #table.set_style(MSWORD_FRIENDLY)
    return table.get_string()

def main():
    load_settings()
    dataset = DataSet.get_dataset_from_name_pattern(dataset_name)
    test_cases = get_qpadm_test_cases()
    test_results = {}
    print("References:\t",references)
    
    for target in targets:
        test_results[target] = []
        for test_case in test_cases:
            (left_pops, right_pops) = test_case
            test_result = run_qpadm_test(dataset, [target] + left_pops, right_pops)
            test_results[target].append(test_result)
            print(get_short_summary(target, right_pops, test_result))
    # print(get_short_summary(test_results))


if __name__ == "__main__":
    main()
