import pandas as pd
from pathlib import Path
from pysolve_lp_for_year import solve_lp_for_year

CUR_PATH = Path(__file__).resolve().parent
STAGE_1_PATH = Path(CUR_PATH, "..", "puf_stage1", "Stage_I_factors.csv")
STAGE_2_PATH = Path(CUR_PATH, "..", "cps_stage1", "stage_2_targets.csv")


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
    print("Solving for 2014")
    weights['WT2014'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2014, .60)
    print("Solving for 2015")
    weights['WT2015'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2015, .60)
    print("Solving for 2016")
    weights['WT2016'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2016, .60)
    print("Solving for 2017")
    weights['WT2017'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2017, .60)
    print("Solving for 2018")
    weights['WT2018'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2018, .60)
    print("Solving for 2019")
    weights['WT2019'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2019, .60)
    print("Solving for 2020")
    weights['WT2020'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2020, .60)
    print("Solving for 2021")
    weights['WT2021'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2021, .60)
    print("Solving for 2022")
    weights['WT2022'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2022, .60)
    print("Solving for 2023")
    weights['WT2023'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2023, .60)
    print("Solving for 2024")
    weights['WT2024'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2024, .60)
    print("Solving for 2025")
    weights['WT2025'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2025, .60)
    print("Solving for 2026")
    weights['WT2026'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2026, .60)
    print("Solving for 2027")
    weights['WT2027'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2027, .60)
    print("Solving for 2028")
    weights['WT2028'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2028, .60)
    print("Solving for 2029")
    weights['WT2029'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2029, .60)

    weights = weights.round(0).astype("int64")
    weights.to_csv(
        Path(CUR_PATH, "cps_weights.csv.gz"), compression="gzip", index=False
    )


if __name__ == '__main__':
    main()
