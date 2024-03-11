"""
Impute itemized expense amounts to nonitemizers in the puf.csv file.

This is done by using the distribution of itemized expense amounts
among filing units who are itemizers to generate the distribution of
imputed itemized expense amounts among filing units who are
nonitemizers.  We do this using a recursive (or sequential) model in
which the imputed values of previously imputed itemized expense
variables are use as explanatory variables.  This is done to better
represent the correlations between the several itemized expense
variables.  This method is sometimes called sequential regression
multiple imputation.  See Raghunathan, et al., "A Multivariate
Technique for Multiply Imputing Missing Values Using a Sequence of
Regression Models" (2001).

Imputing amounts for nonitemizers using statistical models estimated
on itemizers requires that we handle the resulting Heckman sample
selection problem: any statistical model of the itemizers that is used
to impute itemized expense amounts for nonitemizers will over-estimate
the imputed amounts.  This problem is handled by using three different
ad hoc procedures to handle the Heckman sample selection problem.
(Numbered comments below contain more detail on these three procedures.)

And one additional procedure is used in this work: we scale the
distribution of each itemized expense variable so that the weighted
count of nonitemizers with a positive imputed amount and the weighted
dollar sum of the imputed amounts approximate those estimated by JCT
in JCX-75-15, "Estimating Changes in the Federal Individual Income
Tax: Description of the Individual Tax Model," April 23, 2015, pages
18-22, as summarized in Table 2 on page 22, which is entitled "Number
of Tax Filing Units and Amounts of Imputed Itemized Deductions for
Non-Itemizers, 2011."  (Comments below contain more detail on this
procedure.)
"""

from __future__ import print_function
import numpy as np
import pandas as pd
import statsmodels.api as sm


DUMP0 = False
DUMP1 = False
DUMP2 = False
CALIBRATING = False


def impute(
    ievar, logit_prob_af, log_amount_af, exogenous_vars, itemizer_data, nonitemizer_data
):
    """
    Function that estimates imputation equations for ievar with itemizer_data
    using the list of exogenous variables.  The estimated equations are then
    used (along with the two additive factors) to impute amounts for ievar
    for nonitemizers with the imputed nonitemizer amounts being returned.
    """
    if DUMP1:
        print("****** IMPUTE {} ******".format(ievar))
    # estimate Logit parameters for probability of having a positive amount
    logit_y = (itemizer_data[ievar] > 0).astype(int)
    logit_x = itemizer_data[exogenous_vars]
    logit_res = sm.Logit(logit_y, logit_x).fit(disp=0)
    x_b = logit_res.predict(nonitemizer_data[exogenous_vars], linear=True)
    exp_x_b = np.exp(x_b + logit_prob_af[ievar])
    adj_prob = exp_x_b / (1.0 + exp_x_b)
    np.random.seed(int(ievar[1:]))
    urn = np.random.uniform(size=len(x_b))
    positive_imputed = np.where(urn < adj_prob, True, False)
    if DUMP1:
        print(logit_res.summary())
        print(adj_prob.head())
        print(round(positive_imputed.mean(), 4))
        print(len(nonitemizer_data))
    # estimate OLS parameters for the positive amount using a sample of
    # itemizers who have positive ievar amounts that are less than the
    # itemizer's standard deduction amount
    # (1) This sample limitation is one part of an ad hoc procedure to deal
    # with the Heckman sample selection problems present in this imputation
    # process.
    tpi_data = itemizer_data[
        (itemizer_data[ievar] > 0) & (itemizer_data[ievar] < itemizer_data["stdded"])
    ]
    ols_y = np.log(tpi_data[ievar])
    ols_x = tpi_data[exogenous_vars]
    ols_res = sm.OLS(ols_y, ols_x).fit()
    ols_se = np.sqrt(ols_res.scale)
    error = np.random.normal(loc=0.0, scale=ols_se, size=len(nonitemizer_data))
    raw_imputed_amt = ols_res.predict(nonitemizer_data[exogenous_vars]) + error
    # (2) Limiting the imputed amount to be no more than the standard
    # deduction is a second part of the ad hoc procedure to deal with the
    # Heckman sample selection problems present in this imputation process.
    log_stdded = np.log(nonitemizer_data["stdded"])
    cap_imputed_amt = np.where(
        raw_imputed_amt > log_stdded, log_stdded, raw_imputed_amt
    )
    adj_imputed_amt = cap_imputed_amt + log_amount_af[ievar]
    imputed_amount = np.where(
        positive_imputed, np.exp(adj_imputed_amt).round().astype(int), 0
    )
    if DUMP1:
        print("size of {} OLS sample = {}".format(ievar, len(ols_y)))
        print("max {} value = {}".format(ievar, ols_y.max()))
        print("avg {} value = {:.2f}".format(ievar, ols_y.mean()))
        print(ols_res.summary())
        print("OLS std error of regression = {:.2f}".format(ols_se))
        print("mean cap_imputed_amt = {:.3f}".format(cap_imputed_amt.mean()))
        print("mean adj_imputed_amt = {:.3f}".format(adj_imputed_amt.mean()))
        print("mean imputed_amount = {:.2f}".format(imputed_amount.mean()))
    # return imputed_amount array
    return imputed_amount


