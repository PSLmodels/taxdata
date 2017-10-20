"""
This script contains the functions necessary to complete the imputation process
of the CPS file creation
"""
import numpy as np
import pandas as pd
from scipy.stats import norm


def impute(df, logit_betas, ols_betas, l_adj, o_adj, prob_mult):
    """
    This function first determines if a given record would have claimed a
    deduction, then determines the value of that deduction for each record

    Parameters
    ----------
    df: dataframe will all of the records
    logit_betas: beta coefficients from the logit model
    ols_betas: beta coefficients from the ols model
    l_adj: specific adjustment added when determining logit probabilities
    o_adj: specific adjustment added during ols calculations
    prob_mult: multiplier for the probabilities from the logit model

    Returns
    -------
    Array of imputed values
    """

    def impute_val(df, betas, params, adj):
        """
        Determines the value of the deduction if the record is flagged as
        'impute.' Otherwise it will return zero
        """
        # return zero if the record shouldn't receive an imputation
        if not df['impute']:
            val = 0.
        # Otherwise, determine the value given the beta coefficients
        else:
            xb = 0.
            for param in params:
                xb += df[param] * betas[param]
            z2 = np.random.randn()
            val = np.exp(xb + adj * z2)
        return val

    # list of parameters used in both models
    params = ['lnincome', 'mars_reg', 'famsize', 'agede',
              'lnintst', 'lndbe', 'lnpensions', 'constant']

    # calculate probabilty using coefficients from the logit model
    xb = np.zeros(len(df))
    for param in params:
        xb += df[param] * logit_betas[param]
    prob = np.exp(xb) / (1. + np.exp(xb)) + l_adj
    prob *= prob_mult

    # flag which records should recieve and imputation
    z1 = np.random.uniform(0, 1, len(prob))
    df['impute'] = np.where(z1 <= prob, True, False)
    val = df.apply(impute_val, axis=1, args=(ols_betas, params, o_adj))
    return val


def impute_dpad(cps):
    """
    Logic for imputing DPAD values
    """
    if cps['dpad_indicator']:
        prob = cps['prob_base'] * cps['prob_mult']
        z1 = np.random.uniform(0, 1)
        if z1 < prob:
            z2 = np.random.randn()
            val = cps['base_dpad'] + 0.25 * z2
        else:
            val = 0.
    else:
        val = 0.
    return val


def tobit(cps, betas, sigma, prob_mult):
    """
    Impute values using a tobit model

    Parameters
    ----------
    cps: DataFrame with all CPS records
    betas: beta coefficients from the tobit regression
    sigma: value used in tobit calculations
    prob_mult: multiplier for probability values

    Returns
    -------
    val: an array of values for the imputed variable
    """

    def impute_val(df, xb, sigma):
        """
        Computational portion of the imputation
        """
        lamb = norm.pdf(xb / sigma) / norm.cdf(xb / sigma)
        z2 = np.random.randn()
        charitable = xb + sigma * lamb
        return charitable
    # list of parameters used in the imputation
    params = ['constant', 'lnincome', 'mars_reg', 'famsize', 'agede']
    xb = np.zeros(len(cps))
    for param in params:
        xb += cps[param] * betas[param]
    #
    prob = norm.cdf(xb / sigma) * prob_mult
    z1 = np.random.uniform(0, 1, len(prob))
    val = np.where(z1 <= prob, impute_val(cps, xb, sigma), 0.)
    return val


