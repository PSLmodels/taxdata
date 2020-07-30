import pandas as pd
import os

CUR_PATH = os.path.abspath(os.path.dirname(__file__))
SYR = 2011  # calendar year used to normalize factors
BEN_SYR = 2014  # calendar year used just for the benefit start year
EYR = 2030  # last calendar year we have data for
SOI_YR = 2014  # most recently available SOI estimates

# define constants for the number refers total population,
# dependent age upper limit, and senior age lower limit
TOTES = 999
DEP = 19
SENIOR = 65

# Import Census projection on population:
# - Projection from 2014
#   <http://www.census.gov/population/projections/data/national/2014/downloadablefiles.html>
# - Historical estimates from 2010 to 2014
#   <http://www.census.gov/popest/data/datasets.html>
# - Historical estimates from 2000 to 2010
#   <http://www.census.gov/popest/data/intercensal/national/nat2010.html>

# projection for 2014+

pop_projection = pd.read_csv(os.path.join(CUR_PATH, "NP2014_D1.csv"),
                             index_col='year')
pop_projection = pop_projection[(pop_projection.sex == 0) &
                                (pop_projection.race == 0) &
                                (pop_projection.origin == 0)]
pop_projection = pop_projection.drop(['sex', 'race', 'origin'], axis=1)
# We're dropping the rows for years 2014 to EYR from the pop_projection DF
num_drop = EYR + 1 - 2014
pop_projection = pop_projection.drop(pop_projection.index[num_drop:],
                                     axis=0)
pop_projection = pop_projection.drop(pop_projection.index[:1], axis=0)


# data for 2010-2014
historical1 = pd.read_csv(os.path.join(CUR_PATH, "NC-EST2014-AGESEX-RES.csv"))
historical1 = historical1[historical1.SEX == 0]
historical1 = historical1.drop(['SEX', 'CENSUS2010POP', 'ESTIMATESBASE2010'],
                               axis=1)

pop_dep1 = historical1[historical1.AGE <= DEP].sum()
pop_dep1 = pop_dep1.drop(['AGE'], axis=0)

pop_snr1 = historical1[(historical1.AGE >= SENIOR) &
                       (historical1.AGE < TOTES)].sum()
pop_snr1 = pop_snr1.drop(['AGE'], axis=0)

total_pop1 = historical1[historical1.AGE == TOTES]
total_pop1 = total_pop1.drop(['AGE'], axis=1)

# data for 2008-2009
historical2 = pd.read_csv(os.path.join(CUR_PATH, "US-EST00INT-ALLDATA.csv"))
historical2 = historical2[(historical2.MONTH == 7) &
                          (historical2.YEAR >= 2008) &
                          (historical2.YEAR < 2010)]
historical2 = historical2.drop(historical2.columns[4:], axis=1)
historical2 = historical2.drop(historical2.columns[0], axis=1)

year08under19 = (historical2.YEAR == 2008) & (historical2.AGE <= DEP)
year09under19 = (historical2.YEAR == 2009) & (historical2.AGE <= DEP)
pop_dep2 = []
pop_dep2.append(historical2.TOT_POP[year08under19].sum())
pop_dep2.append(historical2.TOT_POP[year09under19].sum())

year08over65 = ((historical2.YEAR == 2008) &
                (historical2.AGE >= SENIOR) &
                (historical2.AGE < TOTES))
year09over65 = ((historical2.YEAR == 2009) &
                (historical2.AGE >= SENIOR) &
                (historical2.AGE < TOTES))
pop_snr2 = []
pop_snr2.append(historical2.TOT_POP[year08over65].sum())
pop_snr2.append(historical2.TOT_POP[year09over65].sum())

year08total = (historical2.YEAR == 2008) & (historical2.AGE == TOTES)
year09total = (historical2.YEAR == 2009) & (historical2.AGE == TOTES)
total_pop2 = []
total_pop2.append(historical2.TOT_POP[year08total].sum())
total_pop2.append(historical2.TOT_POP[year09total].sum())

# combine data for 2008-2014 with projection data
popdf = pd.DataFrame(pop_projection[pop_projection.columns[1:21]].sum(axis=1))
POP_DEP = pd.concat([pd.DataFrame(pop_dep2),
                     pd.DataFrame(pop_dep1),
                     popdf])
popdf = pd.DataFrame(pop_projection[pop_projection.columns[66:]].sum(axis=1))
POP_SNR = pd.concat([pd.DataFrame(pop_snr2),
                     pd.DataFrame(pop_snr1),
                     popdf])
