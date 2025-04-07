"""Pre-process OSeMOSYS data file to reduce matrix generation time

This script pre-processes an OSeMOSYS input data file by adding lines that list 
commodity-technology-mode combinations that data is provided for. Pre-processing 
a data file before starting a model run significantly reduces the time taken 
for matrix generation. 

 Pre-processing consists of the following steps:

1. Reading the ``InputActivityRatio`` and ``OutputActivityRatio`` sections of the 
data file to identify commodity-technology-mode combinations that data has been 
explicitly provided for.
2. Adding a set entry for each commodity that lists all technology-mode combinations 
that are associated with it.  
3. Values from the ``InputActivityRatios`` and ``OutputActivityRatios`` sections are 
added to the sets ``MODExTECHNOLOGYperFUELin`` and ``MODExTECHNOLOGYperFUELout`` respectively.
4. Values from the ``TechnologyToStorage`` and ``TechnologyFromStorage`` sections 
are added to the sets ``MODExTECHNOLOGYperSTORAGEto`` and ``MODExTECHNOLOGYperSTORAGEfrom`` respectively.
5. All values for technology-mode combinations are added to the sets 
``MODEperTECHNOLOGY``.

 In order to start a model run with a pre-processed data file, the following sets 
need to be introduced to its associated OSeMOSYS model file::

    set MODEperTECHNOLOGY{TECHNOLOGY} within MODE_OF_OPERATION;
    set MODExTECHNOLOGYperFUELout{COMMODITY} within MODE_OF_OPERATION cross TECHNOLOGY;
    set MODExTECHNOLOGYperFUELin{COMMODITY} within MODE_OF_OPERATION cross TECHNOLOGY;
    set MODExTECHNOLOGYperSTORAGEto{STORAGE} within MODE_OF_OPERATION cross TECHNOLOGY;
    set MODExTECHNOLOGYperSTORAGEfrom{STORAGE} within MODE_OF_OPERATION cross TECHNOLOGY;

"""

import pandas as pd
import os, sys
from collections import defaultdict
import re


