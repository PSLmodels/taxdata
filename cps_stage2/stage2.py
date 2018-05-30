import pandas as pd
import numpy as np
import time
from solve_lp_for_year import solve_lp_for_year


def main():
    """
    """
    start_time = time.time()
    print('Reading Data')
    cps = pd.read_csv('../cps_data/cps_raw.csv.gz', compression='gzip')
    cps = cps.fillna(0.)
    cps['MARS'] = np.where(cps.JS == 3, 4, cps.JS)
    cps['e00100'] = cps['JCPS9'] + cps['JCPS19']
    stage_1_factors = pd.read_csv('../puf_stage1/Stage_I_factors.csv',
                                  index_col=0)
    stage_2_targets = pd.read_csv('../cps_stage1/stage_2_targets.csv',
                                  index_col=0)

    # DataFrame for holding each year's weights
    weights = pd.DataFrame()
    weights['WT2014'] = cps.WT * 100
    weights['WT2015'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2015, .50)
    weights['WT2016'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2016, .50)
    weights['WT2017'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2017, .50)
    weights['WT2018'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2018, .50)
    weights['WT2019'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2019, .50)
    weights['WT2020'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2020, .50)
    weights['WT2021'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2021, .50)
    weights['WT2022'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2022, .50)
    weights['WT2023'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2023, .50)
    weights['WT2024'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2024, .50)
    weights['WT2025'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2025, .50)
    weights['WT2026'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2026, .50)
    weights['WT2027'] = solve_lp_for_year(cps, stage_1_factors,
                                          stage_2_targets, 2027, .50)

    weights = weights.round(0).astype('int64')
    weights.to_csv('cps_weights.csv.gz', compression='gzip', index=False)
    end_time = time.time()
    print('Total time (minutes):', (end_time - start_time) / 60)


if __name__ == '__main__':
    main()
