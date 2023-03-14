import pandas as pd
import os

CUR_PATH = os.path.abspath(os.path.dirname(__file__))
SYR = 2011  # calendar year used to normalize factors
BEN_SYR = 2014  # calendar year used just for the benefit start year
EYR = 2033  # last calendar year we have data for
SOI_YR = 2017  # most recently available SOI estimates
IRS_RET_YR = 2022  # most recently available IRS return projections

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
pop_projection = pd.read_csv(os.path.join(CUR_PATH, "NP2014_D1.csv"), index_col="year")
pop_projection = pop_projection[
    (pop_projection.sex == 0)
    & (pop_projection.race == 0)
    & (pop_projection.origin == 0)
]
pop_projection = pop_projection.drop(["sex", "race", "origin"], axis=1)
# We're dropping the rows for years 2014 to EYR from the pop_projection DF
num_drop = EYR + 1 - 2014
pop_projection = pop_projection.drop(pop_projection.index[num_drop:], axis=0)
pop_projection = pop_projection.drop(pop_projection.index[:1], axis=0)


# data for 2010-2014
historical1 = pd.read_csv(os.path.join(CUR_PATH, "NC-EST2014-AGESEX-RES.csv"))
historical1 = historical1[historical1.SEX == 0]
historical1 = historical1.drop(["SEX", "CENSUS2010POP", "ESTIMATESBASE2010"], axis=1)

pop_dep1 = historical1[historical1.AGE <= DEP].sum()
pop_dep1 = pop_dep1.drop(["AGE"], axis=0)

pop_snr1 = historical1[(historical1.AGE >= SENIOR) & (historical1.AGE < TOTES)].sum()
pop_snr1 = pop_snr1.drop(["AGE"], axis=0)

total_pop1 = historical1[historical1.AGE == TOTES]
total_pop1 = total_pop1.drop(["AGE"], axis=1)

# data for 2008-2009
historical2 = pd.read_csv(os.path.join(CUR_PATH, "US-EST00INT-ALLDATA.csv"))
historical2 = historical2[
    (historical2.MONTH == 7) & (historical2.YEAR >= 2008) & (historical2.YEAR < 2010)
]
historical2 = historical2.drop(historical2.columns[4:], axis=1)
historical2 = historical2.drop(historical2.columns[0], axis=1)

year08under19 = (historical2.YEAR == 2008) & (historical2.AGE <= DEP)
year09under19 = (historical2.YEAR == 2009) & (historical2.AGE <= DEP)
pop_dep2 = []
pop_dep2.append(historical2.TOT_POP[year08under19].sum())
pop_dep2.append(historical2.TOT_POP[year09under19].sum())

year08over65 = (
    (historical2.YEAR == 2008) & (historical2.AGE >= SENIOR) & (historical2.AGE < TOTES)
)
year09over65 = (
    (historical2.YEAR == 2009) & (historical2.AGE >= SENIOR) & (historical2.AGE < TOTES)
)
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
POP_DEP = pd.concat([pd.DataFrame(pop_dep2), pd.DataFrame(pop_dep1), popdf])
popdf = pd.DataFrame(pop_projection[pop_projection.columns[66:]].sum(axis=1))
POP_SNR = pd.concat([pd.DataFrame(pop_snr2), pd.DataFrame(pop_snr1), popdf])
TOTAL_POP = pd.concat(
    [
        pd.DataFrame(total_pop2),
        pd.DataFrame(total_pop1.values.transpose()),
        pd.DataFrame(pop_projection.total_pop.values),
    ]
)

# create Stage_II_targets to store all targets used in stage2 logic
Stage_II_targets = pd.DataFrame(TOTAL_POP)
Stage_II_targets.columns = ["TOTAL_POP"]

# add number of dependents and number of seniors to Stage_II_targets
Stage_II_targets["POP_DEP"] = POP_DEP.values
Stage_II_targets["POP_SNR"] = POP_SNR.values

index = list(range(2008, EYR + 1))
Stage_II_targets.index = index

