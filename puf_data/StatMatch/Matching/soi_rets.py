"""
Create a composite extract from the SOI 2009 Public Use File
Input file: puf2009.sas7bdat
Output file: SOIRETS2009.csv
"""
# import pandas as pd
import numpy as np


def create_soi(SOI):

    SOI.loc[:, 'filer'] = 1
    SOI.loc[:, 'dmfs'] = 1
    SOI.loc[(SOI['mars'] == 3) | (SOI['mars'] == 6), 'dmfs'] = 0.5
    SOI.loc[:, 'js'] = 2
    SOI.loc[SOI['mars'] == 1, 'js'] = 1
    SOI.loc[SOI['mars'] == 4, 'js'] = 3
    SOI.loc[:, 'depne'] = (SOI['xocah'] + SOI['xocawh'] + SOI['xoodep'] +
                           SOI['xopar'])
    SOI.loc[:, 'agep'] = np.nan
    SOI.loc[:, 'ages'] = np.nan
    SOI.loc[:, 'agede'] = 0
    SOI.loc[SOI['e02400'] > 0, 'agede'] = 1
    SOI.loc[:, 'wasp'] = np.nan
    SOI.loc[:, 'wass'] = np.nan
    SOI.loc[:, 'ssincp'] = np.nan
    SOI.loc[:, 'ssincs'] = np.nan
    SOI.loc[:, 'returns'] = 1
    SOI.loc[:, 'oldest'] = np.nan
    SOI.loc[:, 'youngest'] = np.nan
    SOI.loc[:, 'agepsqr'] = np.nan

    adjust = (SOI['e03150'] + SOI['e03210'] + SOI['e03220'] + SOI['e03230'] +
              SOI['e03260'] + SOI['e03270'] + SOI['e03240'] + SOI['e03290'] +
              SOI['e03300'] + SOI['e03400'] + SOI['e03500'])
    SOI.loc[:, 'totincx'] = SOI['e00100'] + adjust

    SOI.rename(columns={'xocah': 'cahe', 'xocawh': 'cafhe',
                        'xoodep': 'othdep', 'dsi': 'ifdept',
                        'xopar': 'parents',
                        'e00200': 'was', 'e00300': 'intst', 'e00400': 'texint',
                        'e00600': 'dbe', 'e00800': 'alimony', 'e00900': 'bil',
                        'e01500': 'pensions', 'e01700': 'ptpen',
                        'e02100': 'fil', 'e02300': 'ucagix', 'e02400': 'ssinc',
                        'e02500': 'ssagix', 'e00100': 'agix',
                        'e04800': 'tincx'},
               inplace=True)

    # I wanted to include 'e02000' in SOI.rename list. But somehow the column
    # is series before renaming, and DataFrame afterwards.
    SOI.loc[:,  'sche'] = SOI['e02000']

    SOI.loc[:, 'xifdept'] = SOI['ifdept']
    SOI.loc[:, 'xdepne'] = SOI['depne']
    SOI.loc[:, 'xagede'] = SOI['agede']
    SOI.loc[:, 'income'] = SOI['totincx']

    wt = SOI['s006'] / 100.0
    SOI.loc[:, 'wt'] = wt * 1.03  # TODO: check the number

    SOI.loc[:, 'sequence'] = SOI.index + 1
    SOI.loc[:, 'soiseq'] = SOI.index + 1

    columns_to_keep = ['js', 'parents',
                       'ifdept', 'cahe', 'cafhe', 'othdep', 'depne', 'agep',
                       'ages', 'agede', 'was', 'wasp', 'wass', 'intst',
                       'texint', 'dbe', 'alimony', 'bil', 'pensions', 'ptpen',
                       'sche', 'fil', 'ucagix', 'ssinc', 'ssincp', 'ssincs',
                       'ssagix', 'totincx', 'agix', 'tincx', 'returns',
                       'oldest', 'youngest', 'agepsqr', 'xagede', 'xifdept',
                       'xdepne', 'income', 'recid', 'sequence', 'soiseq',
                       'wt', 'filer', 's006', 'xtot']

    return SOI[columns_to_keep]
