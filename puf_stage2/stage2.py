import os
import numpy as np
import pandas as pd
from solve_lp_for_year import solve_lp_for_year

CUR_PATH = os.path.abspath(os.path.dirname(__file__))
# Read private CPS-matched-PUF file into a Pandas DataFrame
puf = pd.read_csv(os.path.join(CUR_PATH, "../puf_data/cps-matched-puf.csv"))

# Read stage1 factors and stage2 targets written by stage1.py script
factors = pd.read_csv(os.path.join(CUR_PATH,
                                   "../puf_stage1/Stage_I_factors.csv"),
                      index_col=0)
Stage_I_factors = factors.transpose()
stage2_path = os.path.join(CUR_PATH, "../puf_stage1/Stage_II_targets.csv")
Stage_II_targets = pd.read_csv(stage2_path, index_col=0)

# Use the matched_weight variable in CPS as the final weight
puf.s006 = puf.matched_weight * 100


z = pd.DataFrame()
z["WT2011"] = puf.s006


# Execute stage2 logic for each year using a year-specific LP tolerance
z["WT2012"] = solve_lp_for_year(puf, Stage_I_factors, Stage_II_targets,
                                year=2012, tol=0.40)
z['WT2013'] = solve_lp_for_year(puf, Stage_I_factors, Stage_II_targets,
                                year=2013, tol=0.38)
z['WT2014'] = solve_lp_for_year(puf, Stage_I_factors, Stage_II_targets,
                                year=2014, tol=0.35)
z["WT2015"] = solve_lp_for_year(puf, Stage_I_factors, Stage_II_targets,
                                year=2015, tol=0.33)
z["WT2016"] = solve_lp_for_year(puf, Stage_I_factors, Stage_II_targets,
                                year=2016, tol=0.30)
z["WT2017"] = solve_lp_for_year(puf, Stage_I_factors, Stage_II_targets,
                                year=2017, tol=0.37)
z["WT2018"] = solve_lp_for_year(puf, Stage_I_factors, Stage_II_targets,
                                year=2018, tol=0.38)
z["WT2019"] = solve_lp_for_year(puf, Stage_I_factors, Stage_II_targets,
                                year=2019, tol=0.38)
z["WT2020"] = solve_lp_for_year(puf, Stage_I_factors, Stage_II_targets,
                                year=2020, tol=0.39)
z["WT2021"] = solve_lp_for_year(puf, Stage_I_factors, Stage_II_targets,
                                year=2021, tol=0.39)
z["WT2022"] = solve_lp_for_year(puf, Stage_I_factors, Stage_II_targets,
                                year=2022, tol=0.38)
z["WT2023"] = solve_lp_for_year(puf, Stage_I_factors, Stage_II_targets,
                                year=2023, tol=0.40)
z["WT2024"] = solve_lp_for_year(puf, Stage_I_factors, Stage_II_targets,
                                year=2024, tol=0.39)
z["WT2025"] = solve_lp_for_year(puf, Stage_I_factors, Stage_II_targets,
                                year=2025, tol=0.41)
z["WT2026"] = solve_lp_for_year(puf, Stage_I_factors, Stage_II_targets,
                                year=2026, tol=0.41)
z["WT2027"] = solve_lp_for_year(puf, Stage_I_factors, Stage_II_targets,
                                year=2027, tol=0.42)
z["WT2028"] = solve_lp_for_year(puf, Stage_I_factors, Stage_II_targets,
                                year=2028, tol=0.42)

# Write all weights (rounded to nearest integer) to puf_weights.csv file
z = z.round(0).astype('int64')
z.to_csv(os.path.join(CUR_PATH, 'puf_weights.csv'),
         index=False, compression='gzip')
