"""
puf-cps-processing.py transforms puf-cps.csv into final puf.csv file.

COMMAND-LINE USAGE: python puf-cps-processing.py INPUT

This script transforms the raw csv file in several ways as described below.
"""
# CODING-STYLE CHECKS:
# pep8 --ignore=E402 puf-cps-processing.py
# pylint --disable=locally-disabled --extension-pkg-whitelist=numpy xxx.py
# (when importing numpy, add "--extension-pkg-whitelist=numpy" pylint option)

# disable pylint warning about script name having dashes instead of underscores
# pylint: disable=invalid-name


import argparse
import sys
import pandas
import numpy as np


def main():
    """
    Contains all the logic of the puf-cps-processing.py script.
    """
    parser = argparse.ArgumentParser(
        prog='python puf-cps-processing.py',
    )
    parser.add_argument('INPUT',
                        help=('INPUT is name of required CSV file that '
                              'contains data from original PUF or '
                              'CPS-matched PUF.'))
    args = parser.parse_args()

    # (*) Read unprocessed puf-cps.csv file into a Pandas Dataframe
    data = pandas.read_csv(args.INPUT)

    # check the PUF year
    max_flpdyr = max(data['flpdyr'])
    if max_flpdyr == 2008:
        data = transform_2008_varnames_to_2009_varnames(data)
    else:  # if PUF year is 2009+
        data = age_consistency(data)

    # (A) Make recid variable be a unique integer key:
    data = create_new_recid(data)

    # (B) Make several variable names be uppercase as in SOI PUF:
    data = capitalize_varnames(data)

    # (C) Impute cmbtp_standard and cmbtp_itemizer variables:
    data['cmbtp_standard'] = data['e62100'] - data['e00100'] + data['e00700']
    zero = np.zeros(len(data.index))
    medical_limit = np.maximum(zero, data['e17500'] -
                               np.maximum(zero, data['e00100']) * 0.075)
    med_adj = np.minimum(medical_limit,
                         0.025 * np.maximum(zero, data['e00100']))
    stx_adj = np.maximum(zero, data['e18400'])
    data['cmbtp_itemizer'] = (data['e62100'] - med_adj + data['e00700'] +
                              data['p04470'] + data['e21040'] - stx_adj -
                              data['e00100'] - data['e18500'] -
                              data['e20800'])

    # (D) Split earnings variables into taxpayer (p) and spouse (s) amounts:
    total = np.where(data['MARS'] == 2,
                     data['wage_head'] + data['wage_spouse'], 0)
    earnings_split = np.where(total != 0,
                              data['wage_head'] / total, 1.)
    one_minus_earnings_split = 1.0 - earnings_split
    data['e00200p'] = earnings_split * data['e00200']
    data['e00200s'] = one_minus_earnings_split * data['e00200']
    data['e00900p'] = earnings_split * data['e00900']
    data['e00900s'] = one_minus_earnings_split * data['e00900']
    data['e02100p'] = earnings_split * data['e02100']
    data['e02100s'] = one_minus_earnings_split * data['e02100']

    # (E) Remove variables not expected by Tax-Calculator
    if max_flpdyr >= 2009:
        data = remove_unused_variables(data)

    # (*) Write processed data to the final puf.csv file
    data.to_csv('puf.csv', index=False)

    return 0
# end of main function code


def create_new_recid(data):
    """
    Construct unique recid.
    """
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


