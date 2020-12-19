"""
Impute DC pension contributions in PUF using aggregate data from IRS Form W-2.

The imputation strategy has two steps.  In the first step, use
aggregate W-2 data on the number of individuals with positive pension
contributions for each of 16 positive wage groups in each of 8 age
groups (that is, for each of 128 age-wage cells) to impute
stochastically whether or not an individual with earnings makes an
elective deferral to a defined-contribution (DC) pension plan.  Then
in the second step, use aggregate W-2 data on the dollar amount of
elective DC deferrals among those with a positive deferral for each of
16 positive wage groups in each of 8 age groups (that is, for the same
128 age-wage cells) to impute the pension contribution (that is, elective
deferral) amount.

This strategy would be straight forward to implement if the W-2 sample
was the same as the PUF sample.  But because the W-2 sample is larger
(at least for the high-wage groups), there is a need to make a minor
adjustment among higer-wage individuals (that is, among individuals
with wages over $200,000).  For details on the logic of the adjustment
and the results with and without the adjustment, see the comments
below on the HIWAGE parameters, which have been calibrated by hand.

Another tactical complication is that the amount of each individual's
pension contribution was legally limited to $16,500 during 2011.  The
second imputation stage uses an iterative procedure to cap individual
pension contributions in a way that maintains the age-wage cell's
aggregate pension contribution.

And finally, individuals cannot defer more than their gross earnings,
which in PUF records is equal to the sum of net earnings and pension
contributions, which is (e00200p + pencon_p) for the filing-unit head
and (e00200s + pencon_s) for the filing-unit spouse, if present.  For
CPS records in the puf.csv file, gross earnings is equal to e00200p for
the filing-unit head and e00200s for the filing-unit spouse, if present.
Gross earnings and pension contributions out of gross earnings are
calculated for the PUF records by conducting the whole imputation
process twice.  See the impute_pension_contributions() function code
for details.
"""
from __future__ import print_function
import sys
import numpy as np
import pandas as pd

if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO


DUMP0 = False
DUMP1 = False
DUMP2 = False


