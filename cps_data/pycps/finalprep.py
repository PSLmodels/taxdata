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
    np.random.seed(79)
    # Determine amount of qualified dividends
    # percent of units where all dividends are qualified
    all_qualified_prob = 0.429
    # percent of units where no dividends are qualified
    no_qualified_prob = 0.093
    # percent of units where either all or no dividends are qualified
    non_avg_prob = all_qualified_prob + no_qualified_prob
    # percent of dividends that are qualified among remaining units
    qualified_frac = 0.678
    # Determine qualified dividend percentage
    probs = np.random.random(len(data['e00600']))
    qualified = np.ones(len(data['e00600']))
    qualified = np.where((probs > all_qualified_prob) &
                         (probs <= non_avg_prob), 0.0, qualified)
    qualified = np.where(probs > non_avg_prob, qualified_frac, qualified)
    data['e00650'] = data["e00600"] * qualified

    # Split interest income into taxable and tax exempt
    slope = 0.068
    ratio = 0.46
    prob = 1. - slope * (data["interest"] * 1e-3)
    uniform_rn = np.random.random(len(prob))
    data['e00300'] = np.where(uniform_rn < prob,
                              data["interest"],
                              data["interest"] * ratio)
    data['e00400'] = data['interest'] - data['e00300']

    # Split pentions and annuities using random assignment
    # probabiliies used for random assignment
    probs = np.random.random(len(data['e01500']))
    fully_taxable_prob = 0.612
    zero_tax_prob = 0.073
    non_avg_prob = fully_taxable_prob + zero_tax_prob
    avg_taxable_amout = 0.577
    # determine tax ability
    taxability = np.ones(len(data['e01500']))
    taxability = np.where((probs > fully_taxable_prob) &
                          (probs <= non_avg_prob), 0.0, taxability)
    taxability = np.where(probs > non_avg_prob, avg_taxable_amout, taxability)
    data['e01700'] = data['e01500'] * taxability

    data["MARS"] = data["mars"]

    # add record ID
    data["RECID"] = data.index + 1
    data = drop_vars(data)
    # clean data
    data = data.fillna(0.)
    # data = data.astype(np.int32)
    data['e00200'] = data['e00200p'] + data['e00200s']
    data['e00900'] = data['e00900p'] + data['e00900s']
    data['e02100'] = data['e02100p'] + data['e02100s']
    data['s006'] *= 100

    return data


if __name__ == "__main__":
    data = pd.read_csv("raw_cps.csv")
    cps = final_prep(data)
    cps.to_csv("pycps.csv", index=False)
