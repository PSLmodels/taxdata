import pandas as pd
import numpy as np

# Read in factors, PUF file, targets
puf = pd.read_csv('cps-puf.csv')
targets = pd.read_csv('Stage III Targets.csv', index_col=0)
wght = pd.read_csv('WEIGHTS.csv')
stage_I_factors = pd.read_csv('StageIFactors_current.csv', index_col=0)

# Recreate AINTS variable to match BF.AINTS in TaxCalc
AINTS = stage_I_factors.AINTS / stage_I_factors.APOPN
AINTS = 1.0 + AINTS.pct_change()
AINTS[2009] = 1.0357

# Create DataFrames to hold the distribution of each targeted variable
distribution_INTS = pd.DataFrame()
# For each year available find the distribution from SOI data
for year in range(2009, 2015):
    distribution_INTS[year] = targets[str(year)] / targets[str(year)].sum()
# Use 2014 distribution for all subsequent years
for year in range(2015, 2027):
    distribution_INTS[year] = distribution_INTS[2014]
factorsDf = pd.DataFrame()
for year in range(2009, 2027):
    puf.e00300 *= AINTS[year]
    wt_year = 'WT' + str(year)
    interest = (puf.e00300[puf.e00100 >= 1] *
                wght[wt_year][puf.e00100 >= 1]).sum()
    goal_dist = pd.Series(interest * distribution_INTS[year])
    ints_0 = np.where(puf.e00100 <= 0,
                      puf.e00300 * wght[wt_year], 0).sum()
    ints_1 = np.where((puf.e00100 >= 1) & (puf.e00100 < 25000),
                      puf.e00300 * wght[wt_year], 0).sum()
    ints_2 = np.where((puf.e00100 >= 25000) & (puf.e00100 < 100000),
                      puf.e00300 * wght[wt_year], 0).sum()
    ints_3 = np.where((puf.e00100 >= 100000) & (puf.e00100 < 1e6),
                      puf.e00300 * wght[wt_year], 0).sum()
    ints_4 = np.where((puf.e00100 >= 1e6) & (puf.e00100 < 1e7),
                      puf.e00300 * wght[wt_year], 0).sum()
    ints_5 = np.where((puf.e00100 >= 1e7),
                      puf.e00300 * wght[wt_year], 0).sum()
    actual_dist = pd.Series([ints_0, ints_1, ints_2, ints_3, ints_4, ints_5],
                            index=goal_dist.index)
    factors = goal_dist / actual_dist
    adj = np.where(puf.e00100 <= 0,
                   factors['INT_0'],
                   np.where(((puf.e00100 >= 1) & (puf.e00100 < 25000)),
                            factors['INT_1'],
                            np.where(((puf.e00100 >= 25000) & (puf.e00100 < 100000)),
                                     factors['INT_2'],
                                     np.where(((puf.e00100 >= 100000) & (puf.e00100 < 1e6)),
                                              factors['INT_3'],
                                              np.where(((puf.e00100 >= 1e6) & (puf.e00100 < 1e7)),
                                                       factors['INT_4'],
                                                       factors['INT_5'])))))

    factorsDf['INT' + str(year)] = adj

factorsDf.to_csv('adjustmentFactors.csv', index=False)
