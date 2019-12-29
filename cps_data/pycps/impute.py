import pandas as pd
import numpy as np
from scipy.stats import norm
from helpers import log, LOG_VARS, X_VARS, FILINGPARAMS, CPS_YR_IDX


def impute(df, logit_betas, ols_betas, x_vars, l_adj, o_adj, prob_mult):
    """
    This function first determines if a given record would have claimed a
    deduction, then determines the value of that deduction for each record

    Parameters
    ----------
    df: dataframe will all of the records
    logit_betas: beta coefficients from the logit model
    ols_betas: beta coefficients from the ols model
    x_vars: x variables used in the imputation
    l_adj: specific adjustment added when determining logit probabilities
    o_adj: specific adjustment added during ols calculations
    prob_mult: multiplier for the probabilities from the logit model

    Returns
    -------
    Array of imputed values
    """

    def impute_val(df, betas, x_vars, adj):
        """
        Determines the value of the deduction if the record is flagged as
        'impute.' Otherwise it will return zero
        """
        # return zero if the record shouldn't receive an imputation
        if not df["impute"]:
            val = 0.
        # Otherwise, determine the value given the beta coefficients
        else:
            xb = 0.
            for param in x_vars:
                xb += df[param] * betas[param]
            z2 = np.random.randn()
            val = np.exp(xb + adj * z2)
        return val

    # calculate probability using coefficients from the logit model
    xb = np.zeros(len(df))
    for param in x_vars:
        xb += df[param] * logit_betas[param]
    prob = np.exp(xb) / (1. + np.exp(xb)) + l_adj
    prob *= prob_mult

    # flag which records should recieve and imputation
    z1 = np.random.uniform(0, 1, len(prob))
    df["impute"] = np.where(z1 <= prob, True, False)
    val = df.apply(impute_val, axis=1, args=(ols_betas, x_vars, o_adj))
    return val


