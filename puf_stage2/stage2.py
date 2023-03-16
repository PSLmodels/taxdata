import os
import glob
import json
import hashlib
import numpy as np
import pandas as pd
from pathlib import Path
from dataprep import dataprep


CUR_PATH = Path(__file__).resolve().parent

# Read hashes used to see which years can be skipped
with open(Path(CUR_PATH, "..", "datahashes.json")) as f:
    HASHES = json.load(f)["puf"]

# compare hashes of all files used in stage 2 to ensure they didn't change
file_paths = [
    Path(CUR_PATH, "..", "data", "cps-matched-puf.csv"),
    Path(CUR_PATH, "solver.jl"),
    Path(CUR_PATH, "dataprep.py"),
    Path(CUR_PATH, "stage2.py"),
]
key_names = ["data", "solver", "dataprep", "stage2"]
files_match = True
for key, file_path in zip(key_names, file_paths):
    with open(file_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    files_match = HASHES[key] == file_hash
    if not files_match:
        print(f"{key} has changed")
        break

# Read current factors and targets
CUR_FACTORS = pd.read_csv(
    "https://raw.githubusercontent.com/PSLmodels/taxdata/master/puf_stage1/Stage_I_factors.csv",
    index_col=0,
).transpose()
CUR_TARGETS = pd.read_csv(
    "https://raw.githubusercontent.com/PSLmodels/taxdata/master/puf_stage1/Stage_II_targets.csv",
    index_col=0,
)
CUR_WEIGHTS = pd.read_csv(Path(CUR_PATH, "puf_weights.csv.gz"))
# Read private CPS-matched-PUF file into a Pandas DataFrame
puf = pd.read_csv(Path(CUR_PATH, "..", "data", "cps-matched-puf.csv"))

# Read stage1 factors and stage2 targets written by stage1.py script
factors = pd.read_csv(
    Path(CUR_PATH, "..", "puf_stage1", "Stage_I_factors.csv"), index_col=0
)
Stage_I_factors = factors.transpose()
stage2_path = Path(CUR_PATH, "..", "puf_stage1", "Stage_II_targets.csv")
Stage_II_targets = pd.read_csv(stage2_path, index_col=0)

# Use the matched_weight variable in CPS as the final weight
puf.s006 = puf.matched_weight * 100

# Dataprep
year_list = [x for x in range(2012, 2033 + 1)]
skipped_years = []
for i in year_list:
    try:
        factor_match = Stage_I_factors[i].equals(CUR_FACTORS[i])
        target_match = Stage_II_targets[f"{i}"].equals(CUR_TARGETS[f"{i}"])
        if files_match and factor_match and target_match:
            print(f"Skipping {i}")
            skipped_years.append(i)
            continue
    except KeyError:
        pass
    dataprep(puf, Stage_I_factors, Stage_II_targets, year=i)

# Solver (in Julia)
env_path = os.path.join(CUR_PATH, "../Project.toml")
os.system(f"julia --project={env_path} solver.jl")


# Initialize weights dataframe
z = pd.DataFrame()
z["WT2011"] = puf.s006

# write solution to dataframe
for i in year_list:
    if i in skipped_years:
        z[f"WT{i}"] = CUR_WEIGHTS[f"WT{i}"]
        continue
    s006 = np.where(
        puf.e02400 > 0,
        puf.s006 * Stage_I_factors[i]["APOPSNR"] / 100,
        puf.s006 * Stage_I_factors[i]["ARETS"] / 100,
    )

    array = np.load(str(str(i) + "_output.npz"))
    r_val = array["r"]
    s_val = array["s"]

    z_val = (1.0 + r_val - s_val) * s006 * 100
    z[str("WT" + str(i))] = z_val

# Write all weights (rounded to nearest integer) to puf_weights.csv file
z = z.round(0).astype("int64")
z.to_csv(os.path.join(CUR_PATH, "puf_weights.csv.gz"), index=False, compression="gzip")

# remove all .npz (numpy array) files
for file in glob.glob("*.npz"):
    os.remove(file)
