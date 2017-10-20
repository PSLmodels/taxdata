import pandas as pd
import numpy as np


def impute(df, logit_betas, ols_betas, ols_mult1, ols_mult2):
    """
    This function first determines if a given record would have a non-zero
    value for the specified variable, then determines the value of that
    variable

    Parameters
    ----------
    df: DataFrame with all of the records
    logit_betas: beta coefficients for the probability calculations
    ols_betas: beta coefficients for the value calculations
    ols_mult1: multiplier applied during value calculations
    ols_mult2: multiplier applied during value calculations

    Returns
    -------
    Array of imputed values
    """

    def impute_val(df, betas, params, ols_mult1, ols_mult2):
        """
        Determines value of variable if record is flagged, otherwise returns 0.
        """
        if not df['impute']:
            val = 0.
        else:
            xb = 0.
            for param in params:
                xb += df[param] * betas[param]
            val = np.exp(xb) * ols_mult1 * ols_mult2
        return val

    # list of parameters used in calculations
    params = ['constant', 'lnincome', 'married', 'ageh', 'agesqr']

    # calculate probability using logit coefficients
    xb = np.zeros(len(df))
    for param in params:
        xb += df[param] * logit_betas[param]
    prob = np.exp(xb) / (1. + np.exp(xb))
    # flag records for imputation
    z1 = np.random.uniform(0, 1, len(prob))
    df['impute'] = np.where(z1 <= prob, True, False)
    val = df.apply(impute_val, axis=1, args=(ols_betas, params, ols_mult1,
                                             ols_mult2))
    return val


def home_sales(df, limit):
    """
    This function imputes home sales based on home ownership
    """
    if df['zowner'] == 1:
        z1 = np.random.uniform(0, 1)
        if z1 < 0.07:
            val = min(limit, df['homeequity'] * 0.25)
        else:
            val = 0.
    else:
        val = 0.
    return val


def model(df, params, betas):
    """
    Function used to calculate a value
    """
    xb = 0
    for param in params:
        xb += df[param] * betas[param]
    return xb


def health_insurance(df, primary=True):
    """
    Function to compute health insurance premiums
    """
    # Employer share of health insurance
    # set values for premiums: average and standard deviation
    # TODO: update values (currently for 2004)
    # family coverage
    avgprem_f = 10006.
    stdprem_f = 28.25
    # single coverage
    avgprem_s = 3705.
    stdprem_s = 16.42

    # set values for employee share, average, and standard deviation
    avgshare_f = 0.2440
    stdshare_f = 0.0041
    avgshare_s = 0.1810
    stdshare_s = 0.0023

    # set values for life insurance contributions
    # (from BLS employee compensation survery)
    problife = 0.6200
    wageshare = 0.0025

    # inititalize employershare variable
    employershare = 0.

    # impute total premium for principle tax payer
    hi_var = 'hi'
    priv_var = 'priv'
    hi_spouse_var = 'hi_spouse'
    paid_var = 'paid'
    if not primary:
        hi_var = 'hi_spouse'
        priv_var = 'priv_spouse'
        hi_spouse_var = 'hi'
        paid_var = 'priv_spouse'
    if df[hi_var] == 1 and df[priv_var] == 1 and df['ifdept'] == 0:
        if df['depne'] > 0 or df[hi_spouse_var] == 2:
            avgprm = avgprem_f
            stdprm = stdprem_f
            avgshr = avgshare_f
            stdshr = stdshare_f
            plantype_p = 2
        else:
            avgprm = avgprem_s
            stdprm = stdprem_s
            avgshr = avgshare_s
            stdshr = stdshare_s
            plantype_p = 1
        # total premium amount
        z = np.random.randn()
        hipremium = max(0., avgprm + stdprm * z)

        # use CPS variable for employer share
        if df[paid_var] == 1:  # employer pays all
            employershare = hipremium
        elif df[paid_var] == 3:  # employer pays none
            employershare = 0.
        elif df[paid_var] == 2:  # emplyer pays some
            z = np.random.randn()
            employeeshare = max(0., avgshr + stdshr * z) * hipremium
            employershare = max(0., hipremium - employeeshare)
        else:  # not in universe
            employershare = 0.

    return employershare * 1.65


