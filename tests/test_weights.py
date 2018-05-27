import pytest
import numpy as np


@pytest.mark.parametrize('kind', ['puf', 'cps'])
def test_weights(kind, puf_weights, cps_weights, growfactors):
    # test range of years in weights file
    first_growfactors_year = growfactors.index.min()
    last_growfactors_year = growfactors.index.max()
    if kind == 'puf':
        weights = puf_weights
        first_weights_year = 2011  # change value when using newer PUF data
        expected_num_records = 239002  # change value when using newer PUF data
        last_weights_year = last_growfactors_year
    elif kind == 'cps':
        weights = cps_weights
        first_weights_year = 2014  # change value when using newer CPS data
        expected_num_records = 456465  # change value when using newer CPS data
        last_weights_year = last_growfactors_year
    else:
       raise ValueError('illegal kind = {}'.format(kind))
    sorted_weights_columns = sorted([col for col in weights])
    first_weights_column = sorted_weights_columns[0]
    last_weights_column = sorted_weights_columns[-1]
    assert first_weights_column == 'WT{}'.format(first_weights_year)
    assert last_weights_column == 'WT{}'.format(last_weights_year)
    # test number of rows in weights file
    assert weights.shape[0] == expected_num_records
    # test range of weight values for each year
    min_weight = 0  # weight must be non-negative,
    max_weight = 1800000  # but can be quite large
    for col in weights:
       if weights[col].min() < min_weight:
           msg = '{} weights[{}].min()={} < {}'
           raise ValueError(msg.format(kind, col,
                                       weights[col].min(), min_weight))
       if weights[col].max() > max_weight:
           msg = '{} weights[{}].max()={} > {}'
           raise ValueError(msg.format(kind, col,
                                       weights[col].max(), max_weight))
