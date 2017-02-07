"""
Transform Stage_I_factors.csv (written by stage1.py)
into growfactors.csv (used by Tax-Calculator)
"""

import pandas as pd

# pylint: disable=invalid-name
first_data_year = 2009
input_filename = 'Stage_I_factors.csv'
output_filename = 'growfactors.csv'

# read in blowup factors used internally in taxdata repository
data = pd.read_csv(input_filename, index_col='YEAR')

# convert some aggregate factors into per-capita factors
elderly_pop = data['APOPSNR']
data['ASOCSEC'] = data['ASOCSEC'] / elderly_pop
pop = data['APOPN']
data['AWAGE'] = data['AWAGE'] / pop
data['ATXPY'] = data['ATXPY'] / pop
data['ASCHCI'] = data['ASCHCI'] / pop
data['ASCHCL'] = data['ASCHCL'] / pop
data['ASCHF'] = data['ASCHF'] / pop
data['AINTS'] = data['AINTS'] / pop
data['ADIVS'] = data['ADIVS'] / pop
data['ASCHEI'] = data['ASCHEI'] / pop
data['ASCHEL'] = data['ASCHEL'] / pop
data['ACGNS'] = data['ACGNS'] / pop
data['ABOOK'] = data['ABOOK'] / pop
data['AGDPN'] = data['AGDPN'] / pop  # TODO: remove line after Growth redesign

# convert factors into "one plus annual proportion change" format
data = 1.0 + data.pct_change()

# specify first row values because pct_change() leaves first year undefined
# (these values have been transferred from Tax-Calculator records.py)
for var in list(data):
    data[var][first_data_year] = 1.0
data['ACGNS'][first_data_year] = 1.1781
data['ADIVS'][first_data_year] = 1.0606
data['AINTS'][first_data_year] = 1.0357
data['ASCHCI'][first_data_year] = 1.0041
data['ASCHCL'][first_data_year] = 1.1629
data['ASCHEI'][first_data_year] = 1.1089
data['ASCHEL'][first_data_year] = 1.2953
data['AUCOMP'][first_data_year] = 1.0034
data['AWAGE'][first_data_year] = 1.0053

# round converted factors to six decimal digits of accuracy
data = data.round(6)

# delete from data variables not used by Tax-Calculator (TC)
TC_USED_VARS = set(['ABOOK',
                    'ACGNS',
                    'ACPIM',
                    'ACPIU',
                    'ADIVS',
                    'AGDPN',  # TODO: remove this line after Growth redesign
                    'AINTS',
                    'AIPD',
                    'APOPN',  # TODO: remove this line after Growth redesign
                    'ASCHCI',
                    'ASCHCL',
                    'ASCHEI',
                    'ASCHEL',
                    'ASCHF',
                    'ASOCSEC',
                    'ATXPY',
                    'AUCOMP',
                    'AWAGE'])
ALL_VARS = set(list(data))
TC_UNUSED_VARS = ALL_VARS - TC_USED_VARS
data = data.drop(TC_UNUSED_VARS, axis=1)

# write out blowup factors used in Tax-Calculator repository
data.to_csv(output_filename, index='YEAR')