def tobit(cps, betas, x_vars, sigma, prob_mult):
    """
    Impute values using a tobit model

    Parameters
    ----------
    cps: DataFrame with all CPS records
    betas: beta coefficients from the tobit regression
    x_vars: x variables used in the imputations
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
        charitable = xb + sigma * lamb
        return charitable

    xb = np.zeros(len(cps))
    for param in x_vars:
        xb += cps[param] * betas[param]

    prob = norm.cdf(xb / sigma) * prob_mult
    z1 = np.random.uniform(0, 1, len(prob))
    val = np.where(z1 <= prob, impute_val(cps, xb, sigma), 0.)
    return val


def imputation(data, logit_betas, ols_betas, tobit_betas):
    """
    This function uses beta values calculated using the IRS Public Use File
    to impute the value of certain itemized deductions for filing records
    """
    # data prep
    # find log of specified variables
    for var in LOG_VARS:
        # use lowercase because CPS uses lowercase at this stage
        data[f"ln{var.lower()}"] = log(data, var.lower())

    data["joint_filer"] = np.where(
        data["mars"] == 2, 1, 0
    )
    # cap family size at 5 to match with the PUF
    data["fam_size"] = np.minimum(data["XTOT"], 5)
    data["agede"] = (
        (data["age_head"] >=
         FILINGPARAMS.elderly_age[CPS_YR_IDX]).astype(int) +
        (data["age_spouse"] >=
         FILINGPARAMS.elderly_age[CPS_YR_IDX]).astype(int)
    )
    data["constant"] = np.ones(len(data))

    np.random.seed(5410)  # set random seed before imputations

    # calculate imputations
    # dictionary to hold parameters used in logit/ols imputations
    IMPUTATION_PARAMS = {
        "CGAGIX": {
            "x_vars": [
                "lntot_inc", "joint_filer", "fam_size", "lninterest",
                "lndivs", "lne01500", "constant"
            ],
            "logit_betas": logit_betas["cg_logit"],
            "ols_betas": ols_betas["cg_ols"],
            "l_adj": 0.065,
            "o_adj": 1.95,
            "prob_mult": 1.
        },
        "TIRAD": {
            "x_vars": X_VARS,
            "logit_betas": logit_betas["ira_logit"],
            "ols_betas": ols_betas["ira_ols"],
            "l_adj": 0.,
            "o_adj": 1.7,
            "prob_mult": 1.25
        },
        "ADJIRA": {
            "x_vars": X_VARS,
            "logit_betas": logit_betas["irac_logit"],
            "ols_betas": ols_betas["irac_ols"],
            "l_adj": 0.,
            "o_adj": 1.,
            "prob_mult": .06
        },
        "KEOGH": {
            "x_vars": X_VARS,
            "logit_betas": logit_betas["sep_logit"],
            "ols_betas": ols_betas["sep_ols"],
            "l_adj": 0.,
            "o_adj": 1.,
            "prob_mult": 1.
        },
        "SEHEALTH": {
            "x_vars": X_VARS,
            "logit_betas": logit_betas["sehi_logit"],
            "ols_betas": ols_betas["sehi_ols"],
            "l_adj": 0.,
            "o_adj": 1.,
            "prob_mult": 1.6
        },
        "SLINT": {
            "x_vars": X_VARS,
            "logit_betas": logit_betas["sl_logit"],
            "ols_betas": ols_betas["sl_ols"],
            "l_adj": 0.,
            "o_adj": 1.,
            "prob_mult": 1.1
        },
        "CDC": {
            "x_vars": X_VARS,
            "logit_betas": logit_betas["cdc_logit"],
            "ols_betas": ols_betas["cdc_ols"],
            "l_adj": 0.,
            "o_adj": 1.,
            "prob_mult": 1.
        },
        "MEDEX": {
            "x_vars": X_VARS,
            "logit_betas": logit_betas["medex_logit"],
            "ols_betas": ols_betas["medex_ols"],
            "l_adj": 0.,
            "o_adj": 1.,
            "prob_mult": 1.
        }
    }

    for var, params in IMPUTATION_PARAMS.items():
        data[var] = impute(data, **params)

    # tobit models
    TOBIT_XVARS = [
        "lntot_inc", "joint_filer", "fam_size", "agede"
    ]
    data["CHARITABLE"] = tobit(
        data, tobit_betas["charitable"], TOBIT_XVARS, 48765.45, 1.
    )
    data["MISCITEM"] = tobit(
        data, tobit_betas["misc"], TOBIT_XVARS, 14393.99, 0.3
    )

    # add imputed capital gains and IRA distributions to total income
    data["tot_inc"] += data["CGAGIX"] + data["TIRAD"]
    data["lntot_inc"] = log(data, "tot_inc")

    # DPAD imputations
    dpad_indicator = np.where(
        (data["e00900"] > 0) | (data["rents"] > 0), 1, 0
    )
    dpad_bins = [
        -np.inf, 1, 25000, 50000, 75000, 100000, 200000, 500000, 1000000,
        np.inf
    ]
    dpad_bin = pd.cut(data["tot_inc"], dpad_bins, labels=np.arange(1, 10),
                      right=False)
    dpad_probs = [
        0.01524, 0.00477, 0.1517, 0.02488, 0.03368, 0.05089, 0.11659, 0.26060,
        0.54408
    ]
    dpad_prob_dict = {
        x: prob for x, prob in zip(range(1, 10), dpad_probs)
    }
    dpad_prob = pd.Series(
        [dpad_prob_dict[x] for x in dpad_bin]
    ) * dpad_indicator
    dpad_bases = [
        20686, 1784, 2384, 2779, 3312, 4827, 10585, 24358, 116275
    ]
    dpad_base_dict = {
        x: base for x, base in zip(range(1, 10), dpad_bases)
    }
    dpad_base = pd.Series(
        [dpad_base_dict[x] for x in dpad_bin]
    ) * dpad_indicator

    _prob = dpad_prob * 0.7
    z1 = np.random.uniform(0, 1, len(dpad_prob))
    z2 = np.random.randn(len(dpad_base))
    data["DPAD"] = np.where(
        z1 < _prob, dpad_base + 0.25 * z2, 0.
    )

    # interest paid calculations
    married = (data["mars"] == 2).astype(int)
    ratio = (-0.0115935 * data["age_head"] +
             0.0138109 * data["fam_size"] +
             - 0.0336637 * married +
             0.0163805 * data["lntot_inc"] +
             0.8048336)
    ratio = np.maximum(0, np.minimum(1, ratio))
    factor = 1.73855
    home_value = data["prop_value"] * data["home_owner"] * factor
    mortgage_debt = ratio * home_value
    mortgage_interest = mortgage_debt * 0.0575
    data["e19200"] = mortgage_interest

    # final adjustments
    data["DPAD"] *= 0.3
    data["ADJIRA"] = np.minimum(data["ADJIRA"], 6000.) * 1.3
    data['KEOGH'] = np.minimum(data['KEOGH'], 150000.) * 0.7
    data['SLINT'] *= 1.9
    data['CDC'] = np.minimum(data['CDC'], 5000.) * .3333
    data['SEHEALTH'] = np.minimum(data['SEHEALTH'], 50000.) * 1.1
    data['CHARITABLE'] *= 0.175

    return data