def targets():
    """
    Return a DataFrame containing number of taxpayers & spouses with earnings
    that make a pension contribution (in millions of people) and a DataFrame
    containing the aggregate amount of the pension contributions (in billions
    of dollars) by the wage and age categories in "SOI Tax Stats - Individual
    Information Return Form W-2 Statistics," Table 2.B.1 for 2011.  Note that
    in the orginal table, the three cnt and amt cells (for wages in the range
    of $500K to $2M) are combined into one cell for the bottom age range,
    u26, and for the top age range, 75plus.  In each of these four cases,
    the three-cell total is evenly spread across the three cells in the
    revised data specified here.  Also, the top two wage groups (5u10M and
    10u30M) are combined into a single group (5Mplus).
    """
    cnt = """
        ,  total,   u26, 26u35,  35u45,  45u55, 55u60, 60u65, 65u75,75plus
total   ,46.9781,2.7796,8.9035,11.2926,12.9201,5.8450,3.5901,1.5212,0.1261
u5K     ,1.1298,0.2766,0.2415,0.1942,0.1904,0.0785,0.0679,0.0673,0.0135
5u10K   ,1.3069,0.3113,0.3088,0.2089,0.2054,0.0926,0.0908,0.0747,0.0145
10u15K  ,1.6370,0.3211,0.3539,0.2724,0.2990,0.1508,0.1208,0.0995,0.0195
15u20K  ,2.1262,0.3323,0.4603,0.3810,0.4441,0.1947,0.1833,0.1186,0.0119
20u25K  ,2.7738,0.3519,0.6175,0.5553,0.5872,0.3019,0.2284,0.1194,0.0122
25u30K  ,3.1692,0.2899,0.7167,0.6741,0.7544,0.3936,0.2300,0.1063,0.0041
30u40K  ,6.7748,0.3608,1.5822,1.5853,1.7121,0.8025,0.5353,0.1868,0.0098
40u50K  ,6.0192,0.2355,1.3411,1.4875,1.6533,0.7287,0.4167,0.1461,0.0103
50u75K  ,10.1723,0.2178,1.8331,2.6402,3.0594,1.3791,0.7824,0.2488,0.0114
75Ku0.1M,5.0471,0.0486,0.7485,1.3961,1.6301,0.7069,0.3885,0.1237,0.0046
0.1u0.2M,5.1803,0.0309,0.5872,1.4571,1.7622,0.7604,0.4110,0.1627,0.0087
0.2u0.5M,1.3446,0.0024,0.1010,0.3668,0.5043,0.2062,0.1064,0.0530,0.0046
0.5u1.0M,0.2197,0.0001,0.0085,0.0563,0.0855,0.0370,0.0213,0.0098,0.0003
1.0u1.5M,0.0416,0.0001,0.0016,0.0105,0.0174,0.0059,0.0037,0.0025,0.0003
1.5u2.0M,0.0141,0.0001,0.0005,0.0030,0.0062,0.0024,0.0013,0.0008,0.0003
2u5M    ,0.0170,0.0001,0.0008,0.0033,0.0072,0.0030,0.0017,0.0009,0.0001
5Mplus  ,0.0046,0.00006,0.0003,0.0007,0.0018,0.0008,0.0006,0.0003,0.00003
"""
    """
5u10M   ,0.0033,0.00004,0.0002,0.0005,0.0013,0.0006,0.0004,0.0002,0.00002
10u30M  ,0.0013,0.00002,0.0001,0.0002,0.0005,0.0002,0.0002,0.0001,0.00001
    """
    amt = """
        ,   total,   u26,  26u35,  35u45,  45u55,  55u60,  60u65, 65u75,75plus
total   ,220.5554,3.2668,25.0779,49.9194,70.3845,37.9728,23.3431,9.9572,0.6337
u5K     ,1.1581,0.0411,0.0841,0.1733,0.3118,0.1667,0.2209,0.1563,0.0040
5u10K   ,1.1304,0.0743,0.1418,0.1530,0.2795,0.1545,0.1692,0.1414,0.0166
10u15K  ,1.7084,0.1143,0.2178,0.2361,0.3626,0.3336,0.2293,0.1764,0.0384
15u20K  ,2.8057,0.2239,0.3736,0.4198,0.7278,0.3787,0.4233,0.2336,0.0249
20u25K  ,4.3694,0.2873,0.6468,0.6841,1.0589,0.6781,0.6144,0.3710,0.0287
25u30K  ,5.6387,0.2935,0.9197,1.0006,1.3722,1.1272,0.6375,0.2767,0.0112
30u40K  ,16.1258,0.5373,2.6527,3.0594,4.3521,2.7221,1.9665,0.7954,0.0402
40u50K  ,19.1377,0.4829,3.0644,4.0657,5.6255,3.0436,1.9112,0.8700,0.0743
50u75K  ,48.6375,0.7072,6.5134,10.8502,14.9928,8.2860,5.1546,2.0320,0.1013
75Ku0.1M,37.2251,0.2379,4.2673,9.0029,12.1241,6.3733,3.8528,1.3138,0.0529
0.1u0.2M,55.5740,0.2371,4.6679,13.9483,18.9280,9.8799,5.5415,2.2351,0.1361
0.2u0.5M,21.2800,0.0211,1.3460,5.0850,8.0092,3.7434,1.9665,1.0250,0.0838
0.5u1.0M,4.2527,0.0022,0.1305,0.9381,1.6156,0.8203,0.4980,0.2246,0.0063
1.0u1.5M,0.8252,0.0022,0.0276,0.1866,0.3378,0.1288,0.0812,0.0632,0.0063
1.5u2.0M,0.2767,0.0022,0.0071,0.0511,0.1204,0.0507,0.0297,0.0176,0.0063
2u5M    ,0.3171,0.0010,0.0124,0.0535,0.1321,0.0620,0.0354,0.0189,0.0017
5Mplus  ,0.0930,0.0013,0.0046,0.0117,0.0340,0.0240,0.0111,0.0058,0.0006
"""
    """
5u10M   ,0.0674,0.0010,0.0035,0.0088,0.0231,0.0194,0.0074,0.0038,0.0005
10u30M  ,0.0256,0.0003,0.0011,0.0029,0.0109,0.0046,0.0037,0.0020,0.0001
    """
    cnt_df = pd.read_csv(StringIO(cnt), index_col=0)
    cnt_df.columns = [name.strip() for name in cnt_df.columns]
    cnt_df.index = [name.strip() for name in cnt_df.index]
    amt_df = pd.read_csv(StringIO(amt), index_col=0)
    amt_df.columns = [name.strip() for name in amt_df.columns]
    amt_df.index = [name.strip() for name in amt_df.index]
    return cnt_df, amt_df


