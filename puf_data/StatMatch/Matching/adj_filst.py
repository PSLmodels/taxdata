"""
Create tax units from the processed CPS data
Input file: CPSRETS2014.csv
"""

# import pandas as pd
import numpy as np


def adjfilst(cps_recs):
    """
    """
    # cps_recs = pd.read_csv('CPSRETS2014.csv')
    cps_recs['case1'] = np.where(((cps_recs['filst'] == 0) &
                                 (cps_recs['was'] > 0)), 1, 0)
    cps_recs['case2'] = np.where(((cps_recs['filst'] == 0) &
                                  (cps_recs['was'] <= 0)), 1, 0)
    np.random.seed(409)
    # the first iteration allowed all case1 and case2 records to be selected
    # since
    # 1) if record was case1 then case2 was set to zero and thus was selected
    # since it is less than 0.84 and 0.54
    # 2) vice versa but all case1 were set to zero
    cps_recs['z1'] = cps_recs.apply(lambda row: np.random.uniform(0, 1)
                                    if row['case1'] == 1 else 1
                                    if row['case2'] else 0, axis=1)

    cps_recs['z2'] = cps_recs.apply(lambda row: np.random.uniform(0, 1)
                                    if row['case2'] == 1 else 1
                                    if row['case1'] else 0, axis=1)

    # TODO: check the probability
    selected = (cps_recs['z1'] <= 0.84) | (cps_recs['z2'] <= 0.54)
    # cps_recs['filst'][selected] = 1
    cps_recs['filst'] = np.where(selected, 1, cps_recs['filst'])
    cps_recs.drop(['case1', 'case2'], axis=1, inplace=True)
    cps_recs['cpsseq'] = cps_recs.index + 1

    filers = cps_recs.copy()[(cps_recs['filst'] == 1)]
    nonfilers = cps_recs.copy()[(cps_recs['filst'] == 0)]

    # filers.to_csv('cpsrets14.csv', index=False)
    # nonfilers.to_csv('cpsnonf2014.csv', index=False)
    return filers, nonfilers
