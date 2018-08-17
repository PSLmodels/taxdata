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
    Function that estimates imputation equations for ievar with itemizer_data
    using the lists of exogenous variables in logit_x_vars and ols_x_vars.
    The estimated equations are then used to impute amounts for ievar for
    nonitemizers with the imputed nonitemizer amounts being inserted into the
    nonitemizer_data structure, which is returned by this function.
    """
    if dump1:
        print '*** IMPUTE({}):'.format(ievar)
    # estimate Logit parameters for probability of having a positive amount
    logit_y = (itemizer_data[ievar] > 0).astype(int)
    logit_x = itemizer_data[logit_x_vars]
    logit_res = sm.Logit(logit_y, logit_x).fit()
    prob = logit_res.predict(nonitemizer_data[logit_x_vars])
    np.random.seed(len(prob))
    urn = np.random.uniform(size=len(prob))
    positive_imputed = np.where(urn <= prob, True, False)
    if dump1:
        print logit_res.summary()
        print prob.head()
        print positive_imputed.mean()
    # estimate OLS parameters for the positive amount using a sample of
    # itemizers who have positive ievar amounts than are less than the
    # itemizer's standard deduction amount
    # (This approach is part of an ad hoc procedure to deal with the
    # Heckman sample selection problems present in this imputation process.)
    tpi_data = itemizer_data[(itemizer_data[ievar] > 0) &
                             (itemizer_data[ievar] < itemizer_data['stdded'])]
    ols_y = tpi_data[ievar]
    ols_x = tpi_data[ols_x_vars]
    ols_res = sm.OLS(ols_y, ols_x).fit()
    pini_data = nonitemizer_data[positive_imputed]
    positive_amt = ols_res.predict(pini_data[ols_x_vars])
    if dump1:
        print 'size of {} OLS sample = {}'.format(ievar, len(ols_y))
        print 'max {} value = {}'.format(ievar, ols_y.max())
        print 'avg {} value = {:.0f}'.format(ievar, ols_y.mean())
        #print "STARTING SUMMARY"
        print ols_res.summary()
        #print "FINISHING SUMMARY"
        #print ols_y.head()
        #print ols_res.resid.round().head()
        print len(pini_data)
        print len(positive_amt)
        print pini_data['constant'][0:9]
        print positive_amt[0:9]
        """
123727
123727
2     1
3     1
4     1
6     1
7     1
8     1
10    1
11    1
12    1
Name: constant, dtype: int64
2     3596.160528
3     3596.160528
4     3596.160528
6     3596.160528
7     3596.160528
8     3596.160528
10    3596.160528
11    3596.160528
12    3596.160528
dtype: float64
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
    print 'ALL raw count = {:6d}'.format(len(data))
    print 'PUF raw count = {:6d}'.format(len(data[data['filer'] == 1]))
    print 'CPS raw count = {:6d}'.format(len(data[data['filer'] == 0]))
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