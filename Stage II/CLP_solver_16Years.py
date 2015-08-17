
# coding: utf-8

import numpy as np
import pandas as pd
# see comments on 'df' from Stage I
from pandas import DataFrame as df
from cylp.cy import CyClpSimplex
from cylp.py.modeling.CyLPModel import CyLPArray, CyLPModel
from Single_Year_Stage_II import Single_Year_Stage_II


# Import PUF, and results from Stage I

#probably want to just say 'puf.csv' or something user must configure
puf = pd.read_csv("/Users/Amy/Documents/puf.csv")
Stage_I_factors = df.from_csv("Stage_I_factors.csv", index_col = 0)
Stage_II_targets = df.from_csv("Stage_II_targets.csv", index_col= 0)


# all the final weights would be saved in z
length = len(puf.s006)
z = np.empty([length, 17])
z[:,0] = puf.s006/100


# running LP solver for each year, with tolerance given in the tol argument
z[:,1] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2009', tol = 0.24)

z[:,2] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2010', tol = 0.24)

z[:,3] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2011', tol = 0.18)

z[:,4] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2012', tol = 0.22)

z[:,5] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2013', tol = 0.27)

z[:,6] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2014', tol = 0.2)

z[:,7] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2015', tol = 0.24)

z[:,8] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2016', tol = 0.25)

z[:,9] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2017', tol = 0.28)

z[:,10] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2018', tol = 0.3)

z[:,11] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2019', tol = 0.4)

z[:,12] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2020', tol = 0.4)

z[:,13] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2021', tol = 0.35)

z[:,14] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2022', tol = 0.25)

z[:,15] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2023', tol = 0.23)

z[:,16] = Single_Year_Stage_II(puf, Stage_I_factors, Stage_II_targets, year = '2024', tol = 0.33)


# export the final weights
z = df(z, columns=['WT2008','WT2009','WT2010','WT2011','WT2012','WT2013','WT2014',
                   'WT2015','WT2016','WT2017','WT2018','WT2019','WT2020','WT2021',
                   'WT2022','WT2023','WT2024'])
z.to_csv('WEIGHTS.csv', index = False)




