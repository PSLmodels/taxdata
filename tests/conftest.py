import os
import json
import pytest
import pandas as pd


@pytest.fixture(scope='session')
def test_path():
    return os.path.abspath(os.path.dirname(__file__))


@pytest.fixture(scope='session')
def cps(test_path):
    return pd.read_csv(os.path.join(test_path, '../cps_data/cps.csv.gz'))


@pytest.fixture(scope='session')
def puf(test_path):
    return pd.read_csv(os.path.join(test_path, '../puf_data/puf.csv'))


@pytest.fixture(scope='session')
def metadata(test_path):
    with open(os.path.join(test_path, 'records_metadata.json'), 'r') as mdf:
        return json.load(mdf)


@pytest.fixture(scope='session')
def cps_weights_path(test_path):
    return 


@pytest.fixture(scope='session')
def cps_weights(test_path):
    return pd.read_csv(os.path.join(test_path,
                                    '../cps_stage2/cps_weights.csv.gz'))


@pytest.fixture(scope='session')
def puf_weights(test_path):
    return pd.read_csv(os.path.join(test_path,
                                    '../puf_stage2/puf_weights.csv.gz'))


@pytest.fixture(scope='session')
def growfactors(test_path):
    return pd.read_csv(os.path.join(test_path, '../stage1/growfactors.csv'),
                       index_col='YEAR')
