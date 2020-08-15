import os, glob, time
import numpy as np
import pandas as pd
from dataprep import dataprep


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




# Dataprep
year_list = [x for x in range(2012, 2030+1)]
for i in year_list:
    dataprep(puf, Stage_I_factors, Stage_II_targets,
             year=i)

# Solver (in Julia)
os.system('julia solver.jl')




# Initialize weights dataframe
z = pd.DataFrame()
z["WT2011"] = puf.s006

# write solution to dataframe
for i in year_list:
    s006 = np.where(puf.e02400 > 0,
                puf.s006 * Stage_I_factors[i]["APOPSNR"] / 100,
                puf.s006 * Stage_I_factors[i]["ARETS"] / 100)

    array = np.load(str(str(i) + "_output.npz"))
    r_val = array['r']
    s_val = array['s']

    z_val = (1. + r_val - s_val) * s006 * 100
    z[str("WT" + str(i))] = z_val

# Write all weights (rounded to nearest integer) to puf_weights.csv file
z = z.round(0).astype('int64')
z.to_csv(os.path.join(CUR_PATH, 'puf_weights.csv.gz'),
         index=False, compression='gzip')

# remove all .npz (numpy array) files
for file in glob.glob("*.npz"):
  os.remove(file)