def age_consistency(data):
    """
    Construct age_head and age_spouse from agerange if available;
    otherwise use CPS values of age_head and age_spouse.
    """
    # set random-number-generator seed so that always get same random_integers
    np.random.seed(seed=123456789)
    # generate random integers to smooth age distribution in agerange
    shape = data['age_head'].shape
    agefuzz8 = np.random.random_integers(0, 8, size=shape)
    agefuzz9 = np.random.random_integers(0, 9, size=shape)
    agefuzz10 = np.random.random_integers(0, 10, size=shape)
    agefuzz15 = np.random.random_integers(0, 15, size=shape)

    # assign age_head using agerange midpoint or CPS age if agerange absent
    data['age_head'] = np.where(data['agerange'] == 0,
                                data['age_head'],
                                (data['agerange'] + 1 - data['dsi']) * 10)

    # smooth the agerange-based age_head within each agerange
    data['age_head'] = np.where(np.logical_and(data['agerange'] == 1,
                                               data['dsi'] == 0),
                                data['age_head'] - 3 + agefuzz9,
                                data['age_head'])
    data['age_head'] = np.where(np.logical_and(data['agerange'] == 2,
                                               data['dsi'] == 0),
                                data['age_head'] - 4 + agefuzz9,
                                data['age_head'])
    data['age_head'] = np.where(np.logical_and(data['agerange'] == 3,
                                               data['dsi'] == 0),
                                data['age_head'] - 5 + agefuzz10,
                                data['age_head'])
    data['age_head'] = np.where(np.logical_and(data['agerange'] == 4,
                                               data['dsi'] == 0),
                                data['age_head'] - 5 + agefuzz10,
                                data['age_head'])
    data['age_head'] = np.where(np.logical_and(data['agerange'] == 5,
                                               data['dsi'] == 0),
                                data['age_head'] - 5 + agefuzz10,
                                data['age_head'])
    data['age_head'] = np.where(np.logical_and(data['agerange'] == 6,
                                               data['dsi'] == 0),
                                data['age_head'] - 5 + agefuzz15,
                                data['age_head'])
    data['age_head'] = np.where(np.logical_and(data['agerange'] == 1,
                                               data['dsi'] == 1),
                                data['age_head'] - 0 + agefuzz8,
                                data['age_head'])
    data['age_head'] = np.where(np.logical_and(data['agerange'] == 2,
                                               data['dsi'] == 1),
                                data['age_head'] - 2 + agefuzz8,
                                data['age_head'])
    data['age_head'] = np.where(np.logical_and(data['agerange'] == 3,
                                               data['dsi'] == 1),
                                data['age_head'] - 4 + agefuzz10,
                                data['age_head'])

    # assign age_spouse using agerange midpoint or CPS age if agerange absent
    data['age_spouse'] = np.where(data['agerange'] == 0,
                                  data['age_spouse'],
                                  (data['agerange'] + 1 - data['dsi']) * 10)

    # smooth the agerange-based age_spouse within each agerange
    data['age_spouse'] = np.where(np.logical_and(data['agerange'] == 1,
                                                 data['dsi'] == 0),
                                  data['age_spouse'] - 3 + agefuzz9,
                                  data['age_spouse'])
    data['age_spouse'] = np.where(np.logical_and(data['agerange'] == 2,
                                                 data['dsi'] == 0),
                                  data['age_spouse'] - 4 + agefuzz9,
                                  data['age_spouse'])
    data['age_spouse'] = np.where(np.logical_and(data['agerange'] == 3,
                                                 data['dsi'] == 0),
                                  data['age_spouse'] - 5 + agefuzz10,
                                  data['age_spouse'])
    data['age_spouse'] = np.where(np.logical_and(data['agerange'] == 4,
                                                 data['dsi'] == 0),
                                  data['age_spouse'] - 5 + agefuzz10,
                                  data['age_spouse'])
    data['age_spouse'] = np.where(np.logical_and(data['agerange'] == 5,
                                                 data['dsi'] == 0),
                                  data['age_spouse'] - 5 + agefuzz10,
                                  data['age_spouse'])
    data['age_spouse'] = np.where(np.logical_and(data['agerange'] == 6,
                                                 data['dsi'] == 0),
                                  data['age_spouse'] - 5 + agefuzz15,
                                  data['age_spouse'])
    data['age_spouse'] = np.where(np.logical_and(data['agerange'] == 1,
                                                 data['dsi'] == 1),
                                  data['age_spouse'] - 0 + agefuzz8,
                                  data['age_spouse'])
    data['age_spouse'] = np.where(np.logical_and(data['agerange'] == 2,
                                                 data['dsi'] == 1),
                                  data['age_spouse'] - 2 + agefuzz8,
                                  data['age_spouse'])
    data['age_spouse'] = np.where(np.logical_and(data['agerange'] == 3,
                                                 data['dsi'] == 1),
                                  data['age_spouse'] - 4 + agefuzz10,
                                  data['age_spouse'])

    # convert any zero ages to age one
    data['age_head'] = np.where(data['age_head'] == 0,
                                1, data['age_head'])
    data['age_spouse'] = np.where(data['age_spouse'] == 0,
                                  1, data['age_spouse'])

    return data


