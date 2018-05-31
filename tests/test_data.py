import pytest
import numpy as np
import os


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


def aggregate(test_path, data, dataname):
    """
    Test aggregate values in the data
    """
    expected_file_name = '{}_agg_expected.txt'.format(dataname)
    file_path = os.path.join(test_path, expected_file_name)
    with open(file_path, 'r') as f:
        expected_txt = f.readlines()
    expected_dict = {}
    for line in expected_txt[1:]:
        txt = line.rstrip()
        split = txt.split()
        expected_dict[split[0]] = int(split[1])

    # loop through each column in the dataset and check aggregate total
    actual_txt = '{:17} Value\n'.format('Variable')
    diffs = False
    var_list_str = ''  # string to hold all of the variables with errors
    for var in data.columns:
        agg = data[var].sum()
        info_str = '{:17} {}\n'.format(var, agg)
        actual_txt += info_str
        if agg != expected_dict[var]:
            diffs = True
            var_list_str += var + '\n'
    # if there is a change, write new file
    if diffs:
        actual_file_name = '{}_agg_actual.txt'.format(dataname)
        actual_file_path = os.path.join(test_path, actual_file_name)
        with open(actual_file_path, 'w') as f:
            f.write(actual_txt)
        msg = '{} - Aggregate results differ for following '
        msg += 'variables:\n'.format(dataname.upper()) + var_list_str
        msg += 'If new results are OK copy {} to {}'.format(actual_file_name,
                                                            expected_file_name)
        raise ValueError(msg)


@pytest.mark.requires_pufcsv
def test_pufcsv_data(puf, metadata, test_path):
    min_max(puf, metadata, 'puf')
    relationships(puf, 'PUF')
    aggregate(test_path, puf, 'puf')


def test_cpscsv_data(cps, metadata, test_path):
    min_max(cps, metadata, 'cps')
    relationships(cps, 'CPS')
    aggregate(test_path, cps, 'cps')