# calculate Stage_I_factors for population targets
APOPN = Stage_II_targets.TOTAL_POP / Stage_II_targets.TOTAL_POP[SYR]
Stage_I_factors = pd.DataFrame(APOPN, index=index)
Stage_I_factors.columns = ["APOPN"]
data = Stage_II_targets.POP_DEP / Stage_II_targets.POP_DEP[SYR]
Stage_I_factors["APOPDEP"] = pd.DataFrame(data, index=index)
data = Stage_II_targets.POP_SNR / Stage_II_targets.POP_SNR[SYR]
Stage_I_factors["APOPSNR"] = pd.DataFrame(data, index=index)

# specify yearly growth rates used in Stage I to create Stage_I_factors
pop_growth_rates = pd.DataFrame(Stage_II_targets.TOTAL_POP.pct_change() + 1.0)
pop_growth_rates["POPDEP"] = Stage_II_targets.POP_DEP.pct_change() + 1.0
pop_growth_rates["POPSNR"] = Stage_II_targets.POP_SNR.pct_change() + 1.0
pop_growth_rates = pop_growth_rates.drop(pop_growth_rates.index[0], axis=0)

# import CBO baseline projection
cbo_baseline = pd.read_csv(os.path.join(CUR_PATH, "CBO_baseline.csv"), index_col=0)
cbobase = cbo_baseline.transpose()
cbobase.index = index
cbobase = cbobase.astype(float)
Stage_I_factors["AGDPN"] = pd.DataFrame(cbobase.GDP / cbobase.GDP[SYR], index=index)
Stage_I_factors["ATXPY"] = pd.DataFrame(cbobase.TPY / cbobase.TPY[SYR], index=index)
Stage_I_factors["ASCHF"] = pd.DataFrame(cbobase.SCHF / cbobase.SCHF[SYR], index=index)
Stage_I_factors["ABOOK"] = pd.DataFrame(cbobase.BOOK / cbobase.BOOK[SYR], index=index)
Stage_I_factors["ACPIU"] = pd.DataFrame(cbobase.CPIU / cbobase.CPIU[SYR], index=index)
Stage_I_factors["ACPIM"] = pd.DataFrame(cbobase.CPIM / cbobase.CPIM[SYR], index=index)
cbo_growth_rates = cbobase.pct_change() + 1.0
cbo_growth_rates = cbo_growth_rates.drop(cbo_growth_rates.index[0], axis=0)

# read  IRS number-of-returns projection
irs_returns = pd.read_csv(
    os.path.join(CUR_PATH, "IRS_return_projection.csv"), index_col=0
)
irs_returns = irs_returns.transpose()
return_growth_rate = irs_returns.pct_change() + 1.0
vals = []
indicies = []
for year in range(IRS_RET_YR + 1, EYR + 1):
    vals.append(return_growth_rate.Returns[str(IRS_RET_YR)])
    indicies.append(str(year))
ret_growth_vals = pd.DataFrame({"Returns": vals}, index=indicies)
return_growth_rate = return_growth_rate.append(ret_growth_vals)
return_growth_rate.Returns.index = index

# read SOI estimates for 2008+
soi_estimates = pd.read_csv(os.path.join(CUR_PATH, "SOI_estimates.csv"), index_col=0)
soi_estimates = soi_estimates.transpose()
historical_index = list(range(2008, SOI_YR + 1))
soi_estimates.index = historical_index

