import numpy as np
import pandas as pd
from pandas import DataFrame as df
from cylp.cy import CyClpSimplex
from cylp.py.modeling.CyLPModel import CyLPArray, CyLPModel
from Single_Year_Stage_II import Single_Year_Stage_II

# import CPS-matched file
puf = pd.read_csv("cps-puf.csv")
Stage_I_factors = df.from_csv("Stage_I_factors.csv", index_col = 0)
Stage_II_targets = df.from_csv("Stage_II_targets.csv", index_col= 0)

# Use the matched_weight variable in CPS as the final weight
puf.matched_weight = np.where(puf.filer==1, puf.s006/100, puf.matched_weight/100)
puf.s006 = puf.matched_weight * 100

length = len(puf.s006)
z = np.empty([length, 18])
z[:,0] = puf.s006

# Start running stage II year by year
z[:,1] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2010', tol = 0.25)
z[:,2] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2011', tol = 0.25)
z[:,3] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2012', tol = 0.5)
z[:,4] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2013', tol = 0.45)
z[:,5] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2014', tol = 0.49)
z[:,6] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2015', tol = 0.45)
z[:,7] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2016', tol = 0.44)
z[:,8] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2017', tol = 0.43)
z[:,9] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2018', tol = 0.44)
z[:,10] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2019', tol = 0.47)
z[:,11] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2020', tol = 0.43)
z[:,12] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2021', tol = 0.44)
z[:,13] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2022', tol = 0.47)
z[:,14] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2023', tol = 0.45)
z[:,15] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2024', tol = 0.45)
z[:,16] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year='2025', tol=.45)
z[:,17] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year='2026', tol=.45)


# Export all weights
z = df(z, columns=['WT2009','WT2010','WT2011','WT2012','WT2013','WT2014',
                   'WT2015','WT2016','WT2017','WT2018','WT2019','WT2020',
                   'WT2021','WT2022','WT2023','WT2024', 'WT2025', 'WT2026'])
z.to_csv('WEIGHTS.csv', index = False)
# Second copy saved in Stage III directory
z.to_csv(path_or_buf='../Stage III/WEIGHTS/csv', index=False)