def main(data_infile, data_outfile, model_file, model_processed):

    lines = []

    with open(data_infile, 'r') as f1:
        for line in f1:
            if not line.startswith(('set MODEper','set MODEx', 'end;')):
                lines.append(line)

    with open(data_outfile, 'w') as f2:
        f2.writelines(lines)

    parsing = False
    parsing_year = False
    parsing_tech = False
    parsing_fuel = False
    parsing_mode = False
    parsing_storage = False
    parsing_emission = False

    otoole = False

    year_list = []
    fuel_list = []
    tech_list = []
    storage_list = []
    mode_list = []
    emission_list = []

    data_all = []
    data_out = []
    data_inp = []
    output_table = []
    storage_to = []
    storage_from = []
    emission_table = []

    params_to_check = ['OutputActivityRatio', 
                       'InputActivityRatio', 
                       'TechnologyToStorage', 
                       'TechnologyFromStorage', 
                       'EmissionActivityRatio']

    with open(data_infile, 'r') as f:
        for line in f:
            line = line.rstrip().replace('\t', ' ')
            if line.startswith('# Model file written by *otoole*'):
                otoole = True
            if parsing_year:
                year_list += [line.strip()] if line.strip() not in ['', ';'] else []
            if parsing_fuel:
                fuel_list += [line.strip()] if line.strip() not in ['', ';'] else []
            if parsing_tech:
                tech_list += [line.strip()] if line.strip() not in ['', ';'] else []
            if parsing_storage:
                storage_list += [line.strip()] if line.strip() not in ['', ';'] else []
            if parsing_mode:
                mode_list += [line.strip()] if line.strip() not in ['', ';'] else []
            if parsing_emission:
                emission_list += [line.strip()] if line.strip() not in ['', ';'] else []

            if line.startswith('set YEAR'):
                if len(line.split('=')[1]) > 1:
                    year_list = line.split(' ')[3:-1]
                else:
                    parsing_year = True
            if line.startswith('set COMMODITY'):  # Extracts list of COMMODITIES from data file. Some models use FUEL instead.
                if len(line.split('=')[1]) > 1:
                    fuel_list = line.split(' ')[3:-1]
                else:
                    parsing_fuel = True
            if line.startswith('set FUEL'):  # Extracts list of FUELS from data file. Some models use COMMODITIES instead.
                if len(line.split('=')[1]) > 1:
                    fuel_list = line.split(' ')[3:-1]
                else:
                    parsing_fuel = True
            if line.startswith('set TECHNOLOGY'):
                if len(line.split('=')[1]) > 1:
                    tech_list = line.split(' ')[3:-1]
                else:
                    parsing_tech = True
            if line.startswith('set STORAGE '): # Blank space required to avoid double counting from sets like STORAGEINTRAYEAR
                if len(line.split('=')[1]) > 1:
                    storage_list = line.split(' ')[3:-1]
                else:
                    parsing_storage = True
            if line.startswith('set MODE_OF_OPERATION'):
                if len(line.split('=')[1]) > 1:
                    mode_list = line.split(' ')[3:-1]
                else:
                    parsing_mode = True
            if line.startswith('set EMISSION'):
                if len(line.split('=')[1]) > 1:
                    emission_list = line.split(' ')[3:-1]
                else:
                    parsing_emission = True

            if line.startswith(";"):
                parsing_year = False
                parsing_tech = False
                parsing_fuel = False
                parsing_mode = False
                parsing_storage = False
                parsing_emission = False

    start_year = year_list[0]

    if not otoole:
        with open(data_infile, 'r') as f:
            for line in f:
                line = line.rstrip().replace('\t', ' ')
                if line.startswith(";"):
                    parsing = False

                if parsing:
                    if line.startswith('['):
                        fuel = line.split(',')[2]
                        tech = line.split(',')[1]
                    elif line.startswith(start_year):
                        years = line.rstrip(':= ;\n').split(' ')[0:]
                        years = [i.strip(':=') for i in years]
                    else:
                        values = line.rstrip().split(' ')[1:]
                        mode = line.split(' ')[0]

                        if param_current =='OutputActivityRatio':
                            data_out.append(tuple([fuel, tech, mode]))
                            data_all.append(tuple([tech, mode]))
                            for i in range(0,len(years)):
                                output_table.append(tuple([tech, fuel, mode, years[i], values[i]]))

                        if param_current =='InputActivityRatio':
                            data_inp.append(tuple([fuel, tech, mode]))
                            data_all.append(tuple([tech, mode]))

                        if param_current == 'TechnologyToStorage' or param_current == 'TechnologyFromStorage':
                            if not line.startswith(mode_list[0]):
                                storage = line.split(' ')[0]
                                values = line.rstrip().split(' ')[1:]
                                for i in range(0, len(mode_list)):
                                    if values[i] != '0':
                                        if param_current == 'TechnologyToStorage':
                                            storage_to.append(tuple([storage, tech, mode_list[i]]))
                                            data_all.append(tuple([tech, mode_list[i]]))
                                        if param_current == 'TechnologyFromStorage':
                                            storage_from.append(tuple([storage, tech, mode_list[i]]))
                                            data_all.append(tuple([tech, mode_list[i]]))

                if line.startswith(('param OutputActivityRatio',
                                    'param InputActivityRatio',
                                    'param TechnologyToStorage',
                                    'param TechnologyFromStorage')):
                    param_current = line.split(' ')[1]
                    parsing = True

    if otoole:
        with open(data_infile, 'r') as f:
            for line in f:
                details = line.split(' ')
                if line.startswith(";"):
                    parsing = False
                if parsing:
                    if len(details) > 1:
                        if param_current == 'OutputActivityRatio':
                            tech = details[1].strip()
                            fuel = details[2].strip()
                            mode = details[3].strip()
                            year = details[4].strip()
                            value = details[5].strip()

                            if float(value) != 0.0:
                                data_out.append(tuple([fuel, tech, mode]))
                                output_table.append(tuple([tech, fuel, mode, year, value]))
                                data_all.append(tuple([tech, mode]))

                        if param_current == 'InputActivityRatio':
                            tech = details[1].strip()
                            fuel = details[2].strip()
                            mode = details[3].strip()
                            value = details[5].strip()
                            if float(value) != 0.0:
                                data_inp.append(tuple([fuel, tech, mode]))
                                data_all.append(tuple([tech, mode]))

                        if param_current == 'TechnologyToStorage':
                            tech = details[1].strip()
                            storage = details[2].strip()
                            mode = details[3].strip()
                            value = details[4].strip()
                            if float(value) > 0.0:
                                storage_to.append(tuple([storage, tech, mode]))
                                data_all.append(tuple([storage, mode]))

                        if param_current == 'TechnologyFromStorage':
                            tech = details[1].strip()
                            storage = details[2].strip()
                            mode = details[3].strip()
                            value = details[4].strip()
                            if float(value) > 0.0:
                                storage_from.append(tuple([storage, tech, mode]))
                                data_all.append(tuple([storage, mode]))

                        if param_current == 'EmissionActivityRatio':
                            tech = details[1].strip()
                            emission = details[2].strip()
                            mode = details[3].strip()
                            value = details[5].strip()
                            if float(value) != 0.0:
                                emission_table.append(tuple([emission, tech, mode]))
                                data_all.append(tuple([tech, mode]))

                if any(param in line for param in params_to_check):
                    param_current = details[-2]
                    parsing = True

    data_out = list(set(data_out))
    data_inp = list(set(data_inp))
    data_all = list(set(data_all))
    storage_to = list(set(storage_to))
    storage_from = list(set(storage_from))
    emission_table = list(set(emission_table))

    dict_out = defaultdict(list)
    dict_inp = defaultdict(list)
    dict_all = defaultdict(list)
    dict_stt = defaultdict(list)
    dict_stf = defaultdict(list)

    for fuel, tech, mode in data_out:
        dict_out[fuel].append((mode, tech))

    for fuel, tech, mode in data_inp:
        dict_inp[fuel].append((mode, tech))

    for tech, mode in data_all:
        if mode not in dict_all[tech]:
            dict_all[tech].append(mode)

    for storage, tech, mode in storage_to:
        dict_stt[storage].append((mode, tech))

    for storage, tech, mode in storage_from:
        dict_stf[storage].append((mode, tech))

    def file_output_function(if_dict, str_dict, set_list, set_name, extra_char):
        for each in set_list:
            if each in if_dict.keys():
                line = set_name + str(each) + ']:=' + str(str_dict[each]) + extra_char
                if set_list == tech_list:
                    line = line.replace(',', '').replace(':=[', ':= ').replace(']*', '').replace("'", "")
                else:
                    line = line.replace('),', ')').replace('[(', ' (').replace(')]', ')').replace("'", "")
            else:
                line = set_name + str(each) + ']:='
            file_out.write(line + ';' + '\n')

    # Append lines at the end of the data file
    with open(data_outfile, 'w') as file_out:  # 'a' to open in 'append' mode

        file_out.writelines(lines)

        file_output_function(dict_out, dict_out, fuel_list, 'set MODExTECHNOLOGYperFUELout[', '')
        file_output_function(dict_inp, dict_inp, fuel_list, 'set MODExTECHNOLOGYperFUELin[', '')
        file_output_function(dict_all, dict_all, tech_list, 'set MODEperTECHNOLOGY[', '*')

        if '' not in storage_list:
            file_output_function(dict_stt, dict_stt, storage_list, 'set MODExTECHNOLOGYperSTORAGEto[', '')
            file_output_function(dict_stf, dict_stf, storage_list, 'set MODExTECHNOLOGYperSTORAGEfrom[', '')

        file_out.write('end;')

    with open(model_file, 'r') as model_in:

        line_count = 0
        parsing_sets = 0  # 0 - start; 1 - parsing main sets;
        parsing_params = 0
        parsing_all = 0
        model_lines = []
        set_list = []
        sets_new = ['MODExTECHNOLOGYperFUELout',
                    'MODExTECHNOLOGYperFUELin',
                    'MODEperTECHNOLOGY',
                    'MODExTECHNOLOGYperSTORAGEto',
                    'MODExTECHNOLOGYperSTORAGEfrom',
                    'TIMESLICEofSEASON',
                    'TIMESLICEofDAYTYPE',
                    'TIMESLICEofDAILYTIMEBRACKET',
                    'TIMESLICEofSDB',
                    'MODExTECHNOLOGYperEMISSION',
                    'MODExTECHNOLOGYperEMISSIONChange']

        sets_of_sets = False
        var_count = 0

        for line in model_in:
            line_count += 1
            set_name = ''

            if line.startswith('set'):
                set_name = line.replace('{', ' ').strip('#;{\n').split(' ')[1]
                set_list.append(set_name)
                if set_name not in sets_new:
                    model_lines.append(line)
                    parsing_sets = 1

            if parsing_sets == 1:

                if line.startswith('#'):
                    # if not any(item in sets_new for item in set_list):

                    if 'COMMODITY' in set_list:
                        model_lines.append('set MODEperTECHNOLOGY{TECHNOLOGY} within MODE_OF_OPERATION;\n')
                        model_lines.append('set MODExTECHNOLOGYperFUELout{COMMODITY} within MODE_OF_OPERATION cross TECHNOLOGY;\n')
                        model_lines.append('set MODExTECHNOLOGYperFUELin{COMMODITY} within MODE_OF_OPERATION cross TECHNOLOGY;\n')
                        model_lines.append('set MODExTECHNOLOGYperSTORAGEto{STORAGE} within MODE_OF_OPERATION cross TECHNOLOGY;\n')
                        model_lines.append('set MODExTECHNOLOGYperSTORAGEfrom{STORAGE} within MODE_OF_OPERATION cross TECHNOLOGY;\n')
                    if 'FUEL' in set_list:
                        model_lines.append('set MODEperTECHNOLOGY{TECHNOLOGY} within MODE_OF_OPERATION;\n')
                        model_lines.append('set MODExTECHNOLOGYperFUELout{FUEL} within MODE_OF_OPERATION cross TECHNOLOGY;\n')
                        model_lines.append('set MODExTECHNOLOGYperFUELin{FUEL} within MODE_OF_OPERATION cross TECHNOLOGY;\n')
                        model_lines.append('set MODExTECHNOLOGYperSTORAGEto{STORAGE} within MODE_OF_OPERATION cross TECHNOLOGY;\n')
                        model_lines.append('set MODExTECHNOLOGYperSTORAGEfrom{STORAGE} within MODE_OF_OPERATION cross TECHNOLOGY;\n')
                    parsing_sets = 2

            if line.startswith('param'):
                model_lines.append(line)
                parsing_params = 1

            if parsing_params == 1:
                if line.startswith('\t'):
                    model_lines.append(line)

                if line.startswith('  '):
                    if 'exists' not in line:
                        model_lines.append(line)

                if 'MODExTECHNOLOGYperFUELout' in line:
                    sets_of_sets = True

                if 'var' in line:
                    var_count += 1
                    # if sets_of_sets:
                    if var_count == 1:
                        if 'SEASON' in set_list:
                            model_lines.append('set TIMESLICEofSEASON{ls in SEASON} within TIMESLICE := {l in TIMESLICE : Conversionls[l,ls] = 1};\n')
                            model_lines.append('set TIMESLICEofDAYTYPE{ld in DAYTYPE} within TIMESLICE := {l in TIMESLICE : Conversionld[l,ld] = 1};\n')
                            model_lines.append('set TIMESLICEofDAILYTIMEBRACKET{lh in DAILYTIMEBRACKET} within TIMESLICE := {l in TIMESLICE : Conversionlh[l,lh] = 1};\n')
                            model_lines.append('set TIMESLICEofSDB{ls in SEASON, ld in DAYTYPE, lh in DAILYTIMEBRACKET} within TIMESLICE := TIMESLICEofSEASON[ls] inter TIMESLICEofDAYTYPE[ld] inter TIMESLICEofDAILYTIMEBRACKET[lh];\n')
                        model_lines.append('set MODExTECHNOLOGYperEMISSION{e in EMISSION} within MODE_OF_OPERATION cross TECHNOLOGY\n')
                        model_lines.append('    := {m in MODE_OF_OPERATION, t in TECHNOLOGY : exists{r in REGION, y in YEAR} EmissionActivityRatio[r,t,e,m,y] <> 0};\n')
                        model_lines.append('set MODExTECHNOLOGYperEMISSIONChange{e in EMISSION} within MODE_OF_OPERATION cross TECHNOLOGY\n')
                        model_lines.append('    := {m in MODE_OF_OPERATION, t in TECHNOLOGY : exists{r in REGION, y in YEAR} (EmissionToActivityChangeRatio[r,t,e,m,y] <> 0 or EmissionActivityRatio[r,t,e,m,y] <> 0)};\n')
                    parsing_params = 2
                    parsing_all = 1

            if parsing_all == 1:
                if not line.startswith('#'):
                    model_lines.append(line)


        with open(model_processed, 'w') as model_out:
            model_out.writelines(model_lines)


if __name__ == '__main__':

    if len(sys.argv) != 5:
        msg = "Usage: python {} <infile> <outfile> <model_file> <model_processed>"
        print(msg.format(sys.argv[0]))
        sys.exit(1)
    else:
        data_infile = sys.argv[1]
        data_outfile = sys.argv[2]
        model_file = sys.argv[3]
        model_processed = sys.argv[4]
        main(data_infile, data_outfile, model_file, model_processed)