# end of targets() function


# specify top of age and wage brackets
UNDER_AGE = [26, 35, 45, 55, 60, 65, 75, 99]
UNDER_WAGE = [
    5e3,
    10e3,
    15e3,
    20e3,
    25e3,
    30e3,
    40e3,
    50e3,
    75e3,
    100e3,
    200e3,
    500e3,
    1e6,
    2e6,
    5e6,
    30e6,
]


def age_group(row):
    """
    Specify age group of individual.
    """
    if row["age"] == 0:
        return -1
    for grp, underage in enumerate(UNDER_AGE):
        if row["age"] < underage:
            return grp
    raise ValueError("illegal value of age")


# end of age_group() function


def wage_group(row):
    """
    Specify wage group of individual.
    """
    if row["wage"] == 0:
        return -1
    for grp, underwage in enumerate(UNDER_WAGE):
        if row["wage"] < underwage:
            return grp
    raise ValueError("illegal value of wage")


# end of wage_group() function


# specify adjustment of having a positive pencon for high-wage groups
HIWAGE_PROB_SF = 1.47  # prob of positive pension contribution multiplied by SF
MIN_HIWAGE_GROUP = 11  # SF applied to wage groups no less than this MIN

# This adjustment to some cell-specific probabilities of having a
# positive pension contribution is being done because, in some
# high-wage cells, the W-2 data show more people with positive
# pension contributions than the PUF shows with positive earnings.
# Making no imputation probability adjustment (that is, setting
# HIWAGE_PROB_SF equal to one), implies the imputed head count and
# dollar amount of positive pension contributions are both roughly one
# percent below the total in the W-2 data.  Setting the HIWAGE_PROB_SF
# to the value above makes the head count of those with positive
# pension contributions equal to the total in the W-2 data and the
# imputed dollar amount is only about 0.6 of one percent below the
# total in the W-2 data.  The calibration of the HIWAGE_PROB_SF value
# was conducted so that the calibrated SF value produces an imputed count
# of individuals having a positive pension contribution equal to the
# target count of 46.98 million individuals.  SF values below the one
# specified above produce imputed counts that are less than 46.98 million
# and SF values above the one specified above produce imputed counts that
# are more than 46.98 million.  This calibration was done with DUMP0 set
# to True and by executing "python impute_pencon.py > impute_pencon.res"
# several times each with a different value of HIWAGE_PROB_SF.


# specify maximum legal elective deferral amount for DC pensions in 2011
MAX_PENCON_AMT = 16500


