# Recommend not having a space in the name of this file

# coding: utf-8

# This is a non-standard thing to do. Often you see 'df' as the generic name
# for a DataFrame, not as the name for the DataFrame class. The standard thing
# would be 'from pandas import DataFrame'
from pandas import DataFrame as df

import pandas as pd


# Import Census projection on population:
# 
# - [Projection from 2014](http://www.census.gov/population/projections/data/national/2014/downloadablefiles.html)
# - [Historical estimates from 2010 to 2014](http://www.census.gov/popest/data/datasets.html)
# - [Historical estimates from 2000 to 2010](http://www.census.gov/popest/data/intercensal/national/nat2010.html)

#projection 2014+
# Here you would usually see pd.read_csv, but this looks like it works just as well
pop_projection = df.from_csv("NP2014_D1.csv", index_col='year')
pop_projection = pop_projection[(pop_projection.sex == 0) & (pop_projection.race == 0)
                                & (pop_projection.origin == 0)]
pop_projection = pop_projection.drop(['sex', 'race', 'origin'], axis=1)
pop_projection = pop_projection.drop(pop_projection.index[11:], axis=0)
pop_projection = pop_projection.drop(pop_projection.index[:1], axis=0)


#estimates 2010-2014
historical1 = pd.read_csv("NC-EST2014-AGESEX-RES.csv")
historical1 = historical1[historical1.SEX == 0]
# in the following line and throughout, the standard way to pass keyword args is with
# no space between the equal sign, e.g. 'axis=1'. Assignment statements typically
# leave space
historical1 = historical1.drop(['SEX', 'CENSUS2010POP', 'ESTIMATESBASE2010'],axis = 1)

# These ages (19, 65, 999) could be extracted to constants at the top
# of the file. Prevents the 'magic number' phenomenon where you are
# reading code and just come across various magic numbers
pop_dep1 = historical1[historical1.AGE<=19].sum()
# sometimes use see people use the 'inplace=True' flag on drop. Just a heads up
pop_dep1 = pop_dep1.drop(['AGE'],axis = 0)

pop_snr1 = historical1[(historical1.AGE>=65)&(historical1.AGE<999)].sum()
pop_snr1 = pop_snr1.drop(['AGE'], axis = 0)

total_pop1 = historical1[historical1.AGE==999]
total_pop1 = total_pop1.drop(['AGE'], axis = 1)

#estimates 2008-2009
historical2 = pd.read_csv("US-EST00INT-ALLDATA.csv")
historical2 = historical2[(historical2.MONTH==7)&(historical2.YEAR>=2008)&(historical2.YEAR<2010)]
historical2 = historical2.drop(historical2.columns[4:],axis = 1)
historical2 = historical2.drop(historical2.columns[0],axis = 1)

# Here I would recomment splitting these operations over multiple lines using
# the &= operator, so something like
# a = b & c
# a &= d
# a &= e
# instead of a = b & c & d & e
pop_dep2 = [historical2.TOT_POP[(historical2.YEAR ==2008) & (historical2.AGE <=19)].sum(),historical2.TOT_POP[(historical2.YEAR ==2009) & (historical2.AGE <=19)].sum()]
pop_snr2 = [historical2.TOT_POP[(historical2.YEAR ==2008) & (historical2.AGE >=65) & (historical2.AGE < 999)].sum(), historical2.TOT_POP[(historical2.YEAR ==2009) & (historical2.AGE >=65) & (historical2.AGE < 999)].sum()]
total_pop2 = [historical2.TOT_POP[(historical2.YEAR ==2008) & (historical2.AGE == 999)].sum(), historical2.TOT_POP[(historical2.YEAR ==2009) & (historical2.AGE == 999)].sum() ]


#combine the estimates of 08-14 with the projection data
# the 'df' as an indicator that we are making new DataFrames is distracting here
POP_DEP = pd.concat([df(pop_dep2),df(pop_dep1),df(pop_projection[pop_projection.columns[1:21]].sum(axis = 1))])
POP_SNR = pd.concat([df(pop_snr2),df(pop_snr1),df(pop_projection[pop_projection.columns[66:]].sum(axis = 1))])
TOTAL_POP = pd.concat([df(total_pop2), df(total_pop1.values.transpose()),df(pop_projection.total_pop.values)])

#could also do:
# Stage_II_targets = DataFrame(TOTAL_POP, columns=['TOTAL_POP'])
#Stage_II_targets stores all targets later used in Stage II
Stage_II_targets = df(TOTAL_POP)
Stage_II_targets.columns = ['TOTAL_POP']

