import os
import glob
import numpy as np
import pandas as pd
from pathlib import Path
from dataprep import dataprep

CUR_PATH = Path(__file__).resolve().parent
STAGE_1_PATH = Path(CUR_PATH, "..", "puf_stage1", "Stage_I_factors.csv")
STAGE_2_PATH = Path(CUR_PATH, "..", "cps_stage1", "stage_2_targets.csv")
START_YEAR = 2014
END_YEAR = 2031


def main():
    """
    """
    print("Reading Data")
    cps = pd.read_csv(
        Path(CUR_PATH, "..", "data", "cps_raw.csv.gz"), compression="gzip"
    )
    cps = cps.fillna(0.0)
    stage_1_factors = pd.read_csv(STAGE_1_PATH, index_col=0)
    stage_2_targets = pd.read_csv(STAGE_2_PATH, index_col=0)
    # DataFrame for holding each year's weights
    weights = pd.DataFrame()

    # write .npz input files for solver
    for year in range(START_YEAR, END_YEAR + 1):
        dataprep(cps, stage_1_factors, stage_2_targets, year)

    # Solver (in Julia)
    env_path = os.path.join(CUR_PATH, "../Project.toml")
    os.system(f"julia --project={env_path} solver.jl")

    # write output files to dataframe columns
    for year in range(START_YEAR, END_YEAR + 1):

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
