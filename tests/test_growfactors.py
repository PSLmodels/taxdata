import numpy as np


def min_max(data, meta, dataname):
    """
    Test for ensuring all variables are within their logical minimum and
    maximum
    """
    for var in meta.keys():
        availability = meta[var]['availability']
        min_value = meta[var]['range']['min']
        max_value = meta[var]['range']['max']
        in_data = True
        if dataname not in availability:
            in_data = False
        if in_data:
            m = '{}-{} contains values less than min value'.format(dataname,
                                                                   var)
            assert np.all(data[var] >= min_value), m
            m = '{}-{} contains values greater than max value'.format(dataname,
                                                                      var)
            assert np.all(data[var] <= max_value), m


def test_growfactor_start_year(growfactors):
    first_year = growfactors['YEAR'].min()
    first_taxcalc_policy_year = 2013
    assert first_year <= first_taxcalc_policy_year


def test_growfactor_values(growfactors):
    first_year = growfactors['YEAR'].min()
    growfactors.set_index('YEAR', inplace=True)
    for fname in growfactors:
        if fname != 'YEAR':
            assert growfactors[fname][first_year] == 1.0
    min_value = 0.50
    max_value = 1.60
    for fname in growfactors:
        if fname != 'YEAR':
            assert growfactors[fname].min() >= min_value
            assert growfactors[fname].max() <= max_value
