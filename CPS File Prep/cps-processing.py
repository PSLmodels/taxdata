import pandas as pd
import numpy as np

# Import production file
data = pd.read_csv('prod2015_v2e.csv')

# Rename variables where possible
renames = {
    'IFDEPT': 'DSI',
    'TAXYEAR': 'FLPDYR',
    'XXTOT': 'XTOT',
    'JCPS21': 'e00200p',
    'JCPS31': 'e00200s',
    'ALIMONY': 'e00800',
    'JCPS25': 'e00900p',
    'JCPS35': 'e00900s',
    'JCPS28': 'e02100p',
    'JCPS38': 'e02100s',
    'UCOMP': 'e02300',
    'SOCSEC': 'e02400',
    'SEHEALTH': 'e03270',
    'DPAD': 'e03240',
    'MEDICALEXP': 'e17500',
    'REALEST': 'e18500',
    'MISCITEM': 'e20400',
    'CCE': 'e32800',
    'ICPS01': 'age_head',
    'ICPS02': 'age_spouse',
    'WT': 's006',
    'FILST': 'filer',
    'SEQUENCE': 'RECID',
    'PENSIONS': 'e01700',
    'DBE': 'e00600',
    'KEOGH': 'e03300',
    'TIRAD': 'e01400'
}

data = data.rename(columns=renames)

# Adjust MARS to address lack of married filing separately status
# 1 = Single filers
# 2 = Married filing jointly
# 4 = Head of household
data['MARS'] = np.where(data.JS == 3, 4, data.JS)

# Use primary taxpayer and spouse records to get total tax unit earnings
data['e00200'] = data.e00200p + data.e00200s
data['e00900'] = data.e00900p + data.e00900s
data['e02100'] = data.e02100p + data.e02100s

# Impute variables where possible

# Determine amount of qualified dividends using IRS ratio
data['e00650'] = data.e00600 * 0.7556

# Split interest income into taxable and tax exempt using IRS ratio
taxable = 0.6
nontaxable = 1. - taxable
data['e00300'] = data.INTST * taxable
data['e00400'] = data.INTST * nontaxable

# Apply charitable deduction limit
halfAGI = (data.JCPS9 + data.JCPS19) * 0.5
charity = np.where(data.CHARITABLE > halfAGI,
                   halfAGI, data.CHARITABLE)
# Split charitable giving into cash and non-cash using ratio in PUF
cash = 0.82013
non_cash = 1. - cash
data['e19800'] = charity * cash
data['e20100'] = charity * non_cash

# Apply student loan interest deduction limit
data['e03210'] = np.where(data.SLINT > 2500, 2500, data.SLINT)

# Apply IRA contribution limits
deductibleIRA = np.where(data.AGE >= 50,
                         np.where(data.ADJIRA > 6500, 6500, data.ADJIRA),
                         np.where(data.ADJIRA > 5500, 5500, data.ADJIRA))
data['e03150'] = deductibleIRA

# Count number of dependents under 13
# Max of four to match PUF version of nu13
age1 = np.where((data.ICPS03 > 0) & (data.ICPS03 <= 13), 1, 0)
age2 = np.where((data.ICPS04 > 0) & (data.ICPS04 <= 13), 1, 0)
age3 = np.where((data.ICPS05 > 0) & (data.ICPS05 <= 13), 1, 0)
age4 = np.where((data.ICPS06 > 0) & (data.ICPS06 <= 13), 1, 0)
nu13 = age1 + age2 + age3 + age4
data['nu13'] = nu13

# Count number of dependents under 5
age1 = np.where((data.ICPS03 > 0) & (data.ICPS03 <= 5), 1, 0)
age2 = np.where((data.ICPS04 > 0) & (data.ICPS04 <= 5), 1, 0)
age3 = np.where((data.ICPS05 > 0) & (data.ICPS05 <= 5), 1, 0)
age4 = np.where((data.ICPS06 > 0) & (data.ICPS06 <= 5), 1, 0)
age5 = np.where((data.ICPS07 > 0) & (data.ICPS06 <= 5), 1, 0)
nu05 = age1 + age2 + age3 + age4 + age5
data['nu05'] = nu05

# Count number of children eligible for child tax credit
# Max of three to mach PUF version of n24
age1 = np.where((data.ICPS03 > 0) & (data.ICPS03 <= 17), 1, 0)
age2 = np.where((data.ICPS04 > 0) & (data.ICPS04 <= 17), 1, 0)
age3 = np.where((data.ICPS05 > 0) & (data.ICPS05 <= 17), 1, 0)
n24 = age1 + age2 + age3
data['n24'] = n24

# Count number of elderly dependents
age1 = np.where(data.ICPS03 >= 65, 1, 0)
age2 = np.where(data.ICPS04 >= 65, 1, 0)
age3 = np.where(data.ICPS05 >= 65, 1, 0)
age4 = np.where(data.ICPS06 >= 65, 1, 0)
age5 = np.where(data.ICPS07 >= 65, 1, 0)
elderly = age1 + age2 + age3 + age4 + age5
data['elderly_dependent'] = elderly

# List of usable variables in TaxCalc
USABLE_READ_VARS = [
        'DSI', 'EIC', 'FLPDYR',
        'f2441', 'f6251', 'n24', 'XTOT',
        'e00200', 'e00300', 'e00400', 'e00600', 'e00650', 'e00700', 'e00800',
        'e00200p', 'e00200s',
        'e00900', 'e01100', 'e01200', 'e01400', 'e01500', 'e01700',
        'e00900p', 'e00900s',
        'e02000', 'e02100', 'e02300', 'e02400', 'e03150', 'e03210',
        'e02100p', 'e02100s',
        'e03220', 'e03230', 'e03270', 'e03240', 'e03290',
        'e03400', 'e03500',
        'e07240', 'e07260', 'e07300',
        'e07400', 'e07600', 'p08000',
        'e09700', 'e09800', 'e09900',
        'e11200',
        'e17500', 'e18400', 'e18500',
        'e19200', 'e19800', 'e20100',
        'e20400', 'e20500', 'p22250',
        'p23250', 'e24515', 'e24518',
        'p25470',
        'e26270',
        'e27200', 'e32800', 'e03300',
        'e58990',
        'e62900',
        'p87521', 'e87530',
        'MARS', 'MIDR', 'RECID', 'filer',
        'cmbtp_standard', 'cmbtp_itemizer',
        'age_head', 'age_spouse', 'blind_head', 'blind_spouse',
        'nu13', 'elderly_dependent',
        's006', 'nu05']

# Remove unnecessary variables
drop_vars = []
var_list = list(data.columns)
for item in var_list:
    if item not in USABLE_READ_VARS:
        drop_vars.append(item)
data.drop(drop_vars, axis=1, inplace=True)
data.fillna(0, inplace=True)

# Write processed file to a CSV
data.to_csv('cps.csv', index=False)