# end of impute() function


def check(iev, nonitemizer_data, target_cnt, target_amt):
    """
    Function that returns error message if weighted nonitemizer_data for iev
    does not imply filing unit counts and itemized expenses amounts that are
    close to the targets.
    """
    max_diff = 0.2
    var = nonitemizer_data[iev]
    pos = var > 0
    wgt = nonitemizer_data["s006"] * 0.01
    assert len(var) == len(wgt)
    wcnt = wgt[pos].sum() * 1e-6  # millions of filing units
    wamt = (var[pos] * wgt[pos]).sum() * 1e-9  # billions of dollars
    msg = ""
    if not np.allclose([wcnt], [target_cnt[iev]], rtol=0.0, atol=max_diff):
        msg += "\nNONITEMIZER {}>0 CNT TARGET ACTUAL= {:.1f} {:.1f}".format(
            iev, target_cnt[iev], wcnt
        )
    if not np.allclose([wamt], [target_amt[iev]], rtol=0.0, atol=max_diff):
        msg += "\nNONITEMIZER {}>0 AMT TARGET ACTUAL= {:.1f} {:.1f}".format(
            iev, target_amt[iev], wamt
        )
    return msg


# end of check() function


def impute_itemized_expenses(alldata):
    """
    Main function in impute_itmexp.py file.
    Argument: puf.csv DataFrame just before imputation is done.
    Returns: puf.csv DataFrame with imputed itemized expense amounts for
             nonitemizers.
    """
    # specify variable names of itemized-expense variables
    iev_names = [
        "e18400",  # state and local taxes
        "e18500",  # real-estate taxes
        "e19200",  # interest paid
        "e19800",  # charity cash contributions
        "e20100",  # charity non-cash contributions
        "e20400",  # misc itemizable expenses
        "e17500",  # medical expenses
        "g20500",
    ]  # gross casualty/theft loss

    def standard_deduction(row):
        """
        Specifies 2011 standard deduction amount by MARS
        """
        # TODO: parameterize this function
        if row["MARS"] == 1:
            return 5800  # single
        elif row["MARS"] == 2:
            return 11600  # married filing jointly
        elif row["MARS"] == 3:
            return 5800  # married filing separately
        elif row["MARS"] == 4:
            return 8500  # head of household
        else:
            raise ValueError("illegal value of MARS")

    # extract selected variables and construct new variables
    varnames = iev_names + [
        "MARS",
        "filer",
        "s006",
        "XTOT",
        "e00200",
        "e00600",
        "e00900",
        "e02000",
    ]
    data = alldata[varnames].copy()
    data["stdded"] = data.apply(standard_deduction, axis=1)
    data["sum_itmexp"] = data[iev_names].sum(axis=1)
    data["itemizer"] = np.where(data["sum_itmexp"] > data["stdded"], 1, 0)
    data["constant"] = 1
    data["MARS2"] = np.where(data["MARS"] == 2, 1, 0)
    data["MARS3"] = np.where(data["MARS"] == 3, 1, 0)
    data["MARS4"] = np.where(data["MARS"] == 4, 1, 0)

    # separate all the data into data for itemizers and data for nonitemizers
    itemizer_data = data[data["itemizer"] == 1].copy()
    nonitemizer_data = data[data["itemizer"] == 0].copy()

    # descriptive statistics for the data variables
    if DUMP0:
        print("ALL raw count = {:6d}".format(len(data)))
        print("PUF raw count = {:6d}".format(len(data[data["filer"] == 1])))
        print("CPS raw count = {:6d}".format(len(data[data["filer"] == 0])))
        print("PUF fraction of ALL = {:.4f}".format(data["filer"].mean()))
        ier = data["itemizer"]
        print("ALL itemizer mean = {:.4f}".format(ier.mean()))
        print("PUF itemizer mean = {:.4f}".format(ier[data["filer"] == 1].mean()))
        print("CPS itemizer mean = {:.4f}".format(ier[data["filer"] == 0].mean()))
        for iev in iev_names:
            var = itemizer_data[iev]
            varpos = var > 0
            print(
                "{} with {}>0 = {:.4f}  {:.2f}".format(
                    "frac and mean for itemizers",
                    iev,
                    varpos.mean(),
                    var[varpos].mean(),
                )
            )
        print("itmexp correlation coefficients for itemizers:")
        print(itemizer_data[iev_names].corr()[iev_names[:4]])
        print(itemizer_data[iev_names].corr()[iev_names[-4:]])
        for iev in iev_names:
            var = nonitemizer_data[iev]
            varpos = var > 0
            print("frac of non-itemizers with {}>0 = {:.4f}".format(iev, varpos.mean()))

    # specify 2011 JCT count/amount targets for nonitemizers
    # (When JCX-75-15 Table 2 contains more than one line item for a
    #  PUF variable, we assume the largest count represents the count
    #  for the PUF variable, and we assume that the sum of the amounts
    #  for the line items represents the amount for the PUF variable.)
    target_cnt = dict(zip(iev_names, [0.0] * len(iev_names)))
    target_amt = dict(zip(iev_names, [0.0] * len(iev_names)))
    target_cnt["e18400"] = 113.2
    target_amt["e18400"] = 128.1
    target_cnt["e18500"] = 34.7
    target_amt["e18500"] = 46.2
    target_cnt["e19200"] = 16.7
    target_amt["e19200"] = 58.5
    target_cnt["e19800"] = 63.0
    target_amt["e19800"] = 27.7
    target_cnt["e20100"] = 31.5
    target_amt["e20100"] = 15.6
    target_cnt["e20400"] = 16.2
    target_amt["e20400"] = 18.6
    target_cnt["e17500"] = 5.5
    target_amt["e17500"] = 20.4

    # specify calibrated logit-probability and log-amount additive factors
    # (Note that the logit_prob_af value will affect both the count and
    #  the amount for that itmexp variable, so calibrate logit_prob_af
    #  first and then calibrate the log_amount_af value.  Also, note that
    #  because of the recursive nature of the imputation equations, the
    #  two additive factors for each itemexp variable must be calibrated
    #  in the order the equations are estimated.)
    logit_prob_af = dict(zip(iev_names, [0.0] * len(iev_names)))
    log_amount_af = dict(zip(iev_names, [0.0] * len(iev_names)))
    logit_prob_af["e18400"] = 1.40
    log_amount_af["e18400"] = -0.753
    logit_prob_af["e18500"] = -2.73
    log_amount_af["e18500"] = -0.93
    logit_prob_af["e19200"] = -2.90
    log_amount_af["e19200"] = -0.282
    logit_prob_af["e19800"] = -0.70
    log_amount_af["e19800"] = -1.47
    logit_prob_af["e20100"] = -0.73
    log_amount_af["e20100"] = -0.63
    logit_prob_af["e20400"] = -2.25
    log_amount_af["e20400"] = -0.28
    logit_prob_af["e17500"] = -2.70
    log_amount_af["e17500"] = -0.31

    # estimate itemizer equations and use to impute nonitemizer itmexp amounts
    exogenous_vars = [
        "constant",
        "MARS2",
        "MARS3",
        "MARS4",
        "XTOT",
        "e00200",
        "e00600",
        "e00900",
        "e02000",
    ]
    errmsg = ""
    for iev in iev_names:
        if iev == "g20500":
            nonitemizer_data["g20500"] = 0
        else:
            nonitemizer_data[iev] = impute(
                iev,
                logit_prob_af,
                log_amount_af,
                exogenous_vars,
                itemizer_data,
                nonitemizer_data,
            )
            errmsg += check(iev, nonitemizer_data, target_cnt, target_amt)
            # add imputed variable to exogenous variable list in order
            # to better estimate correlation between the imputed variables
        exogenous_vars.append(iev)
    if errmsg:
        if CALIBRATING:
            print(errmsg)
        else:
            raise ValueError(errmsg)

    # proportionally reduce imputed amounts in cases where nonitemizer's
    # sum of imputed amounts exceeds the nonitemizer's standard deduction
    # (3) Reducing the imputed amounts so that their sum is no more than
    # the nonitemizer filing unit's standard deduction is a third part of
    # the ad hoc procedure to deal with the Heckman sample selection problems
    # present in this imputation process.
    stdded = nonitemizer_data["stdded"]
    ratio_ = nonitemizer_data[iev_names].sum(axis=1) / stdded
    ratio = np.maximum(ratio_, 1.0)
    if DUMP2:
        print(
            "BEFORE: num of nonitemizers with sum>stdded = {}".format(
                len(ratio[ratio > 1])
            )
        )
        print(
            "BEFORE: frac of nonitemizers with sum>stdded = {:.4f}".format(
                len(ratio[ratio > 1]) / float(len(ratio))
            )
        )
    for iev in iev_names:
        reduced_amt = np.trunc(nonitemizer_data[iev] / ratio)
        nonitemizer_data[iev] = reduced_amt.astype(int)
    if DUMP2:
        r_a = nonitemizer_data[iev_names].sum(axis=1) / stdded
        print(
            "AFTER: num of nonitemizers with sum>stdded = {}".format(len(r_a[r_a > 1]))
        )
        print(
            "AFTER: frac of nonitemizers with sum>stdded = {:.4f}".format(
                len(r_a[r_a > 1]) / float(len(r_a))
            )
        )

    # set imputed itmexp variable values in alldata and return alldata
    combined_data = pd.concat([nonitemizer_data, itemizer_data]).sort_index()
    for iev in iev_names:
        alldata[iev] = combined_data[iev]
    return alldata


# end of impute_itemized_expenses() function


if __name__ == "__main__":
    RAWDATA = pd.read_csv("puf.csv")
    AUGDATA = impute_itemized_expenses(RAWDATA)
    AUGDATA.to_csv("puf-aug.csv", index=False)
