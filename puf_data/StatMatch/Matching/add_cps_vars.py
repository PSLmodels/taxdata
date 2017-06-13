"""
Put together the final Production File
Note: filers only
Input file: cpsrets14.csv, puf2009.sas7bdat, match.csv
Output file: cpsrets.csv
"""

import pandas as pd


def add_cps(cps_recs, match, puffile):
    # cps_recs = pd.read_csv('cpsrets14.csv')
    cpsfile = cps_recs.filter(regex='jcps\d{1,2}$|icps\d{1}$|jcps100|cpsseq|' +
                                    'nu\d{1,2}|nu18_dep|n1821|n21|' +
                                    'elderly_dependent|wasp|wass')
    # cpsfile = cps_recs
    # match = pd.read_csv('match.csv')
    # puffile = pd.read_sas('puf2009.sas7bdat')
    puffile = puffile[puffile['recid'] != 999999]
    puffile['filer'] = 1
    puffile['wt'] = puffile['s006'] / 100
    puffile['soiseq'] = puffile.index + 1

    match.sort_values(['cpsseq'], inplace=True)
    merge_1 = pd.merge(match, cpsfile,  how='left', on=['cpsseq'])
    merge_1.sort_values(['soiseq'], inplace=True)
    merge_2 = pd.merge(merge_1, puffile,  how='left', on=['soiseq'])

    merge_2['prodseq'] = merge_2.index + 1
    merge_2.rename(columns={'cwt': 'cweight'}, inplace=True)
    merge_2['matched_weight'] = merge_2['cweight']
    merge_2['cweight'] = merge_2['wt']
    # merge_2.to_csv('cpsrets.csv', index=False)
    return merge_2
