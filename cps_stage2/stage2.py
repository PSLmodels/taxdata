import pandas as pd
from pathlib import Path
from solve_lp_for_year import solve_lp_for_year

CUR_PATH = Path(__file__).resolve().parent
STAGE_1_PATH = Path(CUR_PATH, "..", "puf_stage1", "Stage_I_factors.csv")
STAGE_2_PATH = Path(CUR_PATH, "..", "cps_stage1", "stage_2_targets.csv")
START_YEAR = 2014
END_YEAR = 2030


def main():
    """
    """
    print("Reading Data")
    cps = pd.read_csv(
        Path(CUR_PATH, "..", "cps_data", "pycps", "cps_raw.csv.gz"),
        compression="gzip"
    )
    cps = cps.fillna(0.)
    stage_1_factors = pd.read_csv(
        STAGE_1_PATH, index_col=0
    )
    stage_2_targets = pd.read_csv(
        STAGE_2_PATH, index_col=0
    )
    # DataFrame for holding each year's weights
    weights = pd.DataFrame()
    for year in range(START_YEAR, END_YEAR + 1):
        print(f"Solving for {year}")
        weights[f"WT{year}"] = solve_lp_for_year(
            cps, stage_1_factors, stage_2_targets, year, .70
        )

    weights = weights.round(0).astype("int64")
    weights.to_csv(
        Path(CUR_PATH, "cps_weights.csv.gz"), compression="gzip", index=False
    )


if __name__ == '__main__':
    main()