def capitalize_varnames(data):
    """
    Capitalize some variable names.
    """
    renames = {
        'dsi': 'DSI',
        'eic': 'EIC',
        'fded': 'FDED',
        'flpdyr': 'FLPDYR',
        'mars': 'MARS',
        'midr': 'MIDR',
        'xtot': 'XTOT',
        'recid': 'RECID',
    }
    data = data.rename(columns=renames)
    return data


def remove_unused_variables(data):
    """
    Delete variables not expected by Tax-Calculator.
    """
    data['s006'] = data['matched_weight'] * 100

    UNUSED_READ_VARS = [
        'agir1', 'efi', 'elect', 'flpdmo', 'wage_head', 'wage_spouse',
        'f3800', 'f8582', 'f8606', 'f8829', 'f8910', 'f8936',
        'n20', 'n25', 'n30', 'prep', 'schb', 'schcf', 'sche',
        'tform', 'ie', 'txst', 'xfpt', 'xfst',
        'xocah', 'xocawh', 'xoodep', 'xopar', 'agerange',
        'gender', 'earnsplit', 'agedp1', 'agedp2', 'agedp3',
        's008', 's009', 'wsamp', 'txrt', 'matched_weight',
        'e01000', 'e03260', 'e09400', 'e24516', 'e62720', 'e62730',
        'e62740', 'e05100', 'e05800', 'e08800', 'e15360',
        'e00100', 'e20800', 'e21040', 'e62100',
        'e87870', 'e30400', 'e24598', 'e11300', 'e24535', 'e30500',
        'e07180', 'e53458', 'e33000', 'e25940', 'e12000', 'p65400',
        'e15210', 'e24615', 'e07230', 'e11100', 'e10900', 'e11581',
        'e11582', 'e11583', 'e25920', 's27860', 'e10960', 'e59720',
        'e87550', 'e26190', 'e53317', 'e53410', 'e04600', 'e26390',
        'e15250', 'p65300', 'p25350', 'e06500', 'e10300', 'e26170',
        'e26400', 'e11400', 'p25700', 'e04250', 'e07150',
        'e59680', 'e24570', 'e11570', 'e53300', 'e10605', 'e22320',
        'e26160', 'e22370', 'e53240', 'p25380', 'e10700', 'e09600',
        'e06200', 'e24560', 'p61850', 'e25980', 'e53280', 'e25850',
        'e25820', 'e10950', 'e68000', 'e26110', 'e58950', 'e26180',
        'e04800', 'e06000', 'e87880', 't27800', 'e06300', 'e59700',
        'e26100', 'e05200', 'e87875', 'e82200', 'e25860', 'e07220',
        'e11900', 'e18600', 'e25960', 'e15100', 'p27895', 'e12200']
    data = data.drop(UNUSED_READ_VARS, 1)

    data = data.fillna(value=0)
    return data


def transform_2008_varnames_to_2009_varnames(data):
    """
    Convert 2008 IRS-SOI PUF variable names into 2009 PUF variable names.
    """
    data['e18400'] = data['e18425'] + data['e18450']

    # drop unused variables only existing in 2008 IRS-SOI PUF
    UNUSED = {'e18425', 'e18450', 'e25370', 'e25380', 'state',
              'e87500', 'e87510', 'e87520', 'e87540'}
    data = data.drop(UNUSED, 1)

    # drop variables not expected by Tax-Calculator
    UNUSED_READ_VARS = {
        'agir1', 'efi', 'elect', 'flpdmo',
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
        'e26400', 'e11400', 'p25700', 'e04250', 'e07150',
        'e59680', 'e24570', 'e11570', 'e53300', 'e10605', 'e22320',
        'e26160', 'e22370', 'e53240', 'e10700', 'e09600',
        'e06200', 'e24560', 'p61850', 'e25980', 'e53280', 'e25850',
        'e25820', 'e68000', 'e26110', 'e58950', 'e26180',
        'e04800', 'e06000', 't27800', 'e06300', 'e59700',
        'e26100', 'e05200', 'e82200', 'e25860', 'e07220',
        'e11900', 'e25960', 'p27895', 'e12200'}
    data = data.drop(UNUSED_READ_VARS, 1)
    return data


if __name__ == '__main__':
    sys.exit(main())
