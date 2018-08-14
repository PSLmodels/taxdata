"""
Script that imputes itemized expense amounts to non-itemizers in puf.csv file.
"""
import numpy as np
import pandas as pd
import statsmodels as sm


dump = True


# read in puf-new.csv file
alldata = pd.read_csv('puf-new.csv')

# specify variable names of itemized-expense variables
iev_names = ['e17500',  # medical expenses
             'e18400',  # state and local taxes
             'e18500',  # real-estate taxes
             'e19200',  # interest paid
             'e19800',  # charity cash contributions
             'e20100',  # charity non-cash contributions
             'e20400',  # misc itemizable expenses
             'g20500']  # gross casualty/theft loss

def standard_deduction(row):
    """
    Specifies 2011 standard deduction amount by MARS
    """
    if row['MARS'] == 1 :
        return 5800   # single
    elif row['MARS'] == 2:
        return 11600  # married filing jointly
    elif row['MARS'] == 3:
        return 5800   # married filing separately
    elif row['MARS'] == 4:
        return 8500   # head of household
    else:
        raise ValueError('illegal value of MARS')

# extract selected variables and construct new variables
varnames = iev_names + ['MARS', 'inPUF', 'filer']
data = alldata[varnames]
pd.set_option('mode.chained_assignment', None)
data['stdded'] = data.apply(standard_deduction, axis=1)
data['sum_itmexp'] = data[iev_names].sum(axis=1)
data['itemizer'] = np.where(data['sum_itmexp'] > data['stdded'], 1, 0)
pd.reset_option('mode.chained_assignment')

# descriptive statistics for the data variables
if dump:
    diff = data['filer'] != data['inPUF']
    print 'ALL diff number {}'.format(diff.sum())
    del diff
    print 'ALL inPUF mean {:.4f}'.format(data['inPUF'].mean())
    ier = data['itemizer']
    print 'ALL itemizer mean {:.4f}'.format(ier.mean())
    print 'PUF itemizer mean {:.4f}'.format(ier[data['inPUF'] == 1].mean())
    print 'CPS itemizer mean {:.4f}'.format(ier[data['inPUF'] == 0].mean())
    del ier
    for iev in iev_names:
        var = data[iev]
        varpos = var > 0
        print 'fraction with positive {} is {:.4f}'.format(iev, varpos.mean())

# set itmexp variable values in alldata
# TODO: add code here

# write augmented puf-new-plus.csv file
data.to_csv('puf-new-plus.csv', index=False, float_format='%.2f')
