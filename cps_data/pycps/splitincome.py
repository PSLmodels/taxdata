"""
Split up certain income variables
"""
import numpy as np


def split_income(data):
    """
    Split up income variables
    """
    np.random.seed(79)

    # Qualified dividends
    all_qualified_prob = 0.429  # % of units where all dividends are qualified
    no_qualified_prob = 0.093  # % of units where no dividends are qualified
    # % of units where either all or no dividends are qualified
    non_avg_prob = all_qualified_prob + no_qualified_prob
    qualified_frac = 0.678  # % of dividends that are qualified among remaining

    # determine qualified dividend percentage
    probs = np.random.random(len(data["divs"]))
    qualified = np.ones(len(data["divs"]))
    qualified = np.where(
        (probs > all_qualified_prob) & (probs <= non_avg_prob),
        0.0, qualified
    )
    qualified = np.where(
        probs > non_avg_prob, qualified_frac, qualified
    )
    data["e00650"] = data["divs"] * qualified

    # Split interest income into taxable and tax exempt
    slope = 0.068
    ratio = 0.46
    prob = 1. - slope * (data["interest"] * 1e-3)
    uniform_rn = np.random.random(len(prob))
    data["e00300"] = np.where(
        uniform_rn < prob,
        data["interest"], data["interest"] * ratio
    )
    data["e00400"] = data["interest"] - data["e00300"]

    # Pensions and annuities
    probs = np.random.random(len(data["e01500"]))
    full_taxable_prob = 0.612
    zero_tax_prob = 0.073
    non_avg_prob = full_taxable_prob + zero_tax_prob
    avg_taxable_amout = 0.577
    # determine taxability
    taxability = np.ones(len(data["e01500"]))
    taxability = np.where(
        (probs > full_taxable_prob) & (probs <= non_avg_prob),
        0.0, taxability
    )
    taxability = np.where(
        probs > non_avg_prob,
        avg_taxable_amout, taxability
    )
    data["e01700"] = data["e01500"] * taxability

    return data
