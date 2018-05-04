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


def test_data(cps, puf, metadata):
    min_max(cps, metadata, 'cps')
    min_max(puf, metadata, 'puf')
    relationships(cps)
    relationships(puf)


def relationships(data):
    """
    Test the relative relationships between variables
    """
    eq_str = '{} not equal to {}'
    less_than_str = '{} not less than or equal to {}'
    tol = 0.020001

    eq_vars = [('e00200', ['e00200p', 'e00200s']),
               ('e00900', ['e00900p', 'e00900s']),
               ('e02100', ['e02100p', 'e02100s'])]
    for lhs, rhs in eq_vars:
        if not np.allclose(data[lhs], data[rhs].sum(axis=1), atol=tol):
            raise ValueError(eq_str.format(lhs, rhs))

    less_than_vars = [('XTOT', ['nu18', 'n1820', 'n21']),
                      ('n24', ['nu18'])]
    for lhs, rhs in less_than_vars:
        m = less_than_str.format(lhs, 'sum of {}'.format(rhs))
        assert np.all(data[lhs] <= data[rhs].sum(axis=1)), m
