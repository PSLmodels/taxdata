import pandas as pd
import numpy as np
import sys
import copy
import subprocess


def main():

    # Import CPS data file
    data = pd.read_csv('cps_raw.csv.gz', compression='gzip')
    adj_targets = pd.read_csv('adjustment_targets.csv')
    other_ben = pd.read_csv('benefitprograms.csv', index_col='Program')

    # Rename specified variables
    renames = {
        'IFDEPT': 'DSI',
        'TAXYEAR': 'FLPDYR',
        'XXTOT': 'XTOT',
        'JCPS21': 'e00200p',
        'JCPS31': 'e00200s',
        'ALIMONY': 'e00800',
        'JCPS25': 'e00900p',
        'JCPS35': 'e00900s',
        'JCPS28': 'e02100p',
        'JCPS38': 'e02100s',
        'UCOMP': 'e02300',
        'SEHEALTH': 'e03270',
        'DPAD': 'e03240',
        'MEDICALEXP': 'e17500',
        'REALEST': 'e18500',
        'MISCITEM': 'e20400',
        'CCE': 'e32800',
        'ICPS01': 'age_head',
        'ICPS02': 'age_spouse',
        'WT': 's006',
        'FILST': 'filer',
        'SEQUENCE': 'RECID',
        'PENSIONS': 'e01500',
        'DBE': 'e00600',
        'KEOGH': 'e03300',
        'TIRAD': 'e01400',
        'NU18': 'nu18',
        'N1821': 'n1820',
        'N21': 'n21',
        'CGAGIX': 'e01100',
        'BLIND_HEAD': 'blind_head',
        'BLIND_SPOUSE': 'blind_spouse',
        'HMIE': 'e19200',
        'SS': 'e02400',
        'VB': 'vet_ben',
        'MEDICARE': 'mcare_ben',
        'MEDICAID': 'mcaid_ben',
        'SSI': 'ssi_ben',
        'SNAP': 'snap_ben',
        'WIC': 'wic_ben',
        'TANF': 'tanf_ben',
        'UI': 'ui_ben',
        'HOUSING': 'housing_ben',
        'SLTX': 'e18400',
        'XHID': 'h_seq',
        'XFID': 'ffpos',
        'XSTATE': 'fips'
    }
    data = data.rename(columns=renames)
    data['MARS'] = np.where(data.JS == 3, 4, data.JS)

    # Use taxpayer and spouse records to get total tax unit earnings and AGI
    data['e00100'] = data['JCPS9'] + data['JCPS19']
    data['e00200'] = data['e00200p'] + data['e00200s']
    data['e00900'] = data['e00900p'] + data['e00900s']
    data['e02100'] = data['e02100p'] + data['e02100s']
    # Determine amount of qualified dividends using IRS ratio
    data['e00650'] = data.e00600 * 0.7556

    # Split interest income into taxable and tax exempt using IRS ratio
    taxable = 0.6
    nontaxable = 1. - taxable
    data['e00300'] = data.INTST * taxable
    data['e00400'] = data.INTST * nontaxable

    # Split pentions and annuities using PUF ratio
    data['e01700'] = data['e01500'] * 0.1656

    print 'Applying deduction limits'
    data = deduction_limits(data)
    print 'Adding dependents'
    data = add_dependents(data)
    print 'Adding AGI bins'
    data = add_agi_bin(data, 'INCOME')
    print 'Adjusting distribution'
    data = adjust(data, adj_targets)
    print 'Adding Benefits Data'
    data = benefits(data, other_ben)
    print 'Dropping unused variables'
    data = drop_vars(data)

    data = data.fillna(0.)
    print 'Exporting...'
    data.to_csv('cps.csv', index=False)
    subprocess.check_call(["gzip", "-nf", "cps.csv"])


def deduction_limits(data):
    """
    Apply limits on itemized deductions
    """
    half_agi = data['e00100'] * 0.5
    charity = np.where(data.CHARITABLE > half_agi, half_agi, data.CHARITABLE)
    # Split charitable contributions into cash and non-cash using ratio in PUF
    cash = 0.82013
    non_cash = 1. - cash
    data['e19800'] = charity * cash
    data['e20100'] = charity * non_cash

    # Apply student loan interest deduction limit
    data['e03210'] = np.where(data.SLINT > 2500, 2500, data.SLINT)

    # Apply IRA contribution limit
    deductable_ira = np.where(data.AGE >= 50,
                              np.where(data.ADJIRA > 6500, 6500, data.ADJIRA),
                              np.where(data.ADJIRA > 5500, 5500, data.ADJIRA))
    data['e03150'] = deductable_ira

    return data