TOTAL_POP = pd.concat([pd.DataFrame(total_pop2),
                       pd.DataFrame(total_pop1.values.transpose()),
                       pd.DataFrame(pop_projection.total_pop.values)])

# create Stage_II_targets to store all targets used in stage2 logic
Stage_II_targets = pd.DataFrame(TOTAL_POP)
Stage_II_targets.columns = ['TOTAL_POP']

# add number of dependents and number of seniors to Stage_II_targets
Stage_II_targets['POP_DEP'] = POP_DEP.values
Stage_II_targets['POP_SNR'] = POP_SNR.values

index = list(range(2008, EYR + 1))
Stage_II_targets.index = index

# calculate Stage_I_factors for population targets
APOPN = Stage_II_targets.TOTAL_POP / Stage_II_targets.TOTAL_POP[SYR]
Stage_I_factors = pd.DataFrame(APOPN, index=index)
Stage_I_factors.columns = ['APOPN']
data = Stage_II_targets.POP_DEP / Stage_II_targets.POP_DEP[SYR]
Stage_I_factors['APOPDEP'] = pd.DataFrame(data, index=index)
data = Stage_II_targets.POP_SNR/Stage_II_targets.POP_SNR[SYR]
Stage_I_factors['APOPSNR'] = pd.DataFrame(data, index=index)

# specify yearly growth rates used in Stage I to create Stage_I_factors
pop_growth_rates = pd.DataFrame(Stage_II_targets.TOTAL_POP.pct_change() + 1.0)
pop_growth_rates['POPDEP'] = Stage_II_targets.POP_DEP.pct_change() + 1.0
pop_growth_rates['POPSNR'] = Stage_II_targets.POP_SNR.pct_change() + 1.0
pop_growth_rates = pop_growth_rates.drop(pop_growth_rates.index[0],
                                         axis=0)

# import CBO baseline projection
cbo_baseline = pd.read_csv(os.path.join(CUR_PATH, "CBO_baseline.csv"),
                           index_col=0)
cbobase = cbo_baseline.transpose()
cbobase.index = index
Stage_I_factors['AGDPN'] = pd.DataFrame(cbobase.GDP/cbobase.GDP[SYR],
                                        index=index)
Stage_I_factors['ATXPY'] = pd.DataFrame(cbobase.TPY/cbobase.TPY[SYR],
                                        index=index)
Stage_I_factors['ASCHF'] = pd.DataFrame(cbobase.SCHF/cbobase.SCHF[SYR],
                                        index=index)
Stage_I_factors['ABOOK'] = pd.DataFrame(cbobase.BOOK/cbobase.BOOK[SYR],
                                        index=index)
Stage_I_factors['ACPIU'] = pd.DataFrame(cbobase.CPIU/cbobase.CPIU[SYR],
                                        index=index)
Stage_I_factors['ACPIM'] = pd.DataFrame(cbobase.CPIM/cbobase.CPIM[SYR],
                                        index=index)
cbo_growth_rates = cbobase.pct_change() + 1.0
cbo_growth_rates = cbo_growth_rates.drop(cbo_growth_rates.index[0], axis=0)

# read  IRS number-of-returns projection
irs_returns = pd.read_csv(os.path.join(CUR_PATH, "IRS_return_projection.csv"),
                          index_col=0)
irs_returns = irs_returns.transpose()
return_growth_rate = irs_returns.pct_change() + 1.0
for year in range(2023, EYR + 1):
    return_growth_rate.Returns[str(year)] = return_growth_rate.Returns['2022']
return_growth_rate.Returns.index = index

# read SOI estimates for 2008+
soi_estimates = pd.read_csv(os.path.join(CUR_PATH, "SOI_estimates_new.csv"),
                            index_col=0)
soi_estimates = soi_estimates.transpose()
historical_index = list(range(2008, SOI_YR + 1))
soi_estimates.index = historical_index

# use yearly growth rates from Census, CBO, and IRS as blowup factors
num_bins = 12

Single = {}
Joint = {}
HH = {}
SS_return = {}
Dep_return = {}
INTS = {}
DIVS = {}
SCHCI = {}
SCHCL = {}
CGNS = {}
Pension = {}
SCHEI = {}
SCHEL = {}
SS = {}
UCOMP = {}
IPD = {}
Wage = {}

