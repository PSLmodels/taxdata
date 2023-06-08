"""
Test CPS and PUF weights file contents.
"""
import pytest
import numpy as np


DUMP_WEIGHTS = False  # normally set to False; True implies dump with test fail


@pytest.mark.parametrize("kind", ["cps", "puf"])
def test_weights(
    kind,
    cps_weights,
    puf_weights,
    growfactors,
    cps_count,
    puf_count,
    cps_start_year,
    puf_start_year,
):
    """
    Check value of filing-unit weights in each year.
    """
    # specify weights dataframe and related parameters
    if kind == "cps":
        weights = cps_weights
        count = cps_count
        first_year = cps_start_year
    elif kind == "puf":
        weights = puf_weights
        count = puf_count
        first_year = puf_start_year
    else:
        raise ValueError("illegal kind={}".format(kind))
    # test count of records in weights
    if weights.shape[0] != count:
        msg = "{} weights.shape[0]={} != data_count = {}"
        raise ValueError(msg.format(kind, weights.shape[0], count))
    # test range of years in weights file
    sorted_weights_columns = sorted([col for col in weights])
    first_weights_column = sorted_weights_columns[0]
    assert first_weights_column == "WT{}".format(first_year)
    last_weights_column = sorted_weights_columns[-1]
    assert last_weights_column == "WT{}".format(growfactors.index.max())
    # test weight values for each year
    MIN_WEIGHT = 0  # weight must be non-negative,
    MAX_WEIGHT = 2000000  # but can be quite large
    for col in weights:
        if weights[col].min() <= MIN_WEIGHT:
            msg = "{} weights[{}].min()={} <= {}"
            raise ValueError(msg.format(kind, col, weights[col].min(), MIN_WEIGHT))
        if weights[col].max() > MAX_WEIGHT:
            msg = "{} weights[{}].max()={} > {}"
            raise ValueError(msg.format(kind, col, weights[col].max(), MAX_WEIGHT))
    # test sum of weights (in millions) for each year
    MIN_WEIGHT_SUM = 144
    MAX_WEIGHT_SUM = 258
    for col in sorted_weights_columns:
        weight_sum = weights[col].sum() * 1e-2 * 1e-6  # in millions
        if DUMP_WEIGHTS:
            msg = "{} {} {:.3f}"
            print(msg.format(kind, col, weight_sum))
        if weight_sum < MIN_WEIGHT_SUM:
            msg = "{} weights[{}].sum()={:.1f} < {:.1f}"
            raise ValueError(msg.format(kind, col, weight_sum, MIN_WEIGHT_SUM))
        if weight_sum > MAX_WEIGHT_SUM:
            msg = "{} weights[{}].max()={:.1f} > {:.1f}"
            raise ValueError(msg.format(kind, col, weight_sum, MAX_WEIGHT_SUM))
    if DUMP_WEIGHTS:
        raise ValueError("STOPPING because DUMP_WEIGHTS = True")
    # test that there are no weights records with a zero weight in every year
    num_nonzero_weights = np.count_nonzero(weights, axis=1)
    num_allzeros = np.sum(~np.all(num_nonzero_weights))
    if num_allzeros > 0:
        txt = "number {} records with a zero weight in every year = {}"
        msg = txt.format(kind, num_allzeros)
        if kind == "puf" and num_allzeros == 1:
            print("WARNING: " + msg)
        else:
            raise ValueError(msg)