def add_dependents(data):
    # Count number of dependents under 13
    # Max of four to match PUF version of nu13
    age1 = np.where((data.ICPS03 > 0) & (data.ICPS03 <= 13), 1, 0)
    age2 = np.where((data.ICPS04 > 0) & (data.ICPS04 <= 13), 1, 0)
    age3 = np.where((data.ICPS05 > 0) & (data.ICPS05 <= 13), 1, 0)
    age4 = np.where((data.ICPS06 > 0) & (data.ICPS06 <= 13), 1, 0)
    nu13 = age1 + age2 + age3 + age4
    data['nu13'] = nu13

    # Count number of dependents under 5
    age1 = np.where((data.ICPS03 > 0) & (data.ICPS03 <= 5), 1, 0)
    age2 = np.where((data.ICPS04 > 0) & (data.ICPS04 <= 5), 1, 0)
    age3 = np.where((data.ICPS05 > 0) & (data.ICPS05 <= 5), 1, 0)
    age4 = np.where((data.ICPS06 > 0) & (data.ICPS06 <= 5), 1, 0)
    age5 = np.where((data.ICPS07 > 0) & (data.ICPS06 <= 5), 1, 0)
    nu05 = age1 + age2 + age3 + age4 + age5
    data['nu05'] = nu05

    # Count number of children eligible for child tax credit
    age1 = np.where((data.ICPS03 > 0) & (data.ICPS03 <= 17), 1, 0)
    age2 = np.where((data.ICPS04 > 0) & (data.ICPS04 <= 17), 1, 0)
    age3 = np.where((data.ICPS05 > 0) & (data.ICPS05 <= 17), 1, 0)
    age4 = np.where((data.ICPS06 > 0) & (data.ICPS06 <= 17), 1, 0)
    age5 = np.where((data.ICPS07) > 0 & (data.ICPS07 <= 17), 1, 0)
    n24 = age1 + age2 + age3 + age4 + age5
    data['n24'] = n24

    # Count number of elderly dependents
    age1 = np.where(data.ICPS03 >= 65, 1, 0)
    age2 = np.where(data.ICPS04 >= 65, 1, 0)
    age3 = np.where(data.ICPS05 >= 65, 1, 0)
    age4 = np.where(data.ICPS06 >= 65, 1, 0)
    age5 = np.where(data.ICPS07 >= 65, 1, 0)
    elderly = age1 + age2 + age3 + age4 + age5
    data['elderly_dependent'] = elderly

    # Count number elegible for f2441
    age1 = np.where((data.ICPS03 > 0) & (data.ICPS03 < 13), 1, 0)
    age2 = np.where((data.ICPS04 > 0) & (data.ICPS04 < 13), 1, 0)
    age3 = np.where((data.ICPS05 > 0) & (data.ICPS05 < 13), 1, 0)
    age4 = np.where((data.ICPS06 > 0) & (data.ICPS06 < 13), 1, 0)
    age5 = np.where((data.ICPS07 > 0) & (data.ICPS07 < 13), 1, 0)
    qualified = age1 + age2 + age3 + age4 + age5
    data['f2441'] = np.where(qualified <= 3, qualified, 3)

    # Count number elegible for EIC
    age1 = np.where((data.ICPS03 > 0) & (data.ICPS03 < 19), 1, 0)
    age2 = np.where((data.ICPS04 > 0) & (data.ICPS04 < 19), 1, 0)
    age3 = np.where((data.ICPS05 > 0) & (data.ICPS05 < 19), 1, 0)
    age4 = np.where((data.ICPS06 > 0) & (data.ICPS06 < 19), 1, 0)
    age5 = np.where((data.ICPS07 > 0) & (data.ICPS07 < 19), 1, 0)
    qualified = age1 + age2 + age3 + age4 + age5
    data['EIC'] = np.where(qualified > 3, 3, qualified)

    return data


def drop_vars(data):
    """
    Returns PDF of data without unuseable variables
    """
    useable_vars = [
        'DSI', 'EIC', 'FLPDYR', 'MARS', 'MIDR', 'RECID', 'XTOT', 'age_head',
        'age_spouse', 'agi_bin', 'blind_head', 'blind_spouse', 'cmbtp',
        'e00200', 'e00200p', 'e00200s', 'e00300', 'e00400', 'e00600', 'e00650',
        'e00700', 'e00800', 'e00900', 'e00900p', 'e00900s', 'e01100', 'e01200',
        'e01400', 'e01500', 'e01700', 'e02000', 'e02100', 'e02100p', 'e02100s',
        'e02300', 'e02400', 'e03150', 'e03220', 'e03230', 'e03240', 'e03270',
        'e03290', 'e03300', 'e03400', 'e03500', 'e07240', 'e07260', 'e07300',
        'e07400', 'e07600', 'e09700', 'e09800', 'e09900', 'e11200', 'e17500',
        'e18400', 'e18500', 'e19200', 'e19800', 'e20100', 'e20400', 'g20500',
        'e24515', 'e24518', 'e26270', 'e27200', 'e32800', 'e58990', 'e62900',
        'e87530', 'elderly_dependent', 'f2441', 'f6251', 'filer', 'n24',
        'nu05', 'nu13', 'nu18', 'n1820', 'n21', 'p08000', 'p22250', 'p23250',
        'p25470', 'p87521', 's006', 'e03210', 'ssi_ben', 'snap_ben',
        'vet_ben', 'mcare_ben', 'mcaid_ben', 'oasdi_ben', 'other_ben',
        'h_seq', 'ffpos', 'fips', 'a_lineno', 'tanf_ben', 'wic_ben',
        'housing_ben'
    ]

    drop_vars = []
    for item in data.columns:
        if item not in useable_vars:
            drop_vars.append(item)
    data = data.drop(drop_vars, axis=1)
    return data


