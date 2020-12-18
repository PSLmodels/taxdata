import os
import json
import pytest
import pandas as pd
from pathlib import Path


# TODO: revise the following constants when using new or revised CPS/PUF data
CPS_START_YEAR = 2014
PUF_START_YEAR = 2011
PUF_COUNT = 248591
LAST_YEAR = 2029


@pytest.fixture(scope="session")
def test_path():
    return Path(__file__).resolve().parent


@pytest.fixture(scope="session")
def cps_path(test_path):
    return Path(test_path, "..", "taxdata", "cps", "cps.csv.gz")


@pytest.fixture(scope="session")
def growfactors(test_path):
    gf_path = Path(test_path, "..", "puf_stage1", "growfactors.csv")
    return pd.read_csv(gf_path, index_col="YEAR")


@pytest.fixture(scope="session")
def metadata(test_path):
    with Path(test_path, "records_metadata.json").open("r") as mdf:
        return json.load(mdf)


@pytest.fixture(scope="session")
def cps_benefit_metadata(test_path):
    with Path(test_path, "cps_benefits_metadata.json").open("r") as mdf:
        return json.load(mdf)


@pytest.fixture(scope="session")
def cps(test_path, cps_path):
    return pd.read_csv(cps_path)


@pytest.fixture(scope="session")
def cps_count(test_path, cps_path):
    cps_df = pd.read_csv(cps_path)
    return cps_df.shape[0]


@pytest.fixture(scope="session")
def cps_start_year():
    return CPS_START_YEAR


@pytest.fixture(scope="session")
def puf_path(test_path):
    return Path(test_path, "..", "puf_data", "puf.csv")


@pytest.fixture(scope="session")
def puf(puf_path):
    if os.path.isfile(puf_path):
        return pd.read_csv(puf_path)
    else:
        return None


@pytest.fixture(scope="session")
def puf_count(puf_path):
    if os.path.isfile(puf_path):
        puf_df = pd.read_csv(puf_path)
        count = puf_df.shape[0]
        if count != PUF_COUNT:
            msg = "puf.shape[0] = {} not equal to PUF_COUNT = {}"
            raise ValueError(msg.format(count, PUF_COUNT))
    else:
        count = PUF_COUNT
    return count


@pytest.fixture(scope="session")
def puf_start_year():
    return PUF_START_YEAR


@pytest.fixture(scope="session")
def last_year():
    return LAST_YEAR


@pytest.fixture(scope="session")
def cps_weights(test_path):
    cpsw_path = Path(test_path, "..", "cps_stage2", "cps_weights.csv.gz")
    return pd.read_csv(cpsw_path)


@pytest.fixture(scope="session")
def puf_weights(test_path):
    pufw_path = Path(test_path, "..", "puf_stage2", "puf_weights.csv.gz")
    return pd.read_csv(pufw_path)


@pytest.fixture(scope="session")
def cps_ratios(test_path):
    # cpsr_path = os.path.join(test_path, '../cps_stage3/cps_ratios.csv')
    # return pd.read_csv(cpsr_path, index_col=0)
    return None


@pytest.fixture(scope="session")
def puf_ratios(test_path):
    pufr_path = Path(test_path, "..", "puf_stage3", "puf_ratios.csv")
    return pd.read_csv(pufr_path, index_col=0)
