"""
puf-cps-processing.py transforms puf-cps.csv into final puf.csv file.

COMMAND-LINE USAGE: python puf-cps-processing.py

This script transforms the raw csv file in several ways as described below.
"""
# CODING-STYLE CHECKS:
# pep8 --ignore=E402 puf-cps-processing.py
# pylint --disable=locally-disabled puf-cps-processing.py
# (when importing numpy, add "--extension-pkg-whitelist=numpy" pylint option)

# disable pylint warning about script name having dashes instead of underscores
# pylint: disable=invalid-name


import argparse
import sys
import pandas


def main():
    """
    Contains all the logic of the puf-cps-processing.py script.
    """
    parser = argparse.ArgumentParser(
        prog='python puf-cps-processing.csv',
    )

    parser.add_argument('INPUT',
                        help=('INPUT is name of required CSV file that contained'
                              'data from original PUF or cps-matched PUF. '))
                              
    args = parser.parse_args()
    
    # (*) Read unprocessed puf-cps.csv file into a Pandas Dataframe
    data = pandas.read_csv(args.INPUT)
    
    # check the PUF year
    if max(data['flpdyr']) == 2008:
        data = transform_variables_to_09(data)
    else:
        data = remove_unused_variables(data)

    # (A) Make recid variable be a unique integer key:
    data = creat_new_recid(data)

    # (B) Make several variable names be uppercase as in SOI PUF:
    data = capitalize_var_names(data)

    # (*) Write processed data to the final puf.csv file
    data.to_csv('puf.csv', index=False)

    return 0
# end of main function code


def creat_new_recid(data):

    #     The recid (key) for each record is not unique after CPS match
    #     because (1) original SOI PUF records were split in some cases,
    #     and (2) non-filers were added from the CPS.
    #     This problem is fixed by (1) adding a digit at the end of recid
    #     for all original SOI PUF records (if no duplicates, add zero;
    #     otherwise, differentiate duplicates by numbering them with
    #     increment integers starting from zero), and (2) setting recid for
    #     all CPS non-filers to integers beginning with 4000000.
    
    # sort all the records based on old recid
    sorted_dta = data.sort_values(by='recid')
    
    # count how many duplicates each old recid has
    # and save the dup count for each record
    seq = sorted_dta.index
    length = len(sorted_dta['recid'])
    count = [0 for _ in range(length)]
    for index in range(1, length):
        num = seq[index]
        previous = seq[index - 1]
        if sorted_dta['recid'][num] == sorted_dta['recid'][previous]:
            count[num] = count[previous] + 1

    # adding the ending digit for filers and non-filers with the dup count
    new_recid = [0 for _ in range(length)]
    for index in range(0, length):
        if data['recid'][index] == 0:
            new_recid[index] = 4000000 + count[index]
        else:
            new_recid[index] = data['recid'][index] * 10 + count[index]

    # replace the old recid with the new one
    data['recid'] = new_recid

    return data

def capitalize_var_names(data):
    renames = {
        'dsi': 'DSI',
        'eic': 'EIC',
        'fded': 'FDED',
        'flpdyr': 'FLPDYR',
        'mars': 'MARS',
        'midr': 'MIDR',
        'xtot': 'XTOT',
        'recid': 'RECID',
        'agerange': 'AGERANGE',
    }
    data = data.rename(columns=renames)
    return data

def remove_unused_variables(data):
    data['s006'] = data['matched_weight'] * 100
    UNUSED_READ_VARS = {'agir1', 'efi', 'elect', 'flpdmo',
                        'f3800', 'f8582', 'f8606', 'f8829', 'f8910', 'f8936',
                        'n20', 'n25', 'n30', 'prep', 'schb', 'schcf', 'sche',
                        'tform', 'ie', 'txst', 'xfpt', 'xfst',
                        'xocah', 'xocawh', 'xoodep', 'xopar',
                        'gender','earnsplit','agedp1', 'agedp2', 'agedp3',
                        's008', 's009', 'wsamp', 'txrt', 'matched_weight',
                        'e87870', 'e30400', 'e24598', 'e11300', 'e24535', 'e30500',
                        'e07180', 'e53458', 'e33000', 'e25940', 'e12000', 'p65400',
                        'e15210', 'e24615', 'e07230', 'e11100', 'e10900', 'e11581',
                        'e11582', 'e11583', 'e25920', 's27860', 'e10960', 'e59720',
                        'e87550', 'e26190', 'e53317', 'e53410', 'e04600', 'e26390',
                        'e15250', 'p65300', 'p25350', 'e06500', 'e10300', 'e26170',
                        'e26400', 'e11400', 'p25700', 'e01500', 'e04250', 'e07150',
                        'e59680', 'e24570', 'e11570', 'e53300', 'e10605', 'e22320',
                        'e26160', 'e22370', 'e53240', 'p25380', 'e10700', 'e09600',
                        'e06200', 'e24560', 'p61850', 'e25980', 'e53280', 'e25850',
                        'e25820', 'e10950', 'e68000', 'e26110', 'e58950', 'e26180',
                        'e04800', 'e06000', 'e87880', 't27800', 'e06300', 'e59700',
                        'e26100', 'e05200', 'e87875', 'e82200', 'e25860', 'e07220',
                        'e11900', 'e18600', 'e25960', 'e15100', 'p27895', 'e12200'}
    data = data.drop(UNUSED_READ_VARS, 1)
    return data

def transform_variables_to_09(data):
    data['e18400'] = data['e18425'] + data['e18450']

    # drop unused variables only existing in 08 PUF
    UNUSED = {'e18425', 'e18450', 'e25370', 'e25380', 'state',
              'e87500', 'e87510', 'e87520', 'e87540'}
    data = data.drop(UNUSED, 1)

    UNUSED_READ_VARS = {'agir1', 'efi', 'elect', 'flpdmo',
                        'f3800', 'f8582', 'f8606',
                        'n20', 'n25', 'prep', 'schb', 'schcf', 'sche',
                        'tform', 'ie', 'txst', 'xfpt', 'xfst',
                        'xocah', 'xocawh', 'xoodep', 'xopar',
                        's008', 's009', 'wsamp', 'txrt',
                        'e30400', 'e24598', 'e11300', 'e24535', 'e30500',
                        'e07180', 'e53458', 'e33000', 'e25940', 'e12000', 'p65400',
                        'e24615', 'e07230', 'e11100', 'e10900', 'e11581',
                        'e11582', 'e11583', 'e25920', 's27860', 'e59720',
                        'e87550', 'e26190', 'e53317', 'e53410', 'e04600', 'e26390',
                        'p65300', 'p25350', 'e06500', 'e10300', 'e26170',
                        'e26400', 'e11400', 'p25700', 'e01500', 'e04250', 'e07150',
                        'e59680', 'e24570', 'e11570', 'e53300', 'e10605', 'e22320',
                        'e26160', 'e22370', 'e53240', 'e10700', 'e09600',
                        'e06200', 'e24560', 'p61850', 'e25980', 'e53280', 'e25850',
                        'e25820', 'e68000', 'e26110', 'e58950', 'e26180',
                        'e04800', 'e06000', 't27800', 'e06300', 'e59700',
                        'e26100', 'e05200', 'e82200', 'e25860', 'e07220',
                        'e11900', 'e25960', 'p27895', 'e12200'}
    data = data.drop(UNUSED_READ_VARS,1)
    return data

if __name__ == '__main__':
    sys.exit(main())