# use yearly growth rates from Census, CBO, and IRS as blowup factors
return_projection = soi_estimates
for i in range(SOI_YR, EYR):  # SOI Estimates loop
    Single = return_projection.Single[i] * return_growth_rate.Returns[i + 1]
    Joint = return_projection.Joint[i] * return_growth_rate.Returns[i + 1]
    HH = return_projection.HH[i] * return_growth_rate.Returns[i + 1]
    SS_return = return_projection.SS_return[i] * pop_growth_rates.POPSNR[i + 1]
    Dep_return = return_projection.Dep_return[i] * pop_growth_rates.POPDEP[i + 1]
    INTS = return_projection.INTS[i] * cbo_growth_rates.INTS[i + 1]
    DIVS = return_projection.DIVS[i] * cbo_growth_rates.DIVS[i + 1]
    SCHCI = return_projection.SCHCI[i] * cbo_growth_rates.SCHC[i + 1]
    SCHCL = return_projection.SCHCL[i] * cbo_growth_rates.SCHC[i + 1]
    CGNS = return_projection.CGNS[i] * cbo_growth_rates.CGNS[i + 1]
    Pension = return_projection.Pension[i] * cbo_growth_rates.TPY[i + 1]
    SCHEI = return_projection.SCHEI[i] * cbo_growth_rates.BOOK[i + 1]
    SCHEL = return_projection.SCHEL[i] * cbo_growth_rates.BOOK[i + 1]
    SS = return_projection.SS[i] * cbo_growth_rates.SOCSEC[i + 1]
    UCOMP = return_projection.UCOMP[i] * cbo_growth_rates.UCOMP[i + 1]
    IPD = return_projection.IPD[i] * cbo_growth_rates.TPY[i + 1]
    Wage_1 = return_projection.WAGE_1[i] * cbo_growth_rates.Wages[i + 1]
    Wage_2 = return_projection.WAGE_2[i] * cbo_growth_rates.Wages[i + 1]
    Wage_3 = return_projection.WAGE_3[i] * cbo_growth_rates.Wages[i + 1]
    Wage_4 = return_projection.WAGE_4[i] * cbo_growth_rates.Wages[i + 1]
    Wage_5 = return_projection.WAGE_5[i] * cbo_growth_rates.Wages[i + 1]
    Wage_6 = return_projection.WAGE_6[i] * cbo_growth_rates.Wages[i + 1]
    Wage_7 = return_projection.WAGE_7[i] * cbo_growth_rates.Wages[i + 1]
    Wage_8 = return_projection.WAGE_8[i] * cbo_growth_rates.Wages[i + 1]
    Wage_9 = return_projection.WAGE_9[i] * cbo_growth_rates.Wages[i + 1]
    Wage_10 = return_projection.WAGE_10[i] * cbo_growth_rates.Wages[i + 1]
    Wage_11 = return_projection.WAGE_11[i] * cbo_growth_rates.Wages[i + 1]
    Wage_12 = return_projection.WAGE_12[i] * cbo_growth_rates.Wages[i + 1]

    current_year = pd.DataFrame(
        [
            Single,
            Joint,
            HH,
            SS_return,
            Dep_return,
            INTS,
            DIVS,
            SCHCI,
            SCHCL,
            CGNS,
            Pension,
            SCHEI,
            SCHEL,
            SS,
            UCOMP,
            IPD,
            Wage_1,
            Wage_2,
            Wage_3,
            Wage_4,
            Wage_5,
            Wage_6,
            Wage_7,
            Wage_8,
            Wage_9,
            Wage_10,
            Wage_11,
            Wage_12,
        ]
    )
    current_year = current_year.transpose()

    current_year.columns = return_projection.columns
    current_year.index = [i + 1]
    return_projection = return_projection.append(current_year)

# combine historical data with the newly blownup data
Stage_II_targets = pd.concat([Stage_II_targets, return_projection], axis=1)

# create all the rest of the Stage_I_factors
data = Stage_II_targets[Stage_II_targets.columns[3:6]].sum(axis=1)
total_return = pd.DataFrame(data, columns=["ARETS"])

data = Stage_II_targets[Stage_II_targets.columns[19:31]].sum(axis=1)
total_wage = pd.DataFrame(data, columns=["AWAGE"])

Stage_I_factors["ARETS"] = total_return / total_return.ARETS[SYR]

Stage_I_factors["AWAGE"] = total_wage / total_wage.AWAGE[SYR]

Stage_I_factors["ASCHCI"] = Stage_II_targets.SCHCI / Stage_II_targets.SCHCI[SYR]
Stage_I_factors["ASCHCL"] = Stage_II_targets.SCHCL / Stage_II_targets.SCHCL[SYR]

Stage_I_factors["ASCHEI"] = Stage_II_targets.SCHEI / Stage_II_targets.SCHEI[SYR]
Stage_I_factors["ASCHEL"] = Stage_II_targets.SCHEL / Stage_II_targets.SCHEL[SYR]

Stage_I_factors["AINTS"] = Stage_II_targets.INTS / Stage_II_targets.INTS[SYR]
Stage_I_factors["ADIVS"] = Stage_II_targets.DIVS / Stage_II_targets.DIVS[SYR]
Stage_I_factors["ACGNS"] = Stage_II_targets.CGNS / Stage_II_targets.CGNS[SYR]

