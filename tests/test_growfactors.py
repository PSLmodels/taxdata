"""
Test growfactors.csv file contents.
"""


def test_growfactor_start_year(growfactors):
    """
    Check that growfactors.csv can support Tax-Calculator Policy needs.
    """
    first_growfactors_year = growfactors.index.min()
    first_taxcalc_policy_year = 2013
    assert first_growfactors_year <= first_taxcalc_policy_year


def test_growfactor_values(growfactors):
    """
    Check that each grow factor value is in plausible min,max range.
    """
    first_year = growfactors.index.min()
    for fname in growfactors:
        if fname != "YEAR":
            assert growfactors[fname][first_year] == 1.0
    min_value = 0.15
    max_value = 8.70
    for fname in growfactors:
        if fname != "YEAR":
            assert growfactors[fname].min() >= min_value
            assert growfactors[fname].max() <= max_value

    assert growfactors.isnull().sum().sum() == 0