#add the number of dependent and the number of senior population to Stage II targets
Stage_II_targets['POP_DEP'] = POP_DEP.values
Stage_II_targets['POP_SNR'] = POP_SNR.values

index = list(range(2008,2025))
Stage_II_targets.index = index


#Calculate Stage I factors base on population tarets
APOPN = Stage_II_targets.TOTAL_POP/Stage_II_targets.TOTAL_POP[2008]
Stage_I_factors = df(APOPN, index = index)
Stage_I_factors.columns = ['APOPN']

Stage_I_factors['APOPDEP'] = df(Stage_II_targets.POP_DEP/Stage_II_targets.POP_DEP[2008],index = index)
Stage_I_factors['APOPSNR'] = df(Stage_II_targets.POP_SNR/Stage_II_targets.POP_SNR[2008],index = index)


#yearly growth rates used in Stage I to create Stage I factors
pop_growth_rates = df(Stage_II_targets.TOTAL_POP.pct_change()+1)
pop_growth_rates['POPDEP'] = Stage_II_targets.POP_DEP.pct_change()+1
pop_growth_rates['POPSNR'] = Stage_II_targets.POP_SNR.pct_change()+1
pop_growth_rates = pop_growth_rates.drop(pop_growth_rates.index[0],axis = 0)


# Import CBO baseline

cbo_baseline = (df.from_csv("CBO_baseline.csv", index_col=0)).transpose()
cbo_baseline.index = index

Stage_I_factors['AGDPN'] = df(cbo_baseline.GDP/cbo_baseline.GDP[2008], index = index)
Stage_I_factors['ATXPY'] = df(cbo_baseline.TPY/cbo_baseline.TPY[2008], index = index)
Stage_I_factors['ASCHF'] = df(cbo_baseline.SCHF/cbo_baseline.SCHF[2008], index = index)
Stage_I_factors['ABOOK'] = df(cbo_baseline.BOOK/cbo_baseline.BOOK[2008], index = index)
Stage_I_factors['ACPIU'] = df(cbo_baseline.CPIU/cbo_baseline.CPIU[2008], index = index)
Stage_I_factors['ACPIM'] = df(cbo_baseline.CPIM/cbo_baseline.CPIM[2008], index = index)

cbo_growth_rates = cbo_baseline.pct_change()+1
cbo_growth_rates = cbo_growth_rates.drop(cbo_growth_rates.index[0], axis=0)


# Import IRS number of returns projection

irs_returns = (df.from_csv("IRS_return_projection.csv", index_col=0)).transpose()

return_growth_rate = irs_returns.pct_change()+1
return_growth_rate.Returns['2023'] = return_growth_rate.Returns['2022']
return_growth_rate.Returns['2024'] = return_growth_rate.Returns['2022']
return_growth_rate.Returns.index = index


# Import SOI estimates (2008 - 2012)
# 
# Tax-calculator is using 08 PUF.

soi_estimates = (df.from_csv("SOI_estimates.csv", index_col=0)).transpose()
historical_index = list(range(2008,2013))
soi_estimates.index = historical_index


# Use the yearly growth rates from Census, CBO, and IRS to blow up the 2008 PUF

