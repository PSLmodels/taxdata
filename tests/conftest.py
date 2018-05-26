import os
import json
import pandas as pd
import pytest


@pytest.fixture(scope='session')
def test_path():
    return os.path.abspath(os.path.dirname(__file__))


@pytest.fixture(scope='session')
def cps_path(test_path):
    return os.path.join(test_path, '../cps_data/cps.csv.gz')


@pytest.fixture(scope='session')
def cps(cps_path):
    return pd.read_csv(cps_path)


@pytest.fixture(scope='session')
def puf_path(test_path):
    return os.path.join(test_path, '../puf_data/puf.csv')


@pytest.fixture(scope='session')
def puf(puf_path):
    return pd.read_csv(puf_path)


@pytest.fixture(scope='session')
def metadata(test_path):
    path = os.path.join(test_path, 'records_metadata.json')
    with open(path, 'r') as f:
        return json.load(f)


@pytest.fixture(scope='session')
def benefit_growth_rates_path(test_path):
    return os.path.join(test_path, '../cps_stage3/growth_rates.csv')


@pytest.fixture(scope='session')
def raw_cps_path(test_path):
    return os.path.join(test_path, '../cps_data/cps_raw_rename.csv.gz')


@pytest.fixture(scope='session')
def raw_weights_path(test_path):
    return os.path.join(test_path, '../cps_stage2/cps_weights_raw.csv.gz')


@pytest.fixture(scope='session')
def growfactors_path(test_path):
    return os.path.join(test_path, '../stage1/growfactors.csv')


@pytest.fixture(scope='session')
def growfactors(growfactors_path):
    return pd.read_csv(growfactors_path)
