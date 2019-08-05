import pandas as pd
import numpy as np
import statsmodels.api as sm
from pathlib import Path
from helpers import (FILINGPARAMS, CUR_PATH, PUF_YR_IDX, LOG_VARS,
                     X_VARS, PUF_YEAR, log)
from rpy2.robjects.packages import importr
from rpy2 import robjects as ro
from rpy2.robjects.conversion import localconverter
from rpy2.robjects import pandas2ri


censreg = importr("censReg")  # import cenReg R package
# variables we count for total income
PUF_INCOME_VARS = [
    "E00200", "E00300", "E00600", "E00650", "E00800", "E00900", "E01500",
    "E02000", "E02100", "E02300", "E02400"
]


def calc_standard(index, num=1):
    """
    Calculate the standard deduction after accounting for the number of people
    above 65 in the unit

    Parameters
    ----------
    index: index in the paramtools array to use
    num: number of people above 65
    """
    return (
        FILINGPARAMS.std[PUF_YR_IDX][index] +
        (FILINGPARAMS.additional_aged_blind[PUF_YR_IDX][index] * num)
    )


def logit(data, y, x):
    """
    Function for running a Logit model
    Parameters
    ----------
    data: the dataset
    y: dependent variable
    x: list of independent variables
    """
    return sm.Logit(data[y], data[x]).fit()


def ols(data, puf_var, indicator_var, x):
    """
    Prep data and run OLS regression model
    """
    # find log of variable for regression
    data[f"ln_{puf_var}"] = log(data, puf_var)
    sub_data = data[data[indicator_var] == 1]
    return sm.OLS(
        sub_data[f"ln_{puf_var}"],
        sub_data[x]
    ).fit()


