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
    ALL_QUALIFIED_PROB = 0.429  # % of units where all dividends are qualified
    NO_QUALIFIED_PROB = 0.093  # % of units where no dividends are qualified
    # % of units where either all or no dividends are qualified
    NON_AVG_PROB = ALL_QUALIFIED_PROB + NO_QUALIFIED_PROB
    QUALIFIED_FRAC = 0.678  # % of dividends that are qualified among remaining

    # determine qualified dividend percentage
    probs = np.random.random(len(data["divs"]))
    qualified = np.ones(len(data["divs"]))
    qualified = np.where(
        (probs > ALL_QUALIFIED_PROB) & (probs <= NON_AVG_PROB), 0.0, qualified
    )
    qualified = np.where(probs > NON_AVG_PROB, QUALIFIED_FRAC, qualified)
    data["e00650"] = data["divs"] * qualified

    # Split interest income into taxable and tax exempt
    SLOPE = 0.068
    RATIO = 0.46
    prob = 1.0 - SLOPE * (data["interest"] * 1e-3)
    uniform_rn = np.random.random(len(prob))
    data["e00300"] = np.where(
        uniform_rn < prob, data["interest"], data["interest"] * RATIO
    )
    data["e00400"] = data["interest"] - data["e00300"]

    # Pensions and annuities
    probs = np.random.random(len(data["e01500"]))
    FULL_TAXABLE_PROB = 0.612
    ZERO_TAX_PROB = 0.073
    NON_AVG_PROB = FULL_TAXABLE_PROB + ZERO_TAX_PROB
    AVG_TAXABLE_AMOUNT = 0.577
    # determine taxability
    taxability = np.ones(len(data["e01500"]))
    taxability = np.where(
        (probs > FULL_TAXABLE_PROB) & (probs <= NON_AVG_PROB), 0.0, taxability
    )
    taxability = np.where(probs > NON_AVG_PROB, AVG_TAXABLE_AMOUNT, taxability)
    data["e01700"] = data["e01500"] * taxability

    return data