Stage_I_factors["ASOCSEC"] = Stage_II_targets.SS / Stage_II_targets.SS[SYR]
Stage_I_factors["AUCOMP"] = Stage_II_targets.UCOMP / Stage_II_targets.UCOMP[SYR]
Stage_I_factors["AIPD"] = Stage_II_targets.IPD / Stage_II_targets.IPD[SYR]

# Add benefit growth rates to Stage 1 factors
benefit_programs = pd.read_csv(
    os.path.join(CUR_PATH, "../taxdata/cps/benefitprograms.csv"), index_col="Program"
)
benefit_sums = benefit_programs[benefit_programs.columns[2:]].apply(sum)
# Find growth rate between 2020 and 2021 and extrapolate out to EYR
gr = benefit_sums["2021_cost"] / float(benefit_sums["2020_cost"])
for year in range(2022, EYR + 1):
    prev_year = year - 1
    prev_value = benefit_sums["{}_cost".format(prev_year)]
    benefit_sums["{}_cost".format(year)] = prev_value * gr
ABENEFITS = (benefit_sums / benefit_sums["{}_cost".format(BEN_SYR)]).transpose()
benefit_factors = pd.DataFrame()
for year in range(SYR, EYR + 1):
    if year <= BEN_SYR:
        benefit_factors[year] = [1.0]
    else:
        benefit_factors[year] = ABENEFITS["{}_cost".format(year)]

Stage_II_targets = Stage_II_targets.drop("IPD", axis=1)
# rename Stage_II_targets index
rename = {
    "TOTAL_POP": "US Population",
    "Single": "Single Returns",
    "Joint": "Joint Returns",
    "HH": "Head of Household Returns",
    "SS_return": "Number of Returns w/ Gross Security Income",
    "Dep_return": "Number of Dependent Exemptions",
    "INTS": "Taxable Interest Income",
    "DIVS": "Ordinary Dividends",
    "SCHCI": "Business Income (Schedule C)",
    "SCHCL": "Business Loss (Schedule C)",
    "CGNS": "Net Capital Gains in AGI",
    "Pension": "Taxable Pensions and Annuities",
    "SCHEI": "Supplemental Income (Schedule E)",
    "SCHEL": "Supplemental Loss (Schedule E)",
    "SS": "Gross Social Security Income",
    "UCOMP": "Unemployment Compensation",
    "WAGE_1": "Wages and Salaries: Zero or Less",
    "WAGE_2": "Wages and Salaries: $1 Less Than $10,000",
    "WAGE_3": "Wages and Salaries: $10,000 Less Than $20,000",
    "WAGE_4": "Wages and Salaries: $20,000 Less Than $30,000",
    "WAGE_5": "Wages and Salaries: $30,000 Less Than $40,000",
    "WAGE_6": "Wages and Salaries: $40,000 Less Than $50,000",
    "WAGE_7": "Wages and Salaries: $50,000 Less Than $75,000",
    "WAGE_8": "Wages and Salaries: $75,000 Less Than $100,000",
    "WAGE_9": "Wages and Salaries: $100,000 Less Than $200,000",
    "WAGE_10": "Wages and Salaries: $200,000 Less Than $500,000",
    "WAGE_11": "Wages and Salaries: $500,000 Less Than $1 Million",
    "WAGE_12": "Wages and Salaries: $1 Million and Over",
}
Stage_II_targets.rename(columns=rename, inplace=True)

# Delate 2008 row from Stage_I_factors
Stage_I_factors = Stage_I_factors.drop([2008, 2009, 2010])
Stage_II_targets = Stage_II_targets.drop([2008, 2009, 2010])

# add on benefit factors
Stage_I_factors["ABENEFITS"] = benefit_factors.transpose()[0]

# write Stage_I_factors for final preparation and then use by Tax-Calculator
Stage_I_factors.to_csv(
    os.path.join(CUR_PATH, "Stage_I_factors.csv"),
    float_format="%.4f",
    index_label="YEAR",
)

# write Stage_II_targets for use in stage2 weights calculation
Stage_II_targets = Stage_II_targets.transpose()
Stage_II_targets.to_csv(
    os.path.join(CUR_PATH, "Stage_II_targets.csv"), float_format="%.0f"
)
