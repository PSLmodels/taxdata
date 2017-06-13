from adj_filst import adjfilst
import cpsmar
from cps_rets import Returns
from soi_rets import create_soi
from phase1 import phaseone
from phase2 import phasetwo
from add_cps_vars import add_cps
from add_nonfilers import add_nonfiler
import pandas as pd
import argparse

"""
    Script to run each phase of the matching process
"""


def match(mar_cps_path='asec2014_pubuse_tax_fix_5x8.dat',
          puf_path='puf2009.csv'):
    # Add arguments for specifying path to CPS file in CSV format
    # this will allow the program to skip the process of creating the CPS from
    # a .DAT file.
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--cps', help='path to CPS file in CSV format')
    parser.add_argument('-d', '--dat', help='path to CPS file in DAT format')
    parser.add_argument('-p', '--puf', help='path to PUF file in CSV format')
    args = parser.parse_args()

    # Create CPS file either from a CPS or through create_cps method
    if args.cps is not None:
        mar_cps = pd.read_csv(args.cps)
    else:
        if args.dat is not None:
            mar_cps_path = args.dat
        mar_cps = cpsmar.create_cps(mar_cps_path)

    # If you already have the CPS in CSV format, comment out the line above and
    # uncomment the line bellow to skip creation from the DAT file and use CSV

    # do this initially in an effort to fix warning:
    # "A value is trying to be set on a copy of a slice from a DataFrame"
    if args.puf is not None:
        puf_path = args.puf
    puf = pd.read_csv(puf_path)
    puf = puf[puf['recid'] != 999999]

    print('CPS Created')
    rets = Returns(mar_cps)
    cps = rets.computation()

    print('CPS Tax Units Created')
    filers, nonfilers = adjfilst(cps)

    print('Adjustment Complete')
    soi = create_soi(puf.copy())

    print('PUF Created')
    soi_final, cps_final, counts = phaseone(filers, soi)

    print('Start Phase Two')
    match = phasetwo(
                soi_final.loc[:, ['cellid', 'soiseq', 'wt', 'factor', 'yhat']],
                cps_final.loc[:, ['cellid', 'cpsseq', 'wt', 'factor', 'yhat']])

    print('Creating final file')
    cpsrets = add_cps(filers, match, puf)
    cps_matched = add_nonfiler(cpsrets, nonfilers)
    # Rename variables for use in PUF data prep
    renames = {'icps1': 'age_head',
               'icps2': 'age_spouse',
               'wasp': 'wage_head',
               'wass': 'wage_spouse'}
    cps_matched = cps_matched.rename(columns=renames)

    return cps_matched


if __name__ == "__main__":
    cps_matched = match()
    cps_matched.to_csv('cps-matched-puf.csv', index=False)