def imputation(cps, logit_betas, ols_betas, tobit_betas):
    """
    This function uses betas calculated using the 2011 IRS Public Use File to
    impute the value of certain itemized deductions for filing records

    Parameters
    ----------
    cps: CPS data to impute on
    logit_betas: beta coefficients for logit model
    ols_betas: beta coefficients for ols model
    tobit_betas: beta coefficients for tobit models
    """
    # data prep
    # find log of total income
    cps['totinc'] = (cps['was'] + cps['intst'] + cps['dbe'] + cps['pensions'] +
                     cps['alimony'] + cps['bil'] + cps['rents'] + cps['fil'] +
                     cps['ucomp'] + cps['socsec'])
    cps['tincx'] = np.where(cps['totinc'] <= 0, 0, cps['totinc'])
    cps['lnincome'] = np.log(1. + cps['tincx'])

    # logs of interest, dividend, and pension income
    cps['intst_reg'] = np.where(cps['intst'] <= 0., 0., cps['intst'])
    cps['lnintst'] = np.log(1. + cps['intst_reg'])
    cps['dbe_reg'] = np.where(cps['dbe'] <= 0., 0., cps['dbe'])
    cps['lndbe'] = np.log(1. + cps['dbe_reg'])
    cps['pensions_reg'] = np.where(cps['pensions'] <= 0., 0., cps['pensions'])
    cps['lnpensions'] = np.log(1. + cps['pensions_reg'])

    # set martial status for the regressions
    cps['mars_reg'] = np.where(cps['js'] == 2, 1, 0)

    # set family size for regressons
    cps['famsize'] = np.where(cps['js'] == 2, cps['depne'] + 1,
                              cps['depne'] + 1)
    # set a constant
    cps['constant'] = 1.

    np.random.seed(5410)  # set random seed before imputations
    # impute values
    # capital gains
    cps['CGAGIX'] = impute(cps, logit_betas['cg_logit'], ols_betas['cg_ols'],
                           0.065, 1.95, 1.)
    # taxable IRA distributions
    cps['TIRAD'] = impute(cps, logit_betas['ira_logit'],
                          ols_betas['ira_ols'], 0., 1.7, 1.25)
    # Adjusted IRA contributions
    cps['ADJIRA'] = impute(cps, logit_betas['irac_logit'],
                           ols_betas['irac_ols'], 0., 1., .6)
    # Keogh plans
    cps['KEOGH'] = impute(cps, logit_betas['sep_logit'], ols_betas['sep_ols'],
                          0., 1., 1.)
    # self-employed health insurance deduction
    cps['SEHEALTH'] = impute(cps, logit_betas['sehi_logit'],
                             ols_betas['sehi_ols'], 0., 1., 1.6)
    # student loan interest deduction
    cps['SLINT'] = impute(cps, logit_betas['sl_logit'], ols_betas['sl_ols'],
                          0., 1., 1.1)

    # child care expenses
    cps['CCE'] = impute(cps, logit_betas['cdc_logit'], ols_betas['cdc_ols'],
                        0., 1., 1.)
    # medical expense deduction
    cps['MEDICALEXP'] = impute(cps, logit_betas['medex_logit'],
                               ols_betas['medex_ols'], 0., 1., 1.)

    # charitable deduction
    cps['CHARITABLE'] = tobit(cps, tobit_betas['charitable'], 48765.45, 1.)

    # miscellaneous deductions
    cps['MISCITEM'] = tobit(cps, tobit_betas['misc'], 14393.99, 0.3)

    # additional imputations
    cps['homeowner'] = np.where((cps['zowner'] == 1) & (cps['ifdept'] != 1),
                                1, 0)
    cps['jnj'] = np.where(cps['js'] != 2, 2, 1)
    cps['aged'] = np.where(cps['ageh'] >= 65, 1, 0)

    # add imputed capital gains and IRA distributions to income
    cps['totinc'] += cps['CGAGIX'] + cps['TIRAD']
    cps['tincx'] = np.where(cps['totinc'] > 0., cps['totinc'], 0.)
    cps['lnincome'] = np.log(1. + cps['tincx'])

    # impute home value and equity using betas generated by John
    homevalue_betas = [0.006494, 0.0170197, 0.1150217, 0.4372681, 6.753875]
    params = ['ageh', 'famsize', 'mars_reg', 'lnincome', 'constant']
    xb = np.zeros(len(cps))
    for beta, param in zip(homevalue_betas, params):
        xb += beta * cps[param]
    cps['homevalue'] = np.exp(xb)

    homeequity_betas = [-0.0115935, 0.0138109, -0.0336637, 0.0163805,
                        0.8048336]
    ratio = np.zeros(len(cps))
    for beta, param in zip(homeequity_betas, params):
        ratio += beta * cps[param]
    ratio = np.where(ratio > 1., 1., xb)
    ratio = np.where(ratio > 0., xb, 0.)

    factor = 1.73855  # adjustment factor
    cps['homevalue'] *= cps['homeowner'] * factor
    cps['mortgagedebt'] = ratio * cps['homevalue']
    cps['homeequity'] = (1. - ratio) * cps['homevalue']
    cps['HMIE'] = cps['mortgagedebt'] * 0.0575

    # real estate taxes
    cps['REALEST'] = 0.0075 * cps['homevalue']

    # domestic production activity deduction (DPAD)

    # indicator variables used in DPAD imputation
    dpad_indicator = np.where((cps['bil'] != 0) | (cps['rents'] != 0),
                              True, False)

    # set income bins used for value assignment
    inc_bins = pd.Series([0] * len(cps))
    inc_bins = np.where((cps['tincx'] >= 1) & (cps['tincx'] < 25000),
                        1, inc_bins)
    inc_bins = np.where((cps['tincx'] >= 25000) & (cps['tincx'] < 50000),
                        2, inc_bins)
    inc_bins = np.where((cps['tincx'] >= 50000) & (cps['tincx'] < 75000),
                        3, inc_bins)
    inc_bins = np.where((cps['tincx'] >= 75000) & (cps['tincx'] < 100000),
                        4, inc_bins)
    inc_bins = np.where((cps['tincx'] >= 100000) & (cps['tincx'] < 200000),
                        5, inc_bins)
    inc_bins = np.where((cps['tincx'] >= 200000) & (cps['tincx'] < 500000),
                        6, inc_bins)
    inc_bins = np.where((cps['tincx'] >= 500000) & (cps['tincx'] < 1000000),
                        7, inc_bins)
    inc_bins = np.where((cps['tincx'] >= 1000000), 8, inc_bins)
    # base probability used in DPAD calculations
    prob_base = pd.Series([0.7] * len(cps))
    # set value to be multiplied by the probability base based on income
    prob_mult = pd.Series([0.0] * len(cps))
    prob_mult = np.where((dpad_indicator) & (inc_bins == 0),
                         0.01524, prob_mult)
    prob_mult = np.where((dpad_indicator) & (inc_bins == 1),
                         0.00477, prob_mult)
    prob_mult = np.where((dpad_indicator) & (inc_bins == 2),
                         0.1517, prob_mult)
    prob_mult = np.where((dpad_indicator) & (inc_bins == 3),
                         0.02488, prob_mult)
    prob_mult = np.where((dpad_indicator) & (inc_bins == 4),
                         0.03368, prob_mult)
    prob_mult = np.where((dpad_indicator) & (inc_bins == 5),
                         0.05089, prob_mult)
    prob_mult = np.where((dpad_indicator) & (inc_bins == 6),
                         0.11659, prob_mult)
    prob_mult = np.where((dpad_indicator) & (inc_bins == 7),
                         0.26060, prob_mult)
    prob_mult = np.where((dpad_indicator) & (inc_bins == 8),
                         0.54408, prob_mult)
    # set starting point for DPAD based on incoem
    base_dpad = pd.Series([0] * len(cps))
    base_dpad = np.where((dpad_indicator) & (inc_bins == 0), 20686, base_dpad)
    base_dpad = np.where((dpad_indicator) & (inc_bins == 1), 1784, base_dpad)
    base_dpad = np.where((dpad_indicator) & (inc_bins == 2), 2384, base_dpad)
    base_dpad = np.where((dpad_indicator) & (inc_bins == 3), 2779, base_dpad)
    base_dpad = np.where((dpad_indicator) & (inc_bins == 4), 3312, base_dpad)
    base_dpad = np.where((dpad_indicator) & (inc_bins == 5), 4827, base_dpad)
    base_dpad = np.where((dpad_indicator) & (inc_bins == 6), 10585, base_dpad)
    base_dpad = np.where((dpad_indicator) & (inc_bins == 7), 24358, base_dpad)
    base_dpad = np.where((dpad_indicator) & (inc_bins == 8), 116275, base_dpad)
    # add each series to the CPS data frame
    cps['dpad_indicator'] = dpad_indicator
    cps['prob_base'] = prob_base
    cps['prob_mult'] = prob_mult
    cps['base_dpad'] = base_dpad
    # use impute_dpad function to impute DPAD for each CPS tax unit
    cps['DPAD'] = cps.apply(impute_dpad, axis=1)

    # final adjustments
    cps['DPAD'] *= .3
    cps['ADJIRA'] = np.minimum(cps['ADJIRA'], 6000.) * 1.3
    cps['KEOGH'] = np.minimum(cps['KEOGH'], 150000.) * 0.7
    cps['SLINT'] *= 1.9
    cps['CCE'] = np.minimum(cps['CCE'], 5000.) * .3333
    cps['SEHEALTH'] = np.minimum(cps['SEHEALTH'], 50000.) * 1.1
    cps['CHARITABLE'] *= 0.175

    return cps
