"""
Clean up the CPS file and make it ready for Tax-Calculator
"""

import numpy as np
import pandas as pd
import copy
from pathlib import Path
from .helpers import CUR_PATH
from .constants import USEABLE_VARS


ADJ_TARGETS = pd.read_csv(Path(CUR_PATH, "adjustment_targets.csv"))


def drop_vars(data):
    """
    Returns Pandas DataFrame of data without unuseable variables
    """
    drop_vars = list(set(data.columns) - USEABLE_VARS)
    data = data.drop(drop_vars, axis=1)

    return data


def add_agi_bin(data, col_name):
    """
    Add an AGI bin indicator used in Tax-Calc to apply adjustment factors
    """
    THRESHOLDS_K = [
        -np.inf,
        0,
        5,
        10,
        15,
        20,
        25,
        30,
        40,
        50,
        75,
        100,
        200,
        500,
        1000,
        1500,
        2000,
        np.inf,
    ]
    thresholds = [x * 1000 for x in THRESHOLDS_K]
    data["agi_bin"] = pd.cut(
        data[col_name],
        thresholds,
        labels=np.arange(0, len(THRESHOLDS_K) - 1),
        right=False,
    )

    return data


def deduction_limits(data):
    """
    Apply limits on itemized deductions
    """
    # Split charitable contributions into cash and non-cash using ratio in PUF
    cash = 0.82013
    non_cash = 1.0 - cash
    data["e19800"] = data["CHARITABLE"] * cash
    data["e20100"] = data["CHARITABLE"] * non_cash

    # Apply student loan interest deduction limit
    data["e03210"] = np.where(data["SLINT"] > 2500, 2500, data["SLINT"])

    # Apply IRA contribution limit
    deductable_ira = np.where(
        data["age_head"] >= 50,
        np.where(data["ADJIRA"] > 6500, 6500, data["ADJIRA"]),
        np.where(data["ADJIRA"] > 5500, 5500, data["ADJIRA"]),
    )
    data["e03150"] = deductable_ira

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
    assert np.allclose(goal_amts.sum(), goal_total)
    # Find current totals in each bin
    bin_0 = np.where(agi < 0, var * weight, 0).sum()
    bin_1 = np.where((agi >= 0) & (agi < 5000), var * weight, 0).sum()
    bin_2 = np.where((agi >= 5000) & (agi < 10000), var * weight, 0).sum()
    bin_3 = np.where((agi >= 10000) & (agi < 15000), var * weight, 0).sum()
    bin_4 = np.where((agi >= 15000) & (agi < 20000), var * weight, 0).sum()
    bin_5 = np.where((agi >= 20000) & (agi < 25000), var * weight, 0).sum()
    bin_6 = np.where((agi >= 25000) & (agi < 30000), var * weight, 0).sum()
    bin_7 = np.where((agi >= 30000) & (agi < 40000), var * weight, 0).sum()
    bin_8 = np.where((agi >= 40000) & (agi < 50000), var * weight, 0).sum()
    bin_9 = np.where((agi >= 50000) & (agi < 75000), var * weight, 0).sum()
    bin_10 = np.where((agi >= 75000) & (agi < 100_000), var * weight, 0).sum()
    bin_11 = np.where((agi >= 100_000) & (agi < 200_000), var * weight, 0).sum()
    bin_12 = np.where((agi >= 200_000) & (agi < 500_000), var * weight, 0).sum()
    bin_13 = np.where((agi >= 500_000) & (agi < 1e6), var * weight, 0).sum()
    bin_14 = np.where((agi >= 1e6) & (agi < 1.5e6), var * weight, 0).sum()
    bin_15 = np.where((agi >= 1.5e6) & (agi < 2e6), var * weight, 0).sum()
    bin_16 = np.where((agi >= 2e6), var * weight, 0).sum()
    # Create series holding each of the current totals
    actual_amts = pd.Series(
        [
            bin_0,
            bin_1,
            bin_2,
            bin_3,
            bin_4,
            bin_5,
            bin_6,
            bin_7,
            bin_8,
            bin_9,
            bin_10,
            bin_11,
            bin_12,
            bin_13,
            bin_14,
            bin_15,
            bin_16,
        ],
        index=goal_amts.index,
    )
    ratios_index = [num for num in range(0, len(actual_amts))]
    # Determine the ratios
    ratios = pd.Series(goal_amts / actual_amts)
    ratios.index = ratios_index

    # Apply adjustment ratios
    var_array = np.array(var)
    var_array = np.nan_to_num(var_array)
    ratios = np.where(ratios == np.inf, 1.0, ratios)
    adj_array = ratios[agi_bin]
    _var = var * adj_array

    # assert that we don't lose any of the variable
    tot = (_var * weight).sum()
    m = f"{tot:,.2f} != {goal_total:,.2f}"

    try:
        assert np.allclose(np.array(goal_total), np.array(tot)), m
    except AssertionError:
        print(m)
        print("Reversing Adjustment")
        _var = var
    tot = (_var * weight).sum()
    m = f"{tot:,.2f} != {goal_total:,.2f}"
    assert np.allclose(np.array(goal_total), np.array(tot)), m

    return _var


