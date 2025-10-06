"""
Impute W-2 wages share in Qualified Business Income in PUF.

The objective of this imputation is to improve the accuracy of Qualified
Business Income Deduction (QBID) revenue estimates produced by Tax-Calculator.
In the absence of a valid W-2 wage share variable (e.g., when it is set to zero),
Tax-Calculatorgenerates QBID values that diverge significantly from benchmark
estimates published by agencies such as the Congressional Budget Office (CBO).

Since no microdata source contains reliable information on the W-2 wage share
associated with pass-through income, a statistical imputation is required.
We calibrate the imputation to match CBO's published QBID revenue estimates.
To be noticed, there is an observed inconsistency on the CBO published QBID
estimates between the years before 2020 and the years after 2021. So only the
QBID value from the years 2021 ~ 2025 are selected targets, which would better
reflect the policy environments of the recent years. Targets will be updated as
new CBO QBID projections become available.

The imputation strategy is to minimize the distance between Tax-Calculator's
simulated QBID revenue and CBO's published targets through an optimization
process. Specifically, we define a loss function to measure the year-by-year
squared deviations in aggregate QBID amounts and solve for the W-2 wage share
parameter which minimizes this loss.

The imputation will add the PT_w2_binc_wages into puf.csv file.
"""

import pandas as pd
import taxcalc as tc
import numpy as np
from scipy.optimize import minimize_scalar
from functools import partial


def impute_PT_binc_w2_wages(data):
    """
    Main function in impute_qbid_w2.py file.
    Argument: puf.csv DataFrame just before imputation is done.
    Returns: puf.csv DataFrame with imputed W-2 wage share variable.
    """
    # add the qualified business income variable, to be noticed the self employment
    # part is not included, to simplyfy calculation.
    data["qbinc"] = (
        data["e00900"] + data["e26270"] + data["e02100"] + data["e27200"]
    )
    # solve for W-2 wage share in QBI
    w2_ratio = opt_ratio(data)
    data["PT_binc_w2_wages"] = w2_ratio * data["qbinc"]
    del data["qbinc"]
    return data


def qbid_value(data, ratio):
    """
    Function that calculate the QBID aggregates through years.
    """
    qbided = []
    df = data.copy()
    df["PT_binc_w2_wages"] = ratio * df["qbinc"]
    pol = tc.Policy()
    recs = tc.Records(data=df)
    calc0 = tc.Calculator(policy=pol, records=recs)
    for year in range(2021, 2026):
        calc0.advance_to_year(year)
        calc0.calc_all()
        qbided.append(calc0.weighted_total("qbided"))
    return np.array(qbided)


def loss_function(data, ratio):
    """
    Function that estimates loss between between Tax-Calculator's
    simulated QBID revenue and CBO's published targets on QBID aggregates.
    """
    # CBO QBID aggregates for the year 2021 ~ 2025
    target = [205.1e9, 215.7e9, 229.5e9, 247.1e9, 258.3e9]
    return np.sum((qbid_value(data, ratio) - target) ** 2)


def opt_ratio(data):
    """
    Function that solve for the W-2 wage share from the loss function
    Argument: puf.csv before imputation.
    Returns: percentage of W-2 wage income in the Qualified Business Income.
    """
    loss = partial(loss_function, data)
    res = minimize_scalar(loss, bounds=(0, 1), method="bounded")
    # print(f"Optimal ratio: {res.x:.4f}, target: {res.fun:.4f}")
    return res.x