return_projection = soi_estimates
for i in range(SOI_YR, EYR):  # SOI Estimates loop
    for j in range(1,num_bins+1):
        Single[str("Single" + str(j))] = return_projection[str("Single" + str(j))][i]*return_growth_rate.Returns[i+1]
        Joint[str("Joint" + str(j))] = return_projection[str("Joint" + str(j))][i]*return_growth_rate.Returns[i+1]
        HH[str("HH" + str(j))] = return_projection[str("HH" + str(j))][i]*return_growth_rate.Returns[i+1]
        SS_return[str("SS_return" + str(j))] = return_projection[str("SS_return" + str(j))][i]*pop_growth_rates.POPSNR[i+1]
        # Dep_return[str("Dep_return" + str(j))] = return_projection[str("Dep_return" + str(j))][i]*pop_growth_rates.POPDEP[i+1]
        INTS[str("INTS" + str(j))] = return_projection[str("INTS" + str(j))][i]*cbo_growth_rates.INTS[i+1]
        DIVS[str("DIVS" + str(j))] = return_projection[str("DIVS" + str(j))][i]*cbo_growth_rates.DIVS[i+1]
        SCHCI[str("SCHCI" + str(j))] = return_projection[str("SCHCI" + str(j))][i]*cbo_growth_rates.SCHC[i+1]
        SCHCL[str("SCHCL" + str(j))] = return_projection[str("SCHCL" + str(j))][i]*cbo_growth_rates.SCHC[i+1]
        CGNS[str("CGNS" + str(j))] = return_projection[str("CGNS" + str(j))][i]*cbo_growth_rates.CGNS[i+1]
        Pension[str("Pension" + str(j))] = return_projection[str("Pension" + str(j))][i]*cbo_growth_rates.TPY[i+1]
        SCHEI[str("SCHEI" + str(j))] = return_projection[str("SCHEI" + str(j))][i]*cbo_growth_rates.BOOK[i+1]
        SCHEL[str("SCHEL" + str(j))] = return_projection[str("SCHEL" + str(j))][i]*cbo_growth_rates.BOOK[i+1]
        SS[str("SS" + str(j))] = return_projection[str("SS" + str(j))][i]*cbo_growth_rates.SOCSEC[i+1]
        UCOMP[str("UCOMP" + str(j))] = return_projection[str("UCOMP" + str(j))][i]*cbo_growth_rates.UCOMP[i+1]
        # IPD[str("IPD" + str(j))] = return_projection[str("IPD" + str(j))][i]*cbo_growth_rates.TPY[i+1]
        Wage[str("Wage" + str(j))] = return_projection[str("Wage" + str(j))][i]*cbo_growth_rates.Wages[i+1]


    var_dict = {**Single, **Joint, **HH, **SS_return, **Dep_return, **INTS, **DIVS, **SCHCI, **SCHCL,
                **CGNS, **Pension, **SCHEI, **SCHEL, **SS, **UCOMP, **IPD, **Wage}


    current_year = pd.DataFrame([var_dict])

    current_year.index = [i+1]
    return_projection = return_projection.append(current_year)

# combine historical data with the newly blownup data
Stage_II_targets = pd.concat([Stage_II_targets, return_projection], axis=1)

# Create dataframe of aggregate values
cols = ['Single', 'Joint', 'HH', 'SS_return', 'Dep_return', 'INTS', 'DIVS', 'SCHCI', 'SCHCL', 'CGNS', 'Pension',
        'SCHEI', 'SCHEL', 'SS', 'UCOMP', 'IPD', 'Wage']
col_dict = {}

for col in cols:
    s = return_projection[['Single' + str(i) for i in range(1,num_bins+1)]].sum(axis=1)
    col_dict[col] = s

Aggregates = pd.DataFrame(data=col_dict)

# create all the rest of the Stage_I_factors
data = Aggregates[Aggregates.columns[3:6]].sum(axis=1)
total_return = pd.DataFrame(data, columns=['ARETS']) # Returns: Single, Joint, HH

data = Aggregates[Aggregates.columns[19:31]].sum(axis=1)
total_wage = pd.DataFrame(data, columns=['AWAGE']) # Wages

Stage_I_factors['ARETS'] = total_return/total_return.ARETS[SYR]

Stage_I_factors['AWAGE'] = total_wage/total_wage.AWAGE[SYR]

Stage_I_factors['ASCHCI'] = Aggregates.SCHCI/Aggregates.SCHCI[SYR]
Stage_I_factors['ASCHCL'] = Aggregates.SCHCL/Aggregates.SCHCL[SYR]

Stage_I_factors['ASCHEI'] = Aggregates.SCHEI/Aggregates.SCHEI[SYR]
Stage_I_factors['ASCHEL'] = Aggregates.SCHEL/Aggregates.SCHEL[SYR]

