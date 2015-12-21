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


import sys
import pandas


def main():
    """
    Contains all the logic of the puf-cps-processing.py script.
    """

    # (*) Read unprocessed puf-cps.csv file into a Pandas Dataframe
    data = pandas.read_csv('cps-puf.csv')


    # (A) Make recid variable be a unique integer key:
    #     The recid (key) for each record is not unique after CPS match
    #     because (1) original SOI PUF records were split in some cases,
    #     and (2) non-filers were added from the CPS.
    #     This problem is fixed by (1) adding a digit at the end of recid
    #     for all original SOI PUF records (if no duplicates, add zero;
    #     otherwise, differentiate duplicates by numbering them with
    #     increment integers starting from zero), and (2) setting recid for
    #     all CPS non-filers to integers beginning with 4000000.

    # sort all the records based on old recid
    sorted_dta = data.sort(columns='recid')

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

    # (B) Make several variable names be uppercase as in SOI PUF:
    renames = {
        'agir1': 'AGIR1',
        'dsi': 'DSI',
        'efi': 'EFI',
        'eic': 'EIC',
        'elect': 'ELECT',
        'fded': 'FDED',
        'flpdyr': 'FLPDYR',
        'flpdmo': 'FLPDMO',
        'ie': 'IE',
        'mars': 'MARS',
        'midr': 'MIDR',
        'prep': 'PREP',
        'schb': 'SCHB',
        'schcf': 'SCHCF',
        'sche': 'SCHE',
        'tform': 'TFORM',
        'txst': 'TXST',
        'xfpt': 'XFPT',
        'xfst': 'XFST',
        'xocah': 'XOCAH',
        'xocawh': 'XOCAWH',
        'xoodep': 'XOODEP',
        'xopar': 'XOPAR',
        'xtot': 'XTOT',
        'recid': 'RECID',
        'wsamp': 'WSAMP',
        'txrt': 'TXRT',
        'agerange': 'AGERANGE',
    }
    data = data.rename(columns=renames)

    # (*) Write processed data to the final puf.csv file
    data.to_csv('puf.csv', index=False)

    return 0
# end of main function code


if __name__ == '__main__':
    sys.exit(main())
