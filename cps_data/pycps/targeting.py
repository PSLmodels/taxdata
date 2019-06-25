"""
State level targeting of certain income variables
"""
import pandas as pd


def target(cps, state_data_link):
    """
    Read state level income information and adjust CPS data accordingly
    """
    state_data = pd.read_csv(state_data_link, index_col="STATE",
                             thousands=",")
    # only use aggregate data
    state_data = state_data[state_data["AGI_STUB"] == 0].copy()

    # map fips codes and to state abbreviations
    fips_dict = {'AK': 2, 'AL': 1, 'AR': 5, 'AZ': 4, 'CA': 6, 'CO': 8, 'CT': 9,
                 'DC': 11, 'DE': 10, 'FL': 12, 'GA': 13, 'HI': 15, 'IA': 19,
                 'ID': 16, 'IL': 17, 'IN': 18, 'KS': 20, 'KY': 21, 'LA': 22,
                 'MA': 25, 'MD': 24, 'ME': 23, 'MI': 26, 'MN': 27, 'MO': 29,
                 'MS': 28, 'MT': 30, 'NC': 37, 'ND': 38, 'NE': 31, 'NH': 33,
                 'NJ': 34, 'NM': 35, 'NV': 32, 'NY': 36, 'OH': 39, 'OK': 40,
                 'OR': 41, 'PA': 42, 'RI': 44, 'SC': 45, 'SD': 46, 'TN': 47,
                 'TX': 48, 'UT': 49, 'VA': 51, 'VT': 50, 'WA': 53, 'WI': 55,
                 'WV': 54, 'WY': 56}
    # map income variables in the CPS and IRS data
    # TODO: Add imputed variables
    var_map = {
        "A00200": ["e00200p", "e00200s"],
        "A00300": ["e00300"],
        "A00600": ["e00600"],
        "A00650": ["e00650"],
        "A00900": ["e00900p", "e00900s"],
        "A02300": ["e02300"]
    }

    # dictionary to hold factors
    factor_dict = {}

    # loop through each state and variable
    for var, cps_vars in var_map.items():
        factor_dict[var] = []
        print(var)
        for state, fips in fips_dict.items():
            target = state_data[var][state] * 1000  # scale up IRS data
            cps_uw_total = cps[cps_vars][cps["fips"] == fips].sum(axis=1)
            cps_sum = (cps_uw_total * cps["s006"]).sum()
            # compute factor
            factor = target / cps_sum
            factor_dict[var].append(factor)
            print(f"{state} {target:,.2f} {cps_sum:,.2f} {factor:.2f}")

    # create a DataFrame with the factors
    factor_df = pd.DataFrame(factor_dict)
    factor_df.index = fips_dict.values()
    # export factors
    factor_df.to_csv("state_factors.csv")

    # apply factors
    for var, cps_vars in var_map.items():
        factor_array = factor_df[var][cps["fips"]].values
        for v in cps_vars:
            cps[v] += factor_array

    return cps