Stage_I_factors['AINTS'] = Aggregates.INTS/Aggregates.INTS[SYR]
Stage_I_factors['ADIVS'] = Aggregates.DIVS/Aggregates.DIVS[SYR]
Stage_I_factors['ACGNS'] = Aggregates.CGNS/Aggregates.CGNS[SYR]

Stage_I_factors['ASOCSEC'] = Aggregates.SS/Aggregates.SS[SYR]
Stage_I_factors['AUCOMP'] = Aggregates.UCOMP/Aggregates.UCOMP[SYR]
Stage_I_factors['AIPD'] = Aggregates.IPD/Aggregates.IPD[SYR]

# Add benefit growth rates to Stage 1 factors
benefit_programs = pd.read_csv(os.path.join(CUR_PATH,
                               '../cps_data/benefitprograms.csv'),
                               index_col='Program')
benefit_sums = benefit_programs[benefit_programs.columns[2:]].sum()

# Find growth rate between 2020 and 2021 and extrapolate out to EYR
gr = benefit_sums['2021_cost'] / float(benefit_sums['2020_cost'])
for year in range(2022, EYR + 1):
    prev_year = year - 1
    prev_value = benefit_sums['{}_cost'.format(prev_year)]
    benefit_sums['{}_cost'.format(year)] = prev_value * gr
ABENEFITS = (benefit_sums /
             benefit_sums['{}_cost'.format(BEN_SYR)]).transpose()
benefit_factors = pd.DataFrame()
for year in range(SYR, EYR + 1):
    if year <= BEN_SYR:
        benefit_factors[year] = [1.0]
    else:
        benefit_factors[year] = ABENEFITS['{}_cost'.format(year)]

# Stage_II_targets = Stage_II_targets.drop(['IPD' + str(i) for i in range(1,num_bins+1)], axis=1)
# rename Stage_II_targets index
rename = {'TOTAL_POP': 'US Population'}

descriptions = {
    'Single': 'Single Returns',
    'Joint': 'Joint Returns',
    'HH': 'Head of Household Returns',
    'SS_return': 'Number of Returns w/ Gross Security Income',
    'Dep_return': 'Number of Dependent Exemptions',
    'INTS': 'Taxable Interest Income',
    'DIVS': 'Ordinary Dividends',
    'SCHCI': 'Business Income (Schedule C)',
    'SCHCL': 'Business Loss (Schedule C)',
    'CGNS': 'Net Capital Gains in AGI',
    'Pension': 'Taxable Pensions and Annuities',
    'SCHEI': 'Supplemental Income (Schedule E)',
    'SCHEL': 'Supplemental Loss (Schedule E)',
    'SS': 'Gross Social Security Income',
    'UCOMP': 'Unemployment Compensation',
    'Wage': 'Wages and Salaries'
    }

bins = {1: 'Zero or Less',
        2: '$1 Less Than $10,000',
        3: '$10,000 Less Than $20,000',
        4: '$20,000 Less Than $30,000',
        5: '$30,000 Less Than $40,000',
        6: '$40,000 Less Than $50,000',
        7: '$50,000 Less Than $75,000',
        8: '$75,000 Less Than $100,000',
        9: '$100,000 Less Than $200,000',
        10: '$200,000 Less Than $500,000',
        11: '$500,000 Less Than $1 Million',
        12: '$1 Million and Over'
        }

cols.remove('IPD')
for c in cols:
    for r in range(1,num_bins+1):
        rename[c + str(r)] = descriptions[c] + ": " + bins[r]

Stage_II_targets.rename(columns=rename, inplace=True)



# Delete 2008-2010 rows from Stage_I_factors and Stage_II_factors
Stage_I_factors = Stage_I_factors.drop([2008, 2009, 2010])
Stage_II_targets = Stage_II_targets.drop([2008, 2009, 2010])

# add on benefit factors
Stage_I_factors['ABENEFITS'] = benefit_factors.transpose()[0]

# write Stage_I_factors for final preparation and then use by Tax-Calculator
Stage_I_factors.to_csv(os.path.join(CUR_PATH, 'Stage_I_factors.csv'),
                       float_format='%.4f',
                       index_label='YEAR')

# write Stage_II_targets for use in stage2 weights calculation
Stage_II_targets = Stage_II_targets.transpose()
Stage_II_targets.to_csv(os.path.join(CUR_PATH, 'Stage_II_targets.csv'),
                        float_format='%.0f')