def blankslate(cps):
    """
    Function computes blank slate imputations
    """

    # some variable creation
    cps['married'] = np.where(cps.js == 2, 1, 0)
    cps['agesqr'] = cps['ageh'] ** 2
    cps['income'] = (cps['was'] + cps['intst'] + cps['dbe'] + cps['alimony'] +
                     cps['bil'] + cps['pensions'] + cps['rents'] + cps['fil'] +
                     cps['ucomp'] + cps['socsec'] + cps['CGAGIX'] +
                     cps['TIRAD'])
    cps['income2'] = np.minimum(1000000., cps['income']) / 1000.
    cps['income'] /= 1000.
    cps['lnincome'] = np.log(1. + np.maximum(0., cps['income']))
    cps['lnincome2'] = np.log(1. + np.maximum(0., cps['income2']))
    cps['lnintst'] = np.log(1. + (np.maximum(0., cps['intst']) / 1000))

    # create DataFrame with all of the imputation parameters
    param_index = ['constant', 'lnincome', 'married', 'ageh', 'agesqr']
    logit_coefs = pd.DataFrame({'cv_li': [-4.939295, 0.341101, 0.210042,
                                          0.043812, -0.000110],
                                'db_plans': [-5.523435, 0.455226, 0.306575,
                                             0.052442, -0.000023],
                                'dc_plans': [-7.628465, 1.178294, -0.036142,
                                             0.135468, -0.001710]},
                               index=param_index)

    ols_coefs = pd.DataFrame({'cv_li': [2.93293, 0.745429, 0.057145, 0.073103,
                                        -0.000425],
                              'db_plans': [-1.182855, 0.176279, 0.027678,
                                           0.032099, -0.000296],
                              'dc_plans': [-5.382661, 1.267289, -0.129236,
                                           0.115907, -0.000721]},
                             index=param_index)

    # cash value life insurance
    cps['buildup_life'] = impute(cps, logit_coefs['cv_li'],
                                 ols_coefs['cv_li'],
                                 1., 0.04)
    # DB plans
    cps['buildup_pens_db'] = impute(cps, logit_coefs['db_plans'],
                                    ols_coefs['db_plans'],
                                    1000., 0.04)
    # DC plans
    cps['buildup_pens_dc'] = impute(cps, logit_coefs['dc_plans'],
                                    ols_coefs['dc_plans'],
                                    1000., 0.04)
    # home sales
    limit = np.where(cps.js == 2, 500000., 250000.)
    z1 = np.random.uniform(0, 1, len(limit))
    flag = np.where(cps.zowner == 1, True, False)
    cps['gains_on_home_sale'] = np.where((flag) & (z1 < 0.07),
                                         np.minimum(limit,
                                                    cps.homeequity * 0.25), 0.)

    # dictionary of probabilities used when calculating net worth
    agedict = {0: 0.00612, 1: 0.00042, 2: 0.00026, 3: 0.0002, 4: 0.00015,
               5: 0.00014, 6: 0.00012, 7: 0.00012, 8: 0.0001, 9: 9e-05,
               10: 9e-05, 11: 9e-05, 12: 0.00012, 13: 0.00017, 14: 0.00024,
               15: 0.00032, 16: 0.0004, 17: 0.00049, 18: 0.00057, 19: 0.00065,
               20: 0.00074, 21: 0.00082, 22: 0.00088, 23: 0.00091,
               24: 0.00092, 25: 0.00093, 26: 0.00094, 27: 0.00095, 28: 0.00097,
               29: 0.00099, 30: 0.00102, 31: 0.00106, 32: 0.00109, 33: 0.00113,
               34: 0.00118, 35: 0.00124, 36: 0.0013, 37: 0.00138, 38: 0.00147,
               39: 0.00157, 40: 0.00168, 41: 0.00181, 42: 0.00198, 43: 0.00218,
               44: 0.00242, 45: 0.00268, 46: 0.00295, 47: 0.00324, 48: 0.00354,
               49: 0.00385, 50: 0.00418, 51: 0.00454, 52: 0.00491, 53: 0.0053,
               54: 0.00571, 55: 0.00616, 56: 0.00665, 57: 0.00714, 58: 0.00762,
               59: 0.00812, 60: 0.00868, 61: 0.00932, 62: 0.01007, 63: 0.01094,
               64: 0.01193, 65: 0.01306, 66: 0.01431, 67: 0.01563, 68: 0.01701,
               69: 0.01849, 70: 0.02019, 71: 0.02212, 72: 0.02425, 73: 0.02658,
               74: 0.02915, 75: 0.03215, 76: 0.03555, 77: 0.03923, 78: 0.04317,
               79: 0.04751, 80: 0.0525, 81: 0.05825, 82: 0.06468, 83: 0.07183,
               84: 0.07981, 85: 0.08875, 86: 0.09877, 87: 0.10994, 88: 0.12233,
               89: 0.13594, 90: 0.15079, 91: 0.16686, 92: 0.18414, 93: 0.20259,
               94: 0.22218, 95: 0.24179, 96: 0.26109, 97: 0.27974, 98: 0.29735,
               99: 0.31358, 100: 0.33069, 101: 0.34875, 102: 0.3678,
               103: 0.3879, 104: 0.4091, 105: 0.43148, 106: 0.45509,
               107: 0.48001, 108: 0.50629, 109: 0.53404, 110: 0.56331,
               111: 0.5942, 112: 0.6268, 113: 0.6612, 114: 0.69751,
               115: 0.73582, 116: 0.77626, 117: 0.81818, 118: 0.85909,
               119: 0.90205}
    # net worth
    probd = np.array([agedict[x] for x in cps['ageh']])
    z1 = np.random.uniform(0, 1, len(probd))

    networth_coefs = pd.DataFrame({'net_worth': [-3.940298, 1.387882,
                                                 0.164254, 0.0450189,
                                                 0.000056]},
                                  index=param_index)

    params_textint = ['constant', 'lnincome', 'married', 'agede', 'lnintst']
    textint_coefs = pd.DataFrame({'textint1': [-7.206106, 0.539793, -0.442224,
                                               0.463489, 0.4170335],
                                  'textint2': [4.02137, 0.226618, -0.525778,
                                               0.713761, -0.295498]},
                                 index=params_textint)
    net_worth_mask = z1 >= probd
    net_worth = np.where(net_worth_mask, model(cps, param_index,
                                               networth_coefs['net_worth']),
                         0.)
    cps['stepupinbasis'] = np.where(net_worth_mask,
                                    np.exp(net_worth) * 1000. * 0.5, 0.)
    xb_textint = model(cps, params_textint, textint_coefs['textint1'])
    prob_textint = np.exp(xb_textint) / (1. + np.exp(xb_textint))
    z1 = np.random.uniform(0, 1, len(prob_textint))
    textint_mask = z1 <= prob_textint
    textint = np.where(textint_mask,
                       model(cps, params_textint, textint_coefs['textint2']),
                       0.)
    cps['textint'] = np.where(textint_mask, np.exp(textint) * 1000., 0.)

    # emplyer share of health insurance calculations
    cps['eshi_taxpayer'] = cps.apply(health_insurance, axis=1)
    cps['eshi_spouse'] = cps.apply(health_insurance, axis=1, args=(False))

    # rent
    cps['rent_paid'] = np.where(cps['zowner'] != 1,
                                0.15 * np.maximum(0., (cps['was'] +
                                                       cps['intst'] +
                                                       cps['dbe'] +
                                                       cps['alimony'] +
                                                       cps['bil'])), 0.)

    # fix for child and dependent care expenses
    # TODO: check which of these variables should be used in final
    cps['ccer'] = cps['CCE'] * 3.
    # employer contributions to pensions
    # data from National Compensation Survey (BLS)
    cps['ECPENSIONS'] = np.where(cps['buildup_pens_db'] > 0.,
                                 cps['was'] * 0.048, 0.)
    cps['ECPENSIONS'] = np.where(cps['buildup_pens_dc'] > 0.,
                                 cps['ECPENSIONS'] + cps['was'] * 0.277,
                                 cps['ECPENSIONS'])
