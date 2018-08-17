"""
Script that imputes itemized expense amounts to non-itemizers in puf.csv file.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm


dump0 = True
dump1 = True


def impute(ievar, logit_x_vars, ols_x_vars,
           itemizer_data, nonitemizer_data):
    """
    Function that estimates imputation equations for ievar using itemizer_data
    using the lists of exogenous variables in logit_x_vars and ols_x_vars.
    The estimated equations are then used to impute amounts for ievar for
    nonitemizers with the imputed nonitemizer amounts being added to the
    nonitemizer_data structure, which is returned by this function.
    """
    if dump1:
        print '*** IMPUTE({}):'.format(ievar)
    # estimate Logit parameters for probability of having a positive amount
    logit_y = (itemizer_data[ievar] > 0).astype(int)
    logit_x = itemizer_data[logit_x_vars]
    logit_res = sm.Logit(logit_y, logit_x).fit()
    if dump1:
        print logit_res.summary()
        prob = logit_res.predict(nonitemizer_data[logit_x_vars])
        print prob.head()
    """
    # estimate OLS parameters for the positive amount
    pos_itemizer_data = itemizer_data[itemizer_data[ievar] > 0]
    ols_y = pos_itemizer_data[ievar]
    ols_x = pos_itemizer_data[ols_x_vars]
    ols_res = sm.OLS(ols_y, ols_x).fit()
    if dump1:
        print 'num of positive {} values = {}'.format(ievar, len(ols_y.index))
        print 'max {} value = {}'.format(ievar, ols_y.max())
        large = 1e6
        num_large = (ols_y > large).sum()
        print 'num {} values > {} = {}'.format(ievar, large, num_large)
        print 'avg {} value = {:.0f}'.format(ievar, ols_y.mean())
        exit(1)
        #print "STARTING SUMMARY"
        print ols_res.summary()
        #print "FINISHING SUMMARY"
        print ols_y.head()
        print ols_res.resid.round().head()
        #amt = ols_res.predict(nonitemizer_data[logit_x_vars])
        #print amt.head()
    """
    return nonitemizer_data


# read in puf.csv file
alldata = pd.read_csv('puf.csv')

# specify variable names of itemized-expense variables
iev_names = ['e18400',  # state and local taxes
             'e18500',  # real-estate taxes
             'e19200',  # interest paid
             'e19800',  # charity cash contributions
             'e20100',  # charity non-cash contributions
             'e20400',  # misc itemizable expenses
             'e17500',  # medical expenses
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
data = alldata[varnames].copy()
# pd.set_option('mode.chained_assignment', None)
data['stdded'] = data.apply(standard_deduction, axis=1)
data['sum_itmexp'] = data[iev_names].sum(axis=1)
data['itemizer'] = np.where(data['sum_itmexp'] > data['stdded'], 1, 0)
data['constant'] = 1
# pd.reset_option('mode.chained_assignment')

# separate all the data into data for itemizers and data for nonitemizers
itemizer_data = data[data['itemizer'] == 1]
nonitemizer_data = data[data['itemizer'] == 0]
    
# descriptive statistics for the data variables
if dump0:
    print 'ALL raw count = {:6d}'.format(len(data.index))
    print 'PUF raw count = {:6d}'.format(len(data[data['filer'] == 1].index))
    print 'CPS raw count = {:6d}'.format(len(data[data['filer'] == 0].index))
    print 'PUF fraction of ALL = {:.4f}'.format(data['filer'].mean())
    ier = data['itemizer']
    print 'ALL itemizer mean = {:.4f}'.format(ier.mean())
    print 'PUF itemizer mean = {:.4f}'.format(ier[data['filer'] == 1].mean())
    print 'CPS itemizer mean = {:.4f}'.format(ier[data['filer'] == 0].mean())
    for iev in iev_names:
        var = itemizer_data[iev]
        varpos = var > 0
        print '{} with {}>0 = {:.4f}  {:.2f}'.format(
            'frac and mean for itemizers',
            iev, varpos.mean(), var[varpos].mean()
        )
    for iev in iev_names:
        var = nonitemizer_data[iev]
        varpos = var > 0
        print 'frac of non-itemizers with {}>0 = {:.4f}'.format(iev,
                                                                varpos.mean())
# estimate itemizer equations & use to impute itmexp amounts for nonitemizers
for iev in iev_names:
    if iev == 'e18400':  # TODO: remove this debugging statement
        nonitemizer_data = impute(iev, ['constant'], ['constant'],
                                  itemizer_data, nonitemizer_data)

# set imputed itmexp variable values in alldata
# TODO: ... add code here to update alldata

# write augmented puf-new.csv file
# TODO: ... alldata.to_csv('puf-new.csv', index=False, float_format='%.2f')