def add_agi_bin(data, col_name):
    """
    Add an AGI bin indicator used in Tax-Calc to apply adjustment factors
    """
    agi = pd.Series([0] * len(data[col_name]))
    agi[data[col_name] < 0] = 0
    agi[(data[col_name] >= 0) & (data[col_name] < 5000)] = 1
    agi[(data[col_name] >= 5000) & (data[col_name] < 10000)] = 2
    agi[(data[col_name] >= 10000) & (data[col_name] < 15000)] = 3
    agi[(data[col_name] >= 15000) & (data[col_name] < 20000)] = 4
    agi[(data[col_name] >= 20000) & (data[col_name] < 25000)] = 5
    agi[(data[col_name] >= 25000) & (data[col_name] < 30000)] = 6
    agi[(data[col_name] >= 30000) & (data[col_name] < 40000)] = 7
    agi[(data[col_name] >= 40000) & (data[col_name] < 50000)] = 8
    agi[(data[col_name] >= 50000) & (data[col_name] < 75000)] = 9
    agi[(data[col_name] >= 75000) & (data.INCOME < 100000)] = 10
    agi[(data[col_name] >= 100000) & (data[col_name] < 200000)] = 11
    agi[(data[col_name] >= 200000) & (data[col_name] < 500000)] = 12
    agi[(data[col_name] >= 500000) & (data[col_name] < 1e6)] = 13
    agi[(data[col_name] >= 1e6) & (data[col_name] < 1.5e6)] = 14
    agi[(data[col_name] >= 1.5e6) & (data[col_name] < 2e6)] = 15
    agi[(data[col_name] >= 2e6) & (data[col_name] < 5e6)] = 16
    agi[(data[col_name] >= 5e6) & (data[col_name] < 1e7)] = 17
    agi[(data[col_name] >= 1e7)] = 18

    data['agi_bin'] = agi

    return data


def adjust_helper(agi, var, target, weight, agi_bin):
    """
    Parameters
    ----------
    agi: AGI provided in the CPS
    var: variable being adjusted
    target: target bin levels
    weight: weights

    Returns
    -------
    Series containing the adjusted values of the variable
    """
    # Goal total ensures the weighted sum of the variable wont change
    goal_total = (var * weight).sum()
    # Goal distribution based on IRS data
    distribution = target / target.sum()
    # Find the goal amount in each bin
    goal_amts = goal_total * distribution
    # Find current totals in each bin
    bin_0 = np.where(agi < 0,
                     var * weight, 0).sum()
    bin_1 = np.where((agi >= 0) & (agi < 5000),
                     var * weight, 0).sum()
    bin_2 = np.where((agi >= 5000) & (agi < 10000),
                     var * weight, 0).sum()
    bin_3 = np.where((agi >= 10000) & (agi < 15000),
                     var * weight, 0).sum()
    bin_4 = np.where((agi >= 15000) & (agi < 20000),
                     var * weight, 0).sum()
    bin_5 = np.where((agi >= 20000) & (agi < 25000),
                     var * weight, 0).sum()
    bin_6 = np.where((agi >= 25000) & (agi < 30000),
                     var * weight, 0).sum()
    bin_7 = np.where((agi >= 30000) & (agi < 40000),
                     var * weight, 0).sum()
    bin_8 = np.where((agi >= 40000) & (agi < 50000),
                     var * weight, 0).sum()
    bin_9 = np.where((agi >= 50000) & (agi < 75000),
                     var * weight, 0).sum()
    bin_10 = np.where((agi >= 75000) & (agi < 100000),
                      var * weight, 0).sum()
    bin_11 = np.where((agi >= 100000) & (agi < 200000),
                      var * weight, 0).sum()
    bin_12 = np.where((agi >= 200000) & (agi < 500000),
                      var * weight, 0).sum()
    bin_13 = np.where((agi >= 500000) & (agi < 1e6),
                      var * weight, 0).sum()
    bin_14 = np.where((agi >= 1e6) & (agi < 1.5e6),
                      var * weight, 0).sum()
    bin_15 = np.where((agi >= 1.5e6) & (agi < 2e6),
                      var * weight, 0).sum()
    bin_16 = np.where((agi >= 2e6) & (agi < 5e6),
                      var * weight, 0).sum()
    bin_17 = np.where((agi >= 5e6) & (agi < 1e7),
                      var * weight, 0).sum()
    bin_18 = np.where((agi >= 1e7),
                      var * weight, 0).sum()
    # Create series holding each of the current totals
    actual_amts = pd.Series([bin_0, bin_1, bin_2, bin_3, bin_4, bin_5,
                             bin_6, bin_7, bin_8, bin_9, bin_10, bin_11,
                             bin_12, bin_13, bin_14, bin_15, bin_16,
                             bin_17, bin_18],
                            index=goal_amts.index)
    ratios_index = [num for num in range(0, 19)]
    # Determine the ratios
    ratios = pd.Series(goal_amts / actual_amts)
    ratios.index = ratios_index

    # Apply adjustment ratios
    var_array = np.array(var)
    var_array = np.nan_to_num(var_array)
    ratios = np.where(ratios == np.inf, 1., ratios)
    adj_array = ratios[agi_bin]
    var *= adj_array

    return var


