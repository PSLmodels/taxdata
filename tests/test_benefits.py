"""
Test CPS benefits file contents.
"""
import pytest
import numpy as np
import pandas as pd


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


@pytest.mark.parametrize('kind', ['cps'])
def test_extrapolated_benefits(kind, cps_benefits, puf_benefits,
                               cps, puf, cps_weights, puf_weights,
                               cps_start_year, puf_start_year,
                               cps_count, puf_count,
                               growfactors, growth_rates, last_year):
    """
    Compare actual and target extrapolated benefit amounts and counts.
    (Note that there are no puf_benefits data.)
    """
    rel_tolerance = 0.15  # should be not much more than 0.05
    dump_res = False
    # specify several DataFrames and related parameters
    if kind == 'cps':
        basedata = cps
        benefits = cps_benefits
        weights = cps_weights
        first_year = cps_start_year
        data_count = cps_count
    elif kind == 'puf':
        basedata = puf
        benefits = puf_benefits
        weights = puf_weights
        first_year = puf_start_year
        data_count = puf_count
        raise ValueError('illegal kind={}'.format(kind))
    else:
        raise ValueError('illegal kind={}'.format(kind))
    benefit_names = ['ssi', 'mcare', 'mcaid', 'snap', 'wic',
                     'tanf', 'vet', 'housing']
    # expand benefits DataFrame to include those who don't receive benefits
    recid_df = pd.DataFrame({'RECID': basedata.RECID})
    full_benefits = recid_df.merge(benefits, on='RECID', how='left')
    full_benefits.fillna(0, inplace=True)
    assert len(recid_df.index) == len(full_benefits.index)
    extrapolated_benefits = full_benefits.astype(np.float32)
    del recid_df
    del full_benefits
    assert len(extrapolated_benefits.index) == data_count
    # compute benefit amounts and counts for first_year
    fyr_amount = dict()
    fyr_count = dict()
    wght = basedata['s006'] * 0.01
    for bname in benefit_names:
        ben = basedata['{}_ben'.format(bname)]
        benamt = (ben * wght).sum() * 1e-9
        fyr_amount[bname] = round(benamt, 3)
        bencnt = wght[ben > 0].sum() * 1e-6
        fyr_count[bname] = round(bencnt, 3)
        if dump_res:
            benavg = benamt / bencnt
            res = '{} {}\t{:8.3f}{:8.3f}{:8.1f}'.format(first_year, bname,
                                                        benamt, bencnt, benavg)
            print(res)
    # compare actual and target amounts/counts for each subsequent year
    differences = False
    for year in range(first_year + 1, last_year + 1):
        # compute actual amuonts/counts for year
        wght = weights['WT{}'.format(year)] * 0.01
        actual_amount = dict()
        actual_count = dict()
        for bname in benefit_names:
            ben = extrapolated_benefits['{}_{}'.format(bname, year)]
            assert len(ben.index) == len(wght.index)
            benamt = (ben * wght).sum() * 1e-9
            actual_amount[bname] = round(benamt, 3)
            bencnt = wght[ben > 0].sum() * 1e-6
            actual_count[bname] = round(bencnt, 3)
            if dump_res:
                benavg = benamt / bencnt
                res = '{} {}\t{:8.3f}{:8.3f}{:8.1f} A'.format(year, bname,
                                                              benamt, bencnt,
                                                              benavg)
                print(res)
        # compute target amuonts/counts for year
        target_amount = dict()
        target_count = dict()
        for bname in benefit_names:
            benfyr = fyr_amount[bname]
            col = '{}_benefit_growth'.format(bname)
            benfactor = 1.0 + growth_rates.loc[year, col]
            benamt = benfyr * benfactor
            target_amount[bname] = round(benamt, 3)
            cntfyr = fyr_count[bname]
            col = '{}_participation_growth'.format(bname)
            cntfactor = 1.0 + growth_rates.loc[year, col]
            bencnt = cntfyr * cntfactor
            target_count[bname] = round(bencnt, 3)
            if dump_res:
                benavg = benamt / bencnt
                res = '{} {}\t{:8.3f}{:8.3f}{:8.1f} T'.format(year, bname,
                                                              benamt, bencnt,
                                                              benavg)
                print(res)
        # compare actual and target amuonts/counts for year
        for bname in benefit_names:
            if not np.allclose([actual_amount[bname]],
                               [target_amount[bname]],
                               atol=0.0, rtol=rel_tolerance):
                differences = True
                reldiff = actual_amount[bname] / target_amount[bname] - 1.0
                msg = '{} {}\tAMT\t{:9.3f}{:9.3f}{:8.1f}'
                print(msg.format(year, bname,
                                 actual_amount[bname],
                                 target_amount[bname],
                                 reldiff * 100))
            if not np.allclose([actual_count[bname]],
                               [target_count[bname]],
                               atol=0.0, rtol=rel_tolerance):
                differences = True
                reldiff = actual_count[bname] / target_count[bname] - 1.0
                msg = '{} {}\tCNT\t{:9.3f}{:9.3f}{:8.1f}'
                print(msg.format(year, bname,
                                 actual_count[bname],
                                 target_count[bname],
                                 reldiff * 100))
    # end of year loop
    if differences:
        assert 'differences is' == 'True'
