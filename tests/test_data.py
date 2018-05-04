import numpy as np


def min_max(data, meta, data_name):
    """
    Test for ensuring all variables are within their logical minimum and
    maximum
    """
    for var in meta.keys():
        availability = meta[var]['availability']
        min_value = meta[var]['range']['min']
        max_value = meta[var]['range']['max']
        in_data = True
        if var == 'e19800':
            print('here')
        if data_name not in availability:
            in_data = False
        if in_data:
            m = f'{data_name}-{var} contains values less than minimum value'
            if var == 'e19800':
                print(data_name)
            assert np.all(data[var] >= min_value), m
            m = f'{data_name}-{var} contains values greater than maximum value'
            assert np.all(data[var] <= max_value), m


def test_min_max(cps, puf, metadata):
    min_max(cps, metadata, 'CPS')
    min_max(puf, metadata, 'PUF')
