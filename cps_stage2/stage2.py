import os
import glob
import json
import hashlib
import numpy as np
import pandas as pd
from pathlib import Path
from dataprep import dataprep

CUR_PATH = Path(__file__).resolve().parent
STAGE_1_PATH = Path(CUR_PATH, "..", "puf_stage1", "Stage_I_factors.csv")
STAGE_2_PATH = Path(CUR_PATH, "..", "cps_stage1", "stage_2_targets.csv")
START_YEAR = 2014
END_YEAR = 2033

# Read hashes used to see which years can be skipped
with open(Path(CUR_PATH, "..", "datahashes.json")) as f:
    HASHES = json.load(f)["cps"]

# compare hashes of all files used in stage 2 to ensure they didn't change
file_paths = [
    Path(CUR_PATH, "..", "data", "cps.csv.gz"),
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
        break

# Read current factors and targets
CUR_FACTORS = pd.read_csv(
    "https://raw.githubusercontent.com/PSLmodels/taxdata/master/puf_stage1/Stage_I_factors.csv",
    index_col=0,
).transpose()
CUR_TARGETS = pd.read_csv(
    "https://raw.githubusercontent.com/PSLmodels/taxdata/master/cps_stage1/stage_2_targets.csv",
    index_col=0,
)
CUR_WEIGHTS = pd.read_csv(Path(CUR_PATH, "cps_weights.csv.gz"))


def main():
    """ """
    print("Reading Data")
    cps = pd.read_csv(
        Path(CUR_PATH, "..", "data", "cps_raw.csv.gz"), compression="gzip"
    )
    cps = cps.fillna(0.0)
    stage_1_factors = pd.read_csv(STAGE_1_PATH, index_col=0)
    _factors = stage_1_factors.transpose()
    stage_2_targets = pd.read_csv(STAGE_2_PATH, index_col=0)
    # DataFrame for holding each year's weights
    weights = pd.DataFrame()

    # write .npz input files for solver
    skipped_years = []
    for year in range(START_YEAR, END_YEAR + 1):
        try:
            factor_match = _factors[year].equals(CUR_FACTORS[year])
            target_match = stage_2_targets[f"{year}"].equals(CUR_TARGETS[f"{year}"])
            if files_match and factor_match and target_match:
                print(f"Skipping {year}")
                skipped_years.append(year)
                continue
        except KeyError:
            pass
        dataprep(cps, stage_1_factors, stage_2_targets, year)

    # Solver (in Julia)
    env_path = os.path.join(CUR_PATH, "../Project.toml")
    os.system(f"julia --project={env_path} solver.jl")

    # write output files to dataframe columns
    for year in range(START_YEAR, END_YEAR + 1):
        if year in skipped_years:
            weights[f"WT{year}"] = CUR_WEIGHTS[f"WT{year}"]
            continue
        s006 = np.where(
            cps.e02400 > 0,
            cps.s006 * stage_1_factors["APOPSNR"][year],
            cps.s006 * stage_1_factors["ARETS"][year],
        )

        array = np.load(str(str(year) + "_output.npz"))
        r_val = array["r"]
        s_val = array["s"]

        z_val = (1 + r_val - s_val) * s006 * 100
        weights[str("WT" + str(year))] = z_val

    weights = weights.round(0).astype("int64")
    weights.to_csv(
        Path(CUR_PATH, "cps_weights.csv.gz"), compression="gzip", index=False
    )

    # remove all .npz (numpy array) files
    for file in glob.glob("*.npz"):
        os.remove(file)


if __name__ == "__main__":
    main()
