"""
Test PUF adjust-ratio file contents.
"""

import pytest


@pytest.mark.parametrize("kind", ["puf"])
def test_ratios(
    kind, cps_ratios, puf_ratios, growfactors, cps_start_year, puf_start_year
):
    """
    Check contents of puf_ratios dataframe.
    (Note that there are no cps_ratios data.)
    """
    # specify ratios dataframe and related parameters
    if kind == "cps":
        raw_ratios = cps_ratios
        first_year = cps_start_year
        raise ValueError("illegal kind={}".format(kind))
    elif kind == "puf":
        raw_ratios = puf_ratios
        first_year = puf_start_year
    else:
        raise ValueError("illegal kind={}".format(kind))
    ratios = raw_ratios.transpose()
    ratios.index.name = "agi_bin"
    # test agi_bin values
    agi_bin_list = [str(abin) for abin in range(0, 19)]  # bins from 0 thru 18
    assert set(ratios.index.values) == set(agi_bin_list)
    # test range of years in ratios file
    if kind == "cps":
        sorted_columns = sorted([col for col in ratios if col[:-4] == "???"])
    elif kind == "puf":
        sorted_columns = sorted([col for col in ratios if col[:-4] == "INT"])
    first_ratios_year = int(sorted_columns[0][-4:])
    assert first_ratios_year == first_year
    last_ratios_year = int(sorted_columns[-1][-4:])
    assert last_ratios_year == growfactors.index.max()
    # test ratio values for each year
    min_ratio = 0.2
    max_ratio = 1.8
    for col in ratios:
        if ratios[col].min() < min_ratio:
            msg = "{} ratios[{}].min()={} < {}"
            raise ValueError(msg.format(kind, col, ratios[col].min(), min_ratio))
        if ratios[col].max() > max_ratio:
            msg = "{} ratios[{}].max()={} > {}"
            raise ValueError(msg.format(kind, col, ratios[col].max(), max_ratio))
