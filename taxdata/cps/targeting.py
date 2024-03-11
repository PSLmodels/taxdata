"""
State level targeting of certain income variables
"""

import pandas as pd
import numpy as np
from .constants import FIPS_DICT


def target(cps, state_data_link):
    """
    Read state level income information and adjust CPS data accordingly
    """
    state_data = pd.read_csv(state_data_link, index_col="STATE", thousands=",")
    # only use aggregate data
    state_data = state_data[state_data["AGI_STUB"] == 0].copy()

    # map income variables in the CPS and IRS data
    # TODO: Add imputed variables
    VAR_MAP = {
        "A00200": ["e00200p", "e00200s"],
        "A00300": ["e00300"],
        "A00600": ["divs"],
        "A00650": ["e00650"],
        "A00900": ["e00900p", "e00900s"],
        "A02300": ["e02300"],
        "A03240": ["DPAD"],
        "A01400": ["TIRAD"],
        "A03270": ["SEHEALTH"],
        "A03210": ["SLINT"],
        "A07180": ["CDC"],
    }

    # dictionary to hold factors
    factor_dict = {}

    # loop through each state and variable
    for var, cps_vars in VAR_MAP.items():
        factor_dict[var] = []
        for state, fips in FIPS_DICT.items():
            sub_cps = cps[cps["fips"] == fips]
            target = state_data[var][state] * 1000  # scale up IRS data
            # only count filers
            cps_uw_total = sub_cps[cps_vars].sum(axis=1) * sub_cps["filer"]
            cps_sum = (cps_uw_total * sub_cps["s006"]).sum()
            # compute factor
            factor = target / cps_sum
            factor_dict[var].append(factor)

    # create a DataFrame with the factors
    factor_df = pd.DataFrame(factor_dict)
    factor_df.index = FIPS_DICT.values()
    # export factors
    factor_df.to_csv("state_factors.csv")

    # apply factors
    for var, cps_vars in VAR_MAP.items():
        factor_array = factor_df[var][cps["fips"]].values
        for v in cps_vars:
            cps[v] *= factor_array

    # recalculate total income
    cps["e00200"] = cps["e00200p"] + cps["e00200s"]
    cps["e00900"] = cps["e00900p"] + cps["e00900s"]
    cps["e02100"] = cps["e02100p"] + cps["e02100s"]
    cps["e00650"] = np.minimum(cps["divs"], cps["e00650"])
    cps["tot_inc"] = cps[
        [
            "e00200",
            "e00300",
            "e00400",
            "e00900",
            "divs",
            "e00800",
            "e01500",
            "rents",
            "e02100",
            "e02400",
            "CGAGIX",
            "e02300",
        ]
    ].sum(axis=1)
    assert np.allclose(cps["e00900"], cps[["e00900p", "e00900s"]].sum(axis=1))
    assert np.allclose(cps["e02100"], cps[["e02100p", "e02100s"]].sum(axis=1))
    assert np.allclose(cps["e00200"], cps[["e00200p", "e00200s"]].sum(axis=1))

    return cps
