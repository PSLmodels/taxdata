"""
Test CPS benefits file contents.
"""
import pytest
import numpy as np


@pytest.mark.parametrize('kind', ['cps'])
def test_benefits(kind, cps_benefits, puf_benefits,
                  growfactors, cps_start_year, puf_start_year,
                  cps_count, puf_count):
    """
    Check contents of cps_benefits dataframe.
    (Note that there are no puf_benefits data.)
    """
    # specify benefits dataframe and related parameters
    if kind == 'cps':
        benefits = cps_benefits
        first_year = cps_start_year
        data_count = cps_count
    elif kind == 'puf':
        benefits = puf_benefits
        first_year = puf_start_year
        data_count = puf_count
        raise ValueError('illegal kind={}'.format(kind))
    else:
        raise ValueError('illegal kind={}'.format(kind))
    # test that benefit count is no greater than data_count
    count = benefits.shape[0]
    assert count <= data_count
    # test benefits column names for benefit type and year range
    valid_types = ['ssi', 'mcaid', 'mcare', 'vet', 'snap',
                   'tanf', 'housing', 'wic']
    recid_included = False
    valid_years = range(first_year, growfactors.index.max() + 1)
    min_byear = 9999
    max_byear = 1111
    for colname in benefits:
        if colname == 'RECID':
            recid_included = True
        else:
            parts = colname.split('_')
            assert len(parts) == 2
            btype = parts[0]
            assert btype in valid_types
            byear = int(parts[1])
            assert byear in valid_years
            if byear < min_byear:
                min_byear = byear
            if byear > max_byear:
                max_byear = byear
    assert recid_included
    assert min_byear == first_year + 1
    assert max_byear == growfactors.index.max()
    # test benefit values for each year
    min_benefit = 0
    # TODO: reduce max_benefit after fixing Medicaid/Medicare benefits
    max_benefit = 1200000  # i.e., $1.2 million
    for col in benefits:
        if col == 'RECID':
            continue
        if benefits[col].min() < min_benefit:
            msg = '{} benefits[{}].min()={} < {}'
            raise ValueError(msg.format(kind, col,
                                        benefits[col].min(), min_benefit))
        if benefits[col].max() > max_benefit:
            msg = '{} benefits[{}].max()={} > {}'
            raise ValueError(msg.format(kind, col,
                                        benefits[col].max(), max_benefit))
    # test that there are no benefits records with a zero benefit in every year
    bens = benefits.drop('RECID', axis=1)
    num_nonzero_bens = np.count_nonzero(bens, axis=1)
    num_allzeros = np.sum(~np.all(num_nonzero_bens))
    if num_allzeros > 0:
        msg = 'number {} records with all zero benefits in every year = {}'
        raise ValueError(msg.format(kind, num_allzeros))
