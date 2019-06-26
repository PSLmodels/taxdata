"""
Clean up the CPS file and make it ready for Tax-Calculator
"""
import numpy as np
import pandas as pd


def drop_vars(data):
    """
    Returns Pandas DataFrame of data without unuseable variables
    """
    useable_vars = [
        'DSI', 'EIC', 'FLPDYR', 'MARS', 'MIDR', 'RECID', 'XTOT', 'age_head',
        'age_spouse', 'agi_bin', 'blind_head', 'blind_spouse', 'cmbtp',
        'e00200', 'e00200p', 'e00200s', 'e00300', 'e00400', 'e00600', 'e00650',
        'e00700', 'e00800', 'e00900', 'e00900p', 'e00900s', 'e01100', 'e01200',
        'e01400', 'e01500', 'e01700', 'e02000', 'e02100', 'e02100p', 'e02100s',
        'e02300', 'e02400', 'e03150', 'e03220', 'e03230', 'e03240', 'e03270',
        'e03290', 'e03300', 'e03400', 'e03500', 'e07240', 'e07260', 'e07300',
        'e07400', 'e07600', 'e09700', 'e09800', 'e09900', 'e11200', 'e17500',
        'e18400', 'e18500', 'e19200', 'e19800', 'e20100', 'e20400', 'g20500',
        'e24515', 'e24518', 'e26270', 'e27200', 'e32800', 'e58990', 'e62900',
        'e87530', 'elderly_dependents', 'f2441', 'f6251', 'n24',
        'nu05', 'nu13', 'nu18', 'n1820', 'n21', 'p08000', 'p22250', 'p23250',
        'p25470', 'p87521', 's006', 'e03210', 'ssi_ben', 'snap_ben',
        'vet_ben', 'mcare_ben', 'mcaid_ben', 'oasdi_ben', 'other_ben',
        'h_seq', 'ffpos', 'fips', 'a_lineno', 'tanf_ben', 'wic_ben',
        'housing_ben', "linenos"
    ]

    drop_vars = []
    for item in data.columns:
        if item not in useable_vars:
            drop_vars.append(item)
    data = data.drop(drop_vars, axis=1)

    return data


def sum_income(data):
    """
    Sum up and rename income variables
    """


def add_agi_bin(data, col_name):
    """
    Add an AGI bin indicator used in Tax-Calc to apply adjustment factors
    """
    agi = pd.Series([0] * len(data[col_name]))
    agi[data[col_name] < 0] = 0
    agi[(data[col_name] >= 0) & (data[col_name] < 5000)] = 1
    agi[(data[col_name] >= 5000) & (data[col_name] < 10000)] = 2
    agi[(data[col_name] >= 10000) & (data[col_name] < 15000)] = 3
    agi[(data[col_name] >= 15000) & (data[col_name] < 20000)] = 4
    agi[(data[col_name] >= 20000) & (data[col_name] < 25000)] = 5
    agi[(data[col_name] >= 25000) & (data[col_name] < 30000)] = 6
    agi[(data[col_name] >= 30000) & (data[col_name] < 40000)] = 7
    agi[(data[col_name] >= 40000) & (data[col_name] < 50000)] = 8
    agi[(data[col_name] >= 50000) & (data[col_name] < 75000)] = 9
    agi[(data[col_name] >= 75000) & (data.INCOME < 100000)] = 10
    agi[(data[col_name] >= 100000) & (data[col_name] < 200000)] = 11
    agi[(data[col_name] >= 200000) & (data[col_name] < 500000)] = 12
    agi[(data[col_name] >= 500000) & (data[col_name] < 1e6)] = 13
    agi[(data[col_name] >= 1e6) & (data[col_name] < 1.5e6)] = 14
    agi[(data[col_name] >= 1.5e6) & (data[col_name] < 2e6)] = 15
    agi[(data[col_name] >= 2e6) & (data[col_name] < 5e6)] = 16
    agi[(data[col_name] >= 5e6) & (data[col_name] < 1e7)] = 17
    agi[(data[col_name] >= 1e7)] = 18

    data['agi_bin'] = agi

    return data


def final_prep(data):
    """
    Function for cleaning up the CPS file
    """
    # recode blind variables
    data["blind_head"] = np.where(
        data["blind_head"] == 1, 1, 0
    )
    data["blind_spouse"] = np.where(
        data["blind_spouse"] == 1, 1, 0
    )

    # rename variables
    renames = {
        "mars": "MARS",
        "dep_stat": "DSI"
    }
    data = data.rename(columns=renames)

    # add record ID
    data["RECID"] = data.index + 1

    # add AGI bins
    # TODO: figure out why this was causing an error
    # data = add_agi_bin(data, "agi")
    data = drop_vars(data)
    # clean data
    data = data.fillna(0.)
    data = data.astype(np.int32)
    data['e00200'] = data['e00200p'] + data['e00200s']
    data['e00900'] = data['e00900p'] + data['e00900s']
    data['e02100'] = data['e02100p'] + data['e02100s']
    data['s006'] *= 100

    return data


if __name__ == "__main__":
    data = pd.read_csv("raw_cps.csv")
    cps = final_prep(data)
    cps.to_csv("pycps.csv", index=False)