def adjust(data, targets):
    """
    data: CPS in DataFrame format
    targets: targeted totals provided by the IRS
    """
    # Make copies of values to avoid pandas warning
    inc = copy.deepcopy(data['INCOME'])
    int_inc = copy.deepcopy(data['e00300'])
    odiv_inc = copy.deepcopy(data['e00600'])
    qdiv_inc = copy.deepcopy(data['e00650'])
    biz_inc = copy.deepcopy(data['e00900'])
    data['e00300'] = adjust_helper(inc, int_inc,
                                   targets['INT'], data['s006'],
                                   data['agi_bin'])
    div_ratio = data['e00600'] / (data['e00600'] + data['e00650'])
    data['e00600'] = adjust_helper(inc, odiv_inc,
                                   targets['ODIV'], data['s006'],
                                   data['agi_bin'])
    data['e00650'] = adjust_helper(inc, qdiv_inc,
                                   targets['QDIV'], data['s006'],
                                   data['agi_bin'])
    total = data['e00600'] + data['e00650']
    data['e00600'] = total * div_ratio
    data['e00650'] = total * (1. - div_ratio)
    biz_ratio_p = data['e00900p'] / data['e00900']
    biz_ratio_s = 1. - biz_ratio_p
    data['e00900'] = adjust_helper(inc, biz_inc,
                                   targets['BIZ'], data['s006'],
                                   data['agi_bin'])
    data['e00900p'] = data['e00900'] * biz_ratio_p
    data['e00900s'] = data['e00900'] * biz_ratio_s

    return data


def benefits(data, other_ben):
    """
    Distribute benefits from non-models benefit programs and create total
    benefits variable
    """
    other_ben['2014_cost'] *= 1e6

    # Distribute other benefits
    data['dist_ben'] = (data['mcaid_ben'] + data['ssi_ben'] +
                        data['snap_ben'] + data['vet_ben'])
    data['ratio'] = (data['dist_ben'] * data['s006'] /
                     (data['dist_ben'] * data['s006']).sum())
    # remove TANF and WIC from other_ben
    tanf = (data['tanf_ben'] * data['s006']).sum()
    wic = (data['wic_ben'] * data['s006']).sum()
    other_ben_total = other_ben['2014_cost'].sum() - tanf - wic
    # divide by the weight to account for weighting in Tax-Calculator
    data['other_ben'] = (data['ratio'] * other_ben_total /
                         data['s006'])

    # Convert benefit data to integers
    data['mcaid_ben'] = data['mcaid_ben'].astype(np.int32)
    data['mcare_ben'] = data['mcare_ben'].astype(np.int32)
    data['ssi_ben'] = data['ssi_ben'].astype(np.int32)
    data['snap_ben'] = data['snap_ben'].astype(np.int32)
    data['vet_ben'] = data['vet_ben'].astype(np.int32)
    data['tanf_ben'] = data['tanf_ben'].astype(np.int32)
    data['wic_ben'] = data['wic_ben'].astype(np.int32)
    data['housing_ben'] = data['housing_ben'].astype(np.int32)
    data['e02400'] = data['e02400'].astype(np.int32)
    data['e02300'] = data['ui_ben'].astype(np.int32)
    data['other_ben'] = data['other_ben'].astype(np.int32)

    return data


if __name__ == '__main__':
    sys.exit(main())