def impute(idata, target_cnt, target_amt):
    """
    Impute idata[pencon] given other idata variables and targets.
    """
    if DUMP1 and HIWAGE_PROB_SF != 1.0:
        print("HIWAGE_PROB_SF= {:.4f}".format(HIWAGE_PROB_SF))
        print("MIN_HIWAGE_GROUP= {}".format(MIN_HIWAGE_GROUP))
    # loop through the positive-age and positive-wage cells
    for agrp in range(0, len(UNDER_AGE)):
        for wgrp in range(0, len(UNDER_WAGE)):
            # impute actual count of having positive pencon
            in_cell = (idata["agegrp"] == agrp) & (idata["wagegrp"] == wgrp)
            cell_idata = idata[in_cell].copy()
            wgt_num_earners = cell_idata["weight"].sum() * 1e-6
            if wgt_num_earners <= 0.0:
                msg = "agrp={};wgrp={} has wgt_num_earners={:.4f} <= 0"
                print(msg.format(agrp, wgrp, wgt_num_earners))
                # raise ValueError(msg.format(agrp, wgrp, wgt_num_earners))
            wgt_pos_pencon = target_cnt.iloc[wgrp, agrp]
            prob = wgt_pos_pencon / wgt_num_earners
            if wgrp >= MIN_HIWAGE_GROUP:
                prob *= HIWAGE_PROB_SF
            if DUMP1 and prob > 1.0:
                print("agrp={};wgrp={} ==> prob= {:.3f}".format(agrp, wgrp, prob))
            cell_idata["pencon"] = np.where(cell_idata["urn"] < prob, 1, 0)
            pos_pc = cell_idata["pencon"] > 0
            if pos_pc.sum() == 0:  # no positive pension contributions in cell
                if DUMP1:
                    print("agrp={};wgrp={} has zero pencon".format(agrp, wgrp))
                continue  # to next wgrp in cell loop
            # impute actual amount of each positive pension contribution
            # taking into account that pension contributions are legally capped
            wage = cell_idata["wage"]
            wgt = cell_idata["weight"]
            wgt_pos_pc_wages = (wage[pos_pc] * wgt[pos_pc]).sum() * 1e-9
            cell_target_amt = target_amt.iloc[wgrp, agrp]
            rate0 = min(1.0, cell_target_amt / wgt_pos_pc_wages)
            if DUMP2:
                print("agrp={};wgrp={} ==> rate0= {:.4f}".format(agrp, wgrp, rate0))
            # iteratively raise non-capped deferral rate to hit target_amt
            num_iterations = 10
            for itr in range(0, num_iterations):
                uncapped_amt = np.where(pos_pc, np.round(wage * rate0).astype(int), 0)
                capped_amt = np.minimum(uncapped_amt, MAX_PENCON_AMT)
                over_amt = uncapped_amt - capped_amt
                over_tot = (over_amt * wgt).sum() * 1e-9
                rate1 = min(1.0, (cell_target_amt + over_tot) / wgt_pos_pc_wages)
                if np.allclose([rate1], [rate0]):
                    if DUMP2 and itr > 0:
                        print("  iter={} ==> rate= {:.4f}".format(itr, rate0))
                    break  # out of iteration loop
                else:
                    if DUMP2 and itr == (num_iterations - 1):
                        print("  iter={} ==> rate= {:.4f}".format(itr, rate0))
                    rate0 = rate1
            cell_idata["pencon"] = capped_amt
            # store cell_idata['pencon'] in idata
            idata.loc[in_cell, "pencon"] = cell_idata["pencon"]
            del cell_idata


# end of impute() function


