"""
File partitioning and predictive mean estimation.
Input file: cpsrets14.csv, soirets2009.csv
Output file: cpsrets14_ph1.csv, soirets2009_ph1.csv counts.csv
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm


def partitioning(was, intst, bil, fil, js, depne, ifdept, agede, texint, dbe,
                 sche, ssinc, pensions, alimony, ucagix):
    # begin partitioning phase
    ijs = 9
    iagede = 9
    idepne = 9
    ikids = 9
    iself = 9

    # self-employment
    selfempl = 1
    wageflag = 0
    if was != 0:
        wageflag = 1
    selfflag = 0
    if bil + fil != 0:
        selfflag = 1
    if wageflag == 1 and selfflag == 0:
        selfempl = 1
    if wageflag == 0 and selfflag == 1:
        selfempl = 2
    if wageflag == 1 and selfflag == 1:
        selfempl = 3

    # population check
    people = 1
    if js == 2:
        people = 2
    people += depne
    if ifdept == 1:
        people = np.nan

    # dependent filers
    idept = 1
    if ifdept == 1:
        idept = 2
    # non-dependent filers
    if idept == 1:
        ijs = js
        iagede = 1
        if agede > 0:
            iagede = 2
        if agede == 0:
            if js != 2:
                idepne = min(depne, 3)
            else:
                idepne = min(depne, 5)

    if js == 3 and idepne == 0:
        idepne = 1

    # independent variables
    tpi = (was + intst + texint + dbe + max(0, sche) + max(0, bil) +
           max(0, fil) + ssinc + pensions + alimony + ucagix)
    wageshr = 0
    capshr = 0
    if tpi != 0:
        wageshr = was / tpi
        capshr = (intst + texint + dbe) / tpi

    return pd.Series({'idept': idept, 'ijs': ijs, 'iagede': iagede,
                      'ikids': ikids, 'iself': iself, 'wageflag': wageflag,
                      'selfflag': selfflag, 'selfempl': selfempl,
                      'people': people, 'idepne': idepne, 'wageshr': wageshr,
                      'capshr': capshr})


def counts(file):
    count = file.groupby(['idept', 'ijs', 'iagede', 'idepne',
                          'ikids', 'iself']).size().reset_index(name='count')
    wgt = file.groupby(['idept', 'ijs', 'iagede', 'idepne',
                        'ikids', 'iself'])['wt'].sum().reset_index(name='wgt')
    count = pd.concat([count, wgt['wgt']], axis=1)
    return count


def reg(file):
    indep_vars = ['const', 'agede', 'was', 'intst', 'dbe', 'bil', 'fil',
                  'sche', 'pensions', 'ssinc', 'ucagix', 'alimony', 'wageshr',
                  'capshr', 'wageflag', 'selfflag']
    file['const'] = 1.
    X = file[indep_vars]
    model = sm.WLS(file['tincx'], X, weights=file['wt'])
    results = model.fit()
    params = results.params
    return params


def predict(file):
    indep_vars = ['const', 'agede', 'was', 'intst', 'dbe', 'bil', 'fil',
                  'sche', 'pensions', 'ssinc', 'ucagix', 'alimony', 'wageshr',
                  'capshr', 'wageflag', 'selfflag']
    parameters = ['params_const', 'params_agede', 'params_was', 'params_intst',
                  'params_dbe', 'params_bil', 'params_fil', 'params_sche',
                  'params_pensions', 'params_ssinc', 'params_ucagix',
                  'params_alimony', 'params_wageshr', 'params_capshr',
                  'params_wageflag', 'params_selfflag']
    file['const'] = 1.
    X = file[indep_vars]
    P = file[parameters]
    predictions = X.mul(P.values, axis="index").sum(axis=1)
    return predictions


def phaseone(CPS, SOI):
    # CPS = pd.read_csv('cpsrets14.csv')
    # SOI = pd.read_csv('soirets2009.csv')

    CPS.rename(columns={'rents': 'sche', 'ucomp': 'ucagix', 'socsec': 'ssinc'},
               inplace=True)
    CPS['texint'] = 0

    df_CPS = CPS.apply(lambda row: partitioning(row['was'], row['intst'],
                                                row['bil'], row['fil'],
                                                row['js'], row['depne'],
                                                row['ifdept'], row['agede'],
                                                row['texint'], row['dbe'],
                                                row['sche'], row['ssinc'],
                                                row['pensions'],
                                                row['alimony'], row['ucagix']),
                       axis=1)

    df_SOI = SOI.apply(lambda row: partitioning(row['was'], row['intst'],
                                                row['bil'], row['fil'],
                                                row['js'], row['depne'],
                                                row['ifdept'], row['agede'],
                                                row['texint'], row['dbe'],
                                                row['sche'], row['ssinc'],
                                                row['pensions'],
                                                row['alimony'], row['ucagix']),
                       axis=1)

    CPS = pd.concat([CPS, df_CPS], axis=1)
    SOI = pd.concat([SOI, df_SOI], axis=1)

    SOI_counts = counts(SOI)
    CPS_counts = counts(CPS)
    SOI_counts.rename(columns={'count': 'SOI_count', 'wgt': 'SOI_wgt'},
                      inplace=True)
    CPS_counts.rename(columns={'count': 'CPS_count', 'wgt': 'CPS_wgt'},
                      inplace=True)

    countx = pd.merge(SOI_counts, CPS_counts, how='inner',
                      on=['idept', 'ijs', 'iagede', 'idepne',
                          'ikids', 'iself'])
    countx['factor'] = np.where(countx['CPS_wgt'] > 0,
                                countx['SOI_wgt'] / countx['CPS_wgt'], 0)
    countx['cellid'] = countx.index + 1

    SOI_reg = pd.merge(SOI, countx, how='inner',
                       on=['idept', 'ijs', 'iagede', 'idepne',
                           'ikids', 'iself'])
    params = SOI_reg.groupby('cellid', as_index=False).apply(reg)
    params = params.add_prefix('params_')
    params['cellid'] = params.index + 1

    SOI_new = pd.merge(SOI, countx, how='inner',
                       on=['idept', 'ijs', 'iagede', 'idepne',
                           'ikids', 'iself'])
    SOI_new = pd.merge(SOI_new, params, on=['cellid'])
    CPS_new = pd.merge(CPS, countx, how='inner',
                       on=['idept', 'ijs', 'iagede', 'idepne',
                           'ikids', 'iself'])
    CPS_new = pd.merge(CPS_new, params, on=['cellid'])

    SOI_new['yhat'] = predict(SOI_new)
    CPS_new['yhat'] = predict(CPS_new)

    SOI_final = pd.merge(SOI, SOI_new[['soiseq', 'cellid', 'yhat', 'factor']],
                         on=['soiseq'])
    CPS_final = pd.merge(CPS, CPS_new[['cpsseq', 'cellid', 'yhat', 'factor']],
                         on=['cpsseq'])

    # SOI_final.to_csv('soirets2009_ph1.csv', index=False)
    # CPS_final.to_csv('cpsrets14_ph1.csv', index=False)
    # countx.to_csv('counts.csv', index=False)
    return SOI_final, CPS_final, countx