def calc_betas(verbose=False):
    """
    Calculate beta values for imputations
    """
    if verbose:
        print("Reading and Preparing Data")
    puf_path = Path(CUR_PATH, "..", "..", "puf_data", "StatMatch",
                    "Matching", f"puf{PUF_YEAR}.csv")
    puf = pd.read_csv(puf_path)
    # remove aggregate variables
    puf = puf[puf["MARS"] != 0]
    puf["tot_inc"] = puf[PUF_INCOME_VARS].sum(axis=1)
    # total dividends
    puf["divs"] = puf[["E00600", "E00650"]].sum(axis=1)
    # total interest
    puf["interest"] = puf[["E00300", "E00400"]].sum(axis=1)
    # find log of specified variables
    for var in LOG_VARS:
        puf[f"ln{var.lower()}"] = log(puf, var)

    # define MARS for the regression
    # 1 for joint files, 0 otherwise
    puf["joint_filer"] = np.where(
        puf["MARS"].isin([1, 4]), 0, 1
    )
    # For the PUF, we'll say familty size is equal to XTOT
    puf["fam_size"] = puf["XTOT"]

    puf["constant"] = np.ones(len(puf))

    single_std_aged = calc_standard(0)
    joint_std_aged1 = calc_standard(1)
    joint_std_aged2 = calc_standard(1, 2)
    hoh_std_aged = calc_standard(2)

    # if they're a single filer and elderly and took the standard deduction,
    # their standard deduction should be equal to the standard deduction for
    # the given year plus the additional standard deduction for elderly filers.
    # Blind filers also may receive this benefit, but we'll ignore that for now
    std_filer = puf["FDED"] == 2
    single_elderly_st = np.where(
        (puf["MARS"] == 1) & (std_filer) & (puf["P04470"] == single_std_aged),
        1, 0
    )
    joint_elderly1_st = np.where(
        (puf["MARS"] == 2) & (std_filer) & (puf["P04470"] == joint_std_aged1),
        1, 0
    )
    joint_elderly2_st = np.where(
        (puf["MARS"] == 2) & (std_filer) & (puf["P04470"] == joint_std_aged2),
        1, 0
    )
    hoh_elderly_st = np.where(
        (puf["MARS"] == 4) & (std_filer) & (puf["P04470"] == hoh_std_aged),
        1, 0
    )
    # for others, if they receive social security we'll assume they're 65
    non_std_filer = np.logical_not(std_filer)
    single_hoh_elderly_item = np.where(
        (puf["MARS"].isin([1, 4])) & (non_std_filer) & (puf["E02400"] > 0.),
        1, 0
    )
    # TODO: figure out why I picked 25000
    joint_elderly1_item = np.where(
        (puf["MARS"] == 2) & (non_std_filer) &
        (puf["E02400"] > 0.) & (puf["E02400"] < 25000),
        1, 0
    )
    joint_elderly2_item = np.where(
        (puf["MARS"] == 2) & (non_std_filer) & (puf["E02400"] >= 25000),
        1, 0
    )
    # determine how many people above 65 are in the unit. We're only counting
    # the primary tax payer and their spouse

    # start with those with one elderly person
    puf["agede"] = np.where(
        (single_elderly_st) | (joint_elderly1_st) | (hoh_elderly_st) |
        (single_hoh_elderly_item) | (joint_elderly1_item),
        1, 0
    )
    # then those with two elderly people
    puf["agede"] = np.where(
        (joint_elderly2_st) | (joint_elderly2_item),
        2, puf["agede"]
    )

    # add boolean indicators for claiming certain deductions/income sources
    # capital gains in agi
    puf["cg_agi"] = np.where(puf["E01100"] > 0, 1, 0)
    # taxable ira distributions
    puf["ira_dist"] = np.where(puf["E01400"] > 0, 1, 0)
    # ira contributions
    puf["ira_con"] = np.where(puf["E03150"] > 0, 1, 0)
    # self-employed sep, simple
    puf["sep"] = np.where(puf["E03300"] > 0, 1, 0)
    # self-employed health insurance deduction
    puf["se_hi"] = np.where(puf["E03270"] > 0, 1, 0)
    # charitable contributions
    tot_charitable = puf["E19800"] + puf["E20100"]
    puf["charitable"] = np.where(tot_charitable > 0, 1, 0)
    # misc. deductions
    puf["misc"] = np.where(puf["E20400"] > 0, 1, 0)
    # child and dependent care credit
    puf["cdc"] = np.where(puf["E07220"] > 0, 1, 0)
    # medical expense deduction
    puf["med_exp"] = np.where(puf["E17500"] > 0, 1, 0)
    # student loan interest deduction
    puf["sl_ded"] = np.where(puf["E03210"] > 0, 1, 0)

    # Run logit models
    if verbose:
        print("Running Logit Models")
    # capital gains in AGI
    cg_model = logit(
        data=puf,
        y="cg_agi",
        x=[
            "lntot_inc", "joint_filer", "fam_size", "lninterest",
            "lndivs", "lne01500", "constant"
        ]
    )
    # taxable IRA distributions
    ira_model = logit(
        data=puf,
        y="ira_dist",
        x=X_VARS
    )
    # IRA contributions
    irac_model = logit(
        data=puf,
        y="ira_con",
        x=X_VARS
    )
    # Self-employed SEP
    sep_model = logit(
        data=puf,
        y="sep",
        x=X_VARS
    )
    # Self-employed healh insurance
    sehi_model = logit(
        data=puf,
        y="se_hi",
        x=X_VARS
    )
    # Child and dependent care credit
    cdc_model = logit(
        data=puf,
        y="cdc",
        x=X_VARS
    )
    # Student loan interest deduction
    sl_model = logit(
        data=puf,
        y="sl_ded",
        x=X_VARS
    )
    # Medical expense deduction
    medex_model = logit(
        data=puf,
        y="med_exp",
        x=X_VARS
    )

    # Run OLS models
    if verbose:
        print("Running OLS Models")
    # Capital gains in AGI
    cg_ols = ols(
        data=puf,
        puf_var="E01100",
        indicator_var="cg_agi",
        x=[
            "lntot_inc", "joint_filer", "fam_size", "agede", "lninterest",
            "lndivs", "lne01500", "constant"
        ]
    )
    # Taxable IRA distributions
    ira_ols = ols(
        data=puf,
        puf_var="E01400",
        indicator_var="ira_dist",
        x=X_VARS
    )
    # IRA contributions
    irac_ols = ols(
        data=puf,
        puf_var="E03150",
        indicator_var="ira_con",
        x=X_VARS
    )
    # Self-employed SEP
    sep_ols = ols(
        data=puf,
        puf_var="E03300",
        indicator_var="sep",
        x=X_VARS
    )
    # Self-employed health insurance deduction
    sehi_ols = ols(
        data=puf,
        puf_var="E03270",
        indicator_var="se_hi",
        x=X_VARS
    )
    # Child and dependent care deduction
    cdc_ols = ols(
        data=puf,
        puf_var="E07220",
        indicator_var="cdc",
        x=X_VARS
    )
    # Medical expenses deduction
    medex_ols = ols(
        data=puf,
        puf_var="E17500",
        indicator_var="med_exp",
        x=X_VARS
    )
    # Student Loan interest deduction
    sl_ols = ols(
        data=puf,
        puf_var="E03210",
        indicator_var="sl_ded",
        x=X_VARS
    )

    # tobit models
    if verbose:
        print("Running Tobit Models")
    # R funtion to run the tobit model
    ro.r(
        """
        cenreg <- function(formula, data) {
                results <- censReg(formula, left = 0, data = data)
                data.frame(coef(results))
            }
        """
    )
    # convert the PUF to an R data.frame
    with localconverter(ro.default_converter + pandas2ri.converter):
        r_puf = ro.conversion.py2rpy(puf)

    # create tobit model
    tobit = ro.globalenv["cenreg"]
    tobit_formula = "charitable ~ lntot_inc + joint_filer + fam_size + agede"
    tobit_charitable = tobit(ro.r(tobit_formula), r_puf)
    tobit_misc = tobit(ro.r(tobit_formula), r_puf)

    # convert R data.frame to pandas DataFrame
    with localconverter(ro.default_converter + pandas2ri.converter):
        charitable_coefs = ro.conversion.rpy2py(tobit_charitable)
        misc_coefs = ro.conversion.rpy2py(tobit_misc)
    charitable_coefs.columns = ["charitable"]
    misc_coefs.columns = ["misc"]

    tobit_betas = pd.concat(
        [charitable_coefs, misc_coefs], axis=1
    ).rename({"(Intercept)": "constant"})

    # extract all parameters
    if verbose:
        print("Exporting Coefficients")
    logit_betas = pd.DataFrame({"cg_logit": cg_model.params,
                                "ira_logit": ira_model.params,
                                "irac_logit": irac_model.params,
                                "sep_logit": sep_model.params,
                                "sehi_logit": sehi_model.params,
                                "cdc_logit": cdc_model.params,
                                "medex_logit": medex_model.params,
                                "sl_logit": sl_model.params}).fillna(0.)
    ols_betas = pd.DataFrame({"cg_ols": cg_ols.params,
                              "ira_ols": ira_ols.params,
                              "irac_ols": irac_ols.params,
                              "sep_ols": sep_ols.params,
                              "sehi_ols": sehi_ols.params,
                              "cdc_ols": cdc_ols.params,
                              "medex_ols": medex_ols.params,
                              "sl_ols": sl_ols.params}).fillna(0.)
    logit_betas.to_csv(Path(CUR_PATH, "data", "logit_betas.csv"))
    ols_betas.to_csv(Path(CUR_PATH, "data", "ols_betas.csv"))
    tobit_betas.to_csv(Path(CUR_PATH, "data", "tobit_betas.csv"))


if __name__ == "__main__":
    calc_betas(verbose=True)
