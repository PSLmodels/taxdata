"""
Script that imputes itemized expense amounts to non-itemizers in puf.csv file.
"""
import numpy as np
import pandas as pd
import statsmodels as sm


dump = True


# read in puf.csv file
alldata = pd.read_csv('puf.csv')

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
varnames = iev_names + ['MARS', 'filer']
data = alldata[varnames]
pd.set_option('mode.chained_assignment', None)
data['stdded'] = data.apply(standard_deduction, axis=1)
data['sum_itmexp'] = data[iev_names].sum(axis=1)
data['itemizer'] = np.where(data['sum_itmexp'] > data['stdded'], 1, 0)
pd.reset_option('mode.chained_assignment')

# descriptive statistics for the data variables
if dump:
    print 'ALL filer mean {:.4f}'.format(data['filer'].mean())
    ier = data['itemizer']
    print 'ALL itemizer mean {:.4f}'.format(ier.mean())
    print 'PUF itemizer mean {:.4f}'.format(ier[data['filer'] == 1].mean())
    print 'CPS itemizer mean {:.4f}'.format(ier[data['filer'] == 0].mean())
    ier_data = data[data['itemizer'] == 1]
    for iev in iev_names:
        var = ier_data[iev]
        varpos = var > 0
        print 'frac of itemizers with {}>0 = {:.4f}'.format(iev,
                                                            varpos.mean())
    del ier_data
    nonier_data = data[data['itemizer'] == 0]
    for iev in iev_names:
        var = nonier_data[iev]
        varpos = var > 0
        print 'frac of non-itemizers with {}>0 = {:.4f}'.format(iev,
                                                                varpos.mean())
    del nonier_data


# set imputed itmexp variable values in alldata
# TODO: add code here to update alldata

# write augmented puf-new.csv file
alldata.to_csv('puf-new.csv', index=False, float_format='%.2f')