def adjust(data, targets):
    """
    data: CPS in DataFrame format
    targets: targeted totals provided by the IRS
    """
    # Make copies of values to avoid pandas warning
    inc = copy.deepcopy(data["tot_inc"])
    int_inc = copy.deepcopy(data["e00300"])
    odiv_inc = copy.deepcopy(data["e00600"])
    qdiv_inc = copy.deepcopy(data["e00650"])
    biz_inc = copy.deepcopy(data["e00900"])
    print("e00300")
    data["e00300"] = adjust_helper(
        inc, int_inc, targets["INT"], data["s006"], data["agi_bin"]
    )
    div_ratio = data["e00600"] / (data["e00600"] + data["e00650"])
    print("e00600")
    data["e00600"] = adjust_helper(
        inc, odiv_inc, targets["ODIV"], data["s006"], data["agi_bin"]
    )
    print("e00650")
    data["e00650"] = adjust_helper(
        inc, qdiv_inc, targets["QDIV"], data["s006"], data["agi_bin"]
    )
    total = data["e00600"] + data["e00650"]
    data["e00600"] = total * div_ratio
    data["e00650"] = total * (1.0 - div_ratio)
    biz_ratio_p = data["e00900p"] / data["e00900"]
    biz_ratio_s = 1.0 - biz_ratio_p
    biz_ratio_p = np.nan_to_num(biz_ratio_p, nan=0, posinf=1, neginf=1)
    biz_ratio_s = np.nan_to_num(biz_ratio_s, nan=0, posinf=1, neginf=1)
    sub = biz_ratio_s[data["MARS"] != 2]
    zeros = np.zeros_like(sub)
    assert np.allclose(sub, zeros)
    print("e00900")
    data["e00900"] = adjust_helper(
        inc, biz_inc, targets["BIZ"], data["s006"], data["agi_bin"]
    )
    data["e00900p"] = data["e00900"] * biz_ratio_p
    data["e00900s"] = data["e00900"] * biz_ratio_s

    return data


def finalprep(data: pd.DataFrame):
    """
    Function for cleaning up the CPS file
    Parameters
    ----------
    data: pandas DataFrame with the raw CPS tax unit file
    """
    data = data.fillna(0.0)
    # recode blind variables
    data["blind_head"] = np.where(data["blind_head"] == 1, 1, 0)
    data["blind_spouse"] = np.where(data["blind_spouse"] == 1, 1, 0)

    # cap EIC
    data["EIC"] = np.minimum(data["EIC"], 3)

    # apply deduction deduction
    data = deduction_limits(data)

    # rename variables
    RENAMES = {
        "mars": "MARS",
        "dep_stat": "DSI",
        "divs": "e00600",
        "CGAGIX": "e01100",
        "DPAD": "e03240",
        "TIRAD": "e01400",
        "SEHEALTH": "e03270",
        "KEOGH": "e03300",
        "MEDEX": "e17500",
        "CDC": "e32800",
        "MISCITEM": "e20400",
        "realest": "e18500",
        "statetax": "e18400",
        "cash_char": "e19800",
        "non_cash_char": "e20100",
    }
    data = data.rename(columns=RENAMES)
    # assert that no non-married filers have non-zero values for spouse income
    sub_data = data[data["MARS"] != 2]
    zeros = np.zeros_like(sub_data["MARS"])
    assert np.allclose(sub_data["e00200s"], zeros)
    assert np.allclose(sub_data["e00900s"], zeros)
    assert np.allclose(sub_data["e02100s"], zeros)

    # add record ID
    data["RECID"] = range(1, len(data.index) + 1)

    # add AGI bins
    data = add_agi_bin(data, "tot_inc")
    # adjust income distributions
    print("Adjusting Income Distribution")
    data = adjust(data, ADJ_TARGETS)
    # assert that no non-married filers have non-zero values for spouse income
    sub_data = data[data["MARS"] != 2]
    zeros = np.zeros_like(sub_data["MARS"])
    assert np.allclose(sub_data["e00200s"], zeros)
    assert np.allclose(sub_data["e00900s"], zeros)
    data = drop_vars(data)
    print("Adding zero pencon_p and pencon_s variables")
    data["pencon_p"] = np.zeros(len(data.index), dtype=np.int32)
    data["pencon_s"] = np.zeros(len(data.index), dtype=np.int32)
    # clean data
    data = data.fillna(0.0)
    data = data.astype(np.int32)
    data["e00200"] = data["e00200p"] + data["e00200s"]
    data["e00900"] = data["e00900p"] + data["e00900s"]
    data["e02100"] = data["e02100p"] + data["e02100s"]
    data["e00650"] = np.minimum(data["e00600"], data["e00650"])
    data["s006"] *= 100

    return data
