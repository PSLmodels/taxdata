"""
Perform the match and evaluate the CPS variables.
Input file: soirets2009_ph1.csv, cpsrets14_ph1.csv
Output file: match.csv
"""
import numpy as np
import pandas as pd
from tqdm import tqdm


def phasetwo(SOI, CPS):

    CPS.loc[:, 'wt_adj'] = CPS['wt'] * CPS['factor']
    factor = 1.
    if CPS['wt'].sum() > 0:
        factor = SOI['wt'].sum() / float(CPS['wt'].sum())

    # CPS['wt_adj'] = CPS['wt'] * factor

    cellid = np.unique(SOI['cellid'].values)

    soi_list = list()
    cps_list = list()
    cwt_list = list()

    for cid in tqdm(cellid):
            soi = SOI[SOI['cellid'] == cid]
            cps = CPS[CPS['cellid'] == cid]
            soi = soi.sort_values('yhat', kind='mergesort')
            cps = cps.sort_values('yhat', kind='mergesort')

            soi = soi.to_dict('records')
            cps = cps.to_dict('records')

            j = 0
            bwt = cps[0]['wt_adj']
            count = len(cps) - 1
            epsilon = 0.001
            for record in soi:
                awt = record['wt']
                while awt > epsilon:
                    cwt = min(awt, bwt)
                    soiseq = record['soiseq']
                    cpsseq = cps[j]['cpsseq']

                    soi_list.append(soiseq)
                    cps_list.append(cpsseq)
                    cwt_list.append(cwt)

                    awt = max(0, awt - cwt)
                    bwt = max(0, bwt - cwt)

                    if bwt <= epsilon:
                        if j < count:
                            j += 1
                            bwt = cps[j]['wt_adj']

    match = pd.DataFrame({'soiseq': soi_list, 'cpsseq': cps_list,
                          'cwt': cwt_list})

    return match