def impute_pension_contributions(alldata):
    """
    Main function in impute_pencon.py file.
    Argument: puf.csv DataFrame just before imputation is done.
    Returns: puf.csv DataFrame with imputed pension contribution amounts.
    """
    # specify target DataFrames with total column and total row removed
    target_cnt, target_amt = targets()
    target_cnt.drop(labels="total", axis="index", inplace=True)
    target_cnt.drop(labels="total", axis="columns", inplace=True)
    target_amt.drop(labels="total", axis="index", inplace=True)
    target_amt.drop(labels="total", axis="columns", inplace=True)
    if DUMP0:
        print(
            "target_cnt.shape={} and size={}".format(target_cnt.shape, target_cnt.size)
        )
        print(
            "target_amt.shape={} and size={}".format(target_amt.shape, target_amt.size)
        )
        print("len(UNDER_AGE)={}".format(len(UNDER_AGE)))
        print("len(UNDER_WAGE)={}".format(len(UNDER_WAGE)))
        cnt = target_cnt.values.sum()
        print("sum(target_cnt)= {:.4f}".format(cnt))
        amt = target_amt.values.sum()
        print("sum(target_amt)= {:.4f}".format(amt))
        avg = amt / cnt
        print("avg(target_amt)= {:.3f}".format(avg))
    # construct individual-level idata from filing-unit alldata
    # (note: PUF records have filer=1 and CPS records have filer=0)
    # ... construct _p DataFrame with renamed variables
    ivars = ["age_head", "e00200p", "filer"]
    idata_p = alldata[ivars].copy()
    idata_p["spouse"] = np.zeros(len(idata_p.index), dtype=np.int8)
    idata_p["weight"] = alldata["s006"] * 0.01
    idata_p.rename(
        {"age_head": "age", "e00200p": "e00200"}, axis="columns", inplace=True
    )
    # ... construct _s DataFrame with renamed variables
    ivars = ["age_spouse", "e00200s", "filer"]
    idata_s = alldata[ivars].copy()
    idata_s["spouse"] = np.ones(len(idata_s.index), dtype=np.int8)
    idata_s["weight"] = alldata["s006"] * 0.01
    idata_s.rename(
        {"age_spouse": "age", "e00200s": "e00200"}, axis="columns", inplace=True
    )
    # ... combine the _p and _s DataFrames
    idata = pd.concat([idata_p, idata_s], copy=True)
    del idata_p
    del idata_s
    # ... construct variables that never change over the imputation process
    idata["agegrp"] = idata.apply(age_group, axis=1)
    np.random.seed(111111)
    idata["urn"] = np.random.uniform(size=len(idata.index))
    # ... initialize pension contributions to zero
    idata["pencon"] = np.zeros(len(idata.index), dtype=np.int64)
    if DUMP0:
        idata["wage"] = idata["e00200"]
        idata["wagegrp"] = idata.apply(wage_group, axis=1)
        print("raw_num_earners(#)=", (idata["wage"] > 0).sum())
        wgt_earners = idata["weight"][idata["wage"] > 0].sum()
        print("wgt_num_earners(#M)= {:.3f}".format(wgt_earners * 1e-6))
        wearnings = idata["weight"] * idata["wage"]
        wgt_earnings = wearnings.sum()
        print("wgt_earnings($B)= {:.3f}".format(wgt_earnings * 1e-9))
        wgt_puf_earnings = wearnings[idata["filer"] == 1].sum()
        print("wgt_PUF_earnings($B)= {:.3f}".format(wgt_puf_earnings * 1e-9))
        wgt_cps_earnings = wearnings[idata["filer"] == 0].sum()
        print("wgt_CPS_earnings($B)= {:.3f}".format(wgt_cps_earnings * 1e-9))
        print("min_agegrp=", idata["agegrp"].min())
        print("max_agegrp=", idata["agegrp"].max())
        print("min_wagegrp=", idata["wagegrp"].min())
        print("max_wagegrp=", idata["wagegrp"].max())
    # do two imputations to construct gross wages for PUF records
    idata["wage"] = idata["e00200"]
    idata["wagegrp"] = idata.apply(wage_group, axis=1)
    impute(idata, target_cnt, target_amt)
    idata["wage"] = np.where(
        idata["filer"] == 1, idata["e00200"] + idata["pencon"], idata["e00200"]
    )
    idata["wagegrp"] = idata.apply(wage_group, axis=1)  # gross wage group
    impute(idata, target_cnt, target_amt)
    if DUMP0:
        cnt = (idata["weight"] * (idata["pencon"] > 0)).sum() * 1e-6
        print("wgt_pencon_cnt(#M)= {:.3f}".format(cnt))
        amt = (idata["weight"] * idata["pencon"]).sum() * 1e-9
        print("wgt_pencon_amt($B)= {:.3f}".format(amt))
        avg = amt / cnt
        print("avg_pencon_amt($K)= {:.3f}".format(avg))
    # subtract pencon from e00200 for CPS records to make them net earnings
    idata["e00200"] = np.where(
        idata["filer"] == 1, idata["e00200"], idata["e00200"] - idata["pencon"]
    )
    if DUMP0:
        wearnings = idata["weight"] * idata["e00200"]
        wgt_earnings = wearnings.sum()
        print("wgt_earnings($B)= {:.3f}".format(wgt_earnings * 1e-9))
        wgt_puf_earnings = wearnings[idata["filer"] == 1].sum()
        print("wgt_PUF_earnings($B)= {:.3f}".format(wgt_puf_earnings * 1e-9))
        wgt_cps_earnings = wearnings[idata["filer"] == 0].sum()
        print("wgt_CPS_earnings($B)= {:.3f}".format(wgt_cps_earnings * 1e-9))
    # set alldata values of pencon_p and pencon_s and the e00200* variables
    alldata["pencon_p"] = idata["pencon"][idata["spouse"] == 0]
    alldata["pencon_s"] = idata["pencon"][idata["spouse"] == 1]
    alldata["e00200p"] = idata["e00200"][idata["spouse"] == 0]
    alldata["e00200s"] = idata["e00200"][idata["spouse"] == 1]
    alldata["e00200"] = alldata["e00200p"] + alldata["e00200s"]
    # return revised alldata
    return alldata


# end of impute_pension_contributions() function


if __name__ == "__main__":
    RAWDATA = pd.read_csv("puf.csv")
    REVDATA = impute_pension_contributions(RAWDATA)
    REVDATA.to_csv("puf-pc.csv", index=False)