return_projection = soi_estimates
for i in range(2012,2024):
    Single = return_projection.Single[i]*return_growth_rate.Returns[i+1]
    Joint = return_projection.Joint[i]*return_growth_rate.Returns[i+1]
    HH = return_projection.HH[i]*return_growth_rate.Returns[i+1]
    SS_return = return_projection.SS_return[i]*pop_growth_rates.POPSNR[i+1]
    Dep_return = return_projection.Dep_return[i]*pop_growth_rates.POPDEP[i+1]
    INTS = return_projection.INTS[i]*cbo_growth_rates.INTS[i+1]
    DIVS = return_projection.DIVS[i]*cbo_growth_rates.DIVS[i+1]
    SCHCI = return_projection.SCHCI[i]*cbo_growth_rates.SCHC[i+1]
    SCHCL = return_projection.SCHCL[i]*cbo_growth_rates.SCHC[i+1]
    CGNS = return_projection.CGNS[i]*cbo_growth_rates.CGNS[i+1]
    Pension = return_projection.Pension[i]*cbo_growth_rates.TPY[i+1]
    SCHEI = return_projection.SCHEI[i]*cbo_growth_rates.BOOK[i+1]
    SCHEL = return_projection.SCHEL[i]*cbo_growth_rates.BOOK[i+1]
    SS = return_projection.SS[i]*cbo_growth_rates.SOCSEC[i+1]
    UCOMP = return_projection.UCOMP[i]*cbo_growth_rates.UCOMP[i+1]
    Wage_1 = return_projection.WAGE_1[i]*cbo_growth_rates.Wages[i+1]
    Wage_2 = return_projection.WAGE_2[i]*cbo_growth_rates.Wages[i+1]
    Wage_3 = return_projection.WAGE_3[i]*cbo_growth_rates.Wages[i+1]
    Wage_4 = return_projection.WAGE_4[i]*cbo_growth_rates.Wages[i+1]
    Wage_5 = return_projection.WAGE_5[i]*cbo_growth_rates.Wages[i+1]
    Wage_6 = return_projection.WAGE_6[i]*cbo_growth_rates.Wages[i+1]
    Wage_7 = return_projection.WAGE_7[i]*cbo_growth_rates.Wages[i+1]
    Wage_8 = return_projection.WAGE_8[i]*cbo_growth_rates.Wages[i+1]
    Wage_9 = return_projection.WAGE_9[i]*cbo_growth_rates.Wages[i+1]
    Wage_10 = return_projection.WAGE_10[i]*cbo_growth_rates.Wages[i+1]
    Wage_11 = return_projection.WAGE_11[i]*cbo_growth_rates.Wages[i+1]
    Wage_12 = return_projection.WAGE_12[i]*cbo_growth_rates.Wages[i+1]
    
    current_year = df([Single, Joint, HH,
                       SS_return,Dep_return,INTS,DIVS,SCHCI,SCHCL,
                       CGNS,Pension, SCHEI, SCHEL,SS,UCOMP,Wage_1,
                       Wage_2,Wage_3,Wage_4,Wage_5,Wage_6,Wage_7,
                       Wage_8, Wage_9, Wage_10, Wage_11, Wage_12]).transpose()
    current_year.columns = return_projection.columns
    current_year.index = [i+1]
    return_projection = return_projection.append(current_year)


# Combine the historical data with the newly blow-up data
Stage_II_targets = pd.concat([Stage_II_targets,return_projection], axis = 1)

# Create all the rest Stage I factors
total_return = df(Stage_II_targets[Stage_II_targets.columns[3:6]].sum(axis = 1), columns=['ARETS'])
Stage_I_factors['ARETS'] = total_return/total_return.ARETS[2008]


total_wage = df(Stage_II_targets[Stage_II_targets.columns[18:30]].sum(axis = 1), columns=['AWAGE'])
Stage_I_factors['AWAGE'] = total_wage/total_wage.AWAGE[2008]


Stage_I_factors['ASCHCI'] = Stage_II_targets.SCHCI/Stage_II_targets.SCHCI[2008]
Stage_I_factors['ASCHCL'] = Stage_II_targets.SCHCL/Stage_II_targets.SCHCL[2008]
Stage_I_factors['ASCHEI'] = Stage_II_targets.SCHEI/Stage_II_targets.SCHEI[2008]
Stage_I_factors['ASCHEL'] = Stage_II_targets.SCHEL/Stage_II_targets.SCHEL[2008]


Stage_I_factors['AINTS'] = Stage_II_targets.INTS/Stage_II_targets.INTS[2008]
Stage_I_factors['ADIVS'] = Stage_II_targets.DIVS/Stage_II_targets.DIVS[2008]
Stage_I_factors['ACGNS'] = Stage_II_targets.CGNS/Stage_II_targets.CGNS[2008]

Stage_I_factors['ASOCSEC'] = Stage_II_targets.SS/Stage_II_targets.SS[2008]
Stage_I_factors['AUCOMP'] = Stage_II_targets.UCOMP/Stage_II_targets.UCOMP[2008]


# First copy saved under the current directory is for taxcalc
# Second copy save under Stage II directory is for Stage II linear programming
Stage_I_factors.to_csv(path_or_buf  = "Stage_I_factors.csv", float_format ='%.4f')
Stage_I_factors = Stage_I_factors.transpose()
Stage_I_factors.to_csv(path_or_buf  = "../Stage II/Stage_I_factors.csv", float_format ='%.4f')

# Export Stage II targets for stage II
Stage_II_targets = Stage_II_targets.transpose()
Stage_II_targets.to_csv(path_or_buf = "../Stage II/Stage_II_targets.csv", float_format = '%.4f')

