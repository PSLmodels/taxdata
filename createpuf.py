import pandas as pd
import numpy as np
from taxdata import cps, puf
from taxdata.matching import statmatch
from pathlib import Path

CUR_PATH = Path(__file__).resolve().parent
DATA_PATH = Path(CUR_PATH, "data")
CPS_YEAR = 2016
PUF_YEAR = 2011
# variables used in the matching process
PARTITION_VARS = ["dsi", "mars", "agede", "_depne", "people"]
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
    # we use a slightly modified version of mars for matching.
    # _mars = 1 if single, 3 if HoH, 2 any type of joint filer
    data["_mars"] = np.where(data["mars"] == 1, 1, np.where(data["mars"] == 4, 3, 2))
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
    data["_depne"] = np.where(
        data["dsi"] == 0,
        np.where(
            data["_mars"] == 2,
            np.minimum(data["depne"], 5),
            np.minimum(data["depne"], 3),
        ),
        0,
    )
    data["people"] = np.where(data["_mars"] == 2, data["depne"] + 2, data["depne"] + 1)
    data["people"] = np.minimum(5, data["people"])
    wage_flag = (data["e00200"] != 0).astype(int)
    # self employment flag
    se_flag = np.logical_or(data["e00900"] != 0, data["e02100"] != 0).astype(int)
    # income source flags
    data["se1"] = np.where(wage_flag & ~se_flag, 1, 0)
    data["se2"] = np.where(~wage_flag & se_flag, 1, 0)
    data["se3"] = np.where(wage_flag & se_flag, 1, 0)
    data["_depne"] = np.where(
        np.logical_and(data["mars"] == 3, data["_depne"] == 0), 1, data["_depne"]
    )

    return data


# create CPS tax units
print("Creating CPS tax units")
raw_cps = cps.create(DATA_PATH, exportpkl=True, cps_files=[CPS_YEAR], benefits=False)
# minor PUF prep
print("Prepping PUF")
puf2011 = pd.read_csv(Path(DATA_PATH, "puf2011.csv"))
raw_puf = puf.preppuf(puf2011, PUF_YEAR)
# raw_puf.to_csv(Path(DATA_PATH, "raw_puf.csv"), index=False)

# rename CPS file to match PUF
print("Prepping CPS")
cps_rename = {
    "dep_stat": "dsi",
    "divs": "e00600",
    "statetax": "e18400",
    "realest": "e18500",
    "miscitem": "e20400",
    "medex": "e17500",
}
raw_cps.rename(columns=cps_rename, inplace=True)
raw_cps.columns = map(str.lower, raw_cps.columns)
raw_cps["flpdyr"] = max(raw_puf["flpdyr"])
raw_cps["g20500"] = 0
# Split charitable contributions into cash and non-cash using ratio in PUF
cash = 0.82013
non_cash = 1.0 - cash
raw_cps["e19800"] = raw_cps["charitable"] * cash
raw_cps["e20100"] = raw_cps["charitable"] * non_cash

# cap number of dependents in CPS to line up with PUF
# raw_cps["depne"] = np.where(
#     raw_cps["mars"] == 2,
#     np.minimum(5, raw_cps["depne"]),
#     np.minimum(3, raw_cps["depne"]),
# )
raw_cps = dataprep(raw_cps)
raw_puf = dataprep(raw_puf)
raw_cps["recid"] = range(1, len(raw_cps.index) + 1)
raw_cps["agerange"] = 0
raw_cps["eic"] = np.minimum(3, raw_cps["eic"])
raw_cps.drop(["mcaid_ben", "mcare_ben"], axis=1, inplace=True)
raw_cps.to_csv(Path(DATA_PATH, "tu16.csv"), index=False)

# split CPS into filers and non-filers
filers = raw_cps[raw_cps["filer"] == 1].copy()
nonfilers = raw_cps[raw_cps["filer"] == 0].copy()

print("Begining statistical match")
# statistical matching
match_index = statmatch.match(
    raw_puf,
    filers,
    "recid",
    "recid",
    "s006",
    "s006",
    "e04800",
    REG_VARS,
    PARTITION_VARS,
)

# merge all the data together
print("Merging matched data")
data = pd.merge(raw_puf, match_index, how="inner", left_on="recid", right_on="recip")
data = pd.merge(
    data,
    filers,
    how="inner",
    left_on="donor",
    right_on="recid",
    suffixes=(None, "_cps"),
)

# filter off the duplicated columns
data.drop(list(data.filter(regex=".*_cps")), axis=1, inplace=True)

# add back non-filers
print("Adding non-filers")
data = pd.concat([data, nonfilers], sort=False, ignore_index=True)
data = data.fillna(0.0)
data.reset_index(inplace=True)
print("Exporting raw data")
data.to_csv(Path(DATA_PATH, "cps-matched-puf.csv"), index=False)
print("Cleaning data")
data = puf.finalprep(data)
print("Exporting data")
data.to_csv(Path(DATA_PATH, "puf.csv"), index=False)
print("Done!")
