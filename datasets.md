# TaxData Documentation

TaxData is an open source library used to prepare micro-data for [Tax-Calculator](https://github.com/PSLmodels/Tax-Calculator),
a microsimulation tax model. This document details the process we create the
datasets. It contains the following sections:

1. [Summary](#Summary)
2. [PUF](#PUF)
3. [CPS](#CPS)

## Summary

TaxData offers two datasets created to run in Tax-Calculator:
`PUF.csv` and `CPS.csv`. Both files are representative micro-datasets containing
tax unit level data. The key differences are the sources used to create each file
and the aggregate results and distributions.

The PUF is created using a statistical match between the
IRS-SOI Public Use File and the Census Current Population Survey. The use of
IRS-SOI data is restricted and therefore we cannot provide access to them to
the general public.

The CPS is created using the Census Current Population Survey, Annual Social
and Economic Supplement data for March 2013, 2014, and 2015. Household and family
information from the surveys are used to create tax units based on income and
relationship data. Because the CPS is not designed for tax reporting purposes,
results from constructed tax units are expected to be different from PUF in
term of both aggregates and distributions. In addition, the CPS includes very
limited data on high income households and has under-coverage issues in lower income
households. Therefore, the wage distribution of CPS is different from that of PUF.
Additional data on welfare and transfer program participation and benefits is
added to the CPS using the open source CPS Transfer Augmentation Model (C-TAM).
C-TAM is used to impute benefit values for SNAP, SSI, Social Security,
Medicare, Medicaid, veterans benefits, housing assistance, TANF, and WIC.

### Variable Availability

Because benefit data is imputed onto the CPS, it is not available in the PUF.
Similarly, the CPS is missing some income and deduction variables only available
in the PUF.

A full list of variables available in each file can be found
[here](https://pslmodels.github.io/Tax-Calculator/#input). The
availability of each variable is specified in the _availability_ section. PUF
availability is indicated by `taxdata_puf`, CPS availability by `taxdata_cps`.

Due to missing variables, certain policy parameters will be ineffective depending
on which file you're using. These will be greyed out in TaxBrain. The policy
parameters available in Tax-Calculator can be found in
[here](https://pslmodels.github.io/Tax-Calculator/#pol). The
dataset(s) compatible with each parameter are indicated by true/false values in
the _Has An Effect When Using_ section.

### Aggregate Totals

The weighted totals of each variable will differ between the two datasets.
Totals by year for the CPS can be found [here](https://github.com/open-source-economics/Tax-Calculator/blob/master/taxcalc/tests/cpscsv_agg_expect.txt).
For the PUF, [here](https://github.com/open-source-economics/Tax-Calculator/blob/master/taxcalc/tests/pufcsv_agg_expect.txt).

## PUF

`puf.csv` (PUF) is created by combining the 2011 IRS-SOI Public Use File and the
2016 Current Population Annual Social and Economic Supplement using a statistical
matching technique. The code used to generate `puf.csv` and its associated files
can be found in the various `puf_*` directories. Because use of the IRS-SOI file
is restricted, we cannot share it with the general public.

### Input files

* [2016 Current Population Annual Social and Economic Supplement](https://www.nber.org/data/current-population-survey-data.html)
* [2011 IRS-SOI Public Use File](https://www.irs.gov/statistics/soi-tax-stats-individual-public-use-microdata-files)

## Data Limitations and Clarifications

As with all datasets, the PUF has some limitations that we are aware of. As we
more are discovered we will add them to this section.

### Mortgage Interest Expense and Investment Interest

These two deductions have been folded into a general "interest paid deduction"
variable. Unfortunately there is not currently any way to separate them.

### Claiming Dependent Filers

There is no way to link dependent filers in the PUF with the tax unit that is
claiming them as a dependent. This should be accounted for when performing tasks
such as calculating average income.

### State, Local, and Real Estate Taxes

The PUF includes two variables that encompass some aspect of state and local
taxes: `e18400` includes either state and local income taxes or state and local
general sales taxes. `e18500` includes all state, local, and foreign taxes on
real estate. There is no way to separate the exact sources of those real estate
taxes.

## CPS

`cps.csv` (CPS) is created by forming tax units out of the 2013, 2014, and 2015
Current Population Annual Social and Economic Supplement.
Household and family information from the surveys are used to create tax units
based on income and relationship data. Because the CPS is not designed
for tax reporting purposes, results from constructed tax units are expected
to be different from those in the PUF in terms of both aggregates and distribution.
Additional data on imputed benefits receipts are merged onto all three CPS
files before the tax units are formed. These imputations are performed by the
open source CPS Transfer Augmentation Model (C-TAM).

### Input Files

* [2013 Current Population Annual Social and Economic Supplement](https://www.nber.org/data/current-population-survey-data.html)
* [2014 Current Population Annual Social and Economic Supplement](https://www.nber.org/data/current-population-survey-data.html)
* [2015 Current Population Annual Social and Economic Supplement](https://www.nber.org/data/current-population-survey-data.html)

### Data Limitations

As previously stated, the CPS was not intended for tax policy analysis. Thus,
we do see less reliable data on income, particularly at the extreme ends of the
spectrum.