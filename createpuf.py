import pandas as pd
import numpy as np
from taxdata import cps, puf
from taxdata.matching import statmatch
from pathlib import Path

CUR_PATH = Path(__file__).resolve().parent
DATA_PATH = Path(CUR_PATH, "data")
CPS_YEAR = 2016
# variables used in the matching process
PARTITION_VARS = ["dsi", "mars", "agede", "depne", "people"]
REG_VARS = [
    "const",
    "agede",
    "e00200",
    "e00300",
    "e00600",
    "e00900",
    "e02100",
    "e01500",
    "e02400",
    "e02300",
    "e00800",
    "wage_share",
    "cap_share",
    "se1",
    "se2",
    "se3",
]
INC_VARS = [
    "e00200",
    "e00300",
    "e00400",
    "e00600",
    "bil",
    "fil",
    "e02400",
    "e01500",
    "e00800",
    "e02300",
]
CAP_VARS = ["e00300", "e00400", "e00600"]


def dataprep(data):
    """
    Prep data for matching
    """
    data["const"] = 1
    data["bil"] = np.maximum(0, data["e00900"])
    data["fil"] = np.maximum(0, data["e02100"])
    data["tpi"] = data[INC_VARS].sum(axis=1)
    data["wage_share"] = np.divide(
        data["e00200"], data["tpi"], out=np.zeros(data.shape[0]), where=data["tpi"] != 0
    )
    data["cap_inc"] = data[CAP_VARS].sum(axis=1)
    data["cap_share"] = np.divide(
        data["cap_inc"],
        data["tpi"],
        out=np.zeros(data.shape[0]),
        where=data["tpi"] != 0,
    )
    data["people"] = np.where(data["mars"] == 2, data["depne"] + 2, data["depne"] + 1)
    data["people"] = np.minimum(5, data["people"])
    wage_flag = (data["e00200"] != 0).astype(int)
    # self employment flag
    se_flag = np.logical_or(data["e00900"] != 0, data["e02100"] != 0).astype(int)
    # income source flags
    data["se1"] = np.where(wage_flag & ~se_flag, 1, 0)
    data["se2"] = np.where(~wage_flag & se_flag, 1, 0)
    data["se3"] = np.where(wage_flag & se_flag, 1, 0)
    data["depne"] = np.where(
        np.logical_and(data["mars"] == 3, data["depne"] == 0), 1, data["depne"]
    )
    return data


# create CPS tax units
print("Creating CPS tax units")
raw_cps = cps.create(DATA_PATH, exportpkl=False, cps_files=[CPS_YEAR], benefits=False)
# minor PUF prep
print("Cleaning up PUF")
puf2011 = pd.read_csv(Path(DATA_PATH, "puf2011.csv"))
raw_puf = puf.preppuf(puf2011, 2011)
raw_puf.to_csv(Path(DATA_PATH, "raw_puf.csv"))

# rename CPS file to match PUF
cps_rename = {"dep_stat": "dsi", "divs": "e00600"}
raw_cps.rename(columns=cps_rename, inplace=True)
# cap number of dependents in CPS to line up with PUF
raw_cps["depne"] = np.where(
    raw_cps["mars"] == 2,
    np.minimum(5, raw_cps["depne"]),
    np.minimum(3, raw_cps["depne"]),
)
raw_cps = dataprep(raw_cps)
raw_puf = dataprep(raw_puf)
raw_cps["recid"] = range(1, len(raw_cps.index) + 1)

# statistical matching
match_index = statmatch.match(
    raw_puf,
    raw_cps,
    "recid",
    "recid",
    "s006",
    "s006",
    "e04800",
    REG_VARS,
    PARTITION_VARS,
)
print("Done!")
