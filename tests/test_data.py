"""
Test CPS and PUF data file contents.
"""
import os
import pytest
import numpy as np


def unique_recid(data, dataname):
    """
    Test that RECID values are unique.
    """
    recid = data['RECID']
    unique, counts = np.unique(recid, return_counts=True)
    recid_count = dict(zip(unique, counts))
    duplicates = False
    msg = ''
    for rid in sorted(recid_count.keys()):
        if recid_count[rid] > 1:
            duplicates = True
            msg += '\nRECID={} has COUNT={}'.format(rid, recid_count[rid])
    if duplicates:
        title = 'The following {} RECIDs have COUNTS greater than one:'
        raise ValueError(title.format(dataname) + msg)


def min_max(data, meta, dataname):
    """
    Test that variable variables are within their minimum/maximum range.
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
    Test the relationships between variables.

    Note (1): we have weakened the XTOT == sum of nu18, n1820, n21 assertion
    for the PUF because in PUF data the value of XTOT is capped by IRS-SOI.

    Note (2): we have weakened the n24 <= nu18 assertion for the PUF because
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
    if dataname == 'CPS':
        m = eq_str.format(dataname, 'XTOT', 'sum of nu18, n1820, n21')
        assert np.all(data['XTOT'] == nsums), m
    else:
        # see Note (1) in docstring
        m = less_than_str.format(dataname, 'XTOT', 'sum of nu18, n1820, n21')
        assert np.all(data['XTOT'] <= nsums), m

    m = less_than_str.format(dataname, 'n24', 'nu18')
    if dataname == 'CPS':
        assert np.all(data['n24'] <= data['nu18']), m
    else:
        # see Note (2) in docstring
        m = 'Number of records where n24 > nu18 has changed'
        assert (data['n24'] > data['nu18']).sum() == 14717, m
        subdata = data[data['n24'] > data['nu18']]
        max_diff = 3
        m = 'n24 > nu18 + {}'.format(max_diff)
        assert np.all(subdata['n24'] <= subdata['nu18'] + max_diff), m

    m = less_than_str.format(dataname, 'e00650', 'e00600')
    assert np.all(data['e00600'] >= data['e00650']), m

    m = less_than_str.format(dataname, 'e01700', 'e01500')
    assert np.all(data['e01500'] >= data['e01700']), m


def variable_check(test_path, data, dataname):
    """
    Test aggregate values in the data.
    """
    expected_file_name = '{}_agg_expected.txt'.format(dataname)
    efile_path = os.path.join(test_path, expected_file_name)
    with open(efile_path, 'r') as efile:
        expected_txt = efile.readlines()
    expected_sum = dict()
    expected_min = dict()
    expected_max = dict()
    for line in expected_txt[1:]:
        txt = line.rstrip()
        split = txt.split()
        assert len(split) == 4
        var = split[0]
        expected_sum[var] = int(split[1])
        expected_min[var] = int(split[2])
        expected_max[var] = int(split[3])

    # loop through each column in the dataset and check sum, min, max
    actual_txt = '{:20}{:>15}{:>15}{:>15}\n'.format('VARIABLE',
                                                    'SUM', 'MIN', 'MAX')
    var_inform = '{:20}{:15d}{:15d}{:15d}\n'
    diffs = False
    diff_list_str = ''  # string to hold all of the variables with errors
    new_vars = False
    new_var_list_str = ''  # srint to hold all of the unexpected variables
    for var in sorted(data.columns):
        sum = int(data[var].sum())
        min = int(data[var].min())
        max = int(data[var].max())
        actual_txt += var_inform.format(var, sum, min, max)
        try:
            var_diff = (sum != expected_sum[var] or
                        min != expected_min[var] or
                        max != expected_max[var])
            if var_diff:
                diffs = True
                diff_list_str += var + '\n'
        except KeyError:
            # if the variable is not expected, print a new message
            new_vars = True
            new_var_list_str += var + '\n'

    # check for any missing variables
    missing_vars = False
    missing_vars_set = set(expected_sum.keys()) - set(data.columns)
    if missing_vars_set:
        missing_vars = True
        missing_vars_str = '\n'.join(v for v in missing_vars_set)

    # if there is an error, write the actual file
    if diffs or new_vars or missing_vars:
        msg = '{}\n'.format(dataname.upper)
        actual_file_name = '{}_agg_actual.txt'.format(dataname)
        actual_file_path = os.path.join(test_path, actual_file_name)
        with open(actual_file_path, 'w') as afile:
            afile.write(actual_txt)
        # modify error message based on which errors are raised
        if diffs:
            diff_msg = 'Aggregate results differ for following variables:\n'
            diff_msg += diff_list_str
            msg += diff_msg + '\n'
        if new_vars:
            new_msg = 'The following unexpected variables were discoverd:\n'
            new_msg += new_var_list_str
            msg += new_msg + '\n'
        if missing_vars:
            msg += 'The following expected variables are missing in the data:'
            msg += '\n' + missing_vars_str + '\n\n'
        msg += 'If new results OK, copy {} to {}'.format(actual_file_name,
                                                         expected_file_name)
        raise ValueError(msg)

@pytest.mark.one
@pytest.mark.requires_pufcsv
def test_pufcsv_data(puf, metadata, test_path):
    """
    Test PUF data.
    """
    unique_recid(puf, 'PUF')
    min_max(puf, metadata, 'puf')
    relationships(puf, 'PUF')
    variable_check(test_path, puf, 'puf')


def test_cpscsv_data(cps, metadata, test_path):
    """
    Test CPS data.
    """
    unique_recid(cps, 'CPS')
    min_max(cps, metadata, 'cps')
    relationships(cps, 'CPS')
    variable_check(test_path, cps, 'cps')
