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


def relationships(data, dataname):
    """
    Test the relative relationships between variables.

    Note: we have weakened the n24 <= nu18 assertion for the PUF because
    the only way to ensure it held true would be to create extreamly small
    bins during the tax unit matching process, which had the potential to
    reduce the overall match accuracy.
    """
    eq_str = '{}-{} not equal to {}'
    less_than_str = '{}-{} not less than or equal to {}'
    tol = 0.020001

    eq_vars = [('e00200', ['e00200p', 'e00200s']),
               ('e00900', ['e00900p', 'e00900s']),
               ('e02100', ['e02100p', 'e02100s'])]
    for lhs, rhs in eq_vars:
        if not np.allclose(data[lhs], data[rhs].sum(axis=1), atol=tol):
            raise ValueError(eq_str.format(dataname, lhs, rhs))

    nsums = data[['nu18', 'n1820', 'n21']].sum(axis=1)
    m = less_than_str.format(dataname, 'XTOT', 'sum of nu18, n1820, n21')
    assert np.all(data['XTOT'] <= nsums), m
    m = less_than_str.format(dataname, 'n24', 'nu18')
    if dataname == 'CPS':
        assert np.all(data['n24'] <= data['nu18']), m
    else:  # see note in docstring
        m = 'Number of records where n24 > nu18 has changed'
        assert (data['n24'] > data['nu18']).sum() == 14928, m
        subdata = data[data['n24'] > data['nu18']]
        m = 'n24 > nu18 + 3'
        assert np.all(subdata['n24'] <= subdata['nu18'] + 3), m

    m = less_than_str.format(dataname, 'e00650', 'e00600')
    assert np.all(data['e00600'] >= data['e00650']), m

    m = less_than_str.format(dataname, 'e01700', 'e01500')
    assert np.all(data['e01500'] >= data['e01700']), m


def test_data(cps, puf, metadata):
    min_max(cps, metadata, 'cps')
    min_max(puf, metadata, 'puf')
    relationships(cps, 'CPS')
    relationships(puf, 'PUF')
