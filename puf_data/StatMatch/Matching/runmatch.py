from adj_filst import adjfilst
import cpsmar
from cps_rets import Returns
from soi_rets import create_soi
from phase1 import phaseone
from phase2 import phasetwo
from add_cps_vars import add_cps
from add_nonfilers import add_nonfiler
import pandas as pd
import os

"""
Script to run each phase of the matching process
"""

CUR_PATH = os.path.abspath(os.path.dirname(__file__))


def match():
    # If there is a .CSV version of the CPS, simply read that in. Otherwise
    # convert the .DAT file to a .CSV
    cps_csv_path = os.path.join(CUR_PATH, 'cpsmar2016.csv')
    if os.path.isfile(cps_csv_path):
        print('Reading CPS Data from .CSV')
        mar_cps = pd.read_csv(cps_csv_path)
    else:
        cps_dat_path = os.path.join(CUR_PATH, 'asec2016_pubuse_v3.dat')
        if os.path.isfile(cps_dat_path):
            print('Converting .DAT to .CSV')
            mar_cps = cpsmar.create_cps(cps_dat_path)
        else:
            m = ('You must have either the .DAT or .CSV version of the 2016' +
                 ' CPS in your directory')
            raise FileNotFoundError(m)
    print('Reading PUF Data')
    puf_path = os.path.join(CUR_PATH, 'puf2011.csv')
    puf = pd.read_csv(puf_path)
    # Change PUF columns to lowercase
    puf.columns = map(str.lower, puf.columns)
    # Remove aggregated variables from the PUF
    puf = puf[(puf['recid'] != 999996) & (puf['recid'] != 999997) &
              (puf['recid'] != 999998) & (puf['recid'] != 999999)]

    print('Creating CPS Tax Units')
    rets = Returns(mar_cps)
    cps = rets.computation()

    print('CPS Tax Units Created')
    filers, nonfilers = adjfilst(cps)

    print('Adjustment Complete')
    soi = create_soi(puf.copy())

    print('Start Phase One')
    filers = filers.fillna(0)
    soi = soi.fillna(0)
    soi_final, cps_final, counts = phaseone(filers, soi)

    print('Start Phase Two')
    match = phasetwo(
                soi_final.loc[:, ['cellid', 'soiseq', 'wt', 'factor', 'yhat']],
                cps_final.loc[:, ['cellid', 'cpsseq', 'wt', 'factor', 'yhat']])

    print('Creating final file')
    cpsrets = add_cps(filers, match, puf)
    cps_matched = add_nonfiler(cpsrets, nonfilers)
    # add age range variable
    cps_matched['agerange'] = 0
    # Rename variables for use in PUF data prep
    renames = {'icps1': 'age_head',
               'icps2': 'age_spouse',
               'wasp': 'wage_head',
               'wass': 'wage_spouse'}
    cps_matched = cps_matched.rename(columns=renames)

    return cps_matched


if __name__ == "__main__":
    cps_matched = match()
    cps_matched_path = os.path.join(CUR_PATH, '../../cps-matched-puf.csv')
    cps_matched.to_csv(cps_matched_path, index=False,
                       float_format='%.2f')
