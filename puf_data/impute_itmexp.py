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
    logit_res = sm.Logit(logit_y, logit_x).fit(disp=0)
    prob = logit_res.predict(nonitemizer_data[logit_x_vars])
    np.random.seed(int(ievar[1:]))
    urn = np.random.uniform(size=len(prob))
    positive_imputed = np.where(urn <= prob, True, False)
    if dump1:
        print logit_res.summary()
        print prob.head()
        print positive_imputed.mean()
        print len(nonitemizer_data)
    # estimate OLS parameters for the positive amount using a sample of
    # itemizers who have positive ievar amounts than are less than the
    # itemizer's standard deduction amount
    # (1) This sample limitation is one part of an ad hoc procedure to deal
    # with the Heckman sample selection problems present in this imputation
    # process.
    tpi_data = itemizer_data[(itemizer_data[ievar] > 0) &
                             (itemizer_data[ievar] < itemizer_data['stdded'])]
    ols_y = np.log(tpi_data[ievar])
    ols_x = tpi_data[ols_x_vars]
    ols_res = sm.OLS(ols_y, ols_x).fit()
    ols_se = np.sqrt(ols_res.scale)
    error = np.random.normal(loc=0.0, scale=ols_se,
                             size=len(nonitemizer_data))
    raw_imputed_amt = ols_res.predict(nonitemizer_data[ols_x_vars]) + error
    # (2) Limiting the imputed amount to be no more than the standard
    # deduction is a second part of the ad hoc procedure to deal with the
    # Heckman sample selection problems present in this imputation process.
    log_stdded = np.log(nonitemizer_data['stdded'])
    capped_imputed_amt = np.where(raw_imputed_amt > log_stdded,
                                  log_stdded, raw_imputed_amt)
    adj_imputed_amt = capped_imputed_amt
    imputed_amount = np.where(positive_imputed,
                              np.exp(adj_imputed_amt).round().astype(int), 0)
    if dump1:
        print 'size of {} OLS sample = {}'.format(ievar, len(ols_y))
        print 'max {} value = {}'.format(ievar, ols_y.max())
        print 'avg {} value = {:.2f}'.format(ievar, ols_y.mean())
        print ols_res.summary()
        print 'OLS std error of regression = {:.2f}'.format(ols_se)
        print 'size(nonitemizer_data)=', len(nonitemizer_data)
        print 'size(imputed_amount)=', len(imputed_amount)
        print 'mean imputed_amount = {:.2f}'.format(imputed_amount.mean())
    # insert imputed_amount into nonitemizer_data
    nonitemizer_data.loc[:, ievar] = imputed_amount
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
data['stdded'] = data.apply(standard_deduction, axis=1)
data['sum_itmexp'] = data[iev_names].sum(axis=1)
data['itemizer'] = np.where(data['sum_itmexp'] > data['stdded'], 1, 0)
data['constant'] = 1

# separate all the data into data for itemizers and data for nonitemizers
itemizer_data = data[data['itemizer'] == 1].copy()
nonitemizer_data = data[data['itemizer'] == 0].copy()
    
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
nonitemizer_data['g20500'] = 0
for iev in iev_names:
    if iev == 'g20500':
        continue  # to next loop iteration
    if iev != 'e18400':  # TODO: debugging statement that needs to be removed
        continue
    nonitemizer_data[iev] = impute(iev, ['constant'], ['constant'],
                                   itemizer_data, nonitemizer_data)

# set imputed itmexp variable values in alldata
combined_data = pd.concat([nonitemizer_data, itemizer_data]).sort_index()
for iev in iev_names:
    alldata[iev] = combined_data[iev]

# write augmented puf-new.csv file
alldata.to_csv('puf-new.csv', index=False, float_format='%.2f')
